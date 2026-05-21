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
st.caption("Real-time Data • Analysis • Portfolio • Educational Tool Only")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Select Page", 
    ["Market Overview", "Stock Analyzer", "Technical Analysis", "Portfolio Tracker", "Watchlist"])

symbol = st.sidebar.text_input("🔎 Stock Symbol (e.g. JKH.N0000)", "JKH.N0000").upper()
# ====================== MARKET OVERVIEW (Ultra Safe Version) ======================
if page == "Market Overview":
    st.header("🌍 Market Overview")
    st.markdown("---")
    
    # Market Summary
    summary = fetch_cse("marketSummery")
    if summary:
        st.subheader("📈 Today's Market Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", f"{summary.get('trades', 0):,}")
        col2.metric("Share Volume", f"{summary.get('shareVolume', 0):,}")
        col3.metric("Trade Value", f"Rs. {summary.get('tradeVolume', 0):,}")
        col4.metric("Date", str(summary.get('tradeDate', 'N/A')))
        st.markdown("---")

    # Top Gainers - Very Safe
    st.subheader("🚀 Top 10 Gainers")
    gainers = fetch_cse("topGainers")
    
    if gainers:
        try:
            df_g = pd.DataFrame(gainers)
            if not df_g.empty:
                # Show all columns first so we can see the structure
                st.dataframe(df_g, use_container_width=True, hide_index=True)
                st.caption("Raw data shown above for debugging. We will beautify it in next step.")
            else:
                st.info("No gainers data available.")
        except Exception as e:
            st.error(f"Error displaying gainers: {e}")
            st.write(gainers)  # fallback
    else:
        st.info("Top Gainers data not available right now.")

    st.markdown("---")

    # Top Losers - Very Safe
    st.subheader("📉 Top 10 Losers")
    losers = fetch_cse("topLooses")
    
    if losers:
        try:
            df_l = pd.DataFrame(losers)
            if not df_l.empty:
                st.dataframe(df_l, use_container_width=True, hide_index=True)
                st.caption("Raw data shown above.")
            else:
                st.info("No losers data available.")
        except Exception as e:
            st.error(f"Error displaying losers: {e}")
            st.write(losers)
    else:
        st.info("Top Losers data not available right now.")
# ====================== STOCK ANALYZER ======================
elif page == "Stock Analyzer":
    st.header(f"🔍 Analysis: {symbol}")
    if st.button("Fetch Data", type="primary"):
        data = fetch_cse("companyInfoSummery", {"symbol": symbol})
        if data and "reqSymbolInfo" in data:
            info = data["reqSymbolInfo"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Last Price", f"Rs. {info.get('lastTradedPrice')}", 
                     f"{info.get('change')} ({info.get('changePercentage'):.2f}%)")
            c2.metric("Market Cap", f"Rs. {info.get('marketCap',0)/1e9:.2f} Bn")
            c3.metric("Volume", f"{info.get('tdyShareVolume',0):,} shares")
            c4.metric("Prev Close", f"Rs. {info.get('previousClose')}")
            
            st.table(pd.DataFrame({
                "Field": ["Company", "Symbol", "ISIN", "Issued Quantity"],
                "Value": [info.get('name'), info.get('symbol'), info.get('isin'), f"{info.get('quantityIssued',0):,}"]
            }))
        else:
            st.error("Data not found")

# ====================== TECHNICAL ANALYSIS (FIXED) ======================
elif page == "Technical Analysis":
    st.header(f"📉 Technical Analysis: {symbol}")
    period = st.selectbox("Select Period", ["1", "5", "10"], index=1)
    
    if st.button("Load Chart & Indicators", type="primary"):
        with st.spinner("Loading chart data..."):
            chart_data = fetch_cse("companyChartDataByStock", {"stockId": symbol, "period": period})
            
            if chart_data and "reqTradeSummery" in chart_data:
                try:
                    df = pd.DataFrame(chart_data["reqTradeSummery"].get("chartData", []))
                    if not df.empty:
                        df = df.rename(columns={'p': 'Close', 't': 'Time'}).reset_index(drop=True)
                        df['Close'] = pd.to_numeric(df['Close'])
                        
                        df['SMA_10'] = df['Close'].rolling(window=10).mean()
                        df['SMA_20'] = df['Close'].rolling(window=20).mean()
                        
                        # RSI
                        delta = df['Close'].diff()
                        gain = delta.where(delta > 0, 0).rolling(14).mean()
                        loss = -delta.where(delta < 0, 0).rolling(14).mean()
                        rs = gain / loss
                        df['RSI'] = 100 - (100 / (1 + rs))
                        
                        # Price Chart
                        fig = px.line(df, y=['Close', 'SMA_10', 'SMA_20'], 
                                    title=f"{symbol} - Price with Moving Averages",
                                    labels={"index": "Time"})
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # RSI Chart
                        fig2 = px.line(df, y='RSI', title="RSI (14 Period)")
                        fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                        fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("No chart data available yet.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Chart data not available for this stock right now.")

# ====================== PORTFOLIO TRACKER (FULL) ======================
elif page == "Portfolio Tracker":
    st.header("💼 Portfolio Tracker")
    
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        new_symbol = st.text_input("Symbol", "JKH.N0000", key="port_sym")
    with col2:
        qty = st.number_input("Quantity", min_value=1, value=100)
    with col3:
        buy_p = st.number_input("Buy Price (Rs.)", min_value=0.0, value=150.0)
    
    if st.button("Add to Portfolio"):
        data = fetch_cse("companyInfoSummery", {"symbol": new_symbol})
        if data and "reqSymbolInfo" in data:
            info = data["reqSymbolInfo"]
            current = info.get('lastTradedPrice', buy_p)
            new_row = pd.DataFrame([{
                "Symbol": new_symbol.upper(),
                "Company": info.get('name'),
                "Quantity": qty,
                "Buy Price": buy_p,
                "Current Price": current
            }])
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
            st.success("Added successfully!")
    
    if not st.session_state.portfolio.empty:
        df = st.session_state.portfolio.copy()
        df["Value"] = df["Quantity"] * df["Current Price"]
        df["Gain/Loss"] = (df["Current Price"] - df["Buy Price"]) * df["Quantity"]
        df["Gain%"] = ((df["Current Price"] - df["Buy Price"]) / df["Buy Price"] * 100).round(2)
        
        total_value = df["Value"].sum()
        total_gain = df["Gain/Loss"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Portfolio Value", f"Rs. {total_value:,.2f}")
        c2.metric("Total P&L", f"Rs. {total_gain:,.2f}")
        
        st.dataframe(df.round(2), use_container_width=True)
        
        if st.button("Export to CSV"):
            st.download_button("Download Portfolio", df.to_csv(index=False), "portfolio.csv", "text/csv")
    else:
        st.info("Your portfolio is empty. Add stocks above.")

# ====================== WATCHLIST ======================
elif page == "Watchlist":
    st.header("⭐ Watchlist")
    add_s = st.text_input("Add Symbol")
    if st.button("Add") and add_s:
        if add_s.upper() not in st.session_state.watchlist:
            st.session_state.watchlist.append(add_s.upper())
    
    for s in st.session_state.watchlist[:]:
        data = fetch_cse("companyInfoSummery", {"symbol": s})
        if data and "reqSymbolInfo" in data:
            i = data["reqSymbolInfo"]
            col1, col2 = st.columns([5,1])
            with col1:
                st.metric(f"{s}", f"Rs. {i.get('lastTradedPrice')}", f"{i.get('changePercentage')}%")
            with col2:
                if st.button("Remove", key=s):
                    st.session_state.watchlist.remove(s)
                    st.rerun()

st.caption("Data from cse.lk • Not financial advice • Always verify with official sources")
