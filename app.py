import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V100", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        df_load = pd.read_csv(DB_FILE)
        # Memastikan tidak ada duplikasi kolom saat memuat data
        st.session_state.history_db = df_load.loc[:, ~df_load.columns.duplicated()]
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_scanner_v100(ticker_list, rs_threshold, target_date=None):
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
                    "SL/TS": int(red_line)
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V100")
tab1, tab2, tab3 = st.tabs(["🔍 NORIS INCARAN", "📊 NORIS PETA (PORTFOLIO)", "⏮️ BACKTEST"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    if st.button("🚀 JALANKAN SCANNER"):
        with st.spinner("Menganalisa Market..."):
            df_res = run_scanner_v100(ALL_TICKERS, min_rs)
            if not df_res.empty:
                st.session_state.current_scan = df_res
                st.markdown(f"**NORIS INCARAN REPORT** | {datetime.now().strftime('%d %b %Y')}")
                st.dataframe(df_res, use_container_width=True, hide_index=True)
                if st.button("💾 SIMPAN KE DATABASE"):
                    # Simpan data tanpa menyertakan kolom yang tidak diinginkan
                    updated_db = pd.concat([st.session_state.history_db, df_res], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                    updated_db.to_csv(DB_FILE, index=False)
                    st.session_state.history_db = updated_db
                    st.success("✅ Data Berhasil Disimpan ke Noris Peta!")
            else: st.warning("Tidak ada saham lolos kriteria.")

with tab2:
    st.subheader("📊 Noris Peta (Portfolio Tracking)")
    db = st.session_state.history_db
    if not db.empty:
        track_list = []
        with st.spinner("Mengambil harga pasar terbaru..."):
            for _, row in db.iterrows():
                try:
                    # Ambil harga terkini untuk kalkulasi G/L%
                    curr_df = yf.Ticker(f"{row['Stock']}.JK").history(period="1d")
                    if not curr_df.empty:
                        last_p = curr_df['Close'].iloc[-1]
                        gain = ((last_p - row['Entry']) / row['Entry']) * 100
                        track_list.append({
                            "Tgl": row['Tgl'], "Stock": row['Stock'], "Syariah": row['Syariah'],
                            "Entry": row['Entry'], "Last": int(last_p),
                            "G/L%": f"{'🟢' if gain >= 0 else '🔴'} {gain:+.2f}%",
                            "SL/TS": row['SL/TS']
                        })
                except: pass
        
        if track_list:
            # Menampilkan tabel tanpa kolom Chart
            st.dataframe(pd.DataFrame(track_list), use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Reset Database"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])
            st.rerun()
    else: st.info("Database Portfolio Kosong.")

with tab3:
    st.subheader("⏮️ Backtest Mundur Tanggal")
    b_date = st.date_input("Pilih Tanggal:", datetime.now() - timedelta(days=30))
    if st.button("⏪ SCAN TANGGAL TERPILIH"):
        df_hist = run_scanner_v100(ALL_TICKERS, min_rs, target_date=b_date.strftime("%Y-%m-%d"))
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
