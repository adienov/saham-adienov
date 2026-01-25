import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V64", layout="wide", initial_sidebar_state="expanded")

# --- 2. GLOBAL MARKET MONITOR (OTOMATIS) ---
def display_global_indices():
    st.markdown("### 🌎 GLOBAL MARKET MONITOR")
    indices = {"IHSG (JKSE)": "^JKSE", "S&P 500 (US)": "^GSPC", "Nasdaq (US)": "^IXIC", "Dow Jones": "^DJI"}
    cols = st.columns(len(indices))
    for i, (name, symbol) in enumerate(indices.items()):
        try:
            data = yf.Ticker(symbol).history(period="6mo")
            if not data.empty:
                curr = data['Close'].iloc[-1]
                pct = ((curr - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
                ma20 = data['Close'].rolling(20).mean().iloc[-1]
                status_txt = "🟢 BULLISH" if curr > ma20 else "🔴 BEARISH"
                with cols[i]:
                    st.markdown(f"**{name}**")
                    st.metric(status_txt, f"{curr:,.0f}", f"{pct:+.2f}%")
                    st.area_chart((data['Close']/data['Close'].iloc[0]-1)*100, height=80, color="#2962FF")
        except: pass
    st.divider()

display_global_indices()

# --- 3. SIDEBAR PARAMETER & PROFIT TRACKER ---
st.sidebar.title("⚙️ Parameter")
st.sidebar.subheader("📊 Profit Tracker (3 Bulan)")
bt_ticker = st.sidebar.text_input("Kode Saham (Contoh: PGAS.JK):", value="PGAS.JK")

if st.sidebar.button("📈 Cek Profit 3 Bln"):
    try:
        df_bt = yf.Ticker(bt_ticker).history(period="4mo")
        p_old, p_now = df_bt['Close'].iloc[0], df_bt['Close'].iloc[-1]
        pnl = ((p_now - p_old) / p_old) * 100
        color = "green" if pnl > 0 else "red"
        st.sidebar.success(f"Cuan/Rugi: {pnl:+.2f}%")
        st.sidebar.caption(f"Price: {p_old:,.0f} -> {p_now:,.0f}")
    except: st.sidebar.error("Data Error")

st.sidebar.divider()
input_mode = st.sidebar.radio("Sumber Saham:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)"])
min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
modal_jt = st.sidebar.number_input("Modal (Juta Rp)", value=100)

# --- 4. ENGINE SCANNER (LIVE MARKET) ---
@st.cache_data(ttl=300)
def scan_market_live(ticker_list, min_rs_val):
    results = []
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except: rs_map = {}

    for ticker in ticker_list:
        try:
            df = yf.Ticker(ticker).history(period="2y")
            if len(df) < 250: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_rating = int(rs_map.get(ticker, 0.5) * 99)
            
            # Kriteria Stage 2
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_rating >= min_rs_val:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                results.append({
                    "Emiten": ticker.replace(".JK",""), "RS": rs_rating, 
                    "Status": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL",
                    "Buy": int(close), "SL": int(red_line), "Risk": f"{((close-red_line)/close)*100:.1f}%",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
                })
        except: continue
    return pd.DataFrame(results).sort_values("RS", ascending=False) if results else pd.DataFrame()

# --- 5. EKSEKUSI SCANNER ---
if st.button("🚀 JALANKAN SCANNER LIVE"):
    lq45 = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ASII.JK", "ADRO.JK", "PGAS.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "MDKA.JK", "EXCL.JK"]
    df_res = scan_market_live(lq45, min_rs)
    
    if not df_res.empty:
        st.subheader("📋 HASIL SCANNER SAHAM LOLOS KRITERIA")
        st.dataframe(df_res, column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
    else:
        st.warning("Belum ada saham yang memenuhi kriteria hari ini.")
