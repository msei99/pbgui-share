from pathlib import Path
from User import Users, User
from Exchange import Exchange
import sqlite3
import pandas as pd
import streamlit as st
from pysqlcipher3 import dbapi2 as sqlite3enc

class Database():
    def __init__(self):
        self.db = 'pbgui-share.db'
        self.key = st.secrets["db_key"]

    def fetch_positions(self, user: User):
        sql = '''SELECT * FROM "position"
                WHERE "position"."user" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user.name])
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)

    def fetch_orders(self, user: User):
        sql = '''SELECT * FROM "orders"
                WHERE "orders"."user" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user.name])
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)
    
    def fetch_orders_by_symbol(self, user: str, symbol: str):
        sql = '''SELECT * FROM "orders"
                WHERE "orders"."user" = ?
                    AND "orders"."symbol" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user, symbol])
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)

    def fetch_prices(self, user: User):
        sql = '''SELECT * FROM "prices"
                WHERE "prices"."user" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user.name])
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)

    def fetch_balances(self, user: list):
        sql = '''SELECT * FROM "balances"
                WHERE "balances"."user" IN ({}) '''.format(','.join('?'*len(user)))
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, user)
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)

    def fetch_ohlcv(self, user: User, symbol: str):
        sql = '''SELECT * FROM "ohlcv"
                WHERE "ohlcv"."user" = ?
                    AND "ohlcv"."symbol" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user.name, symbol])
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)

    def select_top(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        top = 500
        sql = '''SELECT strftime('%Y-%m-%d',"timestamp" / 1000, 'unixepoch') as date, "history"."symbol" AS symbol, SUM("history"."income") AS sum FROM "history"
                WHERE "history"."user" = ?
                    AND "history"."timestamp" >= ?
                    AND "history"."timestamp" <= ?
                GROUP BY "history"."symbol"
                ORDER BY "sum" DESC, "history"."symbol"
                LIMIT ? '''
        sql_parameters = (user.name, start, end, top)
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, sql_parameters)
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)
        
    def select_pnl(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        sql = '''SELECT strftime('%Y-%m-%d',"timestamp" / 1000, 'unixepoch') as date, SUM("income") AS "sum" FROM "history"
                WHERE "history"."user" = ?
                    AND "history"."timestamp" >= ?
                    AND "history"."timestamp" <= ?
                GROUP BY date'''
        sql_parameters = (user.name, start, end)
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, sql_parameters)
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)
    
    def select_income(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        sql = '''SELECT "timestamp", "income" FROM "history"
                WHERE "history"."user" IN ({})
                    AND "history"."timestamp" >= ?
                    AND "history"."timestamp" <= ?
                ORDER BY "timestamp" ASC'''.format(','.join('?'*len(user)))
        sql_parameters = tuple(user) + (start, end)
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, sql_parameters)
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)
    
    # select income grouped by symbol not sum
    def select_income_by_symbol(self, user: User):
        start = self.find_first_timestamp(user)
        end = self.find_last_timestamp(user)
        sql = '''SELECT "timestamp", "symbol", "income" FROM "history"
                WHERE "history"."user" = ?
                    AND "history"."timestamp" >= ?
                    AND "history"."timestamp" <= ?
                ORDER BY "timestamp" ASC'''
        sql_parameters = (user.name, start, end)
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, sql_parameters)
                rows = cur.fetchall()
                return rows
        except sqlite3enc.Error as e:
            print(e)

    def find_last_timestamp(self, user: User):
        sql = '''SELECT MAX("history"."timestamp") FROM "history"
                WHERE "history"."user" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user.name])
                rows = cur.fetchall()
                if rows[0][0] is None:
                    return 0
                return rows[0][0]
        except sqlite3enc.Error as e:
            print(e)
    
    def find_first_timestamp(self, user: User):
        sql = '''SELECT MIN("history"."timestamp") FROM "history"
                WHERE "history"."user" = ? '''
        try:
            with sqlite3enc.connect(self.db) as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA key = {self.key}")
                cur.execute(sql, [user.name])
                rows = cur.fetchall()
                if rows[0][0] is None:
                    return 0
                return rows[0][0]
        except sqlite3enc.Error as e:
            print(e)

    # Copy data from unencrypted db to encrypted db where user is user
    def copy_user(self, source: Path, user: User):
        try:
            with sqlite3.connect(source) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM position WHERE user = '{user.name}'")
                rows = cursor.fetchall()
                with sqlite3enc.connect(self.db) as conn:
                    cur = conn.cursor()
                    cur.execute(f"PRAGMA key = {self.key}")
                    sql = """CREATE TABLE IF NOT EXISTS position (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        psize REAL NOT NULL,
                        upnl REAL NOT NULL,
                        entry REAL NOT NULL,
                        user TEXT NOT NULL)"""
                    cur.execute(sql)
                    cur.execute(f"DELETE FROM position WHERE user = '{user.name}'")
                    cur.executemany('INSERT INTO position VALUES (?,?,?,?,?,?,?)', rows)
                    conn.commit()
                cursor.execute(f"SELECT * FROM orders WHERE user = '{user.name}'")
                rows = cursor.fetchall()
                with sqlite3enc.connect(self.db) as conn:
                    cur = conn.cursor()
                    cur.execute(f"PRAGMA key = {self.key}")
                    sql = """CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        price REAL NOT NULL,
                        side TEXT NOT NULL,
                        uniqueid text NOT NULL UNIQUE,
                        user TEXT NOT NULL)"""
                    cur.execute(sql)
                    cur.execute(f"DELETE FROM orders WHERE user = '{user.name}'")
                    cur.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)', rows)
                    conn.commit()
                cursor.execute(f"SELECT * FROM prices WHERE user = '{user.name}'")
                rows = cursor.fetchall()
                with sqlite3enc.connect(self.db) as conn:
                    cur = conn.cursor()
                    cur.execute(f"PRAGMA key = {self.key}")
                    sql = """CREATE TABLE IF NOT EXISTS prices (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        price REAL NOT NULL,
                        user TEXT NOT NULL)"""
                    cur.execute(sql)
                    cur.execute(f"DELETE FROM prices WHERE user = '{user.name}'")
                    cur.executemany('INSERT INTO prices VALUES (?,?,?,?,?)', rows)
                    conn.commit()
                cursor.execute(f"SELECT * FROM history WHERE user = '{user.name}'")
                rows = cursor.fetchall()
                with sqlite3enc.connect(self.db) as conn:
                    cur = conn.cursor()
                    cur.execute(f"PRAGMA key = {self.key}")
                    sql = """CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        income REAL NOT NULL,
                        uniqueid text NOT NULL UNIQUE,
                        user TEXT NOT NULL)"""
                    cur.execute(sql)
                    cur.execute(f"DELETE FROM history WHERE user = '{user.name}'")
                    cur.executemany('INSERT INTO history VALUES (?,?,?,?,?,?)', rows)
                    conn.commit()
        except sqlite3.Error as e:
            print(e)




        # try:
        #     with sqlite3.connect(source) as conn:
        #         cursor = conn.cursor()
        #         cursor.execute(f"ATTACH DATABASE '{self.db}' AS dest")
        #         cursor.execute(f"CREATE TABLE IF NOT EXISTS dest.position AS SELECT * FROM position WHERE user = '{user.name}'")
        #         cursor.execute(f"DELETE FROM dest.position WHERE user = '{user.name}'")
        #         cursor.execute(f"INSERT INTO dest.position SELECT * FROM position WHERE user = '{user.name}'")
        #         cursor.execute(f"CREATE TABLE IF NOT EXISTS dest.orders AS SELECT * FROM orders WHERE user = '{user.name}'")
        #         cursor.execute(f"DELETE FROM dest.orders WHERE user = '{user.name}'")
        #         cursor.execute(f"INSERT INTO dest.orders SELECT * FROM orders WHERE user = '{user.name}'")
        #         cursor.execute(f"CREATE TABLE IF NOT EXISTS dest.prices AS SELECT * FROM prices WHERE user = '{user.name}'")
        #         cursor.execute(f"DELETE FROM dest.prices WHERE user = '{user.name}'")
        #         cursor.execute(f"INSERT INTO dest.prices SELECT * FROM prices WHERE user = '{user.name}'")
        #         conn.commit()
        # except sqlite3.Error as e:
        #     print(e)
    
    def add_ohlcv(self, user: User):
        # get symbols from table dest.orders
        try:
            with sqlite3enc.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA key = {self.key}")
                cursor.execute(f"SELECT DISTINCT symbol FROM orders WHERE user = '{user.name}'")
                rows = cursor.fetchall()
                symbols = []
                for row in rows:
                    symbols.append(row[0])
                # fetch ohlcv from exchange
                exchange = Exchange(user.exchange, user)
                for symbol in symbols:
                    if symbol[-4:] == "USDT":
                        symbol_ccxt = f'{symbol[0:-4]}/USDT:USDT'
                    elif symbol[-4:] == "USDC":
                        symbol_ccxt = f'{symbol[0:-4]}/USDC:USDC'
                    ohlcv = exchange.fetch_ohlcv(symbol_ccxt, "futures", "1h", 100)
                    #add new table ohlcv with user, symbol and ohlcv dataframe
                    ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    ohlcv_df['user'] = user.name
                    ohlcv_df['symbol'] = symbol
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS ohlcv (timestamp INTEGER, open REAL, high REAL, low REAL, close REAL, volume REAL, user TEXT, symbol TEXT)")
                    cursor.execute(f"DELETE FROM ohlcv WHERE user = '{user.name}' AND symbol = '{symbol}'")
                    cursor.executemany('INSERT INTO ohlcv VALUES (?,?,?,?,?,?,?,?)', ohlcv_df.values.tolist())
                conn.commit()
        except sqlite3enc.Error as e:
            print(e)


def main():
    print("Don't Run this Class from CLI")

if __name__ == '__main__':
    main()
