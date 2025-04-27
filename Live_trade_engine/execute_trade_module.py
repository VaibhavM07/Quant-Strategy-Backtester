from fyers_apiv3.FyersWebsocket import order_ws
from fyers_apiv3.FyersWebsocket import data_ws
from datetime import datetime, timedelta, timezone
import pandas as pd
from fyers_apiv3 import fyersModel
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyotp
import time
import hashlib

def OrderPlacement(symbol: str,
                   quantity: int,
                   LongOrShort: int,
                   limitPrice: float = 0.0,
                   stopPrice: float = 0.0,
                   order_type: int=2,
                   product_type: str="MARGIN",
                   validity: str="DAY",
                   disclosedQty: int=0,
                   offlineOrder: bool=False
                   ):
    data = {
        "symbol": symbol,
        "qty": quantity,
        "type": order_type,
        "side": LongOrShort,
        "productType": product_type,
        "limitPrice": limitPrice,
        "stopPrice": stopPrice,
        "validity": validity,
        "disclosedQty": disclosedQty,
        "offlineOrder": offlineOrder,
    }