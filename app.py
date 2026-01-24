import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Adienov Trading System", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-top: 10px !important; }
        div[data-testid="stCaptionContainer"] { font-size: 0.8rem; }
        div.stButton > button { width: 100%; border-radius: 20px; background-color: #007BFF; color: white !important; font-weight: bold;}
        .dataframe { text-align: center !important; }
        th { text-align: center !important; }
        div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER & INPUT ---
st.title("📱 Adienov Pro: V9")
st.caption("Smart Money Detector • IHSG Barometer • Time Machine")

# --- BAROMETER IHSG ---
def get_ihsg_status():
    try:
        ihsg = yf.download("^JKSE", period="3mo", progress=False)
        if isinstance(ihsg.columns, pd.MultiIndex): ihsg = ihsg.xs("^JKSE", level=1, axis=1)
        
        current_price = ihsg['Close'].iloc[-1]
        prev_price = ihsg['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        ma20 = ihsg['Close'].rolling(window=20).mean().iloc[-1]
        
        if current_price > ma20:
            return current_price, change_pct, "🟢 BULLISH", "Market Aman.", "normal"
        else:
            return current_price, change_pct, "🔴 BEARISH", "Hati-hati!", "inverse"
    except:
        return 0, 0, "OFFLINE", "No Data", "off"

ihsg_price, ihsg_chg, ihsg_stat, ihsg_advice, ihsg_col = get_ihsg_status()
c1, c2 = st.columns([1, 2])
with c1: st.metric("IHSG", f"{ihsg_price:.0f}", f"{ihsg_chg:.2f}%", delta_color=ihsg_col)
with c2: st.info(f"**{ihsg_stat}** | {ihsg_advice}")

st.divider()
st.info("⚙️ **SETTING:** Klik panah **( > )** di kiri atas.")

with st.sidebar:
    st.header("⚙️ Filter & Waktu")
    backtest_days = st.slider("⏳ Backtest", 0, 30, 0)
    st.divider()
    min_trans = st.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
    risk_tol = st.slider("Toleransi Trend (%)", 1.0, 10.0, 5.0)
    turtle_day = st.slider("Periode Breakout (Hari)", 10, 50, 20)
    rr_ratio = st.number_input("Rasio Risk:Reward", value=1.5, step=0.1)

# --- 3. DATABASE SAHAM ---
tickers = [
    "ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK",
    "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK",
    "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK",
    "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"
]
non_syariah_list = ["BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BDMN", "BNGA", "NISP", "GGRM", "HMSP", "WIIM", "RMBA", "MAYA", "NOBU", "ARTO"]

# --- 4. FUNGSI SCANNER ---
@st.cache_data(ttl=60)
def scan_market(min_val_m, risk_pct, turtle_window, reward_ratio, days_back):
    results = []
    text_progress = st.empty()
    bar_progress = st.progress(0)
    
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        ticker_clean = ticker.replace(".JK", "")
        text_progress.text(f"Analisa {ticker_clean}... ({i+1}/{total})")
        
        try:
            df_full = yf.download(ticker, period="6mo", progress=False)
            if df_full.empty or len(df_full) < (turtle_window + 25 + days_back): continue
            try:
                if isinstance(df_full.columns, pd.MultiIndex): df_full = df_full.xs(ticker, level=1, axis=1)
            except: pass

            real_current_price = float(df_full['Close'].iloc[-1])
            if days_back > 0:
                df = df_full.iloc[:-days_back].copy()
            else:
                df = df_full.copy()

            # Indikator
            df['HL2'] = (df['High'] + df['Low']) / 2
            df['Teeth_Raw'] = df.ta.sma(close='HL2', length=8)
            signal_close = float(df['Close'].iloc[-1])
            red_line = float(df['Teeth_Raw'].iloc[-6]) if not pd.isna(df['Teeth_Raw'].iloc[-6]) else 0
            
            # Breakout
            high_rolling = df['High'].rolling(window=turtle_window).max().shift(1)
            breakout_level = float(high_rolling.iloc[-1])

            # --- ANALISA VOLUME SPIKE (Smart Money) ---
            curr_vol = df['Volume'].iloc[-1]
            avg_vol_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
            vol_ratio = curr_vol / avg_vol_20 if avg_vol_20 > 0 else 0
            
            vol_status = "NORMAL"
            if vol_ratio >= 2.0:
                vol_status = "🔥 SPIKE" # Volume 2x Rata-rata
            elif vol_ratio >= 1.5:
                vol_status = "⚡ HIGH" # Volume 1.5x Rata-rata

            # Filter Value Transaksi
            avg_val = (signal_close * df['Volume'].mean()) / 1000000000 
            if avg_val < min_val_m: continue

            # Status Trend
            status = ""
            priority = 0
            if signal_close > breakout_level:
                status = "🚀 BREAKOUT"
                priority = 1
                diff = ((signal_close - breakout_level) / breakout_level) * 100
            elif signal_close > red_line:
                diff_alli = ((signal_close - red_line) / signal_close) * 100
                if diff_alli <= risk_pct:
                    status = "🟢 EARLY TREND"
                    priority = 2
                    diff = diff_alli
                else:
                    status = "⚠️ EXTENDED"
                    priority = 3
                    diff = diff_alli
            else:
                status = "🔴 DOWN"
                priority = 4
                diff = 0

            # Backtest Result
            performance_label = "⏳ WAIT"
            perf_val = 0
            if days_back > 0 and "DOWN" not in status:
                change_pct = ((real_current_price - signal_close) / signal_close) * 100
                perf_val = change_pct
                performance_label = f"✅ WIN +{change_pct:.1f}%" if change_pct > 0 else f"❌ LOSS {change_pct:.1f}%"
            elif days_back == 0:
                performance_label = "🆕 LIVE"

            label_syariah = "⛔ NON" if ticker_clean in non_syariah_list else "✅ SYARIAH"
            stop_loss = int(red_line)
            take_profit = int(signal_close + ((signal_close - stop_loss) * reward_ratio))
            
            results.append({
                "Emiten": ticker_clean,
                "Jenis": label_syariah,
                "Status": status,
                "Vol Spike": vol_status, # Kolom Baru
                "Vol Ratio": vol_ratio, # Untuk Sorting
                "Buy": int(signal_close),
                "Hasil": performance_label,
                "SL": stop_loss,
                "TP": take_profit,
                "Risk%": round(diff, 1),
                "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker_clean}",
                "Priority": priority,
                "PerfVal": perf_val
            })

        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        # Sortir: Prioritas -> Volume Spike Tertinggi -> Risk Terkecil
        if days_back == 0:
            df_res = df_res.sort_values(by=["Priority", "Vol Ratio", "Risk%"], ascending=[True, False, True])
        else:
            df_res = df_res.sort_values(by=["PerfVal"], ascending=False)
            
    return df_res

# --- 5. TAMPILAN UTAMA ---
btn_label = "🔍 SCAN HARI INI" if st.session_state.get('days_back', 0) == 0 else f"⏮️ CEK {st.session_state.get('days_back', 0)} HARI LALU"
if st.button(f"RUN SCANNER ({'HARI INI' if backtest_days==0 else f'MUNDUR {backtest_days} HARI'})"):
    
    tgl_skrg = datetime.now(pytz.timezone('Asia/Jakarta'))
    tgl_sinyal = tgl_skrg - timedelta(days=backtest_days)
    
    if backtest_days > 0: st.warning(f"🕒 **BACKTEST:** Cek sinyal tgl **{tgl_sinyal.strftime('%d %B %Y')}**")
    else: st.success(f"📅 **LIVE:** Data Pasar **{tgl_skrg.strftime('%d %B %Y')}**")

    with st.spinner('Menjalankan scanner...'):
        df = scan_market(min_trans, risk_tol, turtle_day, rr_ratio, backtest_days)
        
        if not df.empty:
            column_config = {
                "Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka"),
                "Buy": st.column_config.NumberColumn("Buy", format="Rp %d"),
                "SL": st.column_config.NumberColumn("SL", format="Rp %d"),
                "TP": st.column_config.NumberColumn("TP", format="Rp %d"),
                "Risk%": st.column_config.NumberColumn("Jarak", format="%.1f %%"),
            }

            df_buy = df[df['Status'].str.contains("BREAKOUT|EARLY")]
            
            if not df_buy.empty:
                st.subheader("📊 HASIL ANALISA")
                
                styled_df = (df_buy.drop(columns=['Priority', 'PerfVal', 'Vol Ratio']).style
                    .format({"Buy": "{:.0f}", "SL": "{:.0f}", "TP": "{:.0f}", "Risk%": "{:.1f}"})
                    .set_properties(**{'text-align': 'center'}) 
                    .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                    .background_gradient(subset=['Risk%'], cmap="Greens")
                    .applymap(lambda x: 'color: red; font-weight: bold;', subset=['SL'])
                    # Warna Volume Spike
                    .applymap(lambda x: 'background-color: #ffcccc; color: red; font-weight: bold;' if 'SPIKE' in str(x) else ('background-color: #fff3cd; color: orange; font-weight: bold;' if 'HIGH' in str(x) else ''), subset=['Vol Spike'])
                )
                st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True)
            else: st.info("Tidak ada sinyal Buy.")
        else: st.error("Data tidak ditemukan.")
