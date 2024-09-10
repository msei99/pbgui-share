import streamlit as st
from MySQLDatabase import Database
from User import Users, User
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def set_page_config():
    st.set_page_config(
        page_title=f"PBGui - Dashboard Share",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get help': 'https://github.com/msei99/pbgui-share/#readme',
            'About': "PBGui Dashboard Share v0.95"
        }
    )

def view():
    user = st.session_state.view
    st.markdown(f'#### Copy Trading: [{user.name}](%s)' % user.url)
    view_pnl(user)
    view_income(user)
    view_top_symbols(user)
    view_positions(user)
    view_orders()

def color_upnl(value):
    color = "red" if value < 0 else "green"
    return f"color: {color};"

@st.fragment
def view_top_symbols(user : User):
    db = st.session_state.db
    st.markdown("#### :blue[Top Symbols]")
    top = db.select_top(user)
    df = pd.DataFrame(top, columns =['Symbol', 'Income'])
    # st.write(df)
    fig = px.bar(df, x="Symbol", y="Income")
    fig.update_traces(marker_color=['red' if val < 0 else 'green' for val in df['Income']])
    st.plotly_chart(fig, key=f"dashboard_top_symbols_plot")

@st.fragment
def view_pnl(user : User):
    db = st.session_state.db
    st.markdown("#### :blue[Daily PNL]")
    pnl = db.select_pnl(user)
    df = pd.DataFrame(pnl, columns =['Date', 'Income'])
    fig = px.bar(df, x='Date', y='Income', text='Income', hover_data={'Income':':.2f'})
    fig.update_traces(texttemplate='%{text:.2f}', textposition='auto')
    fig.update_traces(marker_color=['red' if val < 0 else 'green' for val in df['Income']])
    st.plotly_chart(fig, key=f"dashboard_pnl_plot")

@st.fragment
def view_income(user : User):
    db = st.session_state.db
    st.markdown("#### :blue[Income]")
    income = db.select_income_by_symbol(user)
    df = pd.DataFrame(income, columns=['Date', 'Symbol', 'Income'])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    income = df[['Date', 'Symbol', 'Income']].copy()
    income['Income'] = income['Income'].cumsum()
    fig = px.line(income, x='Date', y='Income', hover_data={'Income':':.2f'})
    # fig = px.line(income, x='Date', y='Income', hover_data={'Income':':.2f'}, title=f"From: {df['Date'].min()} To: {df['Date'].max()}")
    fig.update_layout(height=800)
    fig['data'][0]['showlegend'] = True
    fig['data'][0]['name'] = 'Total Income'
    # Sort df by Symbol
    df = df.sort_values(by=['Symbol', 'Date'])
    for symbol in df['Symbol'].unique():
        symbol_df = df[df['Symbol'] == symbol].copy()
        symbol_df['Income'] = symbol_df['Income'].cumsum()
        fig.add_trace(go.Scatter(x=symbol_df['Date'], y=symbol_df['Income'], name=symbol))
    fig.update_traces(visible="legendonly")
    fig['data'][0].visible=True
    st.plotly_chart(fig, key=f"dashboard_income_plot")

@st.fragment
def view_positions(user : User):
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
    for index, pos in positions.iterrows():
        symbol = pos.iloc[1]
        user = pos.iloc[6]
        orders = db.fetch_orders_by_symbol(user, symbol)
        dca = 0
        next_tp = 0
        next_dca = 0
        for index, order in orders.iterrows():
            if order.iloc[5] == "buy":
                dca += 1
                if next_dca < order[4]:
                    next_dca = order[4]
            elif order.iloc[5] == "sell":
                if next_tp == 0 or next_tp > order.iloc[4]:
                    next_tp = order.iloc[4]
        # Find price from prices
        price = 0
        if not prices.empty:
            for index, p in prices.iterrows():
                if p.iloc[1] == symbol:
                    price = p.iloc[3]
        all_positions.append(tuple(pos) + (price,) + (dca,) + (next_dca,) + (next_tp,))
    df = pd.DataFrame(all_positions, columns =['Id', 'Symbol', 'PosId', 'Size', 'uPnl', 'Entry', 'User', 'Price', 'DCA', 'Next DCA', 'Next TP'])
    # sorty df by User, Symbol
    df = df.sort_values(by=['User', 'Symbol'])
    # Move User to second column
    df = df[['Id', 'User', 'Symbol', 'PosId', 'Size', 'uPnl', 'Entry', 'Price', 'DCA', 'Next DCA', 'Next TP']]
    sdf = df.style.format({'Size': "{:.3f}"}).applymap(color_upnl, subset=['uPnl'])
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
    prices = db.fetch_prices(user)
    price = 0
    for index, p in prices.iterrows():
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
    fig.update_xaxes(tickangle=-90, tickfont=dict(size=14), dtick='12')
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
    # Sort orders df by price
    orders = orders.sort_values(by=['price'])
    for index, order in orders.iterrows():
        color = "red" if order[side] == "sell" else "green"
        legend = f'close: {str(order[price])} amount: {str(order[amount])}' if order[side] == "sell" else f'open: {str(order[price])} amount: {str(order[amount])}'
        fig.add_trace(go.Scatter(x=pd.to_datetime(ohlcv_df["timestamp"], unit='ms'),
                                y=[order[price]] * len(ohlcv_df),
                                mode='lines',
                                line=dict(color=color, width=2, dash = 'dot'), name=legend))
    fig.update_layout(legend = dict(font = dict(size = 14)))
    #legend position left
    fig.update_layout(legend=dict(x=0, y=0))
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