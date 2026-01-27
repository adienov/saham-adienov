import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V92", layout="wide")

DB_FILE = "database_tapak_naga.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Stock", "Syariah", "Harga BUY", "SL/TS"])

# --- 2. ENGINE SCANNER (BASIS V91) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_scanner_v92(ticker_list, rs_threshold):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(period="1y")
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                emiten = t.replace(".JK","")
                results.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d"), "Stock": emiten,
                    "Syariah": "✅" if emiten in SYARIAH_LIST else "❌",
                    "Harga BUY": int(close), "SL/TS": int(red_line),
                    "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{emiten}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V92")
tab1, tab2 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)"])

with tab1:
    if st.button("🚀 JALANKAN SCANNER LIVE"):
        with st.spinner("Menganalisa Market..."):
            df_res = run_scanner_v92(ALL_TICKERS, 70)
            if not df_res.empty:
                st.session_state.current_scan = df_res
                # HEADLINE MINIMALIS
                st.markdown(f"""
                    <div style="border-left: 5px solid #1E3A8A; background-color: #f1f5f9; padding: 10px 20px; border-radius: 5px; margin-bottom: 15px;">
                        <span style="color: #1E3A8A; font-weight: bold; font-size: 1.1rem;">📋 INCARAN TAPAK NAGA</span>
                        <span style="color: #64748b; font-size: 0.85rem; margin-left: 15px;">| {datetime.now().strftime("%d %b %Y")} | Strategi: Stage 2 & Breakout</span>
                    </div>
                """, unsafe_allow_html=True)
                
                st.dataframe(df_res, column_config={"TV": st.column_config.LinkColumn("Chart", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
                
                if st.button("💾 SIMPAN KE PETA (DATABASE)"):
                    new_db = pd.concat([st.session_state.history_db, df_res], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                    new_db.to_csv(DB_FILE, index=False)
                    st.session_state.history_db = new_db
                    st.success("Tersimpan!")
            else: st.warning("Tidak ada saham breakout.")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga")
    if not st.session_state.history_db.empty:
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
    else: st.info("Database PETA masih kosong.")
