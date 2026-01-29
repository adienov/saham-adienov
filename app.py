import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
import time
from datetime import datetime

# --- 1. SETTING IDENTITAS & KONFIGURASI ---
st.set_page_config(
    page_title="NOVA QUANTUM",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# KONFIGURASI PRIBADI
SECRET_PIN = "2026" 
TV_CHART_ID = "q94KuJTY" 

# DATABASE FILES
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# DAFTAR SAHAM (UNIVERSE)
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

# --- 2. FUNGSI BANTUAN (HELPER) ---

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

def get_hybrid_data(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="6mo")
        info = t.info 
        if len(df) < 50: return None, None
        return df, info
    except: return None, None

def get_technical_detail(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 200: return None
        
        close = int(df['Close'].iloc[-1])
        ma50 = int(df['Close'].rolling(50).mean().iloc[-1])
        ma200 = int(df['Close'].rolling(200).mean().iloc[-1])
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        if close > ma50 and ma50 > ma200: trend = f"🚀 Strong Uptrend"
        elif close > ma200: trend = f"📈 Uptrend Normal"
        elif close < ma200: trend = f"📉 Downtrend (Hati-hati)"
        else: trend = "➡️ Sideways"
        
        timing = "Wait"
        if close > ma50:
            dist = abs(close - ma50)/ma50
            if dist < 0.05: timing = f"🟢 BUY AREA: {ma50}-{close}"
            else: timing = f"⏳ TUNGGU KOREKSI: {ma50}"
        elif close < ma200 and rsi < 35: timing = "👀 PANTAU REVERSAL"

        support = int(df['Low'].tail(20).min())
        resistance = int(df['High'].tail(20).max())
        tv_url = f"https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{ticker.replace('.JK','')}"

        return {
            "Stock": ticker.replace(".JK",""), "Price": close, "Trend": trend, "RSI": int(rsi), 
            "Timing": timing, "Support": support, "Resistance": resistance, "TV": tv_url
        }
    except: return None

def get_porto_analysis(ticker, entry_price):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        last_p = int(t.history(period="1d")['Close'].iloc[-1])
        gl_val = ((last_p - entry_price) / entry_price) * 100
        action = "Hold"
        if gl_val <= -7: action = "🚨 CUT LOSS SEGERA"
        elif gl_val >= 15: action = "🔵 TAKE PROFIT"
        return last_p, f"{gl_val:+.2f}%", action
    except: return 0, "0%", "-"

# FUNGSI TANGGAL INDONESIA
def get_indo_date():
    now = datetime.now()
    days = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
    months = {"January": "Januari", "February": "Februari", "March": "Maret", "April": "April", "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus", "September": "September", "October": "Oktober", "November": "November", "December": "Desember"}
    
    day_name = days[now.strftime("%A")]
    month_name = months[now.strftime("%B")]
    day_num = now.strftime("%d")
    year = now.strftime("%Y")
    
    return f"{day_name}, {day_num} {month_name} {year}"

# --- OPTIMASI SPEED: CACHING ---
@st.cache_data(ttl=300)
def fetch_dashboard_data():
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d")
        usd = yf.Ticker("IDR=X").history(period="1d")
        
        ihsg_now = ihsg['Close'].iloc[-1]
        ihsg_chg = ((ihsg_now - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
        usd_now = usd['Close'].iloc[-1]
        
        movers = []
        for t in SYARIAH_TICKERS:
            try:
                tk = yf.Ticker(f"{t}.JK" if ".JK" not in t else t)
                hist = tk.history(period="2d")
                if len(hist) >= 2:
                    chg = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    movers.append({"Stock": t.replace(".JK",""), "Chg": chg})
            except: pass
        
        return ihsg_now, ihsg_chg, usd_now, movers
    except:
        return None, None, None, []

# --- FUNGSI TAMPILAN DASHBOARD ---
def display_market_dashboard():
    ihsg_now, ihsg_chg, usd_now, movers = fetch_dashboard_data()
    
    if ihsg_now is None:
        st.error("Gagal memuat data pasar. Cek koneksi internet.")
        return

    df_movers = pd.DataFrame(movers)
    if not df_movers.empty:
        df_movers = df_movers.sort_values(by="Chg", ascending=False)
        top_gainers = df_movers.head(3) 
        top_losers = df_movers.tail(3).sort_values(by="Chg", ascending=True) 
    else:
        top_gainers, top_losers = pd.DataFrame(), pd.DataFrame()

    # HEADER DASHBOARD DENGAN TANGGAL
    c_title, c_date = st.columns([2, 1])
    with c_title:
        st.markdown("### 📊 MARKET OVERVIEW")
    with c_date:
        st.markdown(f"<p style='text-align: right; color: gray;'>📅 {get_indo_date()}</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        k1, k2 = st.columns(2)
        k1.metric("🇮🇩 IHSG (Composite)", f"{ihsg_now:,.2f}", f"{ihsg_chg:.2f}%")
        k2.metric("🇺🇸 USD/IDR", f"Rp {usd_now:,.0f}", "")
    
    c1, c2 = st.columns(2)
    with c1:
        st.success("🏆 TOP GAINERS (Kenaikan Tertinggi)")
        if not top_gainers.empty:
            df_gain = top_gainers[['Stock', 'Chg']].copy()
            df_gain = df_gain.rename(columns={'Stock': 'Emiten', 'Chg': 'Naik'})
            st.dataframe(df_gain, column_config={"Emiten": st.column_config.TextColumn("Kode"), "Naik": st.column_config.NumberColumn("Kenaikan", format="+%.2f%%")}, hide_index=True, use_container_width=True)
        else: st.write("-")
        
    with c2:
        st.error("🔻 TOP LOSERS (Koreksi Terdalam)")
        if not top_losers.empty:
            df_loss = top_losers[['Stock', 'Chg']].copy()
            df_loss = df_loss.rename(columns={'Stock': 'Emiten', 'Chg': 'Turun'})
            st.dataframe(df_loss, column_config={"Emiten": st.column_config.TextColumn("Kode"), "Turun": st.column_config.NumberColumn("Penurunan", format="%.2f%%")}, hide_index=True, use_container_width=True)
        else: st.write("-")
    st.write("") 

# --- 3. UI UTAMA APLIKASI ---

# JUDUL BARU YANG ELEGAN
st.title("NOVA QUANTUM ANALYTICS")
st.caption("Professional Trading System by Adien Novarisa")

# Tampilkan Dashboard
display_market_dashboard()

# --- DEFINISI TAB ---
tab1, tab2, tab3 = st.tabs(["🔍 STEP 1: SCREENER", "⚡ STEP 2: EXECUTION", "🔐 STEP 3: PORTFOLIO"])

# --- TAB 1: SCREENER ---
with tab1:
    st.header("🔍 Radar Saham")
    
    if 'last_mode' not in st.session_state: st.session_state['last_mode'] = "Radar Diskon (Market Crash)"
    mode = st.radio("Pilih Strategi:", ["Radar Diskon (Market Crash)", "Reversal (Pantulan)", "Breakout (Tren Naik)", "Swing (Koreksi Sehat)"], horizontal=True)
    
    if mode != st.session_state['last_mode']:
        st.session_state['scan_results'] = None 
        st.session_state['last_mode'] = mode    
        st.rerun() 
    
    if 'scan_results' not in st.session_state: st.session_state['scan_results'] = None

    if st.button("🚀 SCAN MARKET SEKARANG", type="primary"):
        st.write(f"⏳ Memindai data market untuk: **{mode}**...")
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(SYARIAH_TICKERS):
            progress_bar.progress((i + 1) / len(SYARIAH_TICKERS))
            df, info = get_hybrid_data(t)
            if df is not None and info is not None:
                # PERSIAPAN DATA
                O = df['Open'].iloc[-1]; H = df['High'].iloc[-1]; L = df['Low'].iloc[-1]; C = df['Close'].iloc[-1]
                O_prev = df['Open'].iloc[-2]; C_prev = df['Close'].iloc[-2]
                body = abs(C - O); upper_shadow = H - max(C, O); lower_shadow = min(C, O) - L
                rsi_series = ta.rsi(df['Close'], length=14); rsi_now = rsi_series.iloc[-1]
                vol_now = df['Volume'].iloc[-1]; vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                
                # DETEKSI POLA
                pola_candle = ""; is_valid_reversal = False
                if rsi_now < 45: 
                    if (lower_shadow > body * 2) and (upper_shadow < body): pola_candle = "🔨 HAMMER"; is_valid_reversal = True
                    elif (C > O) and (C_prev < O_prev) and (C > O_prev) and (O < C_prev): pola_candle = "🔥 ENGULFING"; is_valid_reversal = True
                
                # FILTER LOGIC
                lolos = False
                roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                per = info.get('trailingPE', 999) if info.get('trailingPE') else 999
                f_stat = "⚠️ Mahal"; 
                if roe > 10 and per < 20: f_stat = "✅ Sehat"
                if roe > 15 and per < 15: f_stat = "💎 Super"

                if "Radar Diskon" in mode: lolos = True
                elif "Reversal" in mode:
                    if is_valid_reversal: lolos = True
                    elif rsi_now < 32 and C > df['High'].iloc[-2]: lolos = True; pola_candle = "↗️ REBOUND" 
                elif "Breakout" in mode:
                     high_20 = df['High'].rolling(20).max().iloc[-2]
                     if C > high_20 and vol_now > vol_avg: lolos = True
                elif "Swing" in mode:
                    ma50 = df['Close'].rolling(50).mean().iloc[-1]
                    if C > ma50 and L <= (ma50 * 1.05) and C > C_prev: lolos = True

                if lolos:
                    vol_ratio = vol_now / vol_avg
                    if vol_ratio < 0.6: v_txt = "😴 Sepi"
                    elif vol_ratio < 1.3: v_txt = "😐 Normal"
                    elif vol_ratio < 3.0: v_txt = "⚡ Ramai"
                    else: v_txt = "🔥 MELEDAK"
                    vol_display = f"{v_txt} ({vol_ratio:.1f}x)"
                    
                    if rsi_now < 30: rsi_txt = "🔥 DISKON"
                    elif rsi_now < 45: rsi_txt = "✅ MURAH"
                    else: rsi_txt = "😐 NORMAL"
                    rsi_display = f"{int(rsi_now)} ({rsi_txt})"
                    
                    if roe > 15: roe_txt = "🚀 ISTIMEWA"
                    elif roe > 10: roe_txt = "✅ BAGUS"
                    else: roe_txt = "⚠️ KURANG"
                    roe_display = f"{roe:.1f}%"

                    signal_final = f_stat
                    if "Reversal" in mode and pola_candle != "": signal_final = f"{pola_candle}" 
                    elif "Breakout" in mode: signal_final = "🚀 BREAKOUT"
                    elif "Swing" in mode: signal_final = "🔄 SWING"

                    tv_link = f"https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{t.replace('.JK','')}"
                    
                    results.append({"Pilih": False, "Stock": t.replace(".JK",""), "Price": int(C), "Chg%": ((C - C_prev)/C_prev)*100, "Vol": vol_display, "Signal": signal_final, "ROE": roe_display, "RSI": rsi_display, "Chart": tv_link})
        progress_bar.empty()
        
        if results:
            df_res = pd.DataFrame(results)
            if "Reversal" in mode: df_res = df_res.sort_values(by="Signal", ascending=True) 
            elif "Radar" in mode: df_res = df_res.sort_values(by="ROE", ascending=False)
            st.session_state['scan_results'] = df_res
        else: st.warning("Tidak ada saham yang sesuai kriteria.")

    if st.session_state['scan_results'] is not None:
        edited_df = st.data_editor(st.session_state['scan_results'], column_config={"Pilih": st.column_config.CheckboxColumn("Add", width=50), "Stock": st.column_config.TextColumn("Kode", width=60), "Price": st.column_config.NumberColumn("Harga", format="Rp %d", width=80), "Chg%": st.column_config.NumberColumn("Chg%", format="%.2f%%", width=70), "Vol": st.column_config.TextColumn("Volume", width=120), "Signal": st.column_config.TextColumn("SINYAL", width=130), "ROE": st.column_config.TextColumn("ROE", width=70), "RSI": st.column_config.TextColumn("RSI", width=110), "Chart": st.column_config.LinkColumn("View", display_text="📈 Chart", width=70)}, hide_index=True, use_container_width=True)
        
        if st.button("💾 MASUKKAN KE WATCHLIST"):
            selected = edited_df[edited_df["Pilih"] == True]["Stock"].tolist()
            if selected:
                wl = load_data(WATCHLIST_FILE, ["Stock"])
                new = [s for s in selected if s not in wl["Stock"].values]
                if new: 
                    pd.concat([wl, pd.DataFrame([{"Stock": s} for s in new])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
                    st.success(f"✅ Berhasil! {len(new)} saham ditambahkan.")
                    time.sleep(1.5); st.rerun()
                else: st.warning("⚠️ Saham sudah ada di Watchlist.")
            else: st.warning("⚠️ Belum ada saham yang dicentang.")

# --- TAB 2: WATCHLIST ---
with tab2:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.header("⚡ Kalkulator & Eksekusi")
        st.caption("Analisa lot sebelum membeli.")
    with col_h2:
        if st.button("🗑️ RESET WATCHLIST", type="secondary"):
            if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()

    wl = load_data(WATCHLIST_FILE, ["Stock"])
    
    if wl.empty:
        st.info("📭 Watchlist kosong.")
    else:
        for idx, row in wl.iterrows():
            d = get_technical_detail(row['Stock'])
            if d:
                with st.expander(f"📊 {d['Stock']} | Rp {d['Price']:,} | {d['Timing']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Tren:**\n{d['Trend']}")
                    c2.markdown(f"**RSI:**\n{
