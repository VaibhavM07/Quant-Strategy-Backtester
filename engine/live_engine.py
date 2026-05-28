"""
Generic live options engine.

All trade details (legs, sides, expiry, strikes, timing, SL, TP) come from
the strategy config. The engine resolves symbols, places orders, monitors
P&L in a live console dashboard, and exits on SL / TP / time.

Strategy defines LEGS as a list of dicts:
    LEGS = [
        {"option_type": "CE", "side": -1},   # -1 = sell, 1 = buy
        {"option_type": "PE", "side": -1},
    ]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
import datetime
from types import SimpleNamespace

from fyers_apiv3.FyersWebsocket import data_ws

from Live_trade_engine.symbol_module import SymbolResolver
from Live_trade_engine.execute_trade_module import place_basket, place_order


def _parse_time(t: str) -> datetime.time:
    return datetime.time(*map(int, t.split(":")))


def _resolve(val, *args):
    """Call val(*args) if callable, else return val as-is."""
    return val(*args) if callable(val) else val


def _secs_to_hms(secs: int) -> str:
    h, rem = divmod(max(secs, 0), 3600)
    m, s   = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class _OptionRunner:
    """
    Executes an arbitrary multi-leg option trade driven entirely by config.

    cfg must expose:
        CLIENT_ID, UNDERLYING, EXCHANGE, STRIKE_ROUNDING
        LEGS                  — list of leg dicts
        QUANTITY              — lots applied to every leg
        ENTRY_TIME            — "HH:MM:SS"
        EXIT_TIME             — "HH:MM:SS"
        STOP_LOSS_MULTIPLIER  — e.g. 1.20  (20% of premium as max loss)
        TAKE_PROFIT           — e.g. 0.50  (capture 50% of premium), or None
    """

    _DASH_WIDTH = 68

    def __init__(self, fyers, cfg):
        self.fyers = fyers
        self.cfg   = cfg

        self.legs: list  = []
        self._quantity   = 0     # resolved at entry (may differ from cfg if callable)
        self.sl_amount   = 0.0   # fixed rupee loss limit (set at entry)
        self.tp_amount   = None  # fixed rupee profit target (set at entry), or None

        self.position_active = False
        self.position_closed = False
        self._ws   = None
        self._lock = threading.Lock()
        self._dashboard_lines = 0   # lines printed last refresh (for overwrite)

    # ── Symbol resolution ────────────────────────────────────────────

    def setup(self):
        resolver = SymbolResolver(
            fyers=self.fyers,
            underlying=self.cfg.UNDERLYING,
            exchange=self.cfg.EXCHANGE,
            strike_rounding=self.cfg.STRIKE_ROUNDING,
            expiry_date=getattr(self.cfg, "EXPIRY_DATE", None),
            expiry_term=getattr(self.cfg, "EXPIRY_TERM", None),
        )
        self.legs = resolver.resolve_legs(self.cfg.LEGS)
        print()
        self._init_websocket()

    # ── Websocket ────────────────────────────────────────────────────

    def _init_websocket(self):
        access_token = f"{self.cfg.CLIENT_ID}:{self.fyers.token}"
        self._ws = data_ws.FyersDataSocket(
            access_token=access_token,
            log_path="",
            litemode=False,
            write_to_file=False,
            reconnect=True,
            on_connect=self._on_connect,
            on_close=lambda m: print(f"\n[Live] WS closed: {m}"),
            on_error=lambda m: print(f"\n[Live] WS error: {m}"),
            on_message=self._on_message,
        )
        self._ws.connect()

    def _on_connect(self):
        symbols = [leg["symbol"] for leg in self.legs]
        self._ws.subscribe(symbols=symbols, data_type="SymbolUpdate")
        self._ws.keep_running()
        print(f"[Live] Websocket connected — subscribed to {len(symbols)} symbols\n")

    def _on_message(self, message: dict):
        if not isinstance(message, dict) or "ltp" not in message:
            return
        sym = message.get("symbol", "")
        ltp = message.get("ltp", 0.0)
        with self._lock:
            for leg in self.legs:
                if leg["symbol"] == sym:
                    leg["ltp"] = ltp
                    break
            if self.position_active and not self.position_closed:
                self._check_exit_conditions()

    # ── Entry ────────────────────────────────────────────────────────

    def enter_position(self) -> bool:
        symbols_str = ",".join(leg["symbol"] for leg in self.legs)
        resp = self.fyers.quotes({"symbols": symbols_str})
        if resp.get("s") != "ok":
            print(f"[Live] Quote fetch failed: {resp}")
            return False

        ltp_map = {item["n"]: item["v"]["lp"] for item in resp.get("d", [])}
        for leg in self.legs:
            price        = ltp_map.get(leg["symbol"], 0.0)
            leg["entry"] = price
            leg["ltp"]   = price

        net_premium = sum((-leg["side"]) * leg["entry"] for leg in self.legs)

        # Resolve quantity, SL, TP — each accepts a plain value or a callable.
        # Callable signatures:
        #   QUANTITY(net_premium)             -> int   (lots)
        #   STOP_LOSS(net_premium, quantity)  -> float (max rupee loss)
        #   TAKE_PROFIT(net_premium, quantity)-> float (target rupee profit) or None
        self._quantity = _resolve(self.cfg.QUANTITY, net_premium)

        sl_raw = _resolve(self.cfg.STOP_LOSS_MULTIPLIER, net_premium, self._quantity)
        if callable(self.cfg.STOP_LOSS_MULTIPLIER):
            self.sl_amount = float(sl_raw)                               # callable → rupees directly
        else:
            self.sl_amount = abs(net_premium) * (sl_raw - 1) * self._quantity  # multiplier

        tp_cfg = getattr(self.cfg, "TAKE_PROFIT", None)
        if tp_cfg is None:
            self.tp_amount = None
        else:
            tp_raw = _resolve(tp_cfg, net_premium, self._quantity)
            if callable(tp_cfg):
                self.tp_amount = float(tp_raw)                           # callable → rupees directly
            else:
                self.tp_amount = abs(net_premium) * tp_raw * self._quantity  # fraction of premium

        print(f"\n[Live] ── Entry ─────────────────────────────────────────")
        for leg in self.legs:
            side_label = "SELL" if leg["side"] == -1 else "BUY "
            print(f"[Live]   {side_label} {leg['option_type']}  {leg['symbol'].split(':')[1]}  @ ₹{leg['entry']:.2f}")
        print(f"[Live] Net premium  : ₹{abs(net_premium):.2f} per lot  ×  {self._quantity} lots")
        print(f"[Live] Stop loss    : -₹{self.sl_amount:.2f}")
        print(f"[Live] Take profit  : +₹{self.tp_amount:.2f}" if self.tp_amount else
              f"[Live] Take profit  : not set (time exit only)")
        print(f"[Live] ─────────────────────────────────────────────────\n")

        basket = [
            {"symbol": leg["symbol"], "quantity": self._quantity, "side": leg["side"]}
            for leg in self.legs
        ]
        result = place_basket(self.fyers, basket)

        if result.get("s") == "ok":
            with self._lock:
                self.position_active = True
            return True

        print("[Live] Basket failed — placing individual orders...")
        success = True
        for leg in self.legs:
            r = place_order(self.fyers, leg["symbol"], self._quantity, side=leg["side"])
            print(f"[Live]   {leg['symbol']}: {r}")
            if r.get("s") != "ok":
                success = False

        if success:
            with self._lock:
                self.position_active = True
        return success

    # ── P&L ──────────────────────────────────────────────────────────

    def _current_pnl(self) -> float:
        return sum(
            (-leg["side"]) * (leg["entry"] - leg["ltp"])
            for leg in self.legs
        ) * self._quantity

    # ── Exit conditions ───────────────────────────────────────────────

    def _check_exit_conditions(self):
        """Called inside _lock from _on_message."""
        pnl = self._current_pnl()

        if pnl < -self.sl_amount:
            self._trigger_exit("STOP LOSS", pnl)
            return

        if self.tp_amount is not None and pnl >= self.tp_amount:
            self._trigger_exit("TAKE PROFIT", pnl)
            return

        if datetime.datetime.now().time() >= _parse_time(self.cfg.EXIT_TIME):
            self._trigger_exit("TIME EXIT", pnl)

    def _trigger_exit(self, reason: str, pnl: float):
        print(f"\n\n[Live] ▶ {reason} triggered — P&L ₹{pnl:+.2f}")
        threading.Thread(target=self.exit_position, args=(reason,), daemon=True).start()

    def exit_position(self, reason: str = "MANUAL"):
        with self._lock:
            if self.position_closed:
                return
            self.position_closed = True
            self.position_active = False

        print(f"[Live] Closing all legs ...")
        basket = [
            {"symbol": leg["symbol"], "quantity": self._quantity, "side": -leg["side"]}
            for leg in self.legs
        ]
        result = place_basket(self.fyers, basket)
        if result.get("s") != "ok":
            for leg in self.legs:
                place_order(self.fyers, leg["symbol"], self._quantity, side=-leg["side"])

        pnl = self._current_pnl()
        print(f"[Live] ── Exit Summary ──────────────────────────────────")
        print(f"[Live]   Reason         : {reason}")
        print(f"[Live]   Approx. P&L    : ₹{pnl:+.2f}")
        print(f"[Live] ─────────────────────────────────────────────────\n")

        if self._ws:
            self._ws.close_connection()

    # ── Live console dashboard ────────────────────────────────────────

    def _print_dashboard(self):
        """Overwrite the previous dashboard in-place using ANSI cursor movement."""
        with self._lock:
            legs_snapshot = [dict(leg) for leg in self.legs]
            pnl           = self._current_pnl()
            sl_amt        = self.sl_amount
            tp_amt        = self.tp_amount

        now      = datetime.datetime.now()
        exit_t   = _parse_time(self.cfg.EXIT_TIME)
        exit_dt  = datetime.datetime.combine(now.date(), exit_t)
        secs_left = max(int((exit_dt - now).total_seconds()), 0)

        W    = self._DASH_WIDTH
        sep  = "─" * W
        lines = []

        lines.append(f"┌{sep}┐")
        lines.append(
            f"│  LIVE POSITION   {now.strftime('%Y-%m-%d %H:%M:%S')}"
            f"   Exit in {_secs_to_hms(secs_left)}".ljust(W) + "│"
        )
        lines.append(f"├{sep}┤")
        lines.append(
            f"│  {'Leg':<32} {'Side':<5} {'Entry':>8} {'LTP':>8} {'P&L':>9}  │"
        )
        lines.append(f"├{sep}┤")

        for leg in legs_snapshot:
            sym_short  = leg["symbol"].split(":")[1] if ":" in leg["symbol"] else leg["symbol"]
            sym_short  = sym_short[:32]
            side_lbl   = "SELL" if leg["side"] == -1 else "BUY "
            entry      = leg["entry"]
            ltp        = leg["ltp"]
            leg_pnl    = (-leg["side"]) * (entry - ltp) * self._quantity
            pnl_str    = f"₹{leg_pnl:+.2f}"
            lines.append(
                f"│  {sym_short:<32} {side_lbl:<5} {entry:>8.2f} {ltp:>8.2f} {pnl_str:>9}  │"
            )

        lines.append(f"├{sep}┤")

        pnl_str = f"₹{pnl:+.2f}"
        sl_str  = f"-₹{sl_amt:.2f}"
        tp_str  = f"+₹{tp_amt:.2f}" if tp_amt else "  —  "
        summary = f"  Net P&L: {pnl_str:<12}  SL: {sl_str:<14}  TP: {tp_str}"
        lines.append(f"│{summary.ljust(W)}│")
        lines.append(f"└{sep}┘")

        # Move cursor up to overwrite previous dashboard
        if self._dashboard_lines > 0:
            sys.stdout.write(f"\033[{self._dashboard_lines}A\033[J")

        output = "\n".join(lines) + "\n"
        sys.stdout.write(output)
        sys.stdout.flush()
        self._dashboard_lines = len(lines)

    # ── Main loop ────────────────────────────────────────────────────

    def run(self):
        entry_t = _parse_time(self.cfg.ENTRY_TIME)
        exit_t  = _parse_time(self.cfg.EXIT_TIME)
        print(f"[Live] Waiting for entry at {self.cfg.ENTRY_TIME} ...\n")

        while not self.position_closed:
            now = datetime.datetime.now().time()

            if not self.position_active and entry_t <= now < exit_t:
                if not self.enter_position():
                    print("[Live] Entry failed. Retrying in 30s...")
                    time.sleep(30)
                    continue

            if now >= exit_t and not self.position_active:
                print("[Live] Past exit time, no position taken.")
                break

            if now >= exit_t and self.position_active:
                self.exit_position("TIME EXIT")
                break

            if self.position_active:
                self._print_dashboard()

            time.sleep(1)

        print("[Live] Run complete.")


class LiveEngine:
    """
    Authenticates via Fyers and hands off to the generic _OptionRunner.
    Credentials from Live_trade_engine/config.py.
    All trade parameters from the strategy file.
    """

    def __init__(self,
                 underlying: str,
                 legs: list,
                 entry_time: str,
                 exit_time: str,
                 quantity: int,
                 stop_loss_multiplier: float,
                 take_profit: float = None,
                 strike_rounding: int = 100,
                 expiry_date: str = None,
                 expiry_term: str = None):
        self.underlying           = underlying
        self.legs                 = legs
        self.entry_time           = entry_time
        self.exit_time            = exit_time
        self.quantity             = quantity
        self.stop_loss_multiplier = stop_loss_multiplier
        self.take_profit          = take_profit      # fraction of premium, e.g. 0.50
        self.strike_rounding      = strike_rounding
        self.expiry_date          = expiry_date
        self.expiry_term          = expiry_term

    def run(self):
        from Live_trade_engine import config as cfg
        from Live_trade_engine.Login_module import login_module

        if not cfg.CLIENT_ID or not cfg.SECRET_KEY:
            raise RuntimeError("Fill in CLIENT_ID and SECRET_KEY in Live_trade_engine/config.py.")

        auth = login_module(
            client_id=cfg.CLIENT_ID,
            secret_key=cfg.SECRET_KEY,
            redirect_url=cfg.REDIRECT_URL,
            token_file=cfg.TOKEN_FILE,
        )
        fyers = auth.fyers

        profile = fyers.get_profile()
        if profile.get("s") != "ok":
            raise RuntimeError(f"Login verification failed: {profile}")
        print(f"[Live] Logged in as: {profile['data'].get('name', 'Unknown')}\n")

        live_cfg = SimpleNamespace(
            CLIENT_ID=cfg.CLIENT_ID,
            UNDERLYING=self.underlying,
            EXCHANGE="NSE",
            LEGS=self.legs,
            QUANTITY=self.quantity,
            ENTRY_TIME=self.entry_time,
            EXIT_TIME=self.exit_time,
            STOP_LOSS_MULTIPLIER=self.stop_loss_multiplier,
            TAKE_PROFIT=self.take_profit,
            STRIKE_ROUNDING=self.strike_rounding,
            EXPIRY_DATE=self.expiry_date,
            EXPIRY_TERM=self.expiry_term,
        )

        runner = _OptionRunner(fyers=fyers, cfg=live_cfg)
        runner.setup()
        runner.run()
