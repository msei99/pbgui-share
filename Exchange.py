import ccxt
import configparser
from User import User, Users
from enum import Enum
import json
from pathlib import Path
from time import sleep
from datetime import datetime

class Exchanges(Enum):
    BINANCE = 'binance'
    BYBIT = 'bybit'
    BITGET = 'bitget'
    HYPERLIQUID = 'hyperliquid'
    OKX = 'okx'
    KUCOIN = 'kucoin'
    BINGX = 'bingx'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, Exchanges))

class Spot(Enum):
    BINANCE = 'binance'
    BYBIT = 'bybit'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, Spot))

class Single(Enum):
    BINANCE = 'binance'
    BYBIT = 'bybit'
    OKX = 'okx'
    KUCOIN = 'kucoin'
    BINGX = 'bingx'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, Single))

class Passphrase(Enum):
    BITGET = 'bitget'
    OKX = 'okx'
    KUCOIN = 'kucoin'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, Passphrase))

class Exchange:
    def __init__(self, id: str, user: User = None):
        self.name = id
        self.id = "kucoinfutures" if id == "kucoin" else id
        self.instance = None
        self._markets = None
        self._tf = None
        self.spot = []
        self.swap = []
        self._user = user
        self.error = None

    @property
    def user(self): return self._user

    @property
    def tf(self):
        if not self._tf:
            self.connect()
            self._tf = list(self.instance.timeframes.keys())
            if "1s" in self._tf:
                self._tf.remove('1s')
        return self._tf

    @user.setter
    def user(self, new_user):
        if self._user != new_user:
            self._user = new_user

    def connect(self):
        self.instance = getattr(ccxt, self.id) ()
        self.instance.http_proxy = 'http://130.61.171.71:80'
        if self._user and self.user.key != 'key':
            self.instance.apiKey = self.user.key
            self.instance.secret = self.user.secret
            self.instance.password = self.user.passphrase
            self.instance.walletAddress = self.user.wallet_address
            self.instance.privateKey = self.user.private_key
        try:
            self.instance.checkRequiredCredentials()
        except Exception as e:
            self.error = (str(e))
            return

    def fetch_ohlcv(self, symbol: str, market_type: str, timeframe: str, limit: int):
        if not self.instance: self.connect()
        if self.id == "hyperliquid":
            now = int(datetime.now().timestamp() * 1000)
            since = now - 1000 * 60 * 60 * limit
            ohlcv = self.instance.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=since, limit=limit)
        else:
            ohlcv = self.instance.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        return ohlcv

    def fetch_price(self, symbol: str, market_type: str):
        if not self.instance: self.connect()
        price = self.instance.fetch_ticker(symbol=symbol)
        return price

    def fetch_prices(self, symbols: list, market_type: str):
        if not self.instance: self.connect()
        # Fix for Hyperliquid
        if self.id == "hyperliquid":
            fetched = self.instance.fetch(
                "https://api.hyperliquid.xyz/info",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"type": "allMids"}),
            )
            prices = {}
            for symbol in symbols:
                sym = symbol[0:-10]
                if sym in fetched:
                    prices[symbol] = {
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "last": fetched[sym]
                    }
        else:
            prices = self.instance.fetch_tickers(symbols=symbols)
        return prices

    def fetch_timestamp(self):
        if not self.instance: self.connect()
        return self.instance.milliseconds()
    
    def load_market(self):
        if not self.instance: self.connect()
        self._markets = self.instance.load_markets()
        return self._markets

def main():
    print("Don't Run this Class from CLI")

if __name__ == '__main__':
    main()
