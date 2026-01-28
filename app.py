import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST REBOUND V112", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE REBOUND SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=60)
def run_rebound_scanner(ticker_list, rs_min):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 200: continue
            
            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # --- STRATEGI BARU: REBOUND AT SUPPORT ---
            # 1. Leader (CANSLIM): RS Rating >= 75 (Sedikit dilonggarkan agar pilihan bertambah) [cite: 21]
            # 2. Support Touch: Harga rendah hari ini sempat menyentuh area MA200 (Benteng Terakhir)
            # 3. Reversal: Harga penutupan mulai lebih tinggi dari harga terendah hari ini (Ada perlawanan)
            
            is_near_ma200 = df['Low'].iloc[-1] <= (ma200 * 1.02) and close >= (ma200 * 0.98)
            is_reversal = close > df['Low'].iloc[-1] # Ada ekor bawah (Hammer/Pinbar)
            
            if rs_val >= rs_min and is_near_ma200 and is_reversal:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False, "Stock": s_name, "RS": rs_val, 
                    "Dist to MA200": f"{round(((close/ma200)-1)*100, 2)}%",
                    "Entry": int(close), "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN ---
st.title("🏹 EDU-VEST: REBOUND HUNTER V112")
st.info("Mencari Market Leaders yang memantul di Support MA200 (Benteng Terakhir).")

tab1, tab2 = st.tabs(["🔍 REBOUND SCANNER", "📊 PORTFOLIO"])

with tab1:
    rs_input = st.sidebar.slider("Min. RS Rating (Standard = 75)", 0, 99, 75)
    
    if st.button("🚀 SCAN PANTULAN HARGA"):
        df_res = run_rebound_scanner(ALL_TICKERS, rs_input)
        if not df_res.empty:
            st.session_state.current_scan = df_res
        else:
            st.warning("Belum ada Leader yang menyentuh MA200 pagi ini.")

    if 'current_scan' in st.session_state:
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={"Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                           "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")},
            disabled=["Stock", "RS", "Dist to MA200", "Entry", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN PILIHAN"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RS", "Dist to MA200"])
            if not to_save.empty:
                to_save["Tgl"] = datetime.now().strftime("%Y-%m-%d")
                updated = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Tersimpan!")
