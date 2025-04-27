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


class login_module():
    def __init__(self, client_id, secret_key, redirect_uri, response_type, grant_type, auth_code, token,totp_key,account_id):
        self.client_id = client_id
        self.secret_key = secret_key
        self.redirect_uri = redirect_uri
        self.response_type = response_type
        self.grant_type = grant_type
        self.auth_code = auth_code
        self.token = token
        self.otp = pyotp.TOTP(totp_key)
        self.account_id = account_id
        self.fyers = fyersModel.FyersModel(client_id=self.client_id, token=self.token, is_async=False,
                                           log_path="")
        self.appsession = fyersModel.SessionModel(
            client_id="9MKDYQFWFB-100",
            secret_key="SJI15AAODY",
            redirect_uri="https://trade.fyers.in/api-login/redirect-uri/index.html",
            response_type='code',
            state='sample_state',
            grant_type='authorization_code'
        )

        self.url = self.appsession.generate_authcode()
        print(self.url)
        self.redirect_url = self.url
        self.driver = webdriver.Edge()
        self.driver.get(self.redirect_url)
        print('Page loaded successfully!!')

    def web_automation(self):
        p1 = '1'
        p2 = '2'
        p3 = '3'
        p4 = '4'
        try:
            # Click the login link
            login_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/section/section[2]/section[1]/div[3]/div/form/a'))
            )
            login_link.click()

            # time.sleep(10)
            # Input Client ID
            client_id_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '/html/body/section/section[2]/section[2]/div[3]/div/form/div[1]/input'))
            )
            client_id_input.send_keys(id)

            # Click Client ID button
            client_id_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '/html/body/section/section[2]/section[2]/div[3]/div/form/button'))
            )
            client_id_button.click()

            # Input OTP
            otp_inputs = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '/html/body/section[6]/div[3]/div[3]/form/div[3]/input'))
            )
            otp_digits = str(self.otp.now())
            for i, digit in enumerate(otp_digits, ):
                digit_input = self.driver.find_element(By.XPATH,
                                                  f'/html/body/section[6]/div[3]/div[3]/form/div[3]/input[{i + 1}]')
                self.driver.execute_script("arguments[0].scrollIntoView(true);", digit_input)
                element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, f'/html/body/section[6]/div[3]/div[3]/form/div[3]/input[{i + 1}]')))
                digit_input.send_keys(digit)
            otp_click = self.driver.find_element(by='xpath',
                                            value='/html/body/section[6]/div[3]/div[3]/form/button').click()

            # Input password
            password_inputs = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '/html/body/section[8]/div[3]/div[3]/form/div[2]/input'))
            )
            pin_input = self.driver.find_element(By.XPATH, '//html/body/section[8]/div[3]/div[3]/form/div[2]/input')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", pin_input)
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/section[8]/div[3]/div[3]/form/div[2]/input')))
            password_inputs[0].send_keys(p1)
            password_inputs[1].send_keys(p2)
            password_inputs[2].send_keys(p3)
            password_inputs[3].send_keys(p4)

            access_token_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '/html/body/main/section/div/div/div[2]/div/div/table/tbody/tr[3]/td/p'))
            )
            auth_code = access_token_element.text
            print("Access Token:", auth_code)

        except ElementNotInteractableException as e:
            print("Element is not interactable:", e)


        finally:
            self.driver.quit()
