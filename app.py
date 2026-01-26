import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V69", layout="wide", initial_sidebar_state="expanded")

# --- 2. INITIAL DATABASE (SESSION STATE) ---
if 'history_db' not in st.session_state:
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal", "Chart"])

# --- 3. SIDEBAR PARAMETER (BASIS V59) ---
st.sidebar.title("⚙️ Parameter & Database")
# (Parameter seperti Modal, RS Rating, dll tetap di sini)
if st.sidebar.button("🗑️ Reset Database"):
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal", "Chart"])
    st.rerun()

# --- 4. ENGINE SCANNER (BASIS V59) ---
@st.cache_data(ttl=300)
def scan_market_v59(ticker_list):
    results = []
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except: rs_map = {}

    for ticker in ticker_list:
        try:
            df = yf.Ticker(ticker).history(period="1y")
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_rating = int(rs_map.get(ticker, 0.5) * 99)
            
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_rating >= 70:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                if close > red_line:
                    emiten_clean = ticker.replace(".JK","")
                    results.append({
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Emiten": emiten_clean,
                        "Harga_Awal": int(close),
                        "SL_Awal": int(red_line),
                        "Status_Awal": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL",
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{emiten_clean}"
                    })
        except: continue
    return pd.DataFrame(results)

# --- 5. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V69")

tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER"])

with tab1:
    if st.button("🚀 JALANKAN SCANNER V59"):
        # Contoh Tickers
        tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "PGAS.JK", "MDKA.JK", "EXCL.JK", "BBCA.JK"]
        df_today = scan_market_v59(tickers)
        
        if not df_today.empty:
            st.subheader("📋 Saham Lolos Kriteria")
            # Tampilkan link TV di tabel scanner
            st.dataframe(df_today, column_config={"Chart": st.column_config.LinkColumn("Link", display_text="📈 TV")}, use_container_width=True, hide_index=True)
            
            if st.button("💾 SIMPAN KE DATABASE"):
                st.session_state.history_db = pd.concat([st.session_state.history_db, df_today], ignore_index=True).drop_duplicates(subset=['Emiten'], keep='last')
                st.success("Berhasil Disimpan! Silakan cek Tab Performance Tracker.")
        else: st.warning("Tidak ada saham lolos kriteria.")

with tab2:
    st.subheader("📈 Day-by-Day Tracking")
    if not st.session_state.history_db.empty:
        # Kalkulasi kenaikan otomatis
        track_list = []
        for _, row in st.session_state.history_db.iterrows():
            try:
                curr_p = yf.Ticker(f"{row['Emiten']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr_p - row['Harga_Awal']) / row['Harga_Awal']) * 100
                track_list.append({
                    "Tgl Rekom": row['Tanggal'], "Emiten": row['Emiten'], "Entry": row['Harga_Awal'],
                    "Current": int(curr_p), "% G/L": round(gain, 2), "Status": "✅ PROFIT" if gain > 0 else "❌ LOSS",
                    "Chart": row['Chart']
                })
            except: continue
        
        df_track = pd.DataFrame(track_list)
        # Tampilkan link TV di tabel database
        st.dataframe(df_track, column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka TV")}, use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong.")
