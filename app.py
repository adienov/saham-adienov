import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V78", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal", "Syariah"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. DATABASE EMITEN & STATUS SYARIAH ---
# Daftar ini mencakup gabungan LQ45, Kompas100, dan ISSI yang Liquid
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
NON_SYARIAH_LIST = ["BBCA", "BBRI", "BMRI", "BBNI", "ASII", "ADRO", "PTBA", "UNVR"]

ALL_TICKERS = [f"{s}.JK" for s in (SYARIAH_LIST + NON_SYARIAH_LIST)]

# --- 3. ENGINE SCANNER ---
@st.cache_data(ttl=300)
def scan_engine(ticker_list, rs_threshold, target_date=None):
    results = []
    end_date = datetime.now() if target_date is None else datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
    
    try:
        data_batch = yf.download(ticker_list, start=end_date - timedelta(days=365), end=end_date, progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except: rs_map = {}

    for t in ticker_list:
        try:
            emiten_code = t.replace(".JK","")
            df = yf.Ticker(t).history(start=end_date - timedelta(days=365), end=end_date)
            if len(df) < 200: continue
            
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                is_syariah = "✅" if emiten_code in SYARIAH_LIST else "❌"
                
                results.append({
                    "Tanggal": end_date.strftime("%Y-%m-%d") if target_date is None else target_date,
                    "Emiten": emiten_code,
                    "Syariah": is_syariah,
                    "Harga_Awal": int(close),
                    "SL_Awal": int(red_line),
                    "Status": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. SIDEBAR ---
st.sidebar.title("⚙️ Filter Saham")
mode = st.sidebar.multiselect("Pilih Kelompok:", ["Syariah (ISSI)", "Non-Syariah"], default=["Syariah (ISSI)", "Non-Syariah"])
min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)

# Filter ticker berdasarkan pilihan sidebar
selected_tickers = []
if "Syariah (ISSI)" in mode: selected_tickers += [f"{s}.JK" for s in SYARIAH_LIST]
if "Non-Syariah" in mode: selected_tickers += [f"{s}.JK" for s in NON_SYARIAH_LIST]

if st.sidebar.button("🗑️ Reset Database"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal", "Syariah"])
    st.rerun()

# --- 5. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V78")
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER", "⏮️ BACKTEST"])

with tab1:
    if st.button("🚀 JALANKAN SCANNER"):
        df_live = scan_engine(selected_tickers, min_rs)
        if not df_live.empty:
            st.session_state.current_scan = df_live
            st.dataframe(df_live, use_container_width=True, hide_index=True)
        else: st.warning("Tidak ada saham lolos kriteria.")
    
    if 'current_scan' in st.session_state:
        if st.button("💾 SIMPAN KE DATABASE"):
            updated_db = pd.concat([st.session_state.history_db, st.session_state.current_scan], ignore_index=True).drop_duplicates(subset=['Emiten'], keep='last')
            updated_db.to_csv(DB_FILE, index=False)
            st.session_state.history_db = updated_db
            st.success("Tersimpan!")

with tab2:
    st.subheader("📊 Profit & Loss Tracker")
    db = st.session_state.history_db
    if not db.empty:
        track_list = []
        for _, row in db.iterrows():
            try:
                curr_p = yf.Ticker(f"{row['Emiten']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr_p - row['Harga_Awal']) / row['Harga_Awal']) * 100
                track_list.append({
                    "Tgl": row['Tanggal'], "Emiten": row['Emiten'], "Syariah": row['Syariah'], 
                    "Entry": row['Harga_Awal'], "Last": int(curr_p), "% G/L": round(gain, 2),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{row['Emiten']}"
                })
            except: pass
        st.dataframe(pd.DataFrame(track_list), column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")}, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("⏮️ Backtest Mundur")
    b_date = st.date_input("Pilih Tanggal:", datetime.now() - timedelta(days=30))
    if st.button("⏪ SCAN TANGGAL TERPILIH"):
        df_hist = scan_engine(selected_tickers, min_rs, target_date=b_date.strftime("%Y-%m-%d"))
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
