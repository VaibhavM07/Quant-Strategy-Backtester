"""
PositionMonitor — real-time position and order tracking.

Connects to Fyers order websocket (order_ws) to receive live updates on
orders, positions, and trades without polling the REST API.
"""

import threading
from fyers_apiv3.FyersWebsocket import order_ws


class PositionMonitor:
    """
    Tracks open positions and order status in real time.

    Usage:
        monitor = PositionMonitor(fyers, access_token=f"{client_id}:{token}")
        monitor.start()
        ...
        positions = monitor.get_positions()  # REST snapshot
        monitor.stop()
    """

    def __init__(self, fyers, access_token: str, log_path: str = ""):
        self.fyers = fyers
        self.access_token = access_token
        self.log_path = log_path

        # Callbacks the strategy can hook into
        self.on_order_update = None
        self.on_position_update = None
        self.on_trade_update = None

        self._ws = None
        self._lock = threading.Lock()
        self._orders: dict = {}       # order_id → order dict
        self._positions: list = []    # latest positions snapshot

    # ------------------------------------------------------------------
    # Websocket lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Connect to Fyers order websocket."""
        self._ws = order_ws.FyersOrderSocket(
            access_token=self.access_token,
            write_to_file=False,
            log_path=self.log_path,
            on_connect=self._on_connect,
            on_close=self._on_close,
            on_error=self._on_error,
            on_orders=self._on_order,
            on_positions=self._on_position,
            on_trades=self._on_trade,
        )
        self._ws.connect()

    def stop(self):
        if self._ws:
            self._ws.close_connection()

    # ------------------------------------------------------------------
    # Websocket callbacks
    # ------------------------------------------------------------------

    def _on_connect(self):
        data_type = "OnOrders,OnPositions,OnTrades"
        self._ws.subscribe(data_type=data_type)
        self._ws.keep_running()
        print("[PositionMonitor] Connected to order websocket.")

    def _on_order(self, message):
        if not message:
            return
        with self._lock:
            order_id = message.get("id", "")
            if order_id:
                self._orders[order_id] = message
        if self.on_order_update:
            self.on_order_update(message)

    def _on_position(self, message):
        if not message:
            return
        with self._lock:
            self._positions = message if isinstance(message, list) else [message]
        if self.on_position_update:
            self.on_position_update(message)

    def _on_trade(self, message):
        if self.on_trade_update:
            self.on_trade_update(message)

    def _on_close(self, message):
        print(f"[PositionMonitor] Websocket closed: {message}")

    def _on_error(self, message):
        print(f"[PositionMonitor] Websocket error: {message}")

    # ------------------------------------------------------------------
    # REST API helpers
    # ------------------------------------------------------------------

    def get_positions(self) -> dict:
        """Fetch current open positions via REST."""
        return self.fyers.positions()

    def get_tradebook(self) -> dict:
        """Fetch today's trades via REST."""
        return self.fyers.tradebook()

    def get_orderbook(self) -> dict:
        """Fetch today's orders via REST."""
        return self.fyers.orderbook()

    def get_funds(self) -> dict:
        """Fetch available funds/margin."""
        return self.fyers.funds()

    # ------------------------------------------------------------------
    # In-memory state (populated by websocket)
    # ------------------------------------------------------------------

    def get_cached_positions(self) -> list:
        with self._lock:
            return list(self._positions)

    def get_cached_orders(self) -> dict:
        with self._lock:
            return dict(self._orders)

    def calculate_pnl(self) -> float:
        """
        Compute realized + unrealized P&L from latest position snapshot.
        Returns total P&L in rupees.
        """
        resp = self.get_positions()
        if resp.get("s") != "ok":
            return 0.0
        net_positions = resp.get("netPositions", [])
        total_pnl = sum(
            p.get("unrealizedProfit", 0) + p.get("realizedProfit", 0)
            for p in net_positions
        )
        return total_pnl
