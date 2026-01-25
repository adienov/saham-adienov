import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V65", layout="wide", initial_sidebar_state="expanded")

# --- 2. SIDEBAR PARAMETER (LENGKAP + BACKTEST) ---
st.sidebar.title("⚙️ Parameter")

# --- FITUR BARU: BACKTEST/PROFIT TRACKER ---
st.sidebar.subheader("📊 Profit Tracker (3 Bulan)")
bt_ticker = st.sidebar.text_input("Kode Saham (Contoh: PGAS.JK):", value="PGAS.JK")

if st.sidebar.button("📈 Cek Kinerja 3 Bln"):
    try:
        # Analisis point-to-point 3 bulan terakhir
        df_bt = yf.Ticker(bt_ticker).history(period="4mo")
        if not df_bt.empty:
            p_old = df_bt['Close'].iloc[0]
            p_now = df_bt['Close'].iloc[-1]
            pnl = ((p_now - p_old) / p_old) * 100
            color = "green" if pnl > 0 else "red"
            
            st.sidebar.markdown(f"""
            <div style='background-color:#f0f2f6; padding:10px; border-radius:10px; border-left: 5px solid {color};'>
                <small>Kinerja 3 Bulan Lalu</small><br>
                <b>Estimasi P/L: <span style='color:{color};'>{pnl:+.2f}%</span></b><br>
                <small>Price: {p_old:,.0f} → {p_now:,.0f}</small>
            </div>
            """, unsafe_allow_html=True)
    except: st.sidebar.error("Data tidak tersedia.")

st.sidebar.divider()
st.sidebar.subheader("1. Daftar Saham")
input_mode = st.sidebar.radio("Sumber:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])

# Logika Tickers (Lengkap sesuai V59)
lq45_tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK", "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "GOTO.JK"]
kompas100_tickers = list(set(lq45_tickers + ["ITMG.JK", "TINS.JK", "ENRG.JK", "INDY.JK", "BREN.JK", "CUAN.JK", "AMMN.JK", "ADMR.JK", "TOWR.JK", "TBIG.JK", "BUKA.JK", "EMTK.JK", "SCMA.JK", "GGRM.JK", "HMSP.JK", "MAPI.JK", "CTRA.JK", "BSDE.JK", "PWON.JK", "SMRA.JK", "ASRI.JK", "JSMR.JK", "PTPP.JK", "WIKA.JK", "ADHI.JK", "INKP.JK", "TKIM.JK", "ESSA.JK", "AUTO.JK", "GJTL.JK", "MAPA.JK", "ERAA.JK"]))

if input_mode == "LQ45 (Bluechip)": tickers = lq45_tickers
elif input_mode == "Kompas100 (Market Wide)": tickers = kompas100_tickers
else:
    user_input = st.sidebar.text_area("Kode Saham:", value="BREN, AMMN, CUAN, GOTO, BBRI")
    tickers = [f"{x.strip().upper()}.JK" for x in user_input.split(',') if x.strip()]

st.sidebar.divider()
st.sidebar.subheader("2. Filter & Money Management")
min_rs_rating = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
chart_duration = st.sidebar.selectbox("Durasi Chart", ["3mo", "6mo", "1y"], index=1)
modal_juta = st.sidebar.number_input("Modal (Juta Rp)", value=100)
risk_per_trade = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0)
ext_mult = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5)
min_trans = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0)

# --- 3. ENGINE SCANNER (KODE STABIL V59) ---
@st.cache_data(ttl=300)
def scan_market(ticker_list, min_val_m, modal_jt, risk_pct_trade, ext_mult_val, min_rs_val):
    results = []
    modal_rupiah = modal_jt * 1_000_000
    risk_money_rupiah = modal_rupiah * (risk_pct_trade / 100)
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
            # Minervini Stage 2 Filter
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_rating >= min_rs_val:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                if close > red_line:
                    dist_red = ((close-red_line)/close)*100
                    vcp_score = sum([1 for x in [df.ta.atr(5).iloc[-1]/df.ta.atr(20).iloc[-1]<0.9, (df['High'].tail(250).max()-close)/df['High'].tail(250).max()<0.1, df.ta.rsi().iloc[-1]>60]])
                    results.append({
                        "Emiten": ticker.replace(".JK",""), "RS": rs_rating, "Rating": "⭐"*max(1, vcp_score), 
                        "Status": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL",
                        "Buy": int(close), "SL": int(red_line), "Max Lot": int((risk_money_rupiah * (ext_mult_val if dist_red > 5 else 1.0) / (close-red_line))/100),
                        "Risk": f"{dist_red:.1f}%", "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}", "ScoreRaw": vcp_score
                    })
        except: continue
    return pd.DataFrame(results).sort_values(by=["ScoreRaw", "RS"], ascending=False) if results else pd.DataFrame()

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V65")

if st.button("🚀 SCAN MINERVINI MARKET"):
    df_res = scan_market(tickers, min_trans, modal_juta, risk_per_trade, ext_mult, min_rs_rating)
    if not df_res.empty:
        st.markdown("### 🔍 MARKET CORRELATION")
        ihsg_ticker = yf.Ticker("^JKSE")
        ihsg_hist = ihsg_ticker.history(period="1y")
        is_bull = ihsg_hist['Close'].iloc[-1] > ihsg_hist['Close'].rolling(20).mean().iloc[-1]
        st.markdown(f"**Current Market Status: <span style='color:{'green' if is_bull else 'red'}; font-size:1.5rem;'>{'🟢 BULLISH' if is_bull else '🔴 BEARISH'}</span>**", unsafe_allow_html=True)
        
        cols = st.columns(4)
        with cols[0]:
            st.markdown("**IHSG INDEX**")
            ihsg_data = ihsg_hist['Close'].tail(120 if chart_duration == "6mo" else (60 if chart_duration == "3mo" else 250))
            st.area_chart((ihsg_data/ihsg_data.iloc[0]-1)*100, height=120, color="#2962FF")
        for idx, row in enumerate(df_res.head(3).itertuples()):
            with cols[idx+1]:
                st.markdown(f"**{row.Emiten}** {row.Rating}")
                s_data = yf.Ticker(f"{row.Emiten}.JK").history(period=chart_duration)['Close']
                st.area_chart((s_data/s_data.iloc[0]-1)*100, height=120, color="#2962FF")
        
        st.divider()
        st.subheader("📋 HASIL SCANNER LENGKAP")
        st.dataframe(df_res, column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
