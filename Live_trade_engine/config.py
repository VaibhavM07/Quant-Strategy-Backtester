# Fyers API credentials — fill these before running live
CLIENT_ID  = ""   # Your App ID, e.g. "EGD02YUYIM-100"
SECRET_KEY = ""   # Your App secret key
REDIRECT_URL = "https://trade.fyers.in/api-login/redirect-uri/index.html"

# Token cache file (keeps you logged in between runs)
TOKEN_FILE = "access_token.json"

# All trade parameters (legs, strikes, expiry, qty, SL, timing) live in
# the runner file — e.g. runners/banknifty_short_straddle.py
