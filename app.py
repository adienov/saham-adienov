import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V57", layout="wide", initial_sidebar_state="expanded")

# CSS: Styling Unified
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-top: 5px !important; color: #004085; }
        div.stButton > button { border-radius: 8px; background-color: #007BFF; color: white !important; font-weight: bold; height: 3rem; }
        div[data-testid="stDataFrame"] th { background-color: #f1f3f5; font-size: 0.85rem !important; text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (PARAMETER LENGKAP - KEMBALI) ---
st.sidebar.title("⚙️ Parameter")
st.sidebar.subheader("1. Daftar Saham")
input_mode = st.sidebar.radio("Sumber:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])

lq45_tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK", "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "GOTO.JK"]
kompas100_tickers = list(set(lq45_tickers + ["ITMG.JK", "TINS.JK", "ENRG.JK", "INDY.JK", "BREN.JK", "CUAN.JK", "AMMN.JK", "ADMR.JK", "TOWR.JK", "TBIG.JK", "BUKA.JK", "EMTK.JK", "SCMA.JK", "GGRM.JK", "HMSP.JK", "MAPI.JK", "CTRA.JK", "BSDE.JK", "PWON.JK", "SMRA.JK", "ASRI.JK", "JSMR.JK", "PTPP.JK", "WIKA.JK", "ADHI.JK", "INKP.JK", "TKIM.JK", "ESSA.JK", "AUTO.JK", "GJTL.JK", "MAPA.JK", "ERAA.JK"]))

if input_mode == "LQ45 (Bluechip)": tickers = lq45_tickers
elif input_mode == "Kompas100 (Market Wide)": tickers = kompas100_tickers
else:
    user_input = st.sidebar.text_area("Kode Saham (Pisah Koma):", value="BREN, AMMN, CUAN, GOTO, BBRI")
    tickers = [f"{x.strip().upper()}.JK" for x in user_input.split(',') if x.strip()]

st.sidebar.divider()
st.sidebar.subheader("2. Filter Minervini")
min_rs_rating = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
chart_duration = st.sidebar.selectbox("Durasi Chart", ["3mo", "6mo", "1y"], index=1)

st.sidebar.divider()
st.sidebar.subheader("3. Money Management")
modal_juta = st.sidebar.number_input("Modal (Juta Rp)", value=100, step=10)
risk_per_trade_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0)
extended_multiplier = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5)
min_trans = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
non_syariah_list = ["BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BDMN", "BNGA", "NISP", "GGRM", "HMSP", "WIIM", "RMBA", "MAYA", "NOBU", "ARTO"]

# --- 3. ENGINE SCANNER (PASTIKAN FUNGSI INI ADA) ---
@st.cache_data(ttl=300)
def scan_market(ticker_list, min_val_m, risk_pct_param, modal_jt, risk_pct_trade, ext_mult, min_rs):
    results = []
    selected_tickers = []
    modal_rupiah = modal_jt * 1_000_000
    risk_money_rupiah = modal_rupiah * (risk_pct_trade / 100)
    
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_scores = {t: (data_batch[t].iloc[-1]/data_batch[t].iloc[0]-1) for t in ticker_list if t in data_batch}
        rs_df = pd.DataFrame(list(rs_scores.items()), columns=['Ticker', 'Perf'])
        rs_df['Rank'] = rs_df['Perf'].rank(pct=True) * 99
        rs_map = rs_df.set_index('Ticker')['Rank'].to_dict()
    except: rs_map = {t: 50 for t in ticker_list}

    for ticker in ticker_list:
        try:
            df = yf.Ticker(ticker).history(period="2y")
            if len(df) < 250: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            low_52w, high_52w = df['Low'].tail(250).min(), df['High'].tail(250).max()
            rs_rating = int(rs_map.get(ticker, 50))
            is_stage2 = close > ma150 and ma150 > ma200 and ma200 > df['Close'].rolling(200).mean().iloc[-20] and ma50 > ma150 and close > ma50 and close > low_52w*1.25 and close > high_52w*0.75 and rs_rating >= min_rs
            if is_stage2:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                if close > red_line:
                    vol_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1]
                    dist_to_red = ((close - red_line)/close)*100
                    vcp_score = sum([1 for x in [df.ta.atr(5).iloc[-1]/df.ta.atr(20).iloc[-1]<0.9, (high_52w-close)/high_52w<0.1, df.ta.rsi().iloc[-1]>60, vol_ratio>0.8]])
                    risk_mult = ext_mult if dist_to_red > 5 else 1.0
                    sl, risk_share = int(red_line), close - red_line
                    max_lot = int((risk_money_rupiah * risk_mult / risk_share)/100) if risk_share > 0 else 0
                    results.append({
                        "Emiten": ticker.replace(".JK",""), "RS": rs_rating, "Rating": "⭐"*max(1, vcp_score), 
                        "Status": "🟣 VOL SPIKE" if vol_ratio > 2 else "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL",
                        "Buy": int(close), "SL": sl, "TP": int(close + risk_share*1.5), "Max Lot": max_lot, "Risk": f"{dist_to_red:.1f}%", "ScoreRaw": vcp_score
                    })
                    selected_tickers.append(ticker)
        except: continue
    return pd.DataFrame(results).sort_values(by=["ScoreRaw", "RS"], ascending=False) if results else pd.DataFrame(), selected_tickers

# --- 4. TAMPILAN UTAMA ---
st.title("📱 Noris Trading System V57")

with st.expander("📖 PANDUAN STRATEGI MINERVINI & VCP (Klik Membaca)"):
    st.markdown("""
    1. **Filter Stage 2:** Sistem hanya menampilkan saham *Uptrend* kuat (Lolos 8 syarat Minervini).
    2. **Cek IHSG Index:** Pastikan tren pasar (Kotak Pertama) sedang menanjak.
    3. **Pilih Bintang Terbanyak:** Fokus pada saham dengan rating ⭐⭐⭐⭐⭐.
    """)

if st.button("🚀 SCAN MINERVINI MARKET"):
    df, sel_tickers = scan_market(tickers, min_trans, risk_per_trade_pct, modal_juta, risk_per_trade_pct, extended_multiplier, min_rs_rating)
    if not df.empty:
        st.markdown("### 🔍 MARKET CORRELATION (Unified View)")
        cols = st.columns(4)
        with cols[0]:
            st.markdown("**IHSG INDEX**")
            ihsg_data = yf.Ticker("^JKSE").history(period=chart_duration)['Close']
            st.area_chart((ihsg_data/ihsg_data.iloc[0]-1)*100, height=120, color="#2962FF")
        for idx, row in enumerate(df.head(3).itertuples()):
            with cols[idx+1]:
                st.markdown(f"**{row.Emiten}** {row.Rating}")
                s_data = yf.Ticker(f"{row.Emiten}.JK").history(period=chart_duration)['Close']
                st.area_chart((s_data/s_data.iloc[0]-1)*100, height=120, color="#2962FF")
        st.divider()
        st.subheader("📋 HASIL SCANNER LENGKAP")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else: st.warning("Tidak ada saham lolos kriteria.")
