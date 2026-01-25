import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V61", layout="wide", initial_sidebar_state="expanded")

# CSS: Styling Proporsional
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.8rem !important; padding-top: 10px !important; color: #004085; }
        div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        div.stButton > button { border-radius: 8px; background-color: #007BFF; color: white !important; font-weight: bold; height: 3rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER DENGAN IKON GRAFIK V-SHAPE ---
# Menggunakan ikon grafik naik untuk melambangkan struktur Higher High & Higher Low
st.title("📈 Noris Trading System V61") 
st.caption("Market Structure: Higher High (HH) & Higher Low (HL) | Minervini Stage 2 Strategy")

# --- 3. GLOBAL MARKET DASHBOARD (OTOMATIS TAMPIL) ---
def display_global_indices():
    st.markdown("### 🌎 GLOBAL MARKET MONITOR")
    
    indices = {
        "IHSG (JKSE)": "^JKSE",
        "S&P 500 (US)": "^GSPC",
        "Nasdaq (US)": "^IXIC",
        "Dow Jones": "^DJI"
    }
    
    cols = st.columns(len(indices))
    
    for i, (name, symbol) in enumerate(indices.items()):
        try:
            data = yf.Ticker(symbol).history(period="6mo")
            if not data.empty:
                curr = data['Close'].iloc[-1]
                prev = data['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                
                # Cek Status Bullish/Bearish (di atas MA20)
                ma20 = data['Close'].rolling(20).mean().iloc[-1]
                is_bull = curr > ma20
                status_txt = "🟢 BULLISH" if is_bull else "🔴 BEARISH"
                status_color = "#2962FF" # Unified Blue
                
                with cols[i]:
                    st.markdown(f"**{name}**")
                    st.metric(status_txt, f"{curr:,.0f}", f"{pct:+.2f}%")
                    # Mini Chart Persis Saham VCP
                    norm_chart = (data['Close'] / data['Close'].iloc[0] - 1) * 100
                    st.area_chart(norm_chart.tail(60), height=100, color=status_color)
        except:
            cols[i].error(f"Error {name}")
    st.divider()

display_global_indices()

# --- 4. SIDEBAR PARAMETER ---
st.sidebar.title("⚙️ Parameter")
input_mode = st.sidebar.radio("Sumber Saham:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])
min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
modal_jt = st.sidebar.number_input("Modal (Juta Rp)", value=100, step=10)
risk_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0)
ext_mult = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5)

# --- 5. ENGINE SCANNER ---
@st.cache_data(ttl=300)
def scan_market(ticker_list, modal_jt, risk_pct_trade, ext_mult, min_rs):
    results = []
    modal_rupiah = modal_jt * 1_000_000
    risk_money_rupiah = modal_rupiah * (risk_pct_trade / 100)
    
    try:
        # RS Calculation
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
            
            # Stage 2 Filter (Alignment MA melambangkan HH HL)
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_rating >= min_rs:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                if close > red_line:
                    risk_share = close - red_line
                    dist_to_red = (risk_share / close) * 100
                    mult = ext_mult if dist_to_red > 5 else 1.0
                    max_lot = int((risk_money_rupiah * mult / risk_share)/100) if risk_share > 0 else 0
                    
                    results.append({
                        "Emiten": ticker.replace(".JK",""), "RS": rs_rating, 
                        "Status": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL",
                        "Buy": int(close), "SL": int(red_line), "Max Lot": max_lot, "Risk": f"{dist_to_red:.1f}%",
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
                    })
        except: continue
    return pd.DataFrame(results).sort_values("RS", ascending=False) if results else pd.DataFrame()

# --- 6. EKSEKUSI SCANNER ---
if st.button("🚀 JALANKAN SCANNER MINERVINI"):
    # (Daftar ticker otomatis sesuai pilihan sidebar)
    lq45 = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ASII.JK", "ADRO.JK", "PGAS.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK"]
    tickers = lq45 # Contoh sederhana
    
    df_res = scan_market(tickers, modal_jt, risk_pct, ext_mult, min_rs)
    
    if not df_res.empty:
        st.subheader("📋 HASIL SCANNER SAHAM LOLOS KRITERIA")
        st.dataframe(df_res, column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
