import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST CRASH RECOVERY V111", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SCANNER SEROK (V111) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=60)
def run_crash_screener_v111(ticker_list, rs_min, rsi_max):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 200: continue
            
            close = df['Close'].iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # KRITERIA V111:
            # 1. Leader: RS 80+
            # 2. RSI: Dilonggarkan ke 45 agar saham yang baru mulai crash terbaca
            # 3. Defense: Masih di atas atau dekat MA200
            if rs_val >= rs_min and rsi < rsi_max and close > (ma200 * 0.90):
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False, "Stock": s_name, "RS": rs_val, "RSI": round(rsi, 2),
                    "Entry": int(close), "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN ---
st.title("⚡ EDU-VEST: SEROK CRASH SCANNER V111")
st.warning("⚠️ Market Crash! Melonggarkan filter RSI agar saham leader yang diskon bisa terbaca.")

tab1, tab2 = st.tabs(["🔍 CRASH SCANNER", "📊 PORTFOLIO"])

with tab1:
    rs_threshold = st.sidebar.slider("Min. RS Rating (Standard = 80)", 0, 99, 80)
    rsi_threshold = st.sidebar.slider("Max. RSI (Area Diskon)", 30, 60, 45) # Ditambah slider untuk kontrol manual
    
    if st.button("🚀 SCAN SAHAM DISKON"):
        with st.spinner("Mencari emiten berdiskon..."):
            df_res = run_crash_screener_v111(ALL_TICKERS, rs_threshold, rsi_threshold)
            if not df_res.empty:
                st.session_state.current_scan = df_res
            else:
                st.error(f"Tetap tidak ada saham RS {rs_threshold}+ dengan RSI di bawah {rsi_threshold}.")

    if 'current_scan' in st.session_state:
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={"Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                           "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")},
            disabled=["Stock", "RS", "RSI", "Entry", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN SAHAM PILIHAN"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RS", "RSI"])
            if not to_save.empty:
                to_save["Tgl"] = datetime.now().strftime("%Y-%m-%d")
                updated = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Tersimpan!")
