import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V62", layout="wide", initial_sidebar_state="expanded")

# --- 2. HEADER DENGAN IKON CHART HH-HL ---
st.title("📈 Noris Trading System V62") 
st.caption("Backtest Engine: Validate Minervini Strategy on Historical Data")

# --- 3. GLOBAL MARKET DASHBOARD (OTOMATIS TAMPIL) ---
def display_global_indices():
    st.markdown("### 🌎 GLOBAL MARKET MONITOR")
    indices = {"IHSG (JKSE)": "^JKSE", "S&P 500 (US)": "^GSPC", "Nasdaq (US)": "^IXIC", "Dow Jones": "^DJI"}
    cols = st.columns(len(indices))
    for i, (name, symbol) in enumerate(indices.items()):
        try:
            data = yf.Ticker(symbol).history(period="6mo")
            if not data.empty:
                curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                ma20 = data['Close'].rolling(20).mean().iloc[-1]
                status_txt = "🟢 BULLISH" if curr > ma20 else "🔴 BEARISH"
                with cols[i]:
                    st.markdown(f"**{name}**")
                    st.metric(status_txt, f"{curr:,.0f}", f"{pct:+.2f}%")
                    norm_chart = (data['Close'] / data['Close'].iloc[0] - 1) * 100
                    st.area_chart(norm_chart.tail(60), height=100, color="#2962FF")
        except: cols[i].error(f"Error {name}")
    st.divider()

display_global_indices()

# --- 4. SIDEBAR PARAMETER ---
st.sidebar.title("⚙️ Parameter")
input_mode = st.sidebar.radio("Sumber Saham:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])
min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
modal_jt = st.sidebar.number_input("Modal (Juta Rp)", value=100, step=10)
risk_pct = st.sidebar.slider("Resiko per Trade (%)", 0.5, 5.0, 2.0)
ext_mult = st.sidebar.slider("Multiplier Extended", 0.1, 1.0, 0.5)

# --- 5. ENGINE BACKTEST ---
def run_backtest(ticker, period="2y"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        if df.empty: return None
        
        # Indikator Strategi
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA150'] = df['Close'].rolling(150).mean()
        df['MA200'] = df['Close'].rolling(200).mean()
        df['RedLine'] = ta.sma((df['High'] + df['Low']) / 2, 8)
        
        # Logika Sinyal (Stage 2 + RedLine Cross)
        df['Stage2'] = (df['Close'] > df['MA150']) & (df['MA150'] > df['MA200']) & (df['Close'] > df['MA50'])
        df['Signal'] = (df['Stage2']) & (df['Close'] > df['RedLine']) & (df['Close'].shift(1) <= df['RedLine'].shift(1))
        
        # Simulasi Trade
        trades = []
        in_position = False
        buy_price = 0
        
        for i in range(len(df)):
            if df['Signal'].iloc[i] and not in_position:
                in_position = True
                buy_price = df['Close'].iloc[i]
                entry_date = df.index[i]
            elif in_position and df['Close'].iloc[i] < df['RedLine'].iloc[i]:
                in_position = False
                exit_price = df['Close'].iloc[i]
                profit = (exit_price - buy_price) / buy_price
                trades.append({'Entry': entry_date, 'Exit': df.index[i], 'Profit %': profit * 100})
        
        return pd.DataFrame(trades)
    except: return None

# --- 6. MAIN TABS ---
tab_scan, tab_backtest = st.tabs(["🔍 LIVE SCANNER", "📊 STRATEGY BACKTEST"])

with tab_scan:
    if st.button("🚀 JALANKAN SCANNER MINERVINI"):
        # (Gunakan logika scan_market dari versi sebelumnya)
        st.info("Scanner sedang memproses data...")

with tab_backtest:
    st.subheader("Uji Performa Strategi Noris")
    bt_ticker = st.text_input("Masukkan Kode Saham (Contoh: PGAS.JK):", value="PGAS.JK")
    if st.button("📈 RUN BACKTEST"):
        with st.spinner(f"Menganalisa riwayat {bt_ticker}..."):
            bt_res = run_backtest(bt_ticker)
            if bt_res is not None and not bt_res.empty:
                win_rate = len(bt_res[bt_res['Profit %'] > 0]) / len(bt_res) * 100
                total_return = bt_res['Profit %'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Win Rate", f"{win_rate:.1f}%")
                c2.metric("Total Trades", len(bt_res))
                c3.metric("Total Return", f"{total_return:+.2f}%")
                
                st.dataframe(bt_res, use_container_width=True)
            else:
                st.warning("Tidak ditemukan histori trade yang cocok dengan kriteria strategi pada periode ini.")
