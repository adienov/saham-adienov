import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DATABASE ---
st.set_page_config(page_title="EDU-VEST V118: Auto-Analisa", layout="wide")
WATCHLIST_FILE = "my_watchlist.csv"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE): return pd.read_csv(WATCHLIST_FILE)
    return pd.DataFrame(columns=["Stock"])

# --- 2. FUNGSI ANALISA OTOMATIS WATCHLIST ---
def get_auto_analysis(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 50: return "Data Kurang", "⚪"
        
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        # Logika Analisa Cepat [cite: 21, 28]
        if close < ma200:
            return "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif close < ma50 and rsi < 35:
            return "Oversold di Support MA50", "🟡 PANTAU"
        elif close > ma50 and rsi > 50:
            return "Strong Momentum", "🟢 BAGUS"
        else:
            return "Fase Konsolidasi", "⚪ TUNGGU"
    except: return "Error Data", "❌"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: AUTO-ANALISA WATCHLIST V118")

# FTD Monitor [cite: 29]
ihsg_chg = -5.24 # Berdasarkan data market Bapak
st.error(f"🚨 MARKET CRASH ({ihsg_chg}%). Fokus pada Analisa Watchlist, Jangan Entry Dulu! ")

tab1, tab2 = st.tabs(["⭐ ANALISA WATCHLIST", "🔍 SCANNER REBOUND"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        new_stock = st.text_input("Masukkan Kode (Contoh: NCKL, DEWA):").upper()
        if st.button("➕ Tambah ke Watchlist"):
            wl_df = load_watchlist()
            if new_stock and new_stock not in wl_df['Stock'].values:
                new_row = pd.DataFrame([{"Stock": new_stock}])
                pd.concat([wl_df, new_row], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
                st.rerun()

    with col2:
        st.write("### 📊 Analisa Otomatis Saham Anda")
        wl_df = load_watchlist()
        if not wl_df.empty:
            analysis_data = []
            for s in wl_df['Stock']:
                status, rekomendasi = get_auto_analysis(s)
                # Ambil harga real-time untuk watchlist
                t = yf.Ticker(f"{s}.JK")
                curr_price = t.history(period="1d")['Close'].iloc[-1]
                analysis_data.append({
                    "Stock": s, "Price": int(curr_price),
                    "Kondisi Teknis": status, "Rekomendasi": rekomendasi
                })
            st.table(pd.DataFrame(analysis_data))
            if st.button("🗑️ Kosongkan Watchlist"):
                os.remove(WATCHLIST_FILE)
                st.rerun()
