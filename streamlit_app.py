import streamlit as st
from Database import Database
from User import Users, User
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import numpy as np

def set_page_config():
    st.set_page_config(
        page_title=f"PBGUI - Dashboard Share",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get help': 'https://github.com/msei99/pbgui/#readme',
            'About': "Passivbot GUI v1.12"
        }
    )

def view():
    user = st.session_state.view
    st.markdown(f'#### Copy Trading: [{user.name}](%s)' % user.url)
    view_positions(user)
    view_orders()

def color_upnl(value):
    color = "red" if value < 0 else "green"
    return f"color: {color};"

@st.fragment
def view_positions(user : User):
    users = st.session_state.users
    db = st.session_state.db
    st.markdown("#### :blue[Positions]")
    # Init view_orders that it can be selected in edit mode
    if f"dashboard_positions" in st.session_state:
        if st.session_state[f'dashboard_positions']["selection"]["rows"]:
            row = st.session_state[f'dashboard_positions']["selection"]["rows"][0]
            st.session_state[f'view_orders'] = st.session_state[f'dashboard_positions_sdf'].iloc[row]
            st.rerun()
    all_positions = []
    positions = db.fetch_positions(user)
    prices = db.fetch_prices(user)
    for pos in positions:
        symbol = pos[1]
        user = pos[6]
        orders = db.fetch_orders_by_symbol(user, symbol)
        dca = 0
        next_tp = 0
        next_dca = 0
        for order in orders:
            # print(order)
            if order[5] == "buy":
                dca += 1
                if next_dca < order[4]:
                    next_dca = order[4]
            elif order[5] == "sell":
                if next_tp == 0 or next_tp > order[4]:
                    next_tp = order[4]
        # Find price from prices
        price = 0
        if prices:
            for p in prices:
                if p[1] == symbol:
                    price = p[3]
        all_positions.append(tuple(pos) + (price,) + (dca,) + (next_dca,) + (next_tp,))
    df = pd.DataFrame(all_positions, columns =['Id', 'Symbol', 'PosId', 'Size', 'uPnl', 'Entry', 'User', 'Price', 'DCA', 'Next DCA', 'Next TP'])
    # sorty df by User, Symbol
    df = df.sort_values(by=['User', 'Symbol'])
    # Move User to second column
    df = df[['Id', 'User', 'Symbol', 'PosId', 'Size', 'uPnl', 'Entry', 'Price', 'DCA', 'Next DCA', 'Next TP']]
    sdf = df.style.applymap(color_upnl, subset=['uPnl']).format({'Size': "{:.3f}"})
    st.session_state[f'dashboard_positions_sdf'] = df
    column_config = {
        "Id": None,
        "PosId": None
    }
    st.dataframe(sdf, height=36+(len(df))*35, use_container_width=True, key=f"dashboard_positions", on_select="rerun", selection_mode='single-row', hide_index=None, column_order=None, column_config=column_config)

@st.fragment
def view_orders():
    db = st.session_state.db
    position = None
    if "view_orders" in st.session_state:
        position = st.session_state["view_orders"]
    st.markdown("#### :blue[Orders]")
    if position is None:
        return
    users = st.session_state.users
    user = users.find_user(position["User"])
    symbol = position["Symbol"]
    # symbol to ccxt_symbol
    if symbol[-4:] == "USDT":
        symbol_ccxt = f'{symbol[0:-4]}/USDT:USDT'
    elif symbol[-4:] == "USDC":
        symbol_ccxt = f'{symbol[0:-4]}/USDC:USDC'
    ohlcv = db.fetch_ohlcv(user, symbol)
    ohlcv_df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'user', 'symbol'])
    ohlcv_df["color"] = np.where(ohlcv_df["close"] > ohlcv_df["open"], "green", "red")
    # w = (ohlcv_df["timestamp"][1] - ohlcv_df["timestamp"][0]) * 0.8
    prices = db.fetch_prices(user)
    price = 0
    for p in prices:
        if p[1] == symbol:
            price = p[3]
            timestamp = p[2]
    time = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.2])
    with col1:
        st.markdown(f"#### :blue[User:] :green[{user.name}]")
    with col2:
        st.markdown(f"#### :blue[Symbol:] :green[{symbol}]")
    with col3:
        st.markdown(f"#### :blue[UTC:] :green[{time}]")
    with col4:
        if st.button(":material/refresh:", key=f"dashboard_orders_rerun"):
            st.rerun(scope="fragment")
    # layout = go.Layout(title=f'{symbol} | {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC', title_font=dict(size=36), showlegend=True)
    fig = go.Figure(data=[go.Candlestick(x=pd.to_datetime(ohlcv_df["timestamp"], unit='ms'),
           open=ohlcv_df["open"], high=ohlcv_df["high"],
           low=ohlcv_df["low"], close=ohlcv_df["close"],
           increasing_line_color='green', decreasing_line_color='red')])
    # remove legend from trace 0
    fig.data[0].showlegend = False
    fig.update_layout(yaxis=dict(title='USDT', title_font=dict(size=24)), xaxis_rangeslider_visible=False, height=800, xaxis_type='category')
    fig.update_layout(xaxis_rangeslider_visible=False, xaxis_tickformat='%H:%M')
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=14), dtick='8')
    # fig.update_layout(xaxis_rangeslider_visible=False, width=1280, height=1024)
    orders = db.fetch_orders_by_symbol(user.name, symbol)
    color = "red" if price < ohlcv_df["open"].iloc[-1] else "green"
    # add price line to candlestick
    fig.add_trace(go.Scatter(x=pd.to_datetime(ohlcv_df["timestamp"], unit='ms'), y=[price] * len(ohlcv_df), mode='lines', line=dict(color=color, width=1), name=f'price: {str(round(price,5))}'))
    # position
    color = "red" if price < position["Entry"] else "green"
    size = position["Size"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(ohlcv_df["timestamp"], unit='ms'),
                            y=[position["Entry"]] * len(ohlcv_df), mode='lines',
                            line=dict(color=color, width=1, dash = 'dash'),
                            name=f'position: {str(round(position["Entry"],5))} size: {str(size)}<br>Pnl: {str(round(position["uPnl"],5))}'))
    amount = 3
    price = 4
    side = 5
    orders = sorted(orders, key=lambda x: x[price], reverse=True)
    for order in orders:
        color = "red" if order[side] == "sell" else "green"
        legend = f'close: {str(order[price])} amount: {str(order[amount])}' if order[side] == "sell" else f'open: {str(order[price])} amount: {str(order[amount])}'
        fig.add_trace(go.Scatter(x=pd.to_datetime(ohlcv_df["timestamp"], unit='ms'),
                                y=[order[price]] * len(ohlcv_df),
                                mode='lines',
                                line=dict(color=color, width=2, dash = 'dot'), name=legend))
    fig.update_layout(legend = dict(font = dict(size = 14)))
    st.plotly_chart(fig, key=f"dashboard_orders")

set_page_config()
st.title("PBGui - Dashboard Share")

if "users" not in st.session_state:
    st.session_state.users = Users()
if "db" not in st.session_state:
    st.session_state.db = Database()
with st.sidebar:
    for user in st.session_state.users:
        if st.button(user.name):
            if f"dashboard_positions" in st.session_state:
                del st.session_state.dashboard_positions
            if f"view_orders" in st.session_state:
                del st.session_state.view_orders
            st.session_state.view = user

if "view" in st.session_state:
    view()