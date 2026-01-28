import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST CRASH RECOVERY V110", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SCANNER SEROK (CRASH RECOVERY) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=60) # Cache diperpendek karena market volatile
def run_crash_screener(ticker_list, rs_min):
    results = []
    # Download data batch untuk RS Rating
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
            
            # --- LOGIKA SEROK SAAT CRASH ---
            # 1. CANSLIM Leader: RS Rating >= 80 (Saham terkuat di market)
            # 2. Oversold: RSI < 35 (Sudah jenuh jual karena panik)
            # 3. Last Defense: Harga masih di atas atau dekat MA200 (Tren besar belum patah)
            
            if rs_val >= rs_min and rsi < 35 and close > (ma200 * 0.95): # Toleransi 5% di bawah MA200
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False,
                    "Stock": s_name,
                    "RS Rating": rs_val,
                    "RSI": round(rsi, 2),
                    "Status": "OVERSOLD ⚡",
                    "Entry (Crash)": int(close),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("⚡ EDU-VEST: SEROK CRASH SCANNER")
st.warning("⚠️ Market Crash Detected! Fokus pada Saham Leader (RS 80+) yang terdiskon parah.")

tab1, tab2 = st.tabs(["🔍 CRASH SCANNER", "📊 PORTFOLIO"])

with tab1:
    rs_threshold = st.sidebar.slider("Min. RS Rating (Standard CANSLIM = 80)", 0, 99, 80)
    
    if st.button("🚀 SCAN SAHAM DISKON"):
        with st.spinner("Mencari emiten berdiskon tinggi..."):
            df_res = run_crash_screener(ALL_TICKERS, rs_threshold)
            if not df_res.empty:
                st.session_state.current_scan = df_res
            else:
                st.error("Tidak ada saham Leader yang memenuhi syarat oversold saat ini.")

    if 'current_scan' in st.session_state:
        st.write("### 📋 Daftar Saham Diskon (Konfirmasi via TV):")
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")
            },
            disabled=["Stock", "RS Rating", "RSI", "Status", "Entry (Crash)", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN SAHAM TERPILIH"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RSI", "Status"])
            if not to_save.empty:
                to_save = to_save.rename(columns={"Entry (Crash)": "Entry"})
                to_save["Tgl"] = datetime.now().strftime("%Y-%m-%d")
                updated = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Tersimpan di Portfolio Serok Bapak!")

with tab2:
    st.subheader("📊 Portfolio Serok")
    if not st.session_state.history_db.empty:
        # Menampilkan data portfolio dengan G/L% real-time
        db_show = st.session_state.history_db
        # ... (Logika G/L% sama seperti V109)
