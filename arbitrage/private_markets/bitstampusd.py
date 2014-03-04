# Copyright (C) 2013, Maxime Biais <maxime@biais.org>

from .market import Market, TradeException
import time
import base64
import hmac
import urllib.request
import urllib.parse
import urllib.error
import urllib.request
import urllib.error
import urllib.parse
import hashlib
import sys
import json
import config
import logging


class PrivateBitstampUSD(Market):
    balance_url = "https://www.bitstamp.net/api/balance/"
    buy_url = "https://www.bitstamp.net/api/buy/"
    sell_url = "https://www.bitstamp.net/api/sell/"

    def __init__(self):
        super().__init__()
        self.key = config.bitstamp_key
        self.secret = config.bitstamp_secret.encode("utf-8")
        self.client_id = str(config.bitstamp_client_id)
        self.currency = "USD"
        self.nonce = int(time.time() * 1000000)
        self.get_info()

    def _send_request(self, url, params={}, extra_headers=None):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }
        if extra_headers is not None:
            for k, v in extra_headers.items():
                headers[k] = v
        
        params['key'] = self.key
        message = str(self.nonce) + self.client_id + self.key
        signature = hmac.new(self.secret, msg=message.encode("utf-8"), digestmod=hashlib.sha256).hexdigest().upper() 
        params["signature"] = signature
        params['nonce'] =  self.nonce
        self.nonce += 1
        #
        postdata = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(url, postdata, headers=headers)
        response = urllib.request.urlopen(req)
        code = response.getcode()
        if code == 200:
            jsonstr = response.read().decode('utf-8')
            try:
                return json.loads(jsonstr)
            except Exception:
                logging.error("%s - Can't parse json: %s" % (self.name, jsonstr))
                raise MarketException("Can't parse json: " + jsonstr)
        return None

    def _buy(self, amount, price):
        """Create a buy limit order"""
        params = {"amount": amount, "price": price}
        response = self._send_request(self.buy_url, params)
        if "error" in response:
            raise TradeException(response["error"])

    def _sell(self, amount, price):
        """Create a sell limit order"""
        params = {"amount": amount, "price": price}
        response = self._send_request(self.sell_url, params)
        if "error" in response:
            raise TradeException(response["error"])

    def get_info(self):
        """Get balance"""
        response = self._send_request(self.balance_url)
        if response:
            if "error" in response:
                logging.error("%s - fetched data error: %s" % (self.name, response["error"]))
                raise MarketException(response["error"])
            self.btc_balance = float(response["btc_available"])
            self.usd_balance = float(response["usd_available"])
