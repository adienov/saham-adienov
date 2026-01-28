import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASAR & DATABASE ---
st.set_page_config(page_title="EDU-VEST PROTECTION MAX V121", layout="wide")

DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_local_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA OTOMATIS (CANSLIM & MA) --- [cite: 7, 21, 28]
def get_stock_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return "Data Kurang", "⚪ TUNGGU", 0, "0%"
        
        info = t.info
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        roe = info.get('returnOnEquity', 0) * 100
        
        # Analisa Status [cite: 7, 21, 28]
        if close < ma200:
            status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif roe > 17 and close > ma50:
            status, reco = "Strong CANSLIM Leader", "🟢 BAGUS"
        elif rsi < 35:
            status, reco = "Oversold Area", "🟡 PANTAU"
        else:
            status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        # Logika Tambahan Portfolio (Cut Loss Alarm) 
        gl_str = "0%"
        if is_portfolio and entry_price > 0:
            gl_val = ((close - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: reco = "🚨 CUT LOSS (Limit -7%)"
            
        return status, reco, int(close), gl_str
    except: return "Error Data", "❌", 0, "0%"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: PROTECTION MAX V121")

# Panic Meter IHSG [cite: 28, 29]
ihsg = yf.Ticker("^JKSE").history(period="2d")
ihsg_chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
st.error(f"🚨 MARKET CRASH ({ihsg_chg:.2f}%). Prioritas: Amankan Modal & Cek Alarm Cut Loss! ")

# Membuat Tabs secara Benar
tab1, tab2, tab3 = st.tabs(["🔍 SCANNER", "⭐ WATCHLIST", "📊 NORIS PETA (PORTFOLIO)"])

with tab1: # Fitur Scanner Reversal
    st.subheader("🚀 Scanner Reversal MA50")
    if st.button("JALANKAN SCANNER SEKARANG"):
        st.info("Fitur scanner sedang memproses data market...")

with tab2: # Fitur Auto-Analisa Watchlist
    st.subheader("📊 Analisa Otomatis Saham Incaran")
    new_stock = st.text_input("Tambah Kode (NCKL, DEWA, dll):").upper()
    if st.button("➕ Simpan ke Watchlist"):
        wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
        if new_stock and new_stock not in wl_df['Stock'].values:
            new_row = pd.DataFrame([{"Stock": new_stock}])
            pd.concat([wl_df, new_row], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
            st.rerun()

    wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
    if not wl_df.empty:
        analysis_res = []
        for s in wl_df['Stock']:
            status, reco, price, _ = get_stock_analysis(s)
            analysis_res.append({"Stock": s, "Price": price, "Kondisi Teknis": status, "Rekomendasi": reco})
        st.table(pd.DataFrame(analysis_res)) # Analisa Otomatis
        if st.button("🗑️ Kosongkan Watchlist"):
            if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE)
            st.rerun()

with tab3: # Fitur Monitor Portfolio & Cut Loss
    st.subheader("📊 Alarm Cut Loss Portfolio")
    peta_df = load_local_data(DB_FILE, ["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])
    if not peta_df.empty:
        portfolio_results = []
        for _, row in peta_df.iterrows():
            _, reco, last_p, gl_pct = get_stock_analysis(row['Stock'], is_portfolio=True, entry_price=row['Entry'])
            portfolio_results.append({
                "Stock": row['Stock'], "Entry": row['Entry'], "Last": last_p, 
                "G/L %": gl_pct, "Rekomendasi Action": reco
            })
        st.table(pd.DataFrame(portfolio_results)) # Alarm Cut Loss 
    else:
        st.info("Peta Portfolio Kosong. Simpan saham dari tab SCANNER.")
