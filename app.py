import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE (KEMBALI KE V80 STABIL) ---
st.set_page_config(page_title="Noris Trading System V93", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SCANNER (LOGIKA V80) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_scanner_v93(ticker_list, rs_threshold):
    results = []
    # Download data batch untuk kalkulasi RS
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(period="1y")
            if len(df) < 200: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # Filter Minervini Stage 2 & VCP
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                stock_name = t.replace(".JK","")
                results.append({
                    "Tgl": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": stock_name,
                    "Syariah": "✅" if stock_name in SYARIAH_LIST else "❌",
                    "Entry": int(close),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{stock_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V93")
tab1, tab2 = st.tabs(["🔍 INCARAN (SCANNER)", "📊 PERFORMANCE TRACKER"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    
    if st.button("🚀 JALANKAN SCANNER LIVE"):
        with st.spinner("Menganalisa Market..."):
            df_res = run_scanner_v93(ALL_TICKERS, min_rs)
            
            if not df_res.empty:
                st.session_state.current_scan = df_res
                # HEADLINE MINIMALIS DENGAN KETERANGAN TEKNIKAL & WAKTU
                st.markdown(f"""
                    <div style="border-left: 5px solid #1E3A8A; background-color: #f8fafc; padding: 10px 20px; border-radius: 4px; border: 1px solid #e2e8f0; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #1E3A8A; font-weight: bold; font-size: 1.1rem;">🎯 INCARAN TAPAK NAGA</span>
                            <span style="color: #64748b; font-size: 0.85rem;">🕒 Screener Date: {datetime.now().strftime("%d %B %Y | %H:%M")}</span>
                        </div>
                        <div style="margin-top: 5px; color: #475569; font-size: 0.85rem; border-top: 1px solid #e2e8f0; padding-top: 5px;">
                            ⚙️ <b>Screening:</b> Trend Stage 2 Minervini & VCP Setup | Min. RS Rating: {min_rs}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # TABEL HASIL SCAN
                st.dataframe(
                    df_res, 
                    column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")},
                    use_container_width=True, 
                    hide_index=True
                )
                
                if st.button("💾 SIMPAN KE DATABASE"):
                    updated_db = pd.concat([st.session_state.history_db, df_res], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                    updated_db.to_csv(DB_FILE, index=False)
                    st.session_state.history_db = updated_db
                    st.success("Tersimpan!")
            else:
                st.warning("Tidak ada saham yang memenuhi kriteria Minervini/VCP saat ini.")

with tab2:
    st.subheader("📊 Performance Tracker (Portfolio)")
    if not st.session_state.history_db.empty:
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong. Simpan hasil scan untuk melihat performa.")
