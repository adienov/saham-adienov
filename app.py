import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="EDU-VEST TRADING SYSTEM V99", layout="wide")

DB_FILE = "trading_history.csv"
MAIN_COLS = ["Tanggal", "Stock", "Syariah", "Entry", "SL/TS"]

# FUNGSI PERBAIKAN DATA: Memastikan kolom unik dan standar
def load_and_standardize_db():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # 1. Hapus kolom duplikat secara fisik agar tidak error
            df = df.loc[:, ~df.columns.duplicated()]
            # 2. Sinkronisasi nama kolom lama ke baru
            df = df.rename(columns={'Emiten': 'Stock', 'Harga_Awal': 'Entry', 'Tgl': 'Tanggal'})
            # 3. Paksa hanya ambil kolom utama agar rapi
            df = df[df.columns.intersection(MAIN_COLS)]
            return df
        except:
            return pd.DataFrame(columns=MAIN_COLS)
    return pd.DataFrame(columns=MAIN_COLS)

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_and_standardize_db()

# --- 2. ENGINE SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_edu_scanner(ticker_list, rs_threshold):
    results = []
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
        for t in ticker_list:
            df = yf.Ticker(t).history(period="1y")
            if len(df) < 200: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Stock": s_name, "Syariah": "✅" if s_name in SYARIAH_LIST else "❌", "Entry": int(close), "SL/TS": int(red_line)})
    except: pass
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 EDU-VEST TRADING SYSTEM")

tab1, tab2 = st.tabs(["🔍 EDU-SCANNER (INCARAN)", "📊 EDU-PORTFOLIO (PETA)"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    if st.button("🚀 JALANKAN SCANNER"):
        df_res = run_edu_scanner(TICKERS, min_rs)
        if not df_res.empty:
            st.session_state.current_scan = df_res
            st.dataframe(df_res, use_container_width=True, hide_index=True)
            if st.button("💾 SIMPAN KE PORTFOLIO"):
                # PROSES SIMPAN YANG AMAN DARI DUPLIKAT
                new_data = df_res[MAIN_COLS]
                updated = pd.concat([st.session_state.history_db, new_data], ignore_index=True)
                updated = updated.loc[:, ~updated.columns.duplicated()] # Hapus kolom ganda hasil concat
                updated = updated.drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Sinkronisasi Berhasil!")
        else: st.warning("Tidak ada saham lolos kriteria.")

with tab2:
    st.subheader("📊 Edu-Portfolio Tracking")
    # Tampilan tabel dipastikan bersih dan unik
    if not st.session_state.history_db.empty:
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
        if st.button("🗑️ Reset Database Total"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.history_db = pd.DataFrame(columns=MAIN_COLS)
            st.rerun()
    else: st.info("Database Kosong.")
