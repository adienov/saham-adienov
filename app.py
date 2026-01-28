import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST V115: Safe Entry", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. FUNGSI PANIC METER (IHSG MONITOR) ---
def get_market_sentiment():
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d")
        if len(ihsg) < 2: return "Neutral", 0
        change = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
        if change <= -3.0: return "🔴 PANIC (MARKET CRASH)", change
        elif change <= -1.5: return "🟡 CAUTION (VOLATILE)", change
        else: return "🟢 NORMAL/BULLISH", change
    except: return "N/A", 0

# --- 3. ENGINE SCANNER DENGAN VOLUME FILTER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=60)
def run_safe_scanner(ticker_list, rs_min):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 100: continue
            
            close = df['Close'].iloc[-1]
            low = df['Low'].iloc[-1]
            open_p = df['Open'].iloc[-1]
            vol_now = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
            
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # --- LOGIKA SAFE ENTRY (V115) ---
            # 1. Leader: RS 75+
            # 2. Support: Pantulan di MA50
            # 3. Volume: Vol hari ini < Rata-rata 20 hari (Supply Mengering)
            # 4. Reversal: Harga tutup > Harga buka (Perlawanan)
            
            if rs_val >= rs_min and close > ma200 and low <= (ma50 * 1.01) and close > open_p:
                if vol_now < vol_avg: # Filter Volume Tambahan
                    red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                    s_name = t.replace(".JK","")
                    results.append({
                        "Pilih": False, "Stock": s_name, "RS": rs_val, 
                        "Vol Stat": "Mengering ✅", "Entry": int(close), "SL/TS": int(red_line),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                    })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: SAFE ENTRY V115")

sentiment, chg = get_market_sentiment()
if "PANIC" in sentiment:
    st.error(f"🚨 {sentiment} ({chg:.2f}%) - SARAN: WAIT & SEE. Market sedang dalam tekanan jual tinggi!")
elif "CAUTION" in sentiment:
    st.warning(f"⚠️ {sentiment} ({chg:.2f}%) - SARAN: Serok bertahap hanya pada saham dengan Volume Mengering.")

tab1, tab2 = st.tabs(["🔍 SAFE SCANNER", "📊 PORTFOLIO"])

with tab1:
    rs_limit = st.sidebar.slider("Min. RS Rating", 0, 99, 75)
    if st.button("🚀 SCAN SAFE REVERSAL"):
        df_res = run_safe_scanner(ALL_TICKERS, rs_limit)
        if not df_res.empty:
            st.session_state.current_scan = df_res
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        else:
            st.warning("Tidak ada saham Leader yang pantul di MA50 dengan volume rendah (aman) saat ini.")
