from pathlib import Path
from User import Users, User
from Exchange import Exchange
import sqlite3
import pandas as pd
import streamlit as st

class Database():
    def __init__(self):
        self.db_user = st.secrets["db_user"]
        self.db_password = st.secrets["db_password"]
        self.db_host = st.secrets["db_host"]
        self.db_port = st.secrets["db_port"]
        self.conn = st.connection(
            "pbguishare",
            "sql",
            url = f"mysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/pbguishare",
        )
        self.create_tables()

    def fetch_positions(self, user: User):
        positions = self.conn.query("SELECT * FROM position WHERE user = :user",
                                    ttl=0,
                                    params=dict(user=user.name))
        return positions

    def fetch_orders_by_symbol(self, user: str, symbol: str):
        orders = self.conn.query("SELECT * FROM orders WHERE user = :user AND symbol = :symbol",
                                    ttl=0,
                                    params=dict(user=user, symbol=symbol))
        return orders

    def fetch_prices(self, user: User):
        prices = self.conn.query("SELECT * FROM prices WHERE user = :user",
                                    ttl=0,
                                    params=dict(user=user.name))
        return prices

    def fetch_ohlcv(self, user: User, symbol: str):
        ohlcv = self.conn.query("SELECT * FROM ohlcv WHERE user = :user AND symbol = :symbol",
                                    ttl=0,
                                    params=dict(user=user.name, symbol=symbol))
        return ohlcv

    def select_top(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        top = 500
        top_symbols = self.conn.query("SELECT symbol as Symbol, SUM(income) as Income FROM history WHERE user = :user AND timestamp >= :start AND timestamp <= :end GROUP BY symbol ORDER BY Income DESC LIMIT :top",
                                    ttl=0,
                                    params=dict(user=user.name, start=start, end=end, top=top))
        return top_symbols
        
    def select_pnl(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        pnl = self.conn.query("SELECT DATE_FORMAT(FROM_UNIXTIME(timestamp / 1000), '%Y-%m-%d') as Date, SUM(income) as Income FROM history WHERE user = :user AND timestamp >= :start AND timestamp <= :end GROUP BY Date",
                                        ttl=0,
                                        params=dict(user=user.name, start=start, end=end))
        return pnl
    
    # select income grouped by symbol not sum
    def select_income_by_symbol(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        income = self.conn.query("SELECT timestamp as Date, symbol as Symbol, income as Income FROM history WHERE user = :user AND timestamp >= :start AND timestamp <= :end ORDER BY Date ASC",
                        ttl=0,
                        params=dict(user=user.name, start=start, end=end))
        return income

    def find_last_timestamp(self, user: User):
        timestamp = self.conn.query("SELECT MAX(timestamp) FROM history WHERE user = :user",
                                    ttl=0,
                                    params=dict(user=user.name))
        timestamp = timestamp.iloc[0, 0]
        if timestamp:
            return timestamp
        else:
            return 0
    
    def find_first_timestamp(self, user: User):
        timestamp = self.conn.query("SELECT MIN(timestamp) FROM history WHERE user = :user",
                                    ttl=0,
                                    params=dict(user=user.name))
        timestamp = timestamp.iloc[0, 0]
        if timestamp:
            return timestamp
        else:
            return 0

    def create_tables(self):
        try:
            with self.conn.session as session:
                sql = """CREATE TABLE IF NOT EXISTS position (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    symbol VARCHAR(32) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    psize FLOAT NOT NULL,
                    upnl FLOAT NOT NULL,
                    entry FLOAT NOT NULL,
                    user VARCHAR(32) NOT NULL);"""
                session.execute(sql)
                sql = """CREATE TABLE IF NOT EXISTS orders (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    symbol VARCHAR(32) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    amount FLOAT NOT NULL,
                    price FLOAT NOT NULL,
                    side VARCHAR(4) NOT NULL,
                    uniqueid VARCHAR(64) NOT NULL UNIQUE,
                    user VARCHAR(32) NOT NULL);"""
                session.execute(sql)
                sql = """CREATE TABLE IF NOT EXISTS prices (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    symbol VARCHAR(32) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    price FLOAT NOT NULL,
                    user VARCHAR(32) NOT NULL);"""
                session.execute(sql)
                sql = """CREATE TABLE IF NOT EXISTS history (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    symbol VARCHAR(32) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    income FLOAT NOT NULL,
                    uniqueid VARCHAR(64) NOT NULL UNIQUE,
                    user VARCHAR(32) NOT NULL);"""
                session.execute(sql)
                sql = """CREATE TABLE IF NOT EXISTS ohlcv (
                    timestamp BIGINT NOT NULL,
                    open FLOAT NOT NULL,
                    high FLOAT NOT NULL,
                    low FLOAT NOT NULL,
                    close FLOAT NOT NULL,
                    volume FLOAT NOT NULL,
                    user VARCHAR(32) NOT NULL,
                    symbol VARCHAR(32) NOT NULL);"""
                session.execute(sql)
            session.commit()
        except Exception as e:
            print(e)

    def copy_user_mysql(self, source: Path, user: User):
        # Read positions from SQLite DB
        try:
            with sqlite3.connect(source) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM position WHERE user = '{user.name}'")
                positions = cursor.fetchall()
                cursor.execute(f"SELECT * FROM orders WHERE user = '{user.name}'")
                orders = cursor.fetchall()
                cursor.execute(f"SELECT * FROM prices WHERE user = '{user.name}'")
                prices = cursor.fetchall()
                timestamp = self.find_last_timestamp(user)
                cursor.execute(f"SELECT * FROM history WHERE user = '{user.name}' AND timestamp >= {timestamp}")
                history = cursor.fetchall()
        except sqlite3.Error as e:
            print(e)
        # Write positions to MySQL DB and remove old positions
        position_ids = []
        for position in positions:
            position_ids.append(position[0])
        orders_ids = []
        for order in orders:
            orders_ids.append(order[0])
        prices_ids = []
        for price in prices:
            prices_ids.append(price[0])
        history_ids = []
        for hist in history:
            history_ids.append(hist[0])
        try:
            with self.conn.session as session:
                for position in positions:
                    session.execute("INSERT IGNORE INTO position VALUES (:id, :symbol, :timestamp, :psize, :upnl, :entry, :user);"
                                    ,params=dict(id=position[0], symbol=position[1], timestamp=position[2], psize=position[3], upnl=position[4], entry=position[5], user=position[6]))
                positions = self.conn.query('select * from position where user = :user',
                                        ttl=0,
                                        params=dict(user=user.name))
                for index, position in positions.iterrows():
                    if position[0] not in position_ids:
                        session.execute(f"DELETE FROM position WHERE id = {position[0]}")
                for order in orders:
                    session.execute("INSERT IGNORE INTO orders VALUES (:id, :symbol, :timestamp, :amount, :price, :side, :uniqueid, :user);"
                                    ,params=dict(id=order[0], symbol=order[1], timestamp=order[2], amount=order[3], price=order[4], side=order[5], uniqueid=order[6], user=order[7]))
                orders = self.conn.query('select * from orders where user = :user',
                                        ttl=0,
                                        params=dict(user=user.name))
                for index, order in orders.iterrows():
                    if order[0] not in orders_ids:
                        session.execute(f"DELETE FROM orders WHERE id = {order[0]}")
                for price in prices:
                    session.execute("INSERT IGNORE INTO prices VALUES (:id, :symbol, :timestamp, :price, :user);"
                                    ,params=dict(id=price[0], symbol=price[1], timestamp=price[2], price=price[3], user=price[4]))
                prices = self.conn.query('select * from prices where user = :user',
                                        ttl=0,
                                        params=dict(user=user.name))
                for index, price in prices.iterrows():
                    if price[0] not in prices_ids:
                        session.execute(f"DELETE FROM prices WHERE id = {price[0]}")
                for hist in history:
                    session.execute("INSERT IGNORE INTO history VALUES (:id, :symbol, :timestamp, :income, :uniqueid, :user);"
                                    ,params=dict(id=hist[0], symbol=hist[1], timestamp=hist[2], income=hist[3], uniqueid=hist[4], user=hist[5]))
                history = self.conn.query('select * from history where user = :user',
                                        ttl=0,
                                        params=dict(user=user.name))
                for index, hist in history.iterrows():
                    if hist[0] not in history_ids:
                        session.execute(f"DELETE FROM history WHERE id = {hist[0]}")
                session.commit()
        except Exception as e:
            print(e)
                
    def add_ohlcv(self, user: User):
        # get symbols from table dest.orders
        symbols = self.conn.query("SELECT DISTINCT symbol FROM orders WHERE user = :user",
                                    ttl=0,
                                    params=dict(user=user.name))
        # fetch ohlcv from exchange
        exchange = Exchange(user.exchange, user)
        try:
            for index, sym in symbols.iterrows():
                symbol = sym[0]
                if symbol[-4:] == "USDT":
                    symbol_ccxt = f'{symbol[0:-4]}/USDT:USDT'
                elif symbol[-4:] == "USDC":
                    symbol_ccxt = f'{symbol[0:-4]}/USDC:USDC'
                ohlcv = exchange.fetch_ohlcv(symbol_ccxt, "futures", "1h", 100)
                #add new table ohlcv with user, symbol and ohlcv dataframe
                ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                ohlcv_df['user'] = user.name
                ohlcv_df['symbol'] = symbol
                with self.conn.session as session:
                    session.execute("DELETE FROM ohlcv WHERE user = :user AND symbol = :symbol",
                                    params=dict(user=user.name, symbol=symbol))
                    session.execute("INSERT INTO ohlcv (timestamp, open, high, low, close, volume, user, symbol) VALUES (:timestamp, :open, :high, :low, :close, :volume, :user, :symbol);",
                                    ohlcv_df.to_dict(orient='records'))
                    session.commit()
        except Exception as e:
            print(e)

def main():
    print("Don't Run this Class from CLI")
    PBGUI_DB = Path(f'../pbgui/data/pbgui.db')
    db = Database()
    users = Users()
    user = users.find_user("hl_manicpt")
    print(db.find_last_timestamp(user))
    db.add_ohlcv(user)
    db.copy_user_mysql(f'{PBGUI_DB}', user)

if __name__ == '__main__':
    main()
