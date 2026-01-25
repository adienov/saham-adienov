import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V54", layout="wide", initial_sidebar_state="expanded")

# --- 2. SIDEBAR (PARAMETER LENGKAP) ---
st.sidebar.title("⚙️ Parameter")
st.sidebar.subheader("1. Daftar Saham")
input_mode = st.sidebar.radio("Sumber:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])

st.sidebar.divider()
st.sidebar.subheader("2. Filter Minervini")
min_rs_rating = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
chart_duration = st.sidebar.selectbox("Durasi Chart", ["3mo", "6mo", "1y"], index=1)

st.sidebar.divider()
st.sidebar.subheader("3. Money Management")
modal_juta = st.sidebar.number_input("Modal (Juta Rp)", value=100, step=10)
risk_per_trade_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0)
extended_multiplier = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5)
min_trans = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)

# --- 3. LOGIKA ENGINE ---
# (Pastikan fungsi scan_market tetap ada di file Bapak)

# --- 4. TAMPILAN UTAMA ---
st.title("📱 Noris Trading System V54")

# Barometer Status Singkat di Atas
def get_ihsg_status():
    try:
        ihsg = yf.download("^JKSE", period="1mo", progress=False)
        curr = ihsg['Close'].iloc[-1]
        ma20 = ihsg['Close'].rolling(window=20).mean().iloc[-1]
        return "🟢 BULLISH" if curr > ma20 else "🔴 BEARISH"
    except: return "OFFLINE"

status_mkt = get_ihsg_status()
st.info(f"**MARKET STATUS:** {status_mkt} | Gunakan preview di bawah untuk korelasi visual.")

if st.button("🚀 SCAN MINERVINI MARKET"):
    # (Asumsi fungsi scan_market dipanggil di sini)
    df, sel_tickers = scan_market(tickers, min_trans, risk_per_trade_pct, modal_juta, risk_per_trade_pct, extended_multiplier, min_rs_rating)
    
    if not df.empty:
        # --- BAGIAN VISUAL: IHSG + TOP 3 SAHAM (SEJAJAR) ---
        st.markdown("### 🔍 MARKET CORRELATION (IHSG vs Top Stocks)")
        
        cols = st.columns(4) # 4 Kotak sejajar
        
        # Kotak 1: IHSG
        with cols[0]:
            st.markdown("**IHSG INDEX**")
            st.markdown("📈 Market Trend")
            try:
                ihsg_data = yf.Ticker("^JKSE").history(period=chart_duration)['Close']
                ihsg_norm = (ihsg_data / ihsg_data.iloc[0] - 1) * 100
                st.area_chart(ihsg_norm, height=120, color="#FF4B4B") # Merah untuk IHSG
            except: st.warning("IHSG Error")

        # Kotak 2-4: Top 3 Saham
        top_3_rows = df.head(3)
        for idx, row in enumerate(top_4_rows.itertuples()):
            with cols[idx+1]: # Mulai dari kolom kedua
                st.markdown(f"**{row.Emiten}**")
                st.markdown(f"{row.Rating}")
                try:
                    s_data = yf.Ticker(f"{row.Emiten}.JK").history(period=chart_duration)['Close']
                    s_norm = (s_data / s_data.iloc[0] - 1) * 100
                    st.area_chart(s_norm, height=120, color="#2962FF") # Biru untuk Saham
                except: st.warning("Data Error")
        
        st.divider()
        # (Tabel hasil scanner lengkap tetap di bawah seperti biasa)
