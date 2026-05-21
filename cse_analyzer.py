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

# Initialize session state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Symbol", "Company", "Quantity", "Buy Price", "Current Price"])
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

st.title("📊 CSE Pro Analyzer - Colombo Stock Exchange")
st.caption("Real-time Market Overview • Analysis • Portfolio • Educational Tool Only")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", 
    ["Market Overview", "Stock Analyzer", "Technical Analysis", "Portfolio Tracker", "Watchlist"])

symbol = st.sidebar.text_input("🔎 Enter Symbol (e.g. JKH.N0000, LOLC.N0000)", "JKH.N0000").upper()

# ====================== MARKET OVERVIEW ======================
if page == "Market Overview":
    st.header("🌍 Market Overview")
    
    col1, col2 = st.columns(2)
    with col1:
        summary = fetch_cse("marketSummery")
        if summary:
            st.success("Market Summary Loaded")
            st.json(summary)  # You can beautify this later
    
    daily = fetch_cse("dailyMarketSummery")
    if daily:
        st.subheader("Daily Market Summary")
        st.write(daily)
    
    st.subheader("🚀 Top Gainers")
    gainers = fetch_cse("topGainers")
    if gainers:
        df_g = pd.DataFrame(gainers)
        st.dataframe(df_g, use_container_width=True)
    
    st.subheader("📉 Top Losers")
    losers = fetch_cse("topLooses")
    if losers:
        df_l = pd.DataFrame(losers)
        st.dataframe(df_l, use_container_width=True)

# ====================== STOCK ANALYZER ======================
elif page == "Stock Analyzer":
    st.header(f"🔍 Analysis: {symbol}")
    
    if st.button("Fetch Latest Data"):
        with st.spinner("Fetching company data..."):
            data = fetch_cse("companyInfoSummery", {"symbol": symbol})
            
            if data and "reqSymbolInfo" in data:
                info = data["reqSymbolInfo"]
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Last Traded Price", f"Rs. {info.get('lastTradedPrice')}")
                c2.metric("Change", f"{info.get('change')} ({info.get('changePercentage')}%)")
                c3.metric("Market Cap", f"Rs. {info.get('marketCap', 0)/1e9:.2f} Bn")
                c4.metric("Company", info.get('name', symbol))
                
                # Additional info
                st.write("**More Details:**")
                st.json(info)
            else:
                st.error("Could not fetch data for this symbol. Try JKH.N0000 or LOLC.N0000")

# ====================== TECHNICAL ANALYSIS ======================
elif page == "Technical Analysis":
    st.header("📉 Technical Analysis")
    period = st.selectbox("Chart Period", ["1", "5", "10"], index=1)
    
    if st.button(f"Load Chart for {symbol}"):
        chart_data = fetch_cse("companyChartDataByStock", {"stockId": symbol, "period": period})
        if chart_data:
            try:
                trades = chart_data.get("reqTradeSummery", {}).get("chartData", [])
                df = pd.DataFrame(trades)
                if not df.empty:
                    df = df.rename(columns={'p': 'Close'}).reset_index(drop=True)
                    df['Close'] = pd.to_numeric(df['Close'])
                    
                    df['SMA_10'] = df['Close'].rolling(10).mean()
                    df['SMA_20'] = df['Close'].rolling(20).mean()
                    
                    # RSI
                    delta = df['Close'].diff()
                    gain = delta.where(delta > 0, 0).rolling(14).mean()
                    loss = -delta.where(delta < 0, 0).rolling(14).mean()
                    rs = gain / loss
                    df['RSI'] = 100 - (100 / (1 + rs))
                    
                    fig = px.line(df, y=['Close', 'SMA_10', 'SMA_20'], title=f"{symbol} Price & Moving Averages")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig2 = px.line(df, y='RSI', title="RSI Indicator")
                    fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                    fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                    st.plotly_chart(fig2, use_container_width=True)
            except:
                st.warning("Not enough data for indicators yet.")

# Portfolio and Watchlist pages remain the same as previous version
elif page == "Portfolio Tracker":
    # (Paste the Portfolio code from my previous message here)
    st.info("Portfolio Tracker - Add stocks using the form")
    # ... (I can send full code again if needed)

else:
    st.info("Select a page from the sidebar to begin.")

st.caption("📌 Data from cse.lk • Not financial advice • Always do your own research")
