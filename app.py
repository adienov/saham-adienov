import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V19", layout="wide", initial_sidebar_state="expanded")

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
        .streamlit-expanderHeader { font-weight: bold; color: #007BFF; background-color: #e9ecef; border-radius: 5px; }
        div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER ---
st.title("📱 Noris Trading System V19")
st.caption("Visual Evidence: Performance Chart • System vs IHSG • Transparency")

# --- BAROMETER IHSG (LIVE) ---
def get_ihsg_status():
    try:
        ihsg = yf.download("^JKSE", period="3mo", progress=False)
        if isinstance(ihsg.columns, pd.MultiIndex): ihsg = ihsg.xs("^JKSE", level=1, axis=1)
        current_price = ihsg['Close'].iloc[-1]
        ma20 = ihsg['Close'].rolling(window=20).mean().iloc[-1]
        if current_price > ma20: return "🟢 BULLISH", "Market Aman. Gaspol!", "normal"
        else: return "🔴 BEARISH", "Kurangi Lot. Cash is King.", "inverse"
    except: return "OFFLINE", "No Data", "off"

ihsg_stat, ihsg_advice, ihsg_col = get_ihsg_status()
st.info(f"**STATUS IHSG:** {ihsg_stat} | {ihsg_advice}")

# --- FUNGSI CHART HISTORY (V19) ---
def get_performance_history(tickers_list, days_back):
    # 1. Ambil data IHSG
    try:
        ihsg = yf.download("^JKSE", period="3mo", progress=False)
        if isinstance(ihsg.columns, pd.MultiIndex): ihsg = ihsg.xs("^JKSE", level=1, axis=1)
        # Potong data sesuai hari backtest
        ihsg_cut = ihsg['Close'].iloc[-(days_back+1):]
        # Normalisasi ke Persentase (Mulai dari 0%)
        ihsg_pct = (ihsg_cut / ihsg_cut.iloc[0] - 1) * 100
        ihsg_pct.name = "IHSG (Benchmark)"
    except:
        return None

    # 2. Ambil data Saham Pilihan System
    if not tickers_list:
        return None
        
    try:
        # Download batch untuk mempercepat
        data = yf.download(tickers_list, period="3mo", progress=False)['Close']
        data_cut = data.iloc[-(days_back+1):]
        
        # Hitung Rata-rata Portfolio (Equal Weight)
        # Normalisasi setiap saham dulu, baru dirata-rata
        normalized_stocks = (data_cut / data_cut.iloc[0] - 1) * 100
        system_curve = normalized_stocks.mean(axis=1)
        system_curve.name = "NORIS SYSTEM"
        
        # Gabungkan
        chart_df = pd.concat([system_curve, ihsg_pct], axis=1).dropna()
        return chart_df
    except:
        return None

# --- EXPANDER KAMUS ---
with st.expander("📖 KAMUS & CARA BACA (Klik Disini)"):
    st.markdown("""
    ### 1. 📈 Grafik Crossing
    * **Garis Hijau (Noris):** Kinerja saham-saham pilihan robot.
    * **Garis Merah (IHSG):** Kinerja pasar rata-rata.
    * **Alpha Cross:** Saat garis Hijau menyalip garis Merah ke atas.
    
    ### 2. 🚦 Sinyal Noris
    * **🚀 BREAKOUT:** Harga jebol atap tertinggi 20 hari.
    * **🔥 FOLLOW UP:** Harga jebol High Candle Kemarin.
    """)

# --- 3. SIDEBAR (INPUT) ---
st.sidebar.title("⚙️ Noris Control Panel")

st.sidebar.subheader("💰 Money Management")
modal_juta = st.sidebar.number_input("Modal Trading (Juta Rp)", value=100, step=10)
risk_per_trade_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0, step=0.5)

st.sidebar.divider()
st.sidebar.subheader("🔍 Filter Saham")
backtest_days = st.sidebar.slider("⏳ Mundur Hari (Backtest)", 0, 30, 0)
min_trans = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
risk_tol = st.sidebar.slider("Toleransi Trend (%)", 1.0, 10.0, 5.0)
min_volatility = st.sidebar.slider("Min. Volatilitas/Speed (%)", 0.0, 5.0, 0.0, step=0.5)

# --- DATABASE SAHAM ---
tickers = [
    "ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK",
    "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK",
    "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK",
    "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"
]
non_syariah_list = ["BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BDMN", "BNGA", "NISP", "GGRM", "HMSP", "WIIM", "RMBA", "MAYA", "NOBU", "ARTO"]

# --- 4. ENGINE SCANNER ---
@st.cache_data(ttl=60)
def scan_market(min_val_m, risk_pct, days_back, modal_jt, risk_pct_trade, min_vol_pct):
    results = []
    selected_tickers = [] # Simpan ticker untuk chart
    
    text_progress = st.empty()
    bar_progress = st.progress(0)
    
    total = len(tickers)
    modal_rupiah = modal_jt * 1_000_000
    risk_money_rupiah = modal_rupiah * (risk_pct_trade / 100)

    for i, ticker in enumerate(tickers):
        ticker_clean = ticker.replace(".JK", "")
        text_progress.text(f"Scanning {ticker_clean}... ({i+1}/{total})")
        
        try:
            df_full = yf.download(ticker, period="6mo", progress=False)
            if df_full.empty or len(df_full) < (30 + days_back): continue
            try:
                if isinstance(df_full.columns, pd.MultiIndex): df_full = df_full.xs(ticker, level=1, axis=1)
            except: pass

            if days_back > 0:
                df = df_full.iloc[:-days_back].copy()
            else:
                df = df_full.copy()

            signal_close = float(df['Close'].iloc[-1])
            prev_high = float(df['High'].iloc[-2])
            
            # Filter Volatilitas
            df['ATR'] = df.ta.atr(length=14)
            current_atr = df['ATR'].iloc[-1]
            atr_pct = (current_atr / signal_close) * 100
            if atr_pct < min_vol_pct: continue
            
            vol_label = "NORMAL"
            if atr_pct > 3.0: vol_label = "⚡ HIGH"

            # Indikator Trend
            df['HL2'] = (df['High'] + df['Low']) / 2
            df['Teeth_Raw'] = df.ta.sma(close='HL2', length=8)
            red_line = float(df['Teeth_Raw'].iloc[-6]) if not pd.isna(df['Teeth_Raw'].iloc[-6]) else 0
            
            high_rolling = df['High'].rolling(window=20).max().shift(1)
            breakout_level = float(high_rolling.iloc[-1])

            avg_val = (signal_close * df['Volume'].mean()) / 1000000000 
            if avg_val < min_val_m: continue
            
            curr_vol = df['Volume'].iloc[-1]
            avg_vol_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
            vol_ratio = curr_vol / avg_vol_20 if avg_vol_20 > 0 else 0
            vol_spike_status = "NORMAL"
            if vol_ratio >= 2.0: vol_spike_status = "🔥 SPIKE"

            # Logika Sinyal
            status = ""
            priority = 0
            if signal_close > breakout_level:
                status = "🚀 BREAKOUT"
                priority = 1
                diff = ((signal_close - breakout_level) / breakout_level) * 100
            elif signal_close > prev_high and signal_close > red_line:
                status = "🔥 FOLLOW UP"
                priority = 2
                diff = ((signal_close - prev_high) / prev_high) * 100
                diff_alli = ((signal_close - red_line) / signal_close) * 100
                if diff_alli > risk_pct:
                    status = "⚠️ EXTENDED"
                    priority = 3
            else:
                status = "🔴 WAIT"
                priority = 4
                diff = 0

            # Hitung Hasil (Backtest)
            performance_label = "⏳ WAIT"
            perf_val = 0
            if days_back > 0 and "WAIT" not in status:
                real_current_price = float(df_full['Close'].iloc[-1])
                change_pct = ((real_current_price - signal_close) / signal_close) * 100
                perf_val = change_pct
                if change_pct > 0: performance_label = f"✅ +{change_pct:.1f}%"
                else: performance_label = f"🔻 {change_pct:.1f}%"
                
                # Simpan ticker ini untuk chart
                if "EXTENDED" not in status:
                     selected_tickers.append(ticker)

            elif days_back == 0:
                performance_label = "🆕 LIVE"

            label_syariah = "⛔ NON" if ticker_clean in non_syariah_list else "✅ SYARIAH"
            stop_loss = int(red_line)
            risk_per_share = signal_close - stop_loss
            
            max_lot = 0
            if risk_per_share > 0:
                calc_lot = (risk_money_rupiah / risk_per_share) / 100
                max_lot = int(calc_lot)
                total_buy_val = max_lot * 100 * signal_close
                if total_buy_val > modal_rupiah:
                    max_lot = int((modal_rupiah / signal_close) / 100)
            
            take_profit = int(signal_close + (risk_per_share * 1.5))
            
            results.append({
                "Emiten": ticker_clean,
                "Jenis": label_syariah,
                "Status": status,
                "Speed": f"{atr_pct:.1f}%",
                "Vol Spike": vol_spike_status,
                "Buy": int(signal_close),
                "Hasil": performance_label,
                "Max Lot": max_lot,
                "SL": stop_loss,
                "TP": take_profit,
                "Risk%": round(diff, 1),
                "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker_clean}",
                "Priority": priority,
                "PerfVal": perf_val,
                "VolRatio": vol_ratio
            })

        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        # Sortir Berdasarkan Profit Terbesar (Untuk Transparansi Backtest)
        if days_back > 0:
            df_res = df_res.sort_values(by=["PerfVal"], ascending=False)
        else:
            df_res = df_res.sort_values(by=["Priority", "VolRatio"], ascending=[True, False])
            
    return df_res, selected_tickers

# --- 5. TAMPILAN UTAMA ---
btn_txt = "🔍 SCAN NORIS SYSTEM" if st.session_state.get('days_back', 0) == 0 else f"⏮️ CEK MASA LALU ({st.session_state.get('days_back', 0)} HARI)"
if st.button(btn_txt):
    
    tgl_skrg = datetime.now(pytz.timezone('Asia/Jakarta'))
    tgl_sinyal = tgl_skrg - timedelta(days=backtest_days)
    
    if backtest_days > 0: st.warning(f"🕒 **BACKTEST:** {tgl_sinyal.strftime('%d %B %Y')}")
    else: st.success(f"📅 **LIVE:** {tgl_skrg.strftime('%d %B %Y')}")

    with st.spinner('Menganalisa Kinerja & Pasar...'):
        df, sel_tickers = scan_market(min_trans, risk_tol, backtest_days, modal_juta, risk_per_trade_pct, min_volatility)
        
        if not df.empty:
            df_buy = df[df['Status'].str.contains("BREAKOUT|FOLLOW")]
            
            if backtest_days > 0 and not df_buy.empty:
                # --- VISUALISASI CHART (GRAFIK BALAPAN) ---
                st.subheader("📈 GRAFIK PERFORMA: SYSTEM VS IHSG")
                chart_df = get_performance_history(sel_tickers, backtest_days)
                
                if chart_df is not None:
                    # Plot Chart dengan Warna Custom
                    st.line_chart(chart_df, color=["#00FF00", "#FF0000"]) 
                    st.caption("🟢 Garis Hijau: Noris System | 🔴 Garis Merah: IHSG (Market)")

                # --- RAPOR KINERJA DETAIL ---
                st.subheader("🥊 DETAIL STATISTIK")
                
                avg_sys_return = df_buy['PerfVal'].mean()
                chart_ihsg = get_performance_history(["BBCA.JK"], backtest_days) # Dummy call for IHSG Value
                ihsg_ret = chart_df['IHSG (Benchmark)'].iloc[-1] if chart_df is not None else 0
                alpha = avg_sys_return - ihsg_ret
                
                # Hitung Win Rate
                winners = df_buy[df_buy['PerfVal'] > 0]
                win_rate = (len(winners) / len(df_buy)) * 100
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Kinerja System", f"{avg_sys_return:.2f}%", f"{len(df_buy)} Saham")
                c2.metric("Kinerja IHSG", f"{ihsg_ret:.2f}%", "Benchmark")
                c3.metric("Win Rate", f"{win_rate:.0f}%", f"{len(winners)} Win")
                alpha_label = "MENGALAHKAN PASAR 🔥" if alpha > 0 else "KALAH ⚠️"
                c4.metric("ALPHA", f"{alpha:.2f}%", alpha_label)
                
                st.markdown("---")
            
            # --- TABEL HASIL ---
            if not df_buy.empty:
                df_buy = df_buy.reset_index(drop=True)
                df_buy.insert(0, 'No', range(1, 1 + len(df_buy)))
                
                st.subheader("📋 DAFTAR SAHAM (Diurutkan dari Profit Tertinggi)")
                
                column_config = {
                    "Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka"),
                    "Buy": st.column_config.NumberColumn("Buy", format="Rp %d"),
                    "SL": st.column_config.NumberColumn("SL", format="Rp %d"),
                    "TP": st.column_config.NumberColumn("TP", format="Rp %d"),
                    "Max Lot": st.column_config.NumberColumn("Max Lot", format="%d Lot"),
                    "Risk%": st.column_config.NumberColumn("Jarak", format="%.1f %%"),
                    "Speed": st.column_config.TextColumn("Speed", help="0-5%. Makin tinggi makin liar."),
                }
                
                styled_df = (df_buy.drop(columns=['Priority', 'PerfVal', 'VolRatio']).style
                    .format({"Buy": "{:.0f}", "SL": "{:.0f}", "TP": "{:.0f}", "Risk%": "{:.1f}"})
                    .set_properties(**{'text-align': 'center'}) 
                    .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                    .background_gradient(subset=['Risk%'], cmap="Greens")
                    .applymap(lambda x: 'color: red; font-weight: bold;', subset=['SL'])
                    .applymap(lambda x: 'background-color: #ffcccc; color: red; font-weight: bold;' if 'SPIKE' in str(x) else '', subset=['Vol Spike'])
                    .applymap(lambda x: 'background-color: #d4edda; color: green; font-weight: bold;' if '+' in str(x) else ('background-color: #f8d7da; color: red; font-weight: bold;' if '🔻' in str(x) else ''), subset=['Hasil'])
                    .applymap(lambda x: 'background-color: #cce5ff; color: #004085; font-weight: bold;', subset=['Max Lot'])
                )
                st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True)
            else: st.info(f"Tidak ada sinyal Buy.")
        else: st.error("Data tidak ditemukan.")
