import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import pytz
import io

# --- 1. SETTING HALAMAN & SESSION STATE ---
st.set_page_config(page_title="Noris Trading System V28", layout="wide", initial_sidebar_state="expanded")

# Inisialisasi Session State untuk Menyimpan Portfolio Sementara
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame(columns=['Tanggal', 'Emiten', 'Harga Beli', 'Lot', 'Investasi'])

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
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER ---
st.title("📱 Noris Trading System V28")
st.caption("Portfolio Manager: Scan -> Save -> Track Real Performance")

# --- BAROMETER IHSG ---
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

# --- 3. SIDEBAR (INPUT) ---
st.sidebar.title("⚙️ Noris Control Panel")

st.sidebar.subheader("📂 Manajemen Data")
uploaded_file = st.sidebar.file_uploader("Upload Portfolio Lama (CSV)", type="csv")
if uploaded_file is not None:
    try:
        df_uploaded = pd.read_csv(uploaded_file)
        st.session_state['portfolio'] = df_uploaded
        st.sidebar.success("Portfolio Berhasil Diload!")
    except:
        st.sidebar.error("File CSV rusak.")

st.sidebar.divider()
st.sidebar.subheader("📝 Daftar Saham")
input_mode = st.sidebar.radio("Pilih Sumber Saham:", ["Default (Bluechip LQ45)", "Input Manual"])

default_tickers = [
    "ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK",
    "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK",
    "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK",
    "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"
]

if input_mode == "Default (Bluechip LQ45)":
    tickers = default_tickers
else:
    user_input = st.sidebar.text_area("Kode Saham (Pisahkan koma):", value="BREN, AMMN, CUAN, GOTO, BBRI")
    cleaned_input = [x.strip().upper() for x in user_input.split(',')]
    tickers = [f"{x}.JK" if not x.endswith(".JK") else x for x in cleaned_input if x]

st.sidebar.divider()
st.sidebar.subheader("💰 Money Management")
modal_juta = st.sidebar.number_input("Modal Trading (Juta Rp)", value=100, step=10)
risk_per_trade_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0, step=0.5)

st.sidebar.divider()
st.sidebar.subheader("🔍 Filter Saham")
backtest_days = st.sidebar.slider("⏳ Mundur Hari (Scanner)", 0, 90, 0)
min_trans = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
risk_tol = st.sidebar.slider("Toleransi Trend (%)", 1.0, 10.0, 5.0)
min_volatility = st.sidebar.slider("Min. Volatilitas/Speed (%)", 0.0, 5.0, 0.0, step=0.5)
non_syariah_list = ["BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BDMN", "BNGA", "NISP", "GGRM", "HMSP", "WIIM", "RMBA", "MAYA", "NOBU", "ARTO"]

# --- 4. ENGINE SCANNER ---
@st.cache_data(ttl=60) 
def scan_market(ticker_list, min_val_m, risk_pct, days_back, modal_jt, risk_pct_trade, min_vol_pct):
    results = []
    total = len(ticker_list)
    modal_rupiah = modal_jt * 1_000_000
    risk_money_rupiah = modal_rupiah * (risk_pct_trade / 100)
    
    text_progress = st.empty()
    bar_progress = st.progress(0)

    for i, ticker in enumerate(ticker_list):
        ticker_clean = ticker.replace(".JK", "")
        text_progress.text(f"Scanning {ticker_clean}... ({i+1}/{total})")
        
        try:
            ticker_obj = yf.Ticker(ticker)
            df_full = ticker_obj.history(period="1y")
            
            if df_full.empty or len(df_full) < (30 + days_back): continue
            
            if days_back > 0: df = df_full.iloc[:-days_back].copy()
            else: df = df_full.copy()

            signal_close = float(df['Close'].iloc[-1])
            prev_high = float(df['High'].iloc[-2])
            
            # Volatility
            df['ATR'] = df.ta.atr(length=14)
            current_atr = df['ATR'].iloc[-1]
            atr_pct = (current_atr / signal_close) * 100
            if atr_pct < min_vol_pct: continue
            
            vol_label = "NORMAL"
            if atr_pct > 3.0: vol_label = "⚡ HIGH"

            # Indicators
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
            elif signal_close > red_line:
                status = "🟢 EARLY TREND"
                priority = 3
                diff = ((signal_close - red_line) / signal_close) * 100
                if diff > risk_tol: status = "⚠️ EXTENDED"; priority = 4
            else:
                status = "🔴 WAIT"
                priority = 5
                diff = 0

            # Backtest/Live
            performance_label = "⏳ WAIT"
            if days_back == 0: performance_label = "🆕 LIVE"
            else:
                # Simple backtest calc
                real_current_price = float(df_full['Close'].iloc[-1])
                change = ((real_current_price - signal_close)/signal_close)*100
                performance_label = f"{change:.1f}%"

            label_syariah = "⛔ NON" if ticker_clean in non_syariah_list else "✅ SYARIAH"
            stop_loss = int(red_line)
            risk_per_share = signal_close - stop_loss
            
            max_lot = 0
            if risk_per_share > 0:
                calc_lot = (risk_money_rupiah / risk_per_share) / 100
                max_lot = int(calc_lot)
                total_buy_val = max_lot * 100 * signal_close
                if total_buy_val > modal_rupiah: max_lot = int((modal_rupiah / signal_close) / 100)
            
            take_profit = int(signal_close + (risk_per_share * 1.5))
            
            results.append({
                "Emiten": ticker_clean,
                "Jenis": label_syariah,
                "Status": status,
                "Buy": int(signal_close),
                "Hasil": performance_label,
                "Max Lot": max_lot,
                "SL": stop_loss,
                "TP": take_profit,
                "Risk%": round(diff, 1),
                "Priority": priority,
                "VolRatio": vol_ratio,
                "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker_clean}",
            })

        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["Priority", "VolRatio"], ascending=[True, False])
            
    return df_res

# --- 5. TAMPILAN UTAMA (TABS) ---
tab1, tab2 = st.tabs(["📡 SCANNER (Market Hunter)", "💼 PORTOFOLIO SAYA (Forward Test)"])

with tab1:
    btn_txt = "🔍 SCAN NORIS SYSTEM" if st.session_state.get('days_back', 0) == 0 else f"⏮️ CEK MASA LALU ({st.session_state.get('days_back', 0)} HARI)"
    
    if st.button(btn_txt, key="scan_btn"):
        tgl_skrg = datetime.now(pytz.timezone('Asia/Jakarta'))
        tgl_sinyal = tgl_skrg - timedelta(days=backtest_days)
        
        if backtest_days > 0: st.warning(f"🕒 **BACKTEST:** {tgl_sinyal.strftime('%d %B %Y')}")
        else: st.success(f"📅 **LIVE:** {tgl_skrg.strftime('%d %B %Y')}")

        with st.spinner('Menganalisa Pasar...'):
            df = scan_market(tickers, min_trans, risk_tol, backtest_days, modal_juta, risk_per_trade_pct, min_volatility)
            
            if not df.empty:
                df_buy = df[df['Status'].str.contains("BREAKOUT|FOLLOW|EARLY")]
                
                if not df_buy.empty:
                    # Simpan hasil scan terakhir ke session state agar bisa di-add ke portfolio
                    st.session_state['last_scan_result'] = df_buy
                    
                    st.subheader("🔥 REKOMENDASI SAHAM HARI INI")
                    
                    column_config = {
                        "Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka"),
                        "Buy": st.column_config.NumberColumn("Harga Buy", format="Rp %d"),
                        "SL": st.column_config.NumberColumn("Stop Loss", format="Rp %d"),
                        "TP": st.column_config.NumberColumn("Take Profit", format="Rp %d"),
                        "Max Lot": st.column_config.NumberColumn("Max Lot", format="%d Lot"),
                        "Risk%": st.column_config.NumberColumn("Risk", format="%.1f %%"),
                    }
                    
                    cols_to_show = ['Emiten', 'Status', 'Buy', 'Max Lot', 'SL', 'TP', 'Risk%', 'Chart']
                    final_df = df_buy[cols_to_show].reset_index(drop=True)
                    final_df.insert(0, 'No', range(1, 1 + len(final_df)))

                    styled_df = (final_df.style
                        .set_properties(**{'text-align': 'center'}) 
                        .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                        .applymap(lambda x: 'background-color: #cce5ff; color: #004085; font-weight: bold;', subset=['Max Lot'])
                        .applymap(lambda x: 'color: red; font-weight: bold;', subset=['SL'])
                    )

                    st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True)
                    
                    # TOMBOL SIMPAN
                    st.divider()
                    c1, c2 = st.columns([3,1])
                    with c2:
                        if st.button("📥 SIMPAN HASIL SCAN KE PORTOFOLIO", type="primary"):
                            # Tambahkan data ke Portfolio Session
                            tgl_str = tgl_sinyal.strftime('%Y-%m-%d')
                            for index, row in df_buy.iterrows():
                                new_row = {
                                    'Tanggal': tgl_str,
                                    'Emiten': row['Emiten'],
                                    'Harga Beli': row['Buy'],
                                    'Lot': row['Max Lot'],
                                    'Investasi': row['Buy'] * row['Max Lot'] * 100
                                }
                                # Cek duplikasi hari ini
                                existing = st.session_state['portfolio'][
                                    (st.session_state['portfolio']['Emiten'] == row['Emiten']) & 
                                    (st.session_state['portfolio']['Tanggal'] == tgl_str)
                                ]
                                if existing.empty:
                                    st.session_state['portfolio'] = pd.concat([st.session_state['portfolio'], pd.DataFrame([new_row])], ignore_index=True)
                            
                            st.success("✅ Saham berhasil disimpan ke Tab Portofolio!")
                else: st.info(f"Tidak ada sinyal Buy.")
            else: st.error("Data tidak ditemukan.")

with tab2:
    st.header("💼 Portofolio & Forward Test")
    st.caption("Pantau kinerja saham yang sudah Bapak simpan sebelumnya.")
    
    if st.session_state['portfolio'].empty:
        st.info("Portofolio masih kosong. Silakan lakukan SCAN dulu, lalu klik tombol 'SIMPAN' di bawah tabel hasil.")
    else:
        # Tampilkan Tabel Portfolio
        portfolio_df = st.session_state['portfolio'].copy()
        
        # Cek Harga Terkini (Live)
        current_prices = []
        profits = []
        profit_pcts = []
        
        with st.spinner("Mengupdate Harga Terkini..."):
            ticker_list_port = [f"{x}.JK" for x in portfolio_df['Emiten'].unique()]
            if ticker_list_port:
                try:
                    live_data = yf.download(ticker_list_port, period="1d", progress=False)['Close']
                    # Handle jika cuma 1 saham (Series)
                    if isinstance(live_data, pd.Series) or isinstance(live_data, float):
                        # Re-download if format is weird, or handle single ticker logic
                         current_val = live_data.iloc[-1] if hasattr(live_data, 'iloc') else live_data
                         # Mapping manual for single ticker is tricky with download batch returning series
                         # Fallback looping safer for small portfolio
                         pass
                except: pass

            for index, row in portfolio_df.iterrows():
                try:
                    tick_obj = yf.Ticker(f"{row['Emiten']}.JK")
                    curr_price = tick_obj.history(period='1d')['Close'].iloc[-1]
                    
                    gain = (curr_price - row['Harga Beli']) * row['Lot'] * 100
                    gain_pct = ((curr_price - row['Harga Beli']) / row['Harga Beli']) * 100
                    
                    current_prices.append(int(curr_price))
                    profits.append(int(gain))
                    profit_pcts.append(round(gain_pct, 2))
                except:
                    current_prices.append(0)
                    profits.append(0)
                    profit_pcts.append(0.0)
        
        portfolio_df['Harga Kini'] = current_prices
        portfolio_df['Profit (Rp)'] = profits
        portfolio_df['Profit (%)'] = profit_pcts
        
        # Coloring function
        def color_profit(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}; font-weight: bold;'

        # Tampilkan Tabel
        st.dataframe(
            portfolio_df.style.applymap(color_profit, subset=['Profit (%)', 'Profit (Rp)'])
            .format({"Harga Beli": "Rp {:,.0f}", "Harga Kini": "Rp {:,.0f}", "Investasi": "Rp {:,.0f}", "Profit (Rp)": "Rp {:,.0f}", "Profit (%)": "{:,.2f}%"}),
            use_container_width=True
        )
        
        # TOTAL SUMMARY
        total_inv = portfolio_df['Investasi'].sum()
        total_profit = portfolio_df['Profit (Rp)'].sum()
        total_perf = (total_profit / total_inv * 100) if total_inv > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Investasi", f"Rp {total_inv:,.0f}")
        m2.metric("Total Profit/Loss", f"Rp {total_profit:,.0f}", delta_color="normal")
        m3.metric("Kinerja Portofolio", f"{total_perf:.2f}%", "Hijau = Bagus" if total_perf > 0 else "Merah = Rugi")
        
        st.divider()
        st.subheader("💾 Backup Data (PENTING!)")
        st.caption("Karena ini Web App, data akan hilang jika direfresh. Download file CSV ini untuk menyimpan data portofolio Bapak.")
        
        csv = portfolio_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Portfolio ke Excel/CSV",
            data=csv,
            file_name='noris_portfolio.csv',
            mime='text/csv',
        )
