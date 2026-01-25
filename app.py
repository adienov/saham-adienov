import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V56", layout="wide", initial_sidebar_state="expanded")

# CSS: Styling Proporsional & Elegan
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-top: 5px !important; color: #004085; }
        .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e9ecef; }
        div.stButton > button { border-radius: 8px; background-color: #007BFF; color: white !important; font-weight: bold; height: 3rem; }
        div[data-testid="stDataFrame"] th { background-color: #f1f3f5; font-size: 0.85rem !important; text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER & PANDUAN PENGGUNAAN ---
st.title("📱 Noris Trading System V56")

# Menambahkan Panduan Penggunaan di bagian atas
with st.expander("📖 PANDUAN STRATEGI MINERVINI & VCP (Klik untuk Membaca)"):
    st.markdown("""
    ### 🚀 Langkah Kerja Noris System:
    1. **Filter Stage 2:** Sistem hanya menampilkan saham yang sedang *Uptrend* kuat (Lolos 8 syarat Minervini).
    2. **Cek IHSG Index:** Pastikan tren pasar (Kotak Pertama) sedang menanjak.
    3. **Pilih Bintang Terbanyak:** Fokus pada saham dengan rating **⭐⭐⭐⭐⭐**.
    4. **Visual VCP:** Cari grafik yang 'tenang' di tengah lalu menanjak tajam di ujung kanan.
    5. **Eksekusi di TV:** Buka chart TradingView, konfirmasi sinyal **VOL SPIKE** atau **BREAKOUT** di zona hijau.
    """)

# --- 3. SIDEBAR PARAMETER ---
st.sidebar.title("⚙️ Parameter")
# ... (Parameter tetap sama seperti versi V55 sebelumnya) ...

# --- 4. ENGINE SCANNER ---
# ... (Logika scan_market tetap sama seperti V55) ...

# --- 5. TAMPILAN UTAMA & UNIFIED COLOR ---
if st.button("🚀 SCAN MINERVINI MARKET"):
    df, sel_tickers = scan_market(tickers, min_trans, risk_per_trade_pct, modal_juta, risk_per_trade_pct, extended_multiplier, min_rs_rating)
    
    if not df.empty:
        st.markdown("### 🔍 MARKET CORRELATION (Unified View)")
        cols = st.columns(4)
        
        with cols[0]: # IHSG (Warna disamakan menjadi Biru)
            st.markdown("**IHSG INDEX**")
            st.markdown("📈 Market Benchmark")
            try:
                ihsg_data = yf.Ticker("^JKSE").history(period=chart_duration)['Close']
                ihsg_norm = (ihsg_data / ihsg_data.iloc[0] - 1) * 100
                st.area_chart(ihsg_norm, height=120, color="#2962FF") # <--- SEKARANG BIRU SAMA DENGAN SAHAM
            except: st.warning("IHSG Error")
            
        # Top 3 Saham Preview
        for idx, row in enumerate(df.head(3).itertuples()):
            with cols[idx+1]:
                st.markdown(f"**{row.Emiten}** {row.Rating}")
                try:
                    s_data = yf.Ticker(f"{row.Emiten}.JK").history(period=chart_duration)['Close']
                    s_norm = (s_data / s_data.iloc[0] - 1) * 100
                    st.area_chart(s_norm, height=120, color="#2962FF") 
                except: st.warning("Data Error")
        
        st.divider()
        st.subheader("📋 HASIL SCANNER LENGKAP")
        # ... (Tabel hasil tetap sama) ...
