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

# ==========================================
# ⚙️ KONFIGURASI PENTING (EDIT DI SINI)
# ==========================================
SECRET_PIN = "2026" 
TV_CHART_ID = "q94KuJTY" 

# 👇 MASUKKAN LINK GRUP WA DI BAWAH INI 👇
LINK_WA = "https://chat.whatsapp.com/https://chat.whatsapp.com/IwsFmoVxlNPHy6Sc1vaAqd?mode=gi_t" 
# ==========================================

# DATABASE FILES
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# DAFTAR SAHAM (UNIVERSE: LQ45 + SYARIAH + TECH)
IDX_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BBTN.JK",
    "GOTO.JK", "EMTK.JK", "ARTO.JK", "BUKA.JK",
    "ASII.JK", "TLKM.JK", "UNVR.JK", "ICBP.JK", "INDF.JK", 
    "HMSP.JK", "GGRM.JK", "AMRT.JK", "MAPI.JK", "ACES.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "ANTM.JK", "INCO.JK", 
    "MDKA.JK", "MEDC.JK", "AKRA.JK", "UNTR.JK", "TINS.JK",
    "JSMR.JK", "EXCL.JK", "ISAT.JK", "CPIN.JK", "JPFA.JK",
    "SMGR.JK", "BRIS.JK", "BRMS.JK", "BUMI.JK", "DEWA.JK"
]

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

def get_indo_date():
    now = datetime.now()
    days = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
    months = {"January": "Januari", "February": "Februari", "March": "Maret", "April": "April", "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus", "September": "September", "October": "Oktober", "November": "November", "December": "Desember"}
    day_name = days[now.strftime("%A")]
    month_name = months[now.strftime("%B")]
    return f"{day_name}, {now.strftime('%d')} {month_name} {now.strftime('%Y')}"

def format_large_number(num):
    if num >= 1_000_000_000_000: return f"{num/1_000_000_000_000:.1f}T"
    if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}M"
    if num >= 1_000_000: return f"{num/1_000_000:.1f}jt"
    return str(int(num))

# --- HELPER: HTML TABLE GENERATOR (UNTUK TAMPILAN PADAT & WARNA) ---
def make_pretty_table(df, title, bg_color, header_color, col_map):
    if df.empty: return ""
    
    html = f"""
    <div style="background-color: {bg_color}; padding: 8px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 10px;">
        <h5 style="text-align: center; margin: 0 0 5px 0; font-size: 13px; color: {header_color}; font-weight: bold;">{title}</h5>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; background-color: rgba(255,255,255,0.5); border-radius: 5px;">
            <tr style="border-bottom: 1px solid #ccc;">
                <th style="text-align: center; padding: 4px;">Kode</th>
                <th style="text-align: center; padding: 4px;">Nilai</th>
            </tr>
    """
    for _, row in df.iterrows():
        val_str = ""
        # Logic format nilai berdasarkan tipe data
        if "Chg" in row: 
            color = "green" if row['Chg'] >= 0 else "red"
            val_str = f"<span style='color:{color}; font-weight:bold;'>{row['Chg']:+.2f}%</span>"
        elif "Vol" in row:
            val_str = format_large_number(row['Vol'])
        elif "Val" in row:
            val_str = format_large_number(row['Val'])
            
        html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="text-align: center; padding: 3px; font-weight:500;">{row['Stock']}</td>
                <td style="text-align: center; padding: 3px;">{val_str}</td>
            </tr>
        """
    html += "</table></div>"
    return html

# --- OPTIMASI SPEED: CACHING ---
@st.cache_data(ttl=300)
def fetch_dashboard_data():
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2y") 
        usd = yf.Ticker("IDR=X").history(period="1d")
        gold = yf.Ticker("GC=F").history(period="1d")
        oil = yf.Ticker("CL=F").history(period="1d")

        ihsg_now = ihsg['Close'].iloc[-1]
        ihsg_chg = ((ihsg_now - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
        usd_now = usd['Close'].iloc[-1]
        ma200_ihsg = ihsg['Close'].rolling(200).mean().iloc[-1]
        rsi_ihsg = ta.rsi(ihsg['Close'], length=14).iloc[-1]
        
        commo_data = {
            "Gold": {"Price": gold['Close'].iloc[-1], "Chg": ((gold['Close'].iloc[-1] - gold['Open'].iloc[-1])/gold['Open'].iloc[-1])*100},
            "Oil": {"Price": oil['Close'].iloc[-1], "Chg": ((oil['Close'].iloc[-1] - oil['Open'].iloc[-1])/oil['Open'].iloc[-1])*100}
        }
        
        movers = []
        for t in IDX_TICKERS:
            try:
                tk = yf.Ticker(f"{t}.JK" if ".JK" not in t else t)
                hist = tk.history(period="2d")
                if len(hist) >= 2:
                    close_now = hist['Close'].iloc[-1]
                    chg = ((close_now - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    vol = hist['Volume'].iloc[-1]
                    val = close_now * vol 
                    movers.append({"Stock": t.replace(".JK",""), "Chg": chg, "Vol": vol, "Val": val})
            except: pass
            
        return ihsg_now, ihsg_chg, usd_now, ma200_ihsg, rsi_ihsg, commo_data, movers
    except: return None, None, None, None, None, None, []

# --- LOGIC TEXT OUTLOOK ---
def generate_outlook_text(price, ma200, rsi):
    if pd.isna(price) or pd.isna(ma200) or pd.isna(rsi): return "Data teknikal IHSG sedang dimuat ulang..."
    trend_txt = ""
    action_txt = ""
    if price > ma200:
        trend_txt = "Secara teknikal, IHSG berada dalam fase **BULLISH (Tren Naik)**."
        if rsi > 70: action_txt = "Momentum jenuh beli. **Waspada profit taking**."
        elif rsi > 50: action_txt = "Momentum pasar stabil."
        else: action_txt = "Koreksi wajar, manfaatkan untuk **Buy on Weakness**."
    else:
        trend_txt = "IHSG masih **KONSOLIDASI/BEARISH** di bawah MA200."
        if rsi < 30: action_txt = "Momentum jenuh jual. Potensi **Rebound**."
        else: action_txt = "Disarankan **Wait and See**."
    return f"{trend_txt} {action_txt}"

# --- FUNGSI TAMPILAN DASHBOARD ---
def display_market_dashboard():
    ihsg_now, ihsg_chg, usd_now, ma200, rsi, commo, movers = fetch_dashboard_data()
    
    if ihsg_now is None:
        st.error("Gagal memuat data pasar. Cek koneksi internet.")
        return

    c_title, c_date = st.columns([2, 1])
    with c_title: st.markdown("### 📊 MARKET DASHBOARD")
    with c_date:
        st.markdown(f"<p style='text-align: right; color: gray; margin-bottom: 0px;'>📅 {get_indo_date()}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: right; color: #f57c00; font-size: 11px; margin-top: 0px;'>⚠️ Data Delayed ~15 Min (Yahoo Finance)</p>", unsafe_allow_html=True)
    
    # ROW 1: METRICS
    c1, c2, c3, c4 = st.columns(4)
    col_ihsg = "#d32f2f" if ihsg_chg < 0 else "#388e3c"
    
    with c1: st.markdown(f"<div style='text-align:center; background:#e3f2fd; padding:10px; border-radius:8px;'><p style='margin:0; font-size:11px; font-weight:bold;'>🇮🇩 IHSG</p><h4 style='margin:2px 0;'>{ihsg_now:,.0f}</h4><p style='margin:0; color:{col_ihsg}; font-size:12px;'>{ihsg_chg:+.2f}%</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div style='text-align:center; background:#f1f8e9; padding:10px; border-radius:8px;'><p style='margin:0; font-size:11px; font-weight:bold;'>🇺🇸 USD/IDR</p><h4 style='margin:2px 0;'>Rp {usd_now:,.0f}</h4><p style='margin:0; color:#555; font-size:12px;'>Rate</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div style='text-align:center; background:#fff8e1; padding:10px; border-radius:8px;'><p style='margin:0; font-size:11px; font-weight:bold;'>🥇 GOLD</p><h4 style='margin:2px 0;'>${commo['Gold']['Price']:,.0f}</h4><p style='margin:0; color:#555; font-size:12px;'>{commo['Gold']['Chg']:.2f}%</p></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div style='text-align:center; background:#eceff1; padding:10px; border-radius:8px;'><p style='margin:0; font-size:11px; font-weight:bold;'>🛢️ OIL</p><h4 style='margin:2px 0;'>${commo['Oil']['Price']:,.1f}</h4><p style='margin:0; color:#555; font-size:12px;'>{commo['Oil']['Chg']:.2f}%</p></div>", unsafe_allow_html=True)

    st.write("")
    
    # ROW 2: MARKET OUTLOOK
    outlook_msg = generate_outlook_text(ihsg_now, ma200, rsi)
    st.info(f"📢 **MARKET OUTLOOK:** {outlook_msg}")

    st.write("")
    
    # --- ROW 3: COMPACT & COLORFUL TABLES ---
    df_movers = pd.DataFrame(movers)
    if not df_movers.empty:
        df_gain = df_movers.sort_values(by="Chg", ascending=False).head(3)[['Stock', 'Chg']]
        df_loss = df_movers.sort_values(by="Chg", ascending=True).head(3)[['Stock', 'Chg']]
        df_vol = df_movers.sort_values(by="Vol", ascending=False).head(3)[['Stock', 'Vol']]
        df_val = df_movers.sort_values(by="Val", ascending=False).head(3)[['Stock', 'Val']]
    else:
        df_gain, df_loss, df_vol, df_val = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    col_g, col_l, col_v, col_m = st.columns(4)
    
    with col_g:
        st.markdown(make_pretty_table(df_gain, "🏆 GAINERS", "#e8f5e9", "#2e7d32", "Chg"), unsafe_allow_html=True)
    with col_l:
        st.markdown(make_pretty_table(df_loss, "🔻 LOSERS", "#ffebee", "#c62828", "Chg"), unsafe_allow_html=True)
    with col_v:
        st.markdown(make_pretty_table(df_vol, "🔥 VOLUME", "#e3f2fd", "#1565c0", "Vol"), unsafe_allow_html=True)
    with col_m:
        st.markdown(make_pretty_table(df_val, "💰 VALUE", "#fff8e1", "#f9a825", "Val"), unsafe_allow_html=True)
        
    st.write("") 

# --- 3. UI UTAMA APLIKASI ---

with st.sidebar:
    st.header("🏫 School Of Trader")
    st.info("Komunitas belajar trading & investasi cerdas untuk tenaga pendidik.")
    st.write("Bergabunglah untuk diskusi harian:")
    if LINK_WA != "https://chat.whatsapp.com/GANTILINKDISINI":
        st.link_button("💬 Gabung Grup WhatsApp", LINK_WA, type="primary", use_container_width=True)
    else:
        st.warning("⚠️ Link WA belum di-setting.")
    st.divider()
    st.caption("NOVA QUANTUM ANALYTICS")
    st.caption("© 2026 Adien Novarisa")

st.title("NOVA QUANTUM")
st.caption("Professional Trading System by Adien Novarisa")

display_market_dashboard()

tab1, tab2, tab3 = st.tabs(["🔍 SCREENER & ANALYST", "⚡ EXECUTION", "🔐 PORTFOLIO"])

# --- TAB 1: SCREENER ---
with tab1:
    st.header("🕵️ X-Ray Saham (Analisa Spesifik)")
    with st.container(border=True):
        col_in1, col_in2 = st.columns([3, 1])
        with col_in1:
            ticker_input = st.text_input("Ketik Kode Saham Apapun (Contoh: BREN, SIDO, BBCA):", placeholder="Masukkan Kode Saham...").upper()
        with col_in2:
            st.write(""); st.write("")
            btn_analyze = st.button("🔍 CEK SEKARANG", type="primary")
        
        if btn_analyze and ticker_input:
            with st.spinner(f"Menganalisa {ticker_input}..."):
                df_single, info_single = get_hybrid_data(ticker_input)
                if df_single is not None:
                    curr_price = df_single['Close'].iloc[-1]
                    prev_price = df_single['Close'].iloc[-2]
                    chg_p = ((curr_price - prev_price)/prev_price)*100
                    ma50 = df_single['Close'].rolling(50).mean().iloc[-1]; ma200 = df_single['Close'].rolling(200).mean().iloc[-1]
                    rsi_now = ta.rsi(df_single['Close'], length=14).iloc[-1]
                    
                    if curr_price > ma50 and ma50 > ma200: trend_st = "🚀 STRONG UPTREND"
                    elif curr_price > ma200: trend_st = "📈 UPTREND"
                    elif curr_price < ma200: trend_st = "📉 DOWNTREND (Bahaya)"
                    else: trend_st = "➡️ SIDEWAYS"
                    
                    O = df_single['Open'].iloc[-1]; H = df_single['High'].iloc[-1]; L = df_single['Low'].iloc[-1]; C = df_single['Close'].iloc[-1]
                    O_prev = df_single['Open'].iloc[-2]; C_prev = df_single['Close'].iloc[-2]
                    body = abs(C - O); upper_shadow = H - max(C, O); lower_shadow = min(C, O) - L
                    pola = "Tidak ada pola khusus"
                    if rsi_now < 45:
                        if (lower_shadow > body * 2) and (upper_shadow < body): pola = "🔨 HAMMER (Potensi Rebound)"
                        elif (C > O) and (C_prev < O_prev) and (C > O_prev) and (O < C_prev): pola = "🔥 BULLISH ENGULFING (Pembeli Masuk)"
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric(f"{ticker_input}", f"Rp {int(curr_price):,}", f"{chg_p:.2f}%")
                    k2.metric("RSI (Momentum)", f"{int(rsi_now)}", "Area Murah" if rsi_now < 35 else "Netral")
                    k3.metric("Trend", "MA 200", trend_st)
                    st.info(f"**Analisa Candlestick:** {pola}")
                    st.markdown(f"[➡️ Lihat Grafik Lengkap di TradingView](https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{ticker_input})")
                else: st.error("Saham tidak ditemukan atau data belum tersedia.")

    st.markdown("---")

    st.header("📡 Radar Market (Scanner)")
    with st.expander("ℹ️ Daftar Saham (Universe)"):
        list_saham = ", ".join([s.replace(".JK", "") for s in IDX_TICKERS])
        st.info(f"**Sistem memindai {len(IDX_TICKERS)} Saham Bluechip:**\n\n{list_saham}")

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
        
        for i, t in enumerate(IDX_TICKERS):
            progress_bar.progress((i + 1) / len(IDX_TICKERS))
            df, info = get_hybrid_data(t)
            if df is not None and info is not None:
                O = df['Open'].iloc[-1]; H = df['High'].iloc[-1]; L = df['Low'].iloc[-1]; C = df['Close'].iloc[-1]
                O_prev = df['Open'].iloc[-2]; C_prev = df['Close'].iloc[-2]
                body = abs(C - O); upper_shadow = H - max(C, O); lower_shadow = min(C, O) - L
                rsi_series = ta.rsi(df['Close'], length=14); rsi_now = rsi_series.iloc[-1]
                vol_now = df['Volume'].iloc[-1]; vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                
                pola_candle = ""; is_valid_reversal = False
                if rsi_now < 45: 
                    if (lower_shadow > body * 2) and (upper_shadow < body): pola_candle = "🔨 HAMMER"; is_valid_reversal = True
                    elif (C > O) and (C_prev < O_prev) and (C > O_prev) and (O < C_prev): pola_candle = "🔥 ENGULFING"; is_valid_reversal = True
                
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
                    c2.markdown(f"**RSI:**\n{d['RSI']}")
                    c3.markdown(f"**Grafik:**\n[Buka TradingView]({d['TV']})")
                    st.divider()
                    
                    st.write("💰 **Simulasi Lot**")
                    col_in1, col_in2, col_in3 = st.columns(3)
                    modal = col_in1.number_input("Modal (Rp):", value=10000000, step=1000000, key=f"mod_{d['Stock']}")
                    col_in1.caption(f"💵 Terbaca: **Rp {int(modal):,}**")
                    risiko = col_in2.number_input("Risiko (%):", value=2.0, key=f"ris_{d['Stock']}")
                    sl_price = col_in3.number_input("Cut Loss (Rp):", value=d['Support'], step=10, key=f"sl_{d['Stock']}")
                    col_in3.caption(f"🔻 Terbaca: **Rp {int(sl_price):,}**")

                    if sl_price < d['Price']:
                        risiko_rp = modal * (risiko / 100)
                        max_lot = int((risiko_rp / (d['Price'] - sl_price)) / 100)
                        st.info(f"🛡️ Risiko Max: **Rp {int(risiko_rp):,}**. Beli Max: **{max_lot} LOT**.")
                    else: st.warning("⚠️ Cut Loss harus di bawah harga pasar.")
                    
                    st.divider()
                    col_b1, col_b2 = st.columns([1, 3])
                    
                    if col_b1.button("Hapus", key=f"del_{d['Stock']}"):
                        wl = wl[wl.Stock != d['Stock']]; wl.to_csv(WATCHLIST_FILE, index=False); st.rerun()
                        
                    if col_b2.button(f"🛒 SIMULASI BELI {d['Stock']}", type="primary", key=f"buy_{d['Stock']}"):
                        pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Stock": d['Stock'], "Entry": d['Price']}])], ignore_index=True).to_csv(DB_FILE, index=False)
                        wl = wl[wl.Stock != d['Stock']]; wl.to_csv(WATCHLIST_FILE, index=False)
                        st.success(f"✅ **DATA TERSIMPAN.** {d['Stock']} berhasil dicatat ke Portfolio Admin.")
                        st.warning(f"🔔 **PENGINGAT EKSEKUSI:** Silakan buka aplikasi Sekuritas Anda dan lakukan Order Buy untuk **{d['Stock']}** secara real.")
                        st.stop() 

# --- TAB 3: PORTFOLIO ---
with tab3:
    st.header("🔐 Portfolio Administrator")
    if 'porto_unlocked' not in st.session_state: st.session_state['porto_unlocked'] = False
    if not st.session_state['porto_unlocked']:
        st.warning("🔒 Halaman ini terkunci.")
        with st.form("login_form"):
            user_pin = st.text_input("Masukkan PIN Keamanan:", type="password")
            if st.form_submit_button("BUKA AKSES"):
                if user_pin == SECRET_PIN:
                    st.session_state['porto_unlocked'] = True; st.success("Akses Diterima."); st.rerun()
                else: st.error("PIN Salah.")
    else:
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1: st.success("✅ Akses Administrator Terbuka")
        with col_p2:
            if st.button("🔒 KUNCI KEMBALI"): st.session_state['porto_unlocked'] = False; st.rerun()
        if st.button("🚨 RESET TOTAL PORTFOLIO", type="primary"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()
        
        df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
        if df_p.empty: st.info("Belum ada aset.")
        else:
            st.metric("Total Emiten", f"{len(df_p)}")
            st.write("---")
            for idx, row in df_p.iterrows():
                last, gl, act = get_porto_analysis(row['Stock'], row['Entry'])
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
                    c1.markdown(f"### {row['Stock']}")
                    c1.caption(f"Buy: Rp {row['Entry']:,}")
                    if "Profit" in act: c2.markdown(f"<h3 style='color:#00C853'>{gl}</h3>", unsafe_allow_html=True)
                    elif "CUT" in act: c2.markdown(f"<h3 style='color:#D50000'>{gl}</h3>", unsafe_allow_html=True)
                    else: c2.markdown(f"<h3>{gl}</h3>", unsafe_allow_html=True)
                    c3.info(f"**Saran:** {act}")
                    if c4.button("Jual", key=f"sell_{idx}"):
                        df_p.drop(idx).to_csv(DB_FILE, index=False); st.success("Done."); st.rerun()
                    st.markdown("---")
