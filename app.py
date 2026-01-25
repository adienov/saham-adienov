import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V51", layout="wide", initial_sidebar_state="expanded")

# CSS: Styling untuk tampilan Mini Chart IHSG
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-bottom: 5px !important; color: #004085; }
        .stMetricValue { font-size: 1.3rem !important; font-weight: bold !important; }
        .stMetricLabel { font-size: 0.8rem !important; }
        div.stButton > button { border-radius: 8px; background-color: #007BFF; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (PARAMETER) ---
st.sidebar.title("⚙️ Parameter")
ihsg_duration = st.sidebar.select_slider("Durasi Chart IHSG", options=["3mo", "6mo", "1y"], value="6mo", 
                                       format_func=lambda x: "3 Bulan" if x=="3mo" else ("6 Bulan" if x=="6mo" else "1 Tahun"))

# ... (Parameter lainnya tetap sama seperti V50) ...

# --- 3. HEADER & UNIFORM IHSG DASHBOARD ---
st.title("📱 Noris Trading System V51")

def display_ihsg_uniform(duration):
    try:
        ihsg_ticker = yf.Ticker("^JKSE")
        ihsg_hist = ihsg_ticker.history(period="2y")
        
        if not ihsg_hist.empty:
            curr = ihsg_hist['Close'].iloc[-1]
            prev = ihsg_hist['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            
            ma20 = ihsg_hist['Close'].rolling(window=20).mean().iloc[-1]
            status = "🟢 BULLISH" if curr > ma20 else "🔴 BEARISH"
            
            # Layout: Judul Metrik di Atas, Mini Chart di Bawah (Persis format VCP)
            st.markdown(f"**MARKET INDEX: IHSG** ({status})")
            
            # Kolom untuk Metrik Ringkas
            c1, c2, _ = st.columns([1, 1, 4])
            with c1: st.metric("Index", f"{curr:,.0f}", f"{pct:+.2f}%")
            with c2: st.metric("Trend", status)
            
            # Mini Chart (Area Chart) dengan durasi dinamis
            days = 60 if duration == "3mo" else (120 if duration == "6mo" else 250)
            chart_data = ihsg_hist['Close'].tail(days)
            # Normalisasi (%) agar fluktuasi terlihat jelas seperti VCP
            norm_data = (chart_data / chart_data.iloc[0] - 1) * 100
            
            st.area_chart(norm_data, height=130, color="#FF4B4B")
            st.caption(f"IHSG Relative Performance ({duration})")
        st.divider()
    except:
        st.error("IHSG Data Unavailable")

display_ihsg_uniform(ihsg_duration)

# --- 4. ENGINE & DISPLAY SCANNER ---
# Gunakan logika scan_market dan tampilan VCP Preview dari V50.
# Sekarang tampilan IHSG di atas dan VCP di bawah akan terlihat sangat serasi.
