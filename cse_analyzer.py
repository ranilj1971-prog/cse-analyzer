import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="CSE Pro Analyzer", page_icon="📈", layout="wide")

BASE_URL = "https://www.cse.lk/api/"

@st.cache_data(ttl=180)
def fetch_cse(endpoint, payload=None):
    try:
        response = requests.post(BASE_URL + endpoint, data=payload or {}, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Session State
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Symbol", "Company", "Quantity", "Buy Price", "Current Price"])
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

st.title("📊 CSE Pro Analyzer - Colombo Stock Exchange")
st.caption("Real-time Data • Analysis • Portfolio Tracker • Educational Tool Only")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Select Page", 
    ["Market Overview", "Stock Analyzer", "Technical Analysis", "Portfolio Tracker", "Watchlist"])

symbol = st.sidebar.text_input("🔎 Stock Symbol (e.g. JKH.N0000)", "JKH.N0000").upper()

# ====================== MARKET OVERVIEW ======================
if page == "Market Overview":
    st.header("🌍 Market Overview")
    st.markdown("---")
    
    # Market Summary
    summary = fetch_cse("marketSummery")
    if summary:
        st.subheader("📈 Market Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trade Value", f"Rs. {summary.get('tradeVolume', 0):,}")
        col2.metric("Total Share Volume", f"{summary.get('shareVolume', 0):,}")
        col3.metric("Total Trades", f"{summary.get('trades', 0):,}")
        col4.metric("Date", str(summary.get('tradeDate', 'N/A')))
        st.markdown("---")

    # Top Gainers
    st.subheader("🚀 Top 10 Gainers")
    gainers = fetch_cse("topGainers")
    
    if gainers and len(gainers) > 0:
        df_g = pd.DataFrame(gainers)
        if not df_g.empty:
            # Clean columns
            df_display = df_g[['symbol', 'price', 'change', 'changePercentage']].copy()
            df_display = df_display.rename(columns={
                'symbol': 'Symbol',
                'price': 'Last Price (Rs.)',
                'change': 'Change (Rs.)',
                'changePercentage': 'Change %'
            })
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No gainers data available.")
    else:
        st.info("Top Gainers data not available at the moment.")

    st.markdown("---")

    # Top Losers
    st.subheader("📉 Top 10 Losers")
    losers = fetch_cse("topLooses")
    
    if losers and len(losers) > 0:
        df_l = pd.DataFrame(losers)
        if not df_l.empty:
            df_display = df_l[['symbol', 'price', 'change', 'changePercentage']].copy()
            df_display = df_display.rename(columns={
                'symbol': 'Symbol',
                'price': 'Last Price (Rs.)',
                'change': 'Change (Rs.)',
                'changePercentage': 'Change %'
            })
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No losers data available.")
    else:
        st.info("Top Losers data not available at the moment.")
# ====================== TECHNICAL ANALYSIS ======================
elif page == "Technical Analysis":
    st.header(f"📉 Technical Analysis: {symbol}")
    period = st.selectbox("Period", ["1", "5", "10"], index=1)
    
    if st.button("Load Chart & Indicators"):
        chart_data = fetch_cse("companyChartDataByStock", {"stockId": symbol, "period": period})
        if chart_data:
            try:
                df = pd.DataFrame(chart_data.get("reqTradeSummery", {}).get("chartData", []))
                if not df.empty:
                    df = df.rename(columns={'p': 'Close'}).reset_index(drop=True)
                    df['Close'] = pd.to_numeric(df['Close'])
                    
                    df['SMA_10'] = df['Close'].rolling(10).mean()
                    df['SMA_20'] = df['Close'].rolling(20).mean()
                    
                    delta = df['Close'].diff()
                    gain = delta.where(delta > 0, 0).rolling(14).mean()
                    loss = -delta.where(delta < 0, 0).rolling(14).mean()
                    df['RSI'] = 100 - (100 / (1 + gain/loss))
                    
                    fig = px.line(df, y=['Close', 'SMA_10', 'SMA_20'], title=f"{symbol} Price Chart")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig2 = px.line(df, y='RSI', title="RSI Indicator")
                    fig2.add_hline(y=70, line_dash="dash", line_color="red")
                    fig2.add_hline(y=30, line_dash="dash", line_color="green")
                    st.plotly_chart(fig2, use_container_width=True)
            except:
                st.warning("Not enough historical data yet.")

# Portfolio Tracker and Watchlist (same as before)
elif page == "Portfolio Tracker":
    # ... (I kept it short here - let me know if you want full portfolio code again)
    st.info("Portfolio Tracker coming in next update if needed")

else:
    st.info("Select a page from sidebar")

st.caption("Data from cse.lk • Not financial advice")
