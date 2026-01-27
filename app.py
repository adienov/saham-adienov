import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST HYBRID V109", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE HYBRID DENGAN FILTER VOLUME ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]

@st.cache_data(ttl=300)
def run_hybrid_v109(ticker_list, rs_min):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 150: continue
            
            # --- INDIKATOR TEKNIKAL ---
            close = df['Close'].iloc[-1]
            vol_now = df['Volume'].iloc[-1]
            vol_ma20 = df['Volume'].rolling(20).mean().iloc[-1] # Rata-rata volume 20 hari
            
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # --- FILTER FUNDAMENTAL (CANSLIM) ---
            info = stock.info
            roe = info.get('returnOnEquity', 0)
            
            # --- LOGIKA V109 (VOLUME DRY UP) ---
            # 1. CANSLIM: RS Rating >= 80 (Leader)
            # 2. SWING: Harga di bawah MA20 tapi di atas MA50 (Pullback)
            # 3. VOLUME: Volume hari ini < Rata-rata Volume 20 hari (Mengering)
            # 4. TREND: Harga di atas MA200 (Uptrend)
            
            if rs_val >= rs_min and close > ma200 and close > ma50 and close < ma20:
                if vol_now < vol_ma20: # HANYA LOLOS JIKA VOLUME RENDAH (KOREKSI SEHAT)
                    red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                    s_name = t.replace(".JK","")
                    results.append({
                        "Pilih": False,
                        "Stock": s_name,
                        "RS": rs_val,
                        "ROE%": round(roe * 100, 2) if roe else 0,
                        "Entry": int(close),
                        "RSI": round(rsi, 2),
                        "Vol vs Avg": "Mengering ✅" if vol_now < vol_ma20 else "Tinggi ❌",
                        "SL/TS": int(red_line),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                    })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 EDU-VEST HYBRID V109 (Volume Filter)")
st.info("Kriteria: RS 80+ | Pullback (Price < MA20) | Volume Mengering (Vol < Vol MA20)")

# ... (Sisa kode tampilan tab1 dan tab2 sama seperti sebelumnya)
