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
from Live_trade_engine.Login_module import login_module
class websocket_interation(login_module):

    def __init__(self,entry_price,exit_price,stop_loss,take_profit,postion_flag,symbols:str,expiry:str,
                 exchange:str,
                 option_type: str,
                 quantity: int,
                 LongOrShort: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.postion_flag = postion_flag
        self.symbols = symbols
        self.expiry = expiry
        self.exchange = exchange
        self.quantity = quantity
        self.LongOrShort = LongOrShort
        self.option_type = option_type
        self.fyers_ticks = data_ws.FyersDataSocket(
            access_token=self.token,
            log_path="",
            litemode=False,
            write_to_file=False,
            reconnect=True,
            on_connect=self.onopen_ticks,
            on_close=self.onclose,
            on_error=self.onerror,
            on_message=self.onmessage
        )
        self.fyers_ticks.connect()
        print(self.fyers_ticks)
        print("wesocket data:")

        self.fyers_positions = order_ws.FyersOrderSocket(
            access_token=self.token,
            write_to_file=False,
            log_path="",
            on_connect=self.onopen_position_orders,
            on_close=self.onclose,
            on_error=self.onerror,
            on_positions=self.onPosition,
        )
        self.fyers_positions.connect()

    def onmessage(self, message):
        symbol = self.exchange + ":" + self.symbols + self.expiry
        symbol += "CE" if self.option_type == "CALL" else "PE"

        if not self.postion_flag:
            data_placement = self.getOrderPlacement(symbol=symbol,
                                                    quantity=self.quantity,
                                                    LongOrShort=self.LongOrShort,
                                                    limitPrice=self.entry_price)
            response = self.fyers.place_order(data=data_placement)
            print(response)
        elif self.LongOrShort == 1:
            if message["ltp"] <= self.stop_loss:
                data_placement = self.getOrderPlacement(symbol=symbol,
                                                        quantity=self.quantity,
                                                        LongOrShort=(-1)*self.LongOrShort,
                                                        limitPrice=message["ltp"])
                response = self.fyers.place_order(data=data_placement)
                print(response)
            elif message["ltp"] >= self.take_profit:
                data_placement = self.getOrderPlacement(symbol=symbol,
                                                        quantity=self.quantity,
                                                        LongOrShort=(-1) * self.LongOrShort,
                                                        limitPrice=message["ltp"])
                response = self.fyers.place_order(data=data_placement)
                print(response)
        elif self.LongOrShort == -1:
            if message["ltp"] >= self.stop_loss:
                data_placement = self.getOrderPlacement(symbol=symbol,
                                                        quantity=self.quantity,
                                                        LongOrShort=(-1)*self.LongOrShort,
                                                        limitPrice=message["ltp"])
                response = self.fyers.place_order(data=data_placement)
                print(response)
            elif message["ltp"] <= self.take_profit:
                data_placement = self.getOrderPlacement(symbol=symbol,
                                                        quantity=self.quantity,
                                                        LongOrShort=(-1) * self.LongOrShort,
                                                        limitPrice=message["ltp"])
                response = self.fyers.place_order(data=data_placement)
                print(response)


    def onopen_position_orders(self):
        data_type = "OnPositions,OnOrders"
        self.fyers_ticks.subscribe(symbols=[self.symbols], data_type=data_type)

        self.fyers_ticks.keep_running()

    def onerror(self, message):
        print("Error:", message)

    def onclose(self, message):
        print("Connection closed:", message)

    def onopen_ticks(self):
        data_type = "SymbolUpdate"
        self.fyers_ticks.subscribe(symbols=[self.symbols], data_type=data_type)
        self.fyers_ticks.keep_running()

    def onPosition(self, message):
        print("Realized_PnL: ",message["realized_profit"],"Entry_price: ",message['buyAvg'],"Buy_quantity: ",message['buyQty'],"Sell_price: ",message["sellVal"],"Sell_quantity: ",message["sellQty"])
        # print("Position Response:", message)
        return message

    def onOrder(self, message):
        print("Order Response:", message)

    @staticmethod
    def getOrderPlacement(symbol: str,
                       quantity: int,
                       LongOrShort: int,
                       limitPrice: float = 0.0,
                       stopPrice: float = 0.0,
                       order_type: int = 2,
                       product_type: str = "MARGIN",
                       validity: str = "DAY",
                       disclosedQty: int = 0,
                       offlineOrder: bool = False
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

        return data
