import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DATABASE & WATCHLIST ---
st.set_page_config(page_title="EDU-VEST V119: Screener Status", layout="wide")
WATCHLIST_FILE = "my_watchlist.csv"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE): return pd.read_csv(WATCHLIST_FILE)
    return pd.DataFrame(columns=["Stock"])

# --- 2. ENGINE ANALISA CANSLIM & TEKNIKAL ---
def get_detailed_status(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return "Data Kurang", "⚪", 0
        
        info = t.info
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        roe = info.get('returnOnEquity', 0) * 100
        eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100
        
        # Penentuan Status Berdasarkan CANSLIM & MA
        if close < ma200:
            status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif roe > 17 and eps_growth > 25 and close > ma50:
            status, reco = "Strong CANSLIM Leader", "🟢 BAGUS"
        elif close <= (ma50 * 1.02) and close >= (ma50 * 0.98):
            status, reco = "Pantul Support MA50", "🟡 PANTAU"
        else:
            status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        return status, reco, int(close)
    except: return "Error Data", "❌", 0

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: SCREENER STATUS WATCHLIST V119")
st.error(f"🚨 MARKET CRASH (-5.24%). Gunakan Watchlist untuk mencari Leader yang bertahan!")

# Layouting Sidebar & Main
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("➕ Tambah Watchlist")
    new_stock = st.text_input("Kode Saham (NCKL, DEWA, dll):").upper()
    if st.button("Simpan ke Watchlist"):
        wl_df = load_watchlist()
        if new_stock and new_stock not in wl_df['Stock'].values:
            new_row = pd.DataFrame([{"Stock": new_stock}])
            pd.concat([wl_df, new_row], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
            st.rerun()

with col2:
    st.subheader("📊 Analisa Status Real-time")
    wl_df = load_watchlist()
    if not wl_df.empty:
        results = []
        for s in wl_df['Stock']:
            status, reco, price = get_detailed_status(s)
            results.append({"Stock": s, "Price": price, "Kondisi Teknis": status, "Rekomendasi": reco})
        
        # Tampilkan Tabel Status Seperti Keinginan Bapak
        st.table(pd.DataFrame(results))
        
        if st.button("🗑️ Kosongkan Daftar"):
            os.remove(WATCHLIST_FILE)
            st.rerun()
