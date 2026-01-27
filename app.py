import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V101", layout="wide")

DB_FILE = "trading_history.csv"

# Fungsi muat database agar selalu sinkron
def load_db():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        return df.loc[:, ~df.columns.duplicated()]
    return pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# Selalu muat database terbaru ke session state
st.session_state.history_db = load_db()

# --- 2. ENGINE SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_scanner_v101(ticker_list, rs_threshold):
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
                stock_name = t.replace(".JK","")
                results.append({
                    "Tgl": end_date.strftime("%Y-%m-%d"), "Stock": stock_name,
                    "Syariah": "✅" if stock_name in SYARIAH_LIST else "❌",
                    "Entry": int(close), "SL/TS": int(red_line)
                })
    except: pass
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V101")
tab1, tab2 = st.tabs(["🔍 NORIS INCARAN", "📊 NORIS PETA (PORTFOLIO)"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    if st.button("🚀 JALANKAN SCANNER"):
        df_res = run_scanner_v101(ALL_TICKERS, min_rs)
        if not df_res.empty:
            st.session_state.temp_scan = df_res # Simpan hasil scan sementara
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        else: st.warning("Tidak ada saham lolos kriteria.")

    # Tombol Simpan yang diperbaiki (Force Write to CSV)
    if 'temp_scan' in st.session_state:
        if st.button("💾 SIMPAN KE DATABASE SEKARANG"):
            current_db = load_db()
            updated_db = pd.concat([current_db, st.session_state.temp_scan], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
            updated_db.to_csv(DB_FILE, index=False) # Paksa tulis ke file fisik
            st.session_state.history_db = updated_db
            st.success("✅ BERHASIL! Silakan cek tab NORIS PETA.")

with tab2:
    st.subheader("📊 Noris Peta (Portfolio Tracking)")
    # Muat ulang database fisik setiap kali tab ini dibuka
    db_to_show = load_db()
    if not db_to_show.empty:
        final_list = []
        for _, row in db_to_show.iterrows():
            try:
                curr_p = yf.Ticker(f"{row['Stock']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr_p - row['Entry']) / row['Entry']) * 100
                final_list.append({
                    "Tgl": row['Tgl'], "Stock": row['Stock'], "Syariah": row['Syariah'],
                    "Entry": row['Entry'], "Last": int(curr_p),
                    "G/L%": f"{'🟢' if gain >= 0 else '🔴'} {gain:+.2f}%", "SL/TS": row['SL/TS']
                })
            except: pass
        st.dataframe(pd.DataFrame(final_list), use_container_width=True, hide_index=True)
    else:
        st.info("Database Kosong. Pastikan Bapak sudah klik tombol 'SIMPAN' di tab sebelah.")
