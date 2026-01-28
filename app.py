import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST V116: Rebound Master", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. FUNGSI PANIC METER ---
def get_market_sentiment():
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d")
        change = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
        return change
    except: return 0

# --- 3. ENGINE REBOUND MASTER (BOLLINGER + RS) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=60)
def run_rebound_master(ticker_list, rs_min):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 50: continue
            
            # --- RUMUS ALTERNATIF: BOLLINGER BANDS ---
            bb = ta.bbands(df['Close'], length=20, std=2)
            lower_band = bb['BBL_20_2.0'].iloc[-1]
            
            close, low, open_p = df['Close'].iloc[-1], df['Low'].iloc[-1], df['Open'].iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # KRITERIA REBOUND MASTER:
            # 1. RS Leader: Minimal 75+
            # 2. BB Reversal: Low sempat menembus Lower Band, tapi Close di atas Lower Band.
            # 3. Candle Reversal: Harga tutup > Harga buka (Warna Hijau).
            
            if rs_val >= rs_min and low <= lower_band and close > lower_band and close > open_p:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False, "Stock": s_name, "RS": rs_val, 
                    "Status": "BB REBOUND 📈", "Entry": int(close), "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("🏹 EDU-VEST: REBOUND MASTER V116")

chg = get_market_sentiment()
if chg <= -3.0:
    st.error(f"🚨 MARKET CRASH ({chg:.2f}%) - Fokus pada Reversal di Lower Bollinger Band!")
else:
    st.info(f"📊 Market Condition: {chg:.2f}%")

tab1, tab2 = st.tabs(["🔍 REBOUND SCANNER", "📊 PORTFOLIO"])

with tab1:
    rs_limit = st.sidebar.slider("Min. RS Rating", 0, 99, 75)
    if st.button("🚀 SCAN BOLLINGER REVERSAL"):
        with st.spinner("Mencari pantulan di Lower Band..."):
            df_res = run_rebound_master(ALL_TICKERS, rs_limit)
            if not df_res.empty:
                st.session_state.current_scan = df_res
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            else:
                st.warning("Belum ada Leader yang terdeteksi mantul dari batas bawah Bollinger.")
