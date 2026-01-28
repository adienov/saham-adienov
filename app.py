import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DATABASE & PROTECTION ---
st.set_page_config(page_title="EDU-VEST V120: Protection Max", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA & ACTION ---
def analyze_stock_action(ticker, entry_price):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return 0, "N/A", "⚪ MONITOR"
        
        curr_p = df['Close'].iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        gain_loss = ((curr_p - entry_price) / entry_price) * 100
        
        # LOGIKA CUT LOSS & EXIT (CANSLIM Rule)
        if gain_loss <= -7.0:
            action = "🔴 CUT LOSS (Limit -7%)"
        elif curr_p < ma200:
            action = "🔴 EXIT (Trend Rusak)"
        elif gain_loss >= 10.0:
            action = "🟢 HOLD (Trailing Stop)"
        else:
            action = "⚪ MONITOR"
            
        return int(curr_p), f"{gain_loss:+.2f}%", action
    except: return 0, "0%", "❌ ERROR"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: PROTECTION MAX V120")

# Panic Meter IHSG
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    ihsg_chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if ihsg_chg <= -3.0:
        st.error(f"🚨 MARKET CRASH ({ihsg_chg:.2f}%). Prioritas: Amankan Modal & Cek Tabel Cut Loss!")
except: pass

tab1, tab2, tab3 = st.tabs(["🔍 SCANNER", "⭐ WATCHLIST", "📊 NORIS PETA (PORTFOLIO)"])

with tab2: # Tab Watchlist dari V119
    st.subheader("📊 Auto-Analisa Watchlist")
    # ... (Gunakan kode V119 Bapak di sini untuk tambah & tampilkan watchlist)

with tab3: # Tab Portfolio Baru dengan Alarm Cut Loss
    st.subheader("📊 Monitor Peta & Rekomendasi Action")
    df_peta = load_data(DB_FILE, ["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])
    
    if not df_peta.empty:
        peta_results = []
        with st.spinner("Menghitung risiko real-time..."):
            for _, row in df_peta.iterrows():
                last_p, gl_pct, recommendation = analyze_stock_action(row['Stock'], row['Entry'])
                peta_results.append({
                    "Stock": row['Stock'],
                    "Entry": row['Entry'],
                    "Last": last_p,
                    "G/L %": gl_pct,
                    "Rekomendasi Action": recommendation, # Fitur Baru Bapak
                    "SL/TS Plan": row['SL/TS']
                })
        
        # Tampilkan Tabel dengan Highlight Rekomendasi
        st.table(pd.DataFrame(peta_results))
        
        st.info("💡 Tip: Jika muncul 'CUT LOSS', segera pangkas posisi untuk menghindari kerugian lebih dalam sesuai aturan CANSLIM.")
        
        if st.button("🗑️ RESET PETA"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()
    else:
        st.info("Peta Portfolio Kosong.")
        
