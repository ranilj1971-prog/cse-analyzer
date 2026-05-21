import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="CSE Analyzer", page_icon="📈", layout="wide")

BASE_URL = "https://www.cse.lk/api/"

@st.cache_data(ttl=300)
def fetch_cse(endpoint, payload=None):
    try:
        response = requests.post(BASE_URL + endpoint, data=payload or {}, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

st.title("📊 Colombo Stock Exchange Analyzer & Recommender")
st.caption("Educational tool only • Not financial advice")

symbol = st.text_input("Enter Stock Symbol (e.g. JKH.N0000, LOLC.N0000)", "JKH.N0000").upper()

if st.button("🔍 Analyze Stock"):
    with st.spinner("Fetching latest data..."):
        data = fetch_cse("companyInfoSummery", {"symbol": symbol})
        if data and "reqSymbolInfo" in data:
            info = data["reqSymbolInfo"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Last Price", f"Rs. {info.get('lastTradedPrice')}", 
                     f"{info.get('change')} ({info.get('changePercentage')}%)")
            c2.metric("Market Cap", f"Rs. {info.get('marketCap',0)/1e9:.2f} Bn")
            c3.metric("Company", info.get('name', symbol))
            
            # Chart
            chart = fetch_cse("companyChartDataByStock", {"stockId": symbol})
            if chart:
                try:
                    df = pd.DataFrame(chart.get("reqTradeSummery", {}).get("chartData", []))
                    if not df.empty:
                        fig = px.line(df, x='t', y='p', title=f"{symbol} - Recent Price")
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    pass
        else:
            st.error("Could not fetch data. Try symbols like JKH.N0000 or LOLC.N0000")

st.header("Quick Links")
col1, col2 = st.columns(2)
with col1:
    st.subheader("🚀 Top Gainers")
    gainers = fetch_cse("topGainers")
    if gainers:
        st.dataframe(pd.DataFrame(gainers), use_container_width=True)

with col2:
    st.subheader("📉 Top Losers")
    losers = fetch_cse("topLooses")
    if losers:
        st.dataframe(pd.DataFrame(losers), use_container_width=True)

st.caption("Data from cse.lk • Updates every few minutes")
