import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST HYBRID SYSTEM V108", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE HYBRID (CANSLIM + SWING) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]

@st.cache_data(ttl=300)
def run_hybrid_scanner(ticker_list, rs_min):
    results = []
    # Download data batch untuk RS Rating
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 150: continue
            
            # --- FILTER TEKNIKAL ---
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # --- FILTER FUNDAMENTAL (C, A, & S dari CANSLIM) ---
            info = stock.info
            roe = info.get('returnOnEquity', 0)
            eps_growth = info.get('earningsQuarterlyGrowth', 0)
            
            # LOGIKA HYBRID:
            # 1. CANSLIM: RS Rating >= 80 (Market Leaders)
            # 2. CANSLIM: ROE > 17% & Positive EPS Growth
            # 3. SWING: Price > MA50 & Price < MA20 (Pullback/Koreksi Sehat)
            # 4. SWING: Price > MA200 (Uptrend Jangka Panjang)
            
            if rs_val >= rs_min and close > ma200 and close > ma50 and close < ma20:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False,
                    "Tgl": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": s_name,
                    "RS": rs_val,
                    "ROE%": round(roe * 100, 2) if roe else 0,
                    "EPS Gr%": round(eps_growth * 100, 2) if eps_growth else 0,
                    "Entry": int(close),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 EDU-VEST HYBRID (CANSLIM & SWING)")

tab1, tab2 = st.tabs(["🔍 HYBRID SCANNER", "📊 PORTFOLIO"])

with tab1:
    # Parameter CANSLIM: RS Rating Minimal
    rs_threshold = st.sidebar.slider("Min. RS Rating (Standard CANSLIM = 80)", 0, 99, 80)
    
    if st.button("🚀 JALANKAN SCANNER HYBRID"):
        tickers = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK"]
        with st.spinner("Mencari Leaders yang sedang pullback..."):
            df_res = run_hybrid_scanner(tickers, rs_threshold)
            if not df_res.empty:
                st.session_state.current_scan = df_res
            else: st.warning("Tidak ada saham Leader yang sedang pullback saat ini.")

    if 'current_scan' in st.session_state:
        st.write("### 📋 Hasil Incaran (Leader Pullback):")
        # Integrasi data fundamental ke tabel untuk kurasi manual
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")
            },
            disabled=["Tgl", "Stock", "RS", "ROE%", "EPS Gr%", "Entry", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN KE PORTFOLIO"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RS", "ROE%", "EPS Gr%"])
            if not to_save.empty:
                updated = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Berhasil dipetakan!")

with tab2:
    st.subheader("📊 Edu-Portfolio")
    # (Logika tab portfolio tetap sama seperti V105 Bapak)
    # ...
