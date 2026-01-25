import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V50", layout="wide", initial_sidebar_state="expanded")

# CSS: Styling Proporsional
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-top: 5px !important; color: #004085; }
        .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e9ecef; }
        div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.9rem !important; }
        div.stButton > button { width: 100%; border-radius: 8px; background-color: #007BFF; color: white; font-weight: bold; height: 3rem; }
        div[data-testid="stDataFrame"] th { background-color: #f1f3f5; font-size: 0.85rem !important; }
        div[data-testid="stDataFrame"] td { font-size: 0.85rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (PARAMETER) ---
st.sidebar.title("⚙️ Parameter")

st.sidebar.subheader("1. Market Watch")
ihsg_duration = st.sidebar.select_slider("Durasi Chart IHSG", options=["3mo", "6mo", "1y"], value="6mo", 
                                       format_func=lambda x: "3 Bulan" if x=="3mo" else ("6 Bulan" if x=="6mo" else "12 Bulan"))

st.sidebar.divider()
st.sidebar.subheader("2. Filter Minervini")
min_rs_rating = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
chart_duration_vcp = st.sidebar.selectbox("Durasi Chart VCP", ["3mo", "6mo", "1y"], index=1)

st.sidebar.divider()
st.sidebar.subheader("3. Money Management")
modal_juta = st.sidebar.number_input("Modal (Juta Rp)", value=20, step=10)
risk_per_trade_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0)
extended_multiplier = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5)

# --- 3. HEADER & IHSG DASHBOARD ---
st.title("📱 Noris Trading System V50")

def display_ihsg_proporsional(duration):
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2y")
        if not ihsg.empty:
            curr = ihsg['Close'].iloc[-1]
            prev = ihsg['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            
            ma20 = ihsg['Close'].rolling(window=20).mean().iloc[-1]
            status = "🟢 BULLISH" if curr > ma20 else "🔴 BEARISH"
            
            # Layout Proporsional: Metrik Kecil di Kiri, Chart Besar di Kanan
            c1, c2, c3 = st.columns([1.2, 1.2, 4])
            with c1: st.metric("IHSG Index", f"{curr:,.0f}", f"{pct:+.2f}%")
            with c2: st.metric("Market Status", status)
            with c3:
                # Filter data berdasarkan durasi slider
                days = 60 if duration == "3mo" else (120 if duration == "6mo" else 250)
                st.area_chart(ihsg['Close'].tail(days), height=180, color="#FF4B4B")
                st.caption(f"IHSG Trend ({duration})")
        st.divider()
    except: st.error("IHSG Data Offline")

display_ihsg_proporsional(ihsg_duration)

# --- 4. ENGINE SCANNER (LOGIC V47) ---
# ... (Gunakan fungsi scan_market dari versi V47 sebelumnya) ...
# @st.cache_data(ttl=300) 
# def scan_market(...): 
#    ... (Logika Minervini Stage 2 & VCP Scoring) ...

# --- 5. EXECUTION & RESULTS ---
if st.button("🚀 SCAN MINERVINI MARKET"):
    # (Panggil fungsi scanner dan tampilkan VCP Preview + Tabel Hasil seperti V47-V49)
    st.info("Scanner sedang memproses data berdasarkan Parameter...")
    # [Koding tampilan hasil tetap sama seperti V49 Bapak]
