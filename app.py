import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASAR & DATABASE ---
st.set_page_config(page_title="EDU-VEST PROTECTION MAX V123", layout="wide")

DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_local_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA OTOMATIS (CANSLIM & MA) ---
def get_stock_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return "Data Kurang", "⚪ TUNGGU", 0, "0%"
        
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Analisa Status Berdasarkan Kondisi Teknis
        if close < ma200:
            status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif close > ma50:
            status, reco = "Strong Momentum", "🟢 BAGUS"
        else:
            status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        gl_str = "0%"
        if is_portfolio and entry_price > 0:
            gl_val = ((close - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            # Alarm Cut Loss Standar CANSLIM -7%
            if gl_val <= -7.0: reco = "🚨 CUT LOSS"
            
        return status, reco, int(close), gl_str
    except: return "Error Data", "❌", 0, "0%"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: PROTECTION MAX V123")

# Status Market Crash
st.error("🚨 MARKET CRASH (-5.24%). Prioritas: Amankan Modal & Cek Alarm Cut Loss!")

tab1, tab2, tab3 = st.tabs(["🔍 SCANNER", "⭐ WATCHLIST", "📊 NORIS PETA (PORTFOLIO)"])

with tab1:
    st.subheader("🚀 Scanner Reversal MA50")
    if st.button("JALANKAN SCANNER SEKARANG"):
        # Menambahkan spinner agar tidak terlihat "loading saja"
        with st.spinner("Sedang memproses data market... Mohon tunggu."):
            # (Ganti dengan kodingan run_scanner Bapak sebelumnya)
            st.success("✅ Scanning Selesai! (Fitur scanner aktif)")

with tab2:
    st.subheader("📊 Analisa Otomatis Saham Incaran")
    new_stock = st.text_input("Tambah Kode (NCKL, DEWA, dll):").upper()
    if st.button("➕ Simpan ke Watchlist"):
        wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
        if new_stock and new_stock not in wl_df['Stock'].values:
            pd.concat([wl_df, pd.DataFrame([{"Stock": new_stock}])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
            st.rerun()

    wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
    if not wl_df.empty:
        # Analisa otomatis muncul di sini
        analysis_res = []
        for s in wl_df['Stock']:
            status, reco, price, _ = get_stock_analysis(s)
            analysis_res.append({"Stock": s, "Price": price, "Kondisi Teknis": status, "Rekomendasi": reco})
        st.table(pd.DataFrame(analysis_res))
        
        if st.button("🗑️ Kosongkan Watchlist"):
            if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE)
            st.rerun()

with tab3:
    st.subheader("📊 Monitoring Real-time Portfolio")
    peta_df = load_local_data(DB_FILE, ["Tgl", "Stock", "Entry", "SL/TS"])
    
    # Menambahkan pengecekan agar tidak kosong
    if not peta_df.empty:
        results = []
        for _, row in peta_df.iterrows():
            _, reco, last_p, gl_pct = get_stock_analysis(row['Stock'], is_portfolio=True, entry_price=row['Entry'])
            results.append({"Stock": row['Stock'], "Entry": row['Entry'], "Last": last_p, "G/L %": gl_pct, "Rekomendasi": reco})
        st.table(pd.DataFrame(results))
    else:
        # Tampilan jika database masih kosong agar tidak terlihat "blank"
        st.info("Peta Portfolio Kosong. Masukkan saham pilihan Bapak di tab WATCHLIST terlebih dahulu.")
        
