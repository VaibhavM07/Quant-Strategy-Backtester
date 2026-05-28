import os
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from fyers_apiv3 import fyersModel


TOKEN_DIR = os.path.dirname(os.path.abspath(__file__))


class login_module:
    """
    Handles Fyers authentication with daily token caching.

    Flow:
        1. Check if today's access token exists in TOKEN_FILE.
        2. If yes, reuse it — no browser login needed.
        3. If no, generate auth URL, user opens it, logs in, pastes the
           redirect URL back; auth_code is extracted automatically.
        4. Token is saved to disk keyed by today's date.
    """

    def __init__(self, client_id: str, secret_key: str, redirect_url: str,
                 token_file: str = "access_token.json"):
        self.client_id = client_id
        self.secret_key = secret_key
        self.redirect_url = redirect_url
        self.token_path = os.path.join(TOKEN_DIR, token_file)

        self.access_token = self._load_or_generate_token()
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id,
            token=self.access_token,
            is_async=False,
            log_path=TOKEN_DIR,
        )

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _load_or_generate_token(self) -> str:
        today = datetime.today().strftime("%Y-%m-%d")

        if os.path.exists(self.token_path):
            with open(self.token_path) as f:
                cached = json.load(f)
            if cached.get("date") == today:
                print("[Auth] Using cached access token.")
                return cached["access_token"]

        return self._generate_token(today)

    def _generate_token(self, today: str) -> str:
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_url,
            response_type="code",
            state="trading_session",
            grant_type="authorization_code",
        )

        auth_url = session.generate_authcode()
        print("\n[Auth] Open this URL in your browser and complete login:")
        print(f"\n  {auth_url}\n")
        print("[Auth] After login you will be redirected. Copy the full redirect URL.")
        redirect = input("Paste the full redirect URL here: ").strip()

        auth_code = self._extract_auth_code(redirect)
        session.set_token(auth_code)
        response = session.generate_token()

        if "access_token" not in response:
            raise RuntimeError(f"Token generation failed: {response}")

        access_token = response["access_token"]

        with open(self.token_path, "w") as f:
            json.dump({"access_token": access_token, "date": today}, f)

        print("[Auth] Access token generated and cached.\n")
        return access_token

    @staticmethod
    def _extract_auth_code(redirect_url: str) -> str:
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)
        if "auth_code" in params:
            return params["auth_code"][0]
        # User may have pasted just the code
        return redirect_url.strip()
