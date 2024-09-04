import ccxt
from User import User
from enum import Enum
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
        self._user = user
        self.error = None

    @property
    def user(self): return self._user

    @user.setter
    def user(self, new_user):
        if self._user != new_user:
            self._user = new_user

    def connect(self):
        self.instance = getattr(ccxt, self.id) ()
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

def main():
    print("Don't Run this Class from CLI")

if __name__ == '__main__':
    main()