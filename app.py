import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST TRADING SYSTEM V96", layout="wide")

DB_FILE = "trading_history.csv"

# Fungsi untuk membersihkan database yang berantakan
def load_clean_db():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Standardisasi kolom agar tidak ada 'None'
        # Mengonversi data lama ke format baru jika perlu
        if 'Emiten' in df.columns:
            df = df.rename(columns={'Emiten': 'Stock', 'Harga_Awal': 'Entry', 'Tgl': 'Tanggal'})
        
        # Hanya ambil kolom yang kita inginkan agar tabel rapi
        target_cols = ["Tanggal", "Stock", "Syariah", "Entry", "SL/TS"]
        return df[df.columns.intersection(target_cols)]
    return pd.DataFrame(columns=["Tanggal", "Stock", "Syariah", "Entry", "SL/TS"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_clean_db()

# --- 2. ENGINE SCANNER (BASIS V94) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_edu_scanner(ticker_list, rs_threshold):
    results = []
    end_date = datetime.now()
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
                results.append({
                    "Tanggal": end_date.strftime("%Y-%m-%d"), "Stock": s_name,
                    "Syariah": "✅" if s_name in SYARIAH_LIST else "❌",
                    "Entry": int(close), "SL/TS": int(red_line)
                })
    except: pass
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 EDU-VEST TRADING SYSTEM")

tab1, tab2 = st.tabs(["🔍 EDU-SCANNER", "📊 EDU-PORTFOLIO"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    if st.button("🚀 JALANKAN SCANNER"):
        with st.spinner("Menganalisa Market..."):
            df_res = run_edu_scanner(ALL_TICKERS, min_rs)
            if not df_res.empty:
                st.session_state.current_scan = df_res
                st.markdown(f"**EDU-VEST REPORT** | {datetime.now().strftime('%d %b %Y')}")
                st.dataframe(df_res, use_container_width=True, hide_index=True)
                if st.button("💾 SIMPAN KE PORTFOLIO"):
                    # Simpan dengan kolom yang sudah bersih
                    updated = pd.concat([st.session_state.history_db, df_res], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                    updated.to_csv(DB_FILE, index=False)
                    st.session_state.history_db = updated
                    st.success("Tersimpan dan Terpeta!")
            else: st.warning("Belum ada saham breakout.")

with tab2:
    st.subheader("📊 Portfolio Tracking (Clean View)")
    if not st.session_state.history_db.empty:
        # Menampilkan tabel yang sudah dipaksa bersih dari kolom lama
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
        if st.button("🗑️ Reset Database (Jika Masih Berantakan)"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()
    else: st.info("Database Kosong.")
