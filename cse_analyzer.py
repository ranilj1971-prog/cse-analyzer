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
st.caption("Market Overview • Stock Analysis • Technicals • Portfolio • Educational Tool Only")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Select Page", 
    ["Market Overview", "Stock Analyzer", "Technical Analysis", "Portfolio Tracker", "Watchlist"])

symbol = st.sidebar.text_input("🔎 Stock Symbol (e.g. JKH.N0000, LOLC.N0000)", "JKH.N0000").upper()

# ====================== MARKET OVERVIEW ======================
if page == "Market Overview":
    st.header("🌍 Market Overview")
    
    summary = fetch_cse("marketSummery")
    if summary:
        st.subheader("Market Summary")
        st.json(summary)
    
    st.subheader("🚀 Top Gainers")
    gainers = fetch_cse("topGainers")
    if gainers:
        st.dataframe(pd.DataFrame(gainers), use_container_width=True)
    
    st.subheader("📉 Top Losers")
    losers = fetch_cse("topLooses")
    if losers:
        st.dataframe(pd.DataFrame(losers), use_container_width=True)

# ====================== STOCK ANALYZER ======================
elif page == "Stock Analyzer":
    st.header(f"🔍 Detailed Analysis: {symbol}")
    
    if st.button("Fetch Latest Data", type="primary"):
        with st.spinner("Fetching data..."):
            data = fetch_cse("companyInfoSummery", {"symbol": symbol})
            
            if data and "reqSymbolInfo" in data:
                info = data["reqSymbolInfo"]
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Last Price", f"Rs. {info.get('lastTradedPrice')}")
                c2.metric("Change", f"{info.get('change')} ({info.get('changePercentage')}%)")
                c3.metric("Market Cap", f"Rs. {info.get('marketCap', 0)/1e9:.2f} Bn")
                c4.metric("Volume", info.get('tradeVolume', 'N/A'))
                
                st.subheader("Company Information")
                st.json(info)
            else:
                st.error("Symbol not found or no data available. Try JKH.N0000, LOLC.N0000, etc.")

# ====================== TECHNICAL ANALYSIS ======================
elif page == "Technical Analysis":
    st.header(f"📉 Technical Analysis: {symbol}")
    period = st.selectbox("Select Period", ["1", "5", "10"], index=1)
    
    if st.button("Load Chart & Indicators", type="primary"):
        with st.spinner("Loading chart..."):
            chart_data = fetch_cse("companyChartDataByStock", {"stockId": symbol, "period": period})
            
            if chart_data:
                try:
                    trades = chart_data.get("reqTradeSummery", {}).get("chartData", [])
                    df = pd.DataFrame(trades)
                    if not df.empty:
                        df = df.rename(columns={'p': 'Close'}).reset_index(drop=True)
                        df['Close'] = pd.to_numeric(df['Close'])
                        
                        # Moving Averages
                        df['SMA_10'] = df['Close'].rolling(10).mean()
                        df['SMA_20'] = df['Close'].rolling(20).mean()
                        
                        # RSI
                        delta = df['Close'].diff()
                        gain = delta.where(delta > 0, 0).rolling(14).mean()
                        loss = -delta.where(delta < 0, 0).rolling(14).mean()
                        rs = gain / loss
                        df['RSI'] = 100 - (100 / (1 + rs))
                        
                        # Price Chart
                        fig = px.line(df, y=['Close', 'SMA_10', 'SMA_20'], 
                                    title=f"{symbol} - Price & Moving Averages")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # RSI Chart
                        fig2 = px.line(df, y='RSI', title="RSI (14)")
                        fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                        fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("Not enough data")
                except Exception as e:
                    st.error(f"Error processing chart: {e}")
            else:
                st.warning("Chart data not available right now.")

# ====================== PORTFOLIO TRACKER ======================
elif page == "Portfolio Tracker":
    st.header("💼 My Portfolio Tracker")
    
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        new_symbol = st.text_input("Symbol", key="p_sym")
    with col2:
        qty = st.number_input("Quantity", min_value=1, value=100)
    with col3:
        buy_price = st.number_input("Buy Price (Rs.)", min_value=0.0, value=100.0)
    
    if st.button("Add to Portfolio"):
        if new_symbol:
            data = fetch_cse("companyInfoSummery", {"symbol": new_symbol})
            if data and "reqSymbolInfo" in data:
                info = data["reqSymbolInfo"]
                current = float(info.get('lastTradedPrice', buy_price))
                
                new_row = {
                    "Symbol": new_symbol.upper(),
                    "Company": info.get('name', new_symbol),
                    "Quantity": qty,
                    "Buy Price": buy_price,
                    "Current Price": current
                }
                st.session_state.portfolio = pd.concat([st.session_state.portfolio, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Added {new_symbol}")
            else:
                st.error("Could not fetch current price")

    # Show Portfolio
    if not st.session_state.portfolio.empty:
        df = st.session_state.portfolio.copy()
        df["Value"] = df["Quantity"] * df["Current Price"]
        df["Gain/Loss"] = (df["Current Price"] - df["Buy Price"]) * df["Quantity"]
        df["Gain %"] = ((df["Current Price"] - df["Buy Price"]) / df["Buy Price"]) * 100
        
        total_value = df["Value"].sum()
        total_gain = df["Gain/Loss"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Value", f"Rs. {total_value:,.2f}")
        c2.metric("Total P&L", f"Rs. {total_gain:,.2f}")
        c3.metric("Overall Return", f"{(total_gain/total_value*100):.1f}%" if total_value > 0 else "0%")
        
        st.dataframe(df.round(2), use_container_width=True)
        
        if st.button("Export Portfolio to CSV"):
            csv = df.to_csv(index=False)
            st.download_button("Download CSV File", csv, f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    else:
        st.info("Portfolio is empty. Add stocks above.")

# ====================== WATCHLIST ======================
elif page == "Watchlist":
    st.header("⭐ My Watchlist")
    
    add_symbol = st.text_input("Add Symbol to Watchlist")
    if st.button("Add to Watchlist") and add_symbol:
        s = add_symbol.upper()
        if s not in st.session_state.watchlist:
            st.session_state.watchlist.append(s)
            st.success(f"Added {s}")
    
    if st.session_state.watchlist:
        for s in st.session_state.watchlist[:]:
            data = fetch_cse("companyInfoSummery", {"symbol": s})
            if data and "reqSymbolInfo" in data:
                i = data["reqSymbolInfo"]
                col1, col2 = st.columns([5,1])
                with col1:
                    st.metric(f"{s} - {i.get('name','')}", 
                             f"Rs. {i.get('lastTradedPrice')}", 
                             f"{i.get('changePercentage')}%")
                with col2:
                    if st.button("Remove", key=f"rm_{s}"):
                        st.session_state.watchlist.remove(s)
                        st.rerun()
    else:
        st.info("Your watchlist is empty.")

st.caption("Data Source: cse.lk • This is for educational purposes only • Not financial advice")
