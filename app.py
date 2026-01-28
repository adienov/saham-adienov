import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. DATABASE & WATCHLIST SETTING ---
st.set_page_config(page_title="EDU-VEST V117: Recovery Monitor", layout="wide")

DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. FOLLOW-THROUGH DAY (FTD) DETECTOR ---
def check_ftd_signal():
    try:
        ihsg = yf.Ticker("^JKSE").history(period="10d")
        change = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
        vol_now = ihsg['Volume'].iloc[-1]
        vol_prev = ihsg['Volume'].iloc[-2]
        
        # FTD Signal: IHSG naik > 1.5% dengan volume lebih tinggi dari hari sebelumnya
        if change >= 1.5 and vol_now > vol_prev:
            return "✅ FOLLOW-THROUGH DAY DETECTED! Market Aman untuk Entry.", "success"
        elif change < -2.0:
            return "🚨 MARKET CRASH! Jangan Serok Dulu (Wait for FTD).", "error"
        else:
            return "🟡 MARKET SIDEWAYS/WEAK. Tunggu Konfirmasi FTD.", "warning"
    except: return "Data IHSG Tidak Tersedia", "info"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: MARKET RECOVERY & WATCHLIST V117")

# Panic & FTD Monitor
status_msg, status_type = check_ftd_signal()
if status_type == "success": st.success(status_msg)
elif status_type == "error": st.error(status_msg)
else: st.warning(status_msg)

tab1, tab2, tab3 = st.tabs(["🔍 REBOUND SCANNER", "⭐ MY WATCHLIST", "📊 PORTFOLIO"])

with tab1:
    st.subheader("Cari Saham Leader yang Rebound")
    # (Gunakan Engine V116 Rebound Master di sini)
    if st.button("🚀 SCAN REBOUND"):
        st.info("Scanner sedang mencari pantulan teknikal...")

with tab2:
    st.subheader("⭐ Watchlist Pilihan")
    # Fitur Tambah Watchlist
    new_stock = st.text_input("Tambah Kode Saham (Contoh: NCKL, ASII, BBRI):").upper()
    if st.button("➕ Tambah ke Watchlist"):
        wl_df = load_data(WATCHLIST_FILE, ["Stock"])
        if new_stock and new_stock not in wl_df['Stock'].values:
            new_row = pd.DataFrame([{"Stock": new_stock}])
            wl_df = pd.concat([wl_df, new_row], ignore_index=True)
            wl_df.to_csv(WATCHLIST_FILE, index=False)
            st.rerun()

    # Tampilkan Watchlist dengan Harga Real-time
    wl_df = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl_df.empty:
        wl_results = []
        for s in wl_df['Stock']:
            try:
                t = yf.Ticker(f"{s}.JK")
                hist = t.history(period="2d")
                curr = hist['Close'].iloc[-1]
                chg = ((curr - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                wl_results.append({"Stock": s, "Price": int(curr), "Change": f"{chg:.2f}%", "Action": "Monitor"})
            except: continue
        st.table(pd.DataFrame(wl_results))
        if st.button("🗑️ Reset Watchlist"):
            if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE)
            st.rerun()
