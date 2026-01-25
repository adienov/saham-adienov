import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V45", layout="wide", initial_sidebar_state="expanded")

# CSS: Styling
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.8rem !important; padding-top: 10px !important; color: #004085; }
        div[data-testid="stCaptionContainer"] { font-size: 0.9rem; color: #6c757d; }
        div.stButton > button { width: 100%; border-radius: 8px; background-color: #007BFF; color: white !important; font-weight: bold; border: none; padding: 0.5rem; }
        div.stButton > button:hover { background-color: #0056b3; }
        div[data-testid="stDataFrame"] th { text-align: center !important; background-color: #f8f9fa; color: #495057; }
        div[data-testid="stDataFrame"] td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER ---
st.title("📱 Noris Trading System V45")
st.caption("Visual Fix: Minervini Trend Template & VCP Pattern Preview")

# --- BAROMETER IHSG ---
def get_ihsg_status():
    try:
        ihsg = yf.download("^JKSE", period="3mo", progress=False)
        if isinstance(ihsg.columns, pd.MultiIndex): ihsg = ihsg.xs("^JKSE", level=1, axis=1)
        current_price = ihsg['Close'].iloc[-1]
        ma20 = ihsg['Close'].rolling(window=20).mean().iloc[-1]
        if current_price > ma20: return "🟢 BULLISH", "Market Aman.", "normal"
        else: return "🔴 BEARISH", "Hati-hati.", "inverse"
    except: return "OFFLINE", "No Data", "off"

ihsg_stat, ihsg_advice, ihsg_col = get_ihsg_status()
st.info(f"**STATUS IHSG:** {ihsg_stat} | {ihsg_advice}")

# --- EXPANDER KAMUS ---
with st.expander("📖 KAMUS MINERVINI (Klik Disini)"):
    st.markdown("""
    ### 🏆 Minervini Trend Template (Stage 2)
    Saham **WAJIB** memenuhi syarat ini agar lolos screening:
    1.  Harga > MA 150 & MA 200.
    2.  MA 150 > MA 200.
    3.  MA 200 sedang Menanjak (Uptrend).
    4.  MA 50 > MA 150 & MA 200.
    5.  Harga > MA 50.
    6.  Harga minimal 25% di atas Low 52-Minggu.
    7.  Harga maksimal 25% di bawah High 52-Minggu (Dekat ATH).
    8.  **RS Rating:** Kekuatan relatif saham dibanding IHSG (Skala 1-99).
    """)

# --- 3. SIDEBAR ---
st.sidebar.title("⚙️ Control Panel")
st.sidebar.subheader("📝 Daftar Saham")
input_mode = st.sidebar.radio("Sumber Saham:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])

lq45_tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK", "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "GOTO.JK"]
kompas100_tickers = list(set(lq45_tickers + ["ITMG.JK", "TINS.JK", "ENRG.JK", "INDY.JK", "BREN.JK", "CUAN.JK", "AMMN.JK", "ADMR.JK", "TOWR.JK", "TBIG.JK", "BUKA.JK", "EMTK.JK", "SCMA.JK", "UNVR.JK", "GGRM.JK", "HMSP.JK", "MAPI.JK", "CTRA.JK", "BSDE.JK", "PWON.JK", "SMRA.JK", "ASRI.JK", "JSMR.JK", "PTPP.JK", "WIKA.JK", "ADHI.JK", "INKP.JK", "TKIM.JK", "ESSA.JK", "AUTO.JK", "GJTL.JK", "MAPA.JK", "ERAA.JK"]))

if input_mode == "LQ45 (Bluechip)": tickers = lq45_tickers
elif input_mode == "Kompas100 (Market Wide)": tickers = kompas100_tickers
else:
    user_input = st.sidebar.text_area("Kode Saham:", value="BREN, AMMN, CUAN, GOTO, BBRI")
    cleaned_input = [x.strip().upper() for x in user_input.split(',')]
    tickers = [f"{x}.JK" if not x.endswith(".JK") else x for x in cleaned_input if x]

st.sidebar.divider()
st.sidebar.subheader("💰 Money Management")
modal_juta = st.sidebar.number_input("Modal (Juta Rp)", value=100, step=10)
risk_per_trade_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0, step=0.5)
extended_multiplier = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5, step=0.1)

st.sidebar.divider()
min_trans = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
non_syariah_list = ["BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BDMN", "BNGA", "NISP", "GGRM", "HMSP", "WIIM", "RMBA", "MAYA", "NOBU", "ARTO"]

# --- 4. ENGINE SCANNER ---
@st.cache_data(ttl=300) 
def scan_market(ticker_list, min_val_m, risk_pct, modal_jt, risk_pct_trade, ext_mult):
    results = []
    selected_tickers = []
    text_progress = st.empty()
    bar_progress = st.progress(0)
    total = len(ticker_list)
    modal_rupiah = modal_jt * 1_000_000
    risk_money_rupiah = modal_rupiah * (risk_pct_trade / 100)

    # RS Calculation
    rs_scores = {}
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        for t in ticker_list:
            try:
                series = data_batch[t] if isinstance(data_batch, pd.DataFrame) else data_batch
                perf = (series.iloc[-1] - series.iloc[0]) / series.iloc[0]
                rs_scores[t] = perf
            except: rs_scores[t] = -999
        rs_df = pd.DataFrame(list(rs_scores.items()), columns=['Ticker', 'Perf'])
        rs_df['Rank'] = rs_df['Perf'].rank(pct=True) * 99
        rs_map = rs_df.set_index('Ticker')['Rank'].to_dict()
    except:
        rs_map = {t: 50 for t in ticker_list} 

    for i, ticker in enumerate(ticker_list):
        ticker_clean = ticker.replace(".JK", "")
        text_progress.text(f"Menganalisa {ticker_clean}... ({i+1}/{total})")
        
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period="2y")
            if df.empty or len(df) < 260: continue

            # Minervini Rules
            close = df['Close'].iloc[-1]
            ma50 = df['Close'].rolling(window=50).mean().iloc[-1]
            ma150 = df['Close'].rolling(window=150).mean().iloc[-1]
            ma200 = df['Close'].rolling(window=200).mean().iloc[-1]
            ma200_20ago = df['Close'].rolling(window=200).mean().iloc[-20]
            
            low_52w = df['Low'].tail(250).min()
            high_52w = df['High'].tail(250).max()
            rs_rating = int(rs_map.get(ticker, 50))

            # Rules
            c1 = close > ma150 and close > ma200
            c2 = ma150 > ma200
            c3 = ma200 > ma200_20ago
            c4 = ma50 > ma150 and ma50 > ma200
            c5 = close > ma50
            c6 = close >= (low_52w * 1.25)
            c7 = close >= (high_52w * 0.75) 
            c8 = rs_rating >= 60

            is_stage2 = c1 and c2 and c3 and c4 and c5 and c6 and c7 and c8
            
            # Logic
            status = "🔴 WAIT"
            priority = 5
            
            hl2 = (df['High'] + df['Low']) / 2
            red_line = ta.sma(hl2, 8).iloc[-1] 
            breakout_level = df['High'].rolling(window=20).max().shift(1).iloc[-1]
            
            avg_vol = (close * df['Volume'].mean()) / 1e9
            if avg_vol < min_val_m: continue
            
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1]
            is_spike = vol_ratio >= 2.0
            
            dist_to_red = ((close - red_line) / close) * 100
            is_extended = dist_to_red > 5.0

            if is_stage2:
                if close > red_line:
                    risk_mult = 1.0
                    if is_spike:
                        status = "🟣 VOL SPIKE"
                        priority = 1
                    elif close > breakout_level:
                        status = "🚀 BREAKOUT"
                        priority = 2
                    else:
                        status = "🟢 REVERSAL"
                        priority = 3
                    
                    if is_extended: risk_mult = ext_mult
                    
                    sl = int(red_line)
                    risk_share = close - sl
                    max_lot = 0
                    if risk_share > 0:
                        max_lot = int((risk_money_rupiah * risk_mult / risk_share) / 100)
                        if (max_lot * 100 * close) > modal_rupiah:
                            max_lot = int(modal_rupiah / close / 100)
                    
                    tp = int(close + (risk_share * 1.5))
                    label_syariah = "⛔ NON" if ticker_clean in non_syariah_list else "✅ SYARIAH"
                    display_stat = status + " (EXT)" if is_extended else status

                    results.append({
                        "Emiten": ticker_clean,
                        "RS": rs_rating, 
                        "Jenis": label_syariah,
                        "Status": display_stat,
                        "Buy": int(close),
                        "SL": sl,
                        "TP": tp,
                        "Max Lot": max_lot,
                        "Risk": f"{dist_to_red:.1f}%",
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker_clean}",
                        "Priority": priority
                    })
                    selected_tickers.append(ticker)

        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["Priority", "RS"], ascending=[True, False])
            
    return df_res, selected_tickers

# --- 5. TAMPILAN UTAMA ---
if st.button("🔍 SCAN MINERVINI TEMPLATE"):
    st.success("Memulai Analisa Trend Template (Stage 2) & VCP Logic...")
    with st.spinner('Checking 8 Rules & Volume Patterns...'):
        df, sel_tickers = scan_market(tickers, min_trans, risk_per_trade_pct, modal_juta, risk_per_trade_pct, extended_multiplier)
        
        if not df.empty:
            
            # --- BAGIAN VISUAL CHART (VCP PREVIEW FIX) ---
            st.markdown("### 🔍 VCP PATTERN PREVIEW (Top 4 Stocks)")
            st.caption("Grafik ini sudah dinormalisasi (%) untuk melihat pola kontraksi dengan jelas.")
            
            top_4 = sel_tickers[:4] # Ambil 4 teratas
            if top_4:
                cols = st.columns(4)
                for idx, t in enumerate(top_4):
                    if idx < 4:
                        with cols[idx]:
                            st.markdown(f"**{t.replace('.JK', '')}**")
                            try:
                                # Fix: Gunakan Ticker().history agar data lebih stabil
                                chart_data = yf.Ticker(t).history(period="6mo")['Close']
                                
                                if not chart_data.empty:
                                    # Fix: Normalisasi Data (Mulai dari 0%) agar grafik tidak gepeng
                                    chart_data = (chart_data / chart_data.iloc[0] - 1) * 100
                                    # Gunakan Area Chart agar lebih jelas
                                    st.area_chart(chart_data, height=120, color="#2962FF")
                                else:
                                    st.warning("Data Loading...")
                            except:
                                st.warning("Chart Error")
            
            st.divider()

            # --- TABEL HASIL ---
            st.subheader("📋 HASIL SCANNER LENGKAP")
            column_config = {
                "Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka"),
                "Buy": st.column_config.NumberColumn("Harga Buy", format="Rp %d"),
                "SL": st.column_config.NumberColumn("Stop Loss", format="Rp %d"),
                "TP": st.column_config.NumberColumn("Take Profit", format="Rp %d"),
                "Max Lot": st.column_config.NumberColumn("Max Lot", format="%d Lot"),
                "RS": st.column_config.ProgressColumn("RS Rating", min_value=0, max_value=99, format="%d"),
            }
            
            cols = ['Emiten', 'RS', 'Status', 'Buy', 'Max Lot', 'SL', 'TP', 'Risk', 'Chart']
            styled_df = (df[cols].style
                .set_properties(**{'text-align': 'center'}) 
                .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                .applymap(lambda x: 'background-color: #cce5ff; color: #004085; font-weight: bold;', subset=['Max Lot'])
                .applymap(lambda x: 'color: red; font-weight: bold;', subset=['SL'])
                .applymap(lambda x: 'color: #9C27B0; font-weight: bold;' if 'SPIKE' in str(x) else ('color: blue; font-weight: bold;' if 'BREAKOUT' in str(x) else 'color: green; font-weight: bold;'), subset=['Status'])
            )
            st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True)
        else:
            st.warning("Tidak ada saham yang lolos kriteria 'Minervini Stage 2' hari ini.")
