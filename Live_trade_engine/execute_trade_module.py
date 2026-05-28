"""
Order placement helpers wrapping the Fyers API.

Order types:  1=Limit  2=Market  3=SL-M  4=SL-L
Side:         1=Buy    -1=Sell
Product types: MARGIN / INTRADAY / CNC / CO / BO
"""


def place_order(fyers,
                symbol: str,
                quantity: int,
                side: int,
                order_type: int = 2,
                product_type: str = "MARGIN",
                limit_price: float = 0.0,
                stop_price: float = 0.0,
                validity: str = "DAY") -> dict:
    """Place a single order and return the API response."""
    data = {
        "symbol": symbol,
        "qty": quantity,
        "type": order_type,
        "side": side,
        "productType": product_type,
        "limitPrice": limit_price,
        "stopPrice": stop_price,
        "validity": validity,
        "disclosedQty": 0,
        "offlineOrder": False,
    }
    return fyers.place_order(data=data)


def place_basket(fyers, orders: list) -> dict:
    """
    Place multiple orders simultaneously (basket order).

    Each item in `orders` is a dict with keys matching place_order parameters.
    Returns the API response.
    """
    payload = []
    for o in orders:
        payload.append({
            "symbol": o["symbol"],
            "qty": o["quantity"],
            "type": o.get("order_type", 2),
            "side": o["side"],
            "productType": o.get("product_type", "MARGIN"),
            "limitPrice": o.get("limit_price", 0.0),
            "stopPrice": o.get("stop_price", 0.0),
            "validity": o.get("validity", "DAY"),
            "disclosedQty": 0,
            "offlineOrder": False,
        })
    return fyers.place_basket_orders(data=payload)


def cancel_order(fyers, order_id: str) -> dict:
    """Cancel a pending order by its ID."""
    return fyers.cancel_order(data={"id": order_id})


def exit_all_positions(fyers) -> dict:
    """Emergency: close all open positions at market."""
    return fyers.exit_positions(data={"exit_all": 1})
