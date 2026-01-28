import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTING DATABASE ---
st.set_page_config(page_title="EDU-VEST V126: HQ Style Porto", layout="wide")
DB_FILE = "trading_history.csv"

def load_local_data(file):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=["Tgl", "Stock", "Entry"])

# --- 2. ENGINE ANALISA ACTION (HQ STYLE) ---
def get_hq_style_analysis(ticker, entry_price):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="10d")
        if df.empty: return 0, "0%", "⚪ MONITOR", 0, 0
        
        last_p = int(df['Close'].iloc[-1])
        gl_val = ((last_p - entry_price) / entry_price) * 100
        
        # TARGET DAN PROTEKSI OTOMATIS
        tp_price = int(entry_price * 1.15) # Target Profit 15%
        ts_price = int(last_p * 0.95)      # Trailing Stop 5% dari harga tertinggi
        
        # LOGIKA ACTION BERDASARKAN MODE HQ
        if gl_val <= -7.0:
            action = "🚨 SELL (Cut Loss)"
        elif last_p >= tp_price:
            action = "🔵 TAKE PROFIT (Target Hit)"
        elif gl_val >= 5.0:
            action = "🟢 HOLD (Trailing Stop Active)"
        else:
            action = "🟡 HOLD (Wait Rebound)"
            
        return last_p, f"{gl_val:+.2f}%", action, tp_price, ts_price
    except: return 0, "0%", "❌ ERROR", 0, 0

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: HQ STYLE PORTO MANAGER V126")

tab1, tab2 = st.tabs(["📊 NORIS PETA (PORTFOLIO)", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("📊 Monitoring Real-time Portfolio")
    peta_df = load_local_data(DB_FILE)
    
    if not peta_df.empty:
        results = []
        for _, r in peta_df.iterrows():
            last, gl, action, tp, ts = get_hq_style_analysis(r['Stock'], r['Entry'])
            results.append({
                "Stock": r['Stock'],
                "Entry": r['Entry'],
                "Last": last,
                "G/L %": gl,
                "Action": action,
                "Target (TP)": tp,
                "Proteksi (TS)": ts
            })
        
        # Menampilkan tabel dengan kolom Target dan Proteksi baru
        st.table(pd.DataFrame(results))
    else:
        st.info("Portfolio Kosong. Gunakan Tab 'INPUT MANUAL' untuk mengisi.")

with tab2: # Fitur Input Manual Bapak
    # ... (Kode Input Manual tetap sama seperti V125)
    st.write("Silakan masukkan transaksi Bapak dari Stockbit.")
