import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST TRADING SYSTEM V95", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        df_load = pd.read_csv(DB_FILE)
        # Membersihkan kolom None dari database lama
        st.session_state.history_db = df_load.dropna(axis=1, how='all')
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SCANNER (BASIS V94) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_scanner_v95(ticker_list, rs_threshold, target_date=None):
    results = []
    end_date = datetime.now() if target_date is None else datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
    
    try:
        data_batch = yf.download(ticker_list, start=end_date - timedelta(days=365), end=end_date, progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except: rs_map = {}

    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(start=end_date - timedelta(days=365), end=end_date)
            if len(df) < 200: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                stock_name = t.replace(".JK","")
                results.append({
                    "Tgl": end_date.strftime("%Y-%m-%d") if target_date is None else target_date,
                    "Stock": stock_name,
                    "Syariah": "✅" if stock_name in SYARIAH_LIST else "❌",
                    "Entry": int(close),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{stock_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 EDU-VEST TRADING SYSTEM") # Trade Mark Baru

tab1, tab2, tab3 = st.tabs(["🔍 EDU-SCANNER (INCARAN)", "📊 EDU-PORTFOLIO (PETA)", "⏮️ HISTORICAL BACKTEST"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    if st.button("🚀 JALANKAN SCANNER MARKET"):
        with st.spinner("Menganalisa Market..."):
            df_res = run_scanner_v95(ALL_TICKERS, min_rs)
            if not df_res.empty:
                st.session_state.current_scan = df_res
                st.markdown(f"""
                    <div style="border-left: 5px solid #1E3A8A; background-color: #f8fafc; padding: 10px 20px; border: 1px solid #e2e8f0; margin-bottom: 15px;">
                        <span style="color: #1E3A8A; font-weight: bold;">📋 EDU-VEST SCANNER REPORT</span>
                        <span style="color: #64748b; font-size: 0.8rem; margin-left: 15px;">| {datetime.now().strftime("%d %b %Y | %H:%M")} | Screening: Minervini & VCP</span>
                    </div>
                """, unsafe_allow_html=True)
                st.dataframe(df_res, column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
            else: st.warning("Tidak ada saham lolos kriteria.")

    if 'current_scan' in st.session_state:
        if st.button("💾 SIMPAN KE EDU-PORTFOLIO"):
            # Gabungkan hanya kolom yang valid
            valid_cols = ["Tgl", "Stock", "Syariah", "Entry", "SL/TS"]
            updated_db = pd.concat([st.session_state.history_db, st.session_state.current_scan[valid_cols]], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
            updated_db.to_csv(DB_FILE, index=False)
            st.session_state.history_db = updated_db
            st.toast("✅ Tersimpan di Edu-Portfolio!", icon="💾")

with tab2:
    st.subheader("📊 Edu-Portfolio Tracking")
    if not st.session_state.history_db.empty:
        # Menampilkan tabel yang sudah bersih dari kolom None
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
    else: st.info("Database Portfolio Kosong.")

with tab3:
    st.subheader("⏮️ Historical Backtest")
    b_date = st.date_input("Pilih Tanggal Mundur:", datetime.now() - timedelta(days=30))
    if st.button("⏪ SCAN TANGGAL TERPILIH"):
        df_hist = run_scanner_v95(ALL_TICKERS, min_rs, target_date=b_date.strftime("%Y-%m-%d"))
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
