import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="CSE Pro Analyzer", page_icon="📈", layout="wide")

BASE_URL = "https://www.cse.lk/api/"

@st.cache_data(ttl=300)
def fetch_cse(endpoint, payload=None):
    try:
        response = requests.post(BASE_URL + endpoint, data=payload or {}, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Initialize session state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Symbol", "Company", "Quantity", "Buy Price", "Current Price"])
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

st.title("📊 CSE Pro Analyzer & Portfolio Tracker")
st.caption("Your personal Colombo Stock Exchange dashboard • Educational use only")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Select Page", 
    ["Market Overview", "Stock Analyzer", "Portfolio Tracker", "Watchlist", "Technical Analysis"])

symbol = st.sidebar.text_input("Stock Symbol (e.g. JKH.N0000)", "JKH.N0000").upper()

# ====================== PORTFOLIO TRACKER ======================
if page == "Portfolio Tracker":
    st.header("💼 My Portfolio")
    
    col1, col2 = st.columns([3, 2])
    with col1:
        new_symbol = st.text_input("Add Symbol", key="add_sym")
        qty = st.number_input("Quantity", min_value=1, value=100)
        buy_price = st.number_input("Buy Price (Rs.)", min_value=0.0, value=100.0)
        
        if st.button("Add to Portfolio"):
            data = fetch_cse("companyInfoSummery", {"symbol": new_symbol})
            if data and "reqSymbolInfo" in data:
                info = data["reqSymbolInfo"]
                current = info.get('lastTradedPrice', buy_price)
                
                new_row = pd.DataFrame([{
                    "Symbol": new_symbol,
                    "Company": info.get('name', new_symbol),
                    "Quantity": qty,
                    "Buy Price": buy_price,
                    "Current Price": current
                }])
                st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
                st.success(f"Added {new_symbol}")
            else:
                st.error("Symbol not found")

    # Display Portfolio
    if not st.session_state.portfolio.empty:
        df = st.session_state.portfolio.copy()
        df["Value"] = df["Quantity"] * df["Current Price"]
        df["Gain/Loss"] = (df["Current Price"] - df["Buy Price"]) * df["Quantity"]
        df["Gain%"] = ((df["Current Price"] - df["Buy Price"]) / df["Buy Price"]) * 100
        
        total_value = df["Value"].sum()
        total_gain = df["Gain/Loss"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Portfolio Value", f"Rs. {total_value:,.2f}")
        c2.metric("Total P&L", f"Rs. {total_gain:,.2f}", delta=f"{(total_gain/total_value*100):.1f}%" if total_value else 0)
        
        st.dataframe(df, use_container_width=True)
        
        if st.button("Export Portfolio to Excel"):
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    else:
        st.info("Your portfolio is empty. Add some stocks!")

# ====================== WATCHLIST ======================
elif page == "Watchlist":
    st.header("⭐ My Watchlist")
    add_w = st.text_input("Add symbol to watchlist")
    if st.button("Add") and add_w:
        if add_w not in st.session_state.watchlist:
            st.session_state.watchlist.append(add_w.upper())
    
    if st.session_state.watchlist:
        for s in st.session_state.watchlist[:]:
            col1, col2 = st.columns([4,1])
            with col1:
                data = fetch_cse("companyInfoSummery", {"symbol": s})
                if data and "reqSymbolInfo" in data:
                    i = data["reqSymbolInfo"]
                    st.metric(f"{s} - {i.get('name','')}", 
                             f"Rs. {i.get('lastTradedPrice')}", 
                             f"{i.get('changePercentage')}%")
            with col2:
                if st.button("Remove", key=f"rem_{s}"):
                    st.session_state.watchlist.remove(s)
                    st.rerun()
    else:
        st.info("Your watchlist is empty.")

# ====================== TECHNICAL ANALYSIS ======================
elif page == "Technical Analysis":
    st.header("📉 Technical Analysis")
    if st.button("Analyze " + symbol):
        chart_data = fetch_cse("companyChartDataByStock", {"stockId": symbol, "period": "5"})
        if chart_data:
            try:
                trades = chart_data.get("reqTradeSummery", {}).get("chartData", [])
                df = pd.DataFrame(trades)
                if not df.empty and 'p' in df.columns:
                    df = df.rename(columns={'p': 'Close', 't': 'Date'})
                    df['Close'] = pd.to_numeric(df['Close'])
                    
                    # Moving Averages
                    df['SMA_10'] = df['Close'].rolling(10).mean()
                    df['SMA_20'] = df['Close'].rolling(20).mean()
                    
                    # Simple RSI
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss
                    df['RSI'] = 100 - (100 / (1 + rs))
                    
                    fig = px.line(df, x=df.index, y=['Close', 'SMA_10', 'SMA_20'], 
                                title=f"{symbol} - Price & Moving Averages")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig2 = px.line(df, x=df.index, y='RSI', title="RSI (14)")
                    fig2.add_hline(y=70, line_dash="dash", line_color="red")
                    fig2.add_hline(y=30, line_dash="dash", line_color="green")
                    st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error("Not enough data for technical indicators yet.")

# Other pages (Overview, Analyzer) - keep your previous logic or let me know if you want them enhanced too.

else:
    # Keep your previous Market Overview and Stock Analyzer here if needed
    st.info("Select a page from the sidebar")

st.caption("Data from cse.lk • Not financial advice • Always verify with official sources")
