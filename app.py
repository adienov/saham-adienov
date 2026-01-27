import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V105", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SWING SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_swing_scanner(ticker_list, rs_threshold):
    results = []
    try:
        # Download data batch
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
        
        for t in ticker_list:
            df = yf.Ticker(t).history(period="1y")
            if len(df) < 100: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma150 = df['Close'].rolling(150).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # LOGIKA SWING TRADING (BUY ON WEAKNESS):
            # 1. Tren Utama Uptrend (Stage 2): MA150 > MA200
            # 2. Koreksi Sehat: Harga di bawah MA20 (sedang turun) tapi di atas MA50 (masih aman)
            # 3. RSI Moderat: RSI < 50 (tidak overbought) tapi > 30 (bukan crash parah)
            
            if ma150 > ma200 and close > ma50 and close < ma20 and rsi < 55 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False,
                    "Tgl": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": s_name,
                    "Syariah": "✅" if s_name in SYARIAH_LIST else "❌",
                    "Entry": int(close),
                    "RSI": round(rsi, 2),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
    except: pass
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System - Swing Edition")
tab1, tab2 = st.tabs(["🔍 SWING SCANNER (INCARAN)", "📊 NORIS PETA (PORTFOLIO)"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 60)
    st.info("Sistem mencari saham Uptrend yang sedang koreksi (Price < MA20 & Price > MA50).")
    
    if st.button("🚀 SCAN SAHAM SWING"):
        with st.spinner("Mencari peluang di tengah IHSG merah..."):
            df_res = run_swing_scanner(ALL_TICKERS, min_rs)
            if not df_res.empty:
                st.session_state.current_scan = df_res
            else: st.warning("Belum ada saham yang masuk area 'Buy on Weakness'.")

    if 'current_scan' in st.session_state:
        # Menampilkan tabel dengan Link TV untuk kurasi manual
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")
            },
            disabled=["Tgl", "Stock", "Syariah", "Entry", "RSI", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN SAHAM PILIHAN"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RSI"])
            if not to_save.empty:
                updated_db = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated_db.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated_db
                st.success("Tersimpan ke Noris Peta!")
            else: st.warning("Pilih saham yang sudah dicek chart-nya.")

with tab2:
    st.subheader("📊 Noris Peta (Portfolio)")
    if not st.session_state.history_db.empty:
        # Menghitung G/L% Real-time
        db_show = st.session_state.history_db
        track_list = []
        for _, row in db_show.iterrows():
            try:
                curr_p = yf.Ticker(f"{row['Stock']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr_p - row['Entry']) / row['Entry']) * 100
                track_list.append({
                    "Tgl": row['Tgl'], "Stock": row['Stock'], "Syariah": row['Syariah'],
                    "Entry": row['Entry'], "Last": int(curr_p),
                    "G/L%": f"{'🟢' if gain >= 0 else '🔴'} {gain:+.2f}%", "SL/TS": row['SL/TS']
                })
            except: pass
        st.dataframe(pd.DataFrame(track_list), use_container_width=True, hide_index=True)
        if st.button("🗑️ RESET PETA"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])
            st.rerun()
    else: st.info("Peta masih kosong.")
