import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import math
from datetime import datetime

# --- 1. SETTING IDENTITAS & KONFIGURASI ---
st.set_page_config(
    page_title="NOVA QUANTUM",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ⚙️ KONFIGURASI PENTING
# ==========================================
SECRET_PIN = "2026" 
# 👇 MASUKKAN LINK GRUP WA DI BAWAH INI 👇
LINK_WA = "https://chat.whatsapp.com/GANTILINKDISINI" 
# ==========================================

# UNIVERSE SAHAM
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
        df = t.history(period="2y")
        if len(df) < 20: return None
        
        # OHLC Data
        close = int(df['Close'].iloc[-1])
        prev_close = int(df['Close'].iloc[-2])
        open_p = int(df['Open'].iloc[-1])
        high_p = int(df['High'].iloc[-1])
        low_p = int(df['Low'].iloc[-1])
        
        # 1. Hitung Persentase Change
        chg_pct = ((close - prev_close) / prev_close) * 100
        avg_p = int((high_p + low_p + close) / 3)

        # 2. ANALISA BENTUK CANDLE (Candle Reader Logic)
        body = abs(close - open_p)
        total_range = high_p - low_p
        upper_shadow = high_p - max(close, open_p)
        lower_shadow = min(close, open_p) - low_p
        
        candle_status = "⚪ Neutral (Doji/Spinning)" # Default
        
        if total_range > 0:
            # Bullish Candles
            if close > open_p:
                if body > 0.8 * total_range: candle_status = "🟢 Bullish Marubozu (Strong Buy)"
                elif lower_shadow > 2 * body: candle_status = "🔨 Hammer (Reversal Potential)"
                else: candle_status = "🟢 Bullish Candle"
            # Bearish Candles
            elif close < open_p:
                if body > 0.8 * total_range: candle_status = "🔴 Bearish Marubozu (Strong Sell)"
                elif upper_shadow > 2 * body: candle_status = "☄️ Shooting Star (Reversal Potential)"
                else: candle_status = "🔴 Bearish Candle"
            # Doji
            elif body <= 0.1 * total_range:
                candle_status = "➕ Doji (Market Indecision)"

        # Indikator
        ma20 = int(df['Close'].rolling(20).mean().iloc[-1] if pd.notna(df['Close'].rolling(20).mean().iloc[-1]) else 0)
        ma50 = int(df['Close'].rolling(50).mean().iloc[-1] if pd.notna(df['Close'].rolling(50).mean().iloc[-1]) else 0)
        ma200 = int(df['Close'].rolling(200).mean().iloc[-1] if pd.notna(df['Close'].rolling(200).mean().iloc[-1]) else 0)
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        trend = "➡️ Sideways"
        if ma200 > 0:
            if close > ma200: trend = "🚀 Uptrend"
            else: trend = "📉 Downtrend"
        
        return {
            "Stock": ticker.replace(".JK",""), 
            "Price": close, "Chg": chg_pct,
            "Open": open_p, "Low": low_p, "High": high_p, "Avg": avg_p,
            "Trend": trend, "RSI": rsi, "MA200": ma200, "Candle": candle_status
        }
    except: return None

def get_indo_date():
    now = datetime.now()
    days = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
    months = {"January": "Januari", "February": "Februari", "March": "Maret", "April": "April", "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus", "September": "September", "October": "Oktober", "November": "November", "December": "Desember"}
    return f"{days[now.strftime('%A')]}, {now.strftime('%d')} {months[now.strftime('%B')]} {now.strftime('%Y')}"

def format_large_number(num):
    if num >= 1_000_000_000_000: return f"{num/1_000_000_000_000:.1f}T"
    if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}M"
    if num >= 1_000_000: return f"{num/1_000_000:.1f}jt"
    return str(int(num))

# --- WIDGET CHART ---
def render_tv_widget(symbol):
    html_code = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 380, 
        "symbol": "IDX:{symbol}",
        "interval": "D",
        "timezone": "Asia/Jakarta",
        "theme": "light",
        "style": "1",
        "locale": "id",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart",
        "studies": ["BB@tv-basicstudies", "RSI@tv-basicstudies", "MACD@tv-basicstudies"],
        "hide_side_toolbar": false
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=390)

# --- HTML TABLE GENERATOR ---
def render_html_table(df, title, bg_color, text_color, val_col):
    if df.empty: return ""
    rows_html = ""
    for _, row in df.iterrows():
        val_display = ""
        if val_col == "Chg":
            color = "#007f00" if row['Chg'] >= 0 else "#d32f2f"
            val_display = f"<span style='color:{color}; font-weight:bold;'>{row['Chg']:+.2f}%</span>"
        elif val_col == "Vol":
            val_display = format_large_number(row['Vol'])
        elif val_col == "Val":
            val_display = format_large_number(row['Val'])
        rows_html += f"<tr><td style='padding:4px; text-align:center; border-bottom:1px solid #ddd; font-weight:600;'>{row['Stock']}</td><td style='padding:4px; text-align:center; border-bottom:1px solid #ddd;'>{val_display}</td></tr>"

    html_code = f"""
    <div style='background-color:{bg_color}; border-radius:8px; padding:10px; margin-bottom:10px; border:1px solid {text_color};'>
        <div style='text-align:center; font-weight:bold; color:{text_color}; font-size:14px; margin-bottom:5px; text-transform:uppercase;'>{title}</div>
        <table style='width:100%; border-collapse:collapse; font-size:12px; background-color:rgba(255,255,255,0.7); border-radius:5px;'>
            <thead><tr style='border-bottom:2px solid {text_color};'><th style='padding:5px; text-align:center;'>Emiten</th><th style='padding:5px; text-align:center;'>Nilai</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """
    return html_code

# --- FETCH DASHBOARD (SAFE MODE) ---
@st.cache_data(ttl=300)
def fetch_dashboard_data():
    ihsg_now, ihsg_chg, ma200_ihsg, rsi_ihsg = 0, 0, 0, 0
    try:
        ihsg_df = yf.Ticker("^JKSE").history(period="5d")
        if not ihsg_df.empty:
            ihsg_now = ihsg_df['Close'].iloc[-1]
            ihsg_chg = ((ihsg_now - ihsg_df['Close'].iloc[-2]) / ihsg_df['Close'].iloc[-2]) * 100
            ma200_ihsg = ihsg_df['Close'].rolling(200).mean().iloc[-1] if len(ihsg_df) > 200 else 0
            rsi_ihsg = ta.rsi(ihsg_df['Close'], length=14).iloc[-1]
    except: pass

    usd_now = 0
    try:
        usd_df = yf.Ticker("IDR=X").history(period="1d")
        if not usd_df.empty: usd_now = usd_df['Close'].iloc[-1]
    except: pass

    commo_data = {"Gold": {"Price": 0, "Chg": 0}, "Oil": {"Price": 0, "Chg": 0}}
    try:
        gold_df = yf.Ticker("GC=F").history(period="5d")
        if len(gold_df) >= 2:
            commo_data["Gold"]["Price"] = gold_df['Close'].iloc[-1]
            commo_data["Gold"]["Chg"] = ((gold_df['Close'].iloc[-1] - gold_df['Close'].iloc[-2])/gold_df['Close'].iloc[-2])*100
    except: pass
    
    try:
        oil_df = yf.Ticker("CL=F").history(period="5d")
        if len(oil_df) >= 2:
            commo_data["Oil"]["Price"] = oil_df['Close'].iloc[-1]
            commo_data["Oil"]["Chg"] = ((oil_df['Close'].iloc[-1] - oil_df['Close'].iloc[-2])/oil_df['Close'].iloc[-2])*100
    except: pass

    movers = []
    try:
        for t in ["BBCA", "BBRI", "GOTO", "TLKM", "ASII"]: 
            tk = yf.Ticker(f"{t}.JK")
            hist = tk.history(period="2d")
            if len(hist) >= 2:
                close_now = hist['Close'].iloc[-1]
                chg = ((close_now - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                vol = hist['Volume'].iloc[-1]
                val = close_now * vol 
                movers.append({"Stock": t, "Chg": chg, "Vol": vol, "Val": val})
    except: pass
            
    return ihsg_now, ihsg_chg, usd_now, ma200_ihsg, rsi_ihsg, commo_data, movers

def generate_outlook_text(price, ma200, rsi):
    if price == 0: return "Menunggu data pasar..."
    trend = "**BULLISH (Naik)**" if price > ma200 else "**BEARISH (Turun)**"
    action = "Waspada Profit Taking." if rsi > 70 else "Potensi Rebound." if rsi < 30 else "Pasar Stabil."
    return f"Posisi IHSG saat ini {trend} terhadap MA200. Momentum RSI: {action}"

# --- MAIN UI ---
def display_market_dashboard():
    ihsg_now, ihsg_chg, usd_now, ma200, rsi, commo, movers = fetch_dashboard_data()
    
    c1, c2 = st.columns([2, 1])
    with c1: st.markdown("### 📊 MARKET DASHBOARD")
    with c2: st.markdown(f"<div style='text-align:right; color:gray; font-size:12px;'>📅 {get_indo_date()}<br>⚠️ Data Delayed ~15 Min</div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    col_ihsg = "#d32f2f" if ihsg_chg < 0 else "#388e3c"
    col_gold = "#d32f2f" if commo['Gold']['Chg'] < 0 else "#388e3c"
    col_oil = "#d32f2f" if commo['Oil']['Chg'] < 0 else "#388e3c"

    ihsg_disp = f"{ihsg_now:,.0f}" if ihsg_now > 0 else "N/A"
    usd_disp = f"{int(usd_now):,.0f}" if usd_now > 0 else "N/A"
    gold_disp = f"{int(commo['Gold']['Price']):,.0f}" if commo['Gold']['Price'] > 0 else "N/A"
    oil_disp = f"{commo['Oil']['Price']:,.1f}" if commo['Oil']['Price'] > 0 else "N/A"

    with k1: st.markdown(f"<div style='text-align:center; background:#e3f2fd; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🇮🇩 IHSG</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{ihsg_disp}</span><br><span style='color:{col_ihsg}; font-size:16px; font-weight:bold;'>{ihsg_chg:+.2f}%</span></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div style='text-align:center; background:#f1f8e9; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🇺🇸 USD/IDR</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{usd_disp}</span><br><span style='color:#555; font-size:16px;'>Rupiah</span></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div style='text-align:center; background:#fff8e1; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🥇 GOLD</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{gold_disp}</span><br><span style='color:{col_gold}; font-size:16px; font-weight:bold;'>{commo['Gold']['Chg']:+.2f}%</span></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div style='text-align:center; background:#eceff1; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🛢️ OIL</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{oil_disp}</span><br><span style='color:{col_oil}; font-size:16px; font-weight:bold;'>{commo['Oil']['Chg']:+.2f}%</span></div>", unsafe_allow_html=True)

    st.write("")
    if ihsg_now > 0: st.info(f"📢 **OUTLOOK:** {generate_outlook_text(ihsg_now, ma200, rsi)}")
    else: st.warning("⚠️ Koneksi ke data server sedang tidak stabil. Beberapa data mungkin kosong.")
    st.write("")

    df_m = pd.DataFrame(movers)
    if not df_m.empty:
        g = df_m.sort_values(by="Chg", ascending=False).head(3)
        l = df_m.sort_values(by="Chg", ascending=True).head(3)
        v = df_m.sort_values(by="Vol", ascending=False).head(3)
        m = df_m.sort_values(by="Val", ascending=False).head(3)
        c_g, c_l, c_v, c_m = st.columns(4)
        with c_g: st.markdown(render_html_table(g, "🏆 GAINERS", "#e8f5e9", "#2e7d32", "Chg"), unsafe_allow_html=True)
        with c_l: st.markdown(render_html_table(l, "🔻 LOSERS", "#ffebee", "#c62828", "Chg"), unsafe_allow_html=True)
        with c_v: st.markdown(render_html_table(v, "🔥 VOLUME", "#e3f2fd", "#1565c0", "Vol"), unsafe_allow_html=True)
        with c_m: st.markdown(render_html_table(m, "💰 VALUE", "#fff8e1", "#f9a825", "Val"), unsafe_allow_html=True)

# --- SIDEBAR & HEADER ---
with st.sidebar:
    st.header("🏫 School Of Trader")
    st.info("Komunitas belajar trading & investasi cerdas.")
    st.write("Bergabunglah diskusi:")
    if LINK_WA != "https://chat.whatsapp.com/GANTILINKDISINI":
        st.link_button("💬 Gabung Grup WhatsApp", LINK_WA, type="primary", use_container_width=True)
    else: st.warning("⚠️ Link WA belum di-setting.")
    st.divider(); st.caption("NOVA QUANTUM ANALYTICS\n© 2026 Adien Novarisa")

st.title("NOVA QUANTUM")
st.caption("Professional Trading System by Adien Novarisa")

display_market_dashboard()

tab1, tab2, tab3 = st.tabs(["🔍 SCREENER & ANALYST", "⚡ EXECUTION (CALCULATOR)", "🔐 PORTFOLIO"])

# --- TAB 1: SCREENER ---
with tab1:
    col_chart, col_info = st.columns([1.6, 1])
    
    with col_chart:
        if 'xray_ticker' not in st.session_state: st.session_state['xray_ticker'] = "BBCA"
        st.markdown(f"**📈 Chart: {st.session_state['xray_ticker']}** (Bollinger + RSI + MACD)")
        render_tv_widget(st.session_state['xray_ticker']) 
    
    with col_info:
        with st.container(border=True):
            st.markdown("#### 🕵️ X-Ray Saham")
            c_in, c_btn = st.columns([2, 1])
            with c_in: 
                txt_in = st.text_input("Kode Saham:", value=st.session_state['xray_ticker']).upper()
            with c_btn: 
                st.write(""); st.write("")
                if st.button("🔍 Cek", type="primary", use_container_width=True):
                    st.session_state['xray_ticker'] = txt_in
            
            d_s = get_technical_detail(st.session_state['xray_ticker'])
            if d_s is not None:
                rsi_safe = int(d_s['RSI']) if pd.notna(d_s['RSI']) else 0
                st.metric("Harga Terkini (Close)", f"Rp {int(d_s['Price']):,}", f"{d_s['Chg']:+.2f}%")
                
                # --- NEW CANDLE STATUS DISPLAY ---
                st.success(f"{d_s['Trend']}")
                st.markdown(f"🕯️ **Candle:** {d_s['Candle']}")
                
                # --- GRID LAYOUT ---
                r1, r2 = st.columns(2)
                with r1:
                    st.write(f"🔹 **Open:** {int(d_s['Open']):,}")
                    st.write(f"🔻 **Low:** {int(d_s['Low']):,}")
                with r2:
                    st.write(f"🔺 **High:** {int(d_s['High']):,}")
                    st.write(f"⚖️ **Avg:** {int(d_s['Avg']):,}")
                
                st.info(f"RSI: {rsi_safe} | MA200: {int(d_s['MA200']):,}")
            else: st.warning("Data loading...")
            st.divider()
            st.caption("🛡️ **FUNDAMENTAL SHIELD:** Cek kolom 'Kualitas' & 'Valuasi' di bawah.")

    st.markdown("---")
    
    # --- SCANNER SECTION ---
    st.header("📡 Radar Market (Scanner)")
    
    col_rad1, col_rad2 = st.columns([3, 1])
    with col_rad1:
        if 'mode' not in st.session_state: st.session_state['mode'] = "💎 SUPER SCREENER (Fundamental + Smart Money)"
        
        mode = st.radio("Strategi:", [
            "💎 SUPER SCREENER (Fundamental + Smart Money)",
            "🔄 Swing (Buy on Weakness)", 
            "🦈 Contrarian Sniper (Pisau Jatuh)", 
            "🌟 Golden Cross (Trend Awal)", 
            "🐋 Deteksi Akumulasi Bandar",
            "🚀 Volatilitas Tinggi (Copet)"
        ], horizontal=True)
        
        # FILOSOFI BOX
        if "SUPER" in mode:
            st.info("📖 **Filosofi: Benjamin Graham (The Intelligent Investor)**\n\n'Membeli saham adalah membeli kepemilikan bisnis. Carilah perusahaan bagus yang dijual dengan harga diskon (Undervalued) dan aman secara margin (Safety Margin).'")
        elif "Swing" in mode:
            st.info("📖 **Filosofi: Dr. Alexander Elder (Trading for a Living)**\n\n'Jangan mengejar bus yang sudah jalan. Tunggulah di halte (Koreksi). Belilah saat tren naik sedang istirahat sejenak, lalu jual saat ia berlari lagi.'")
        elif "Contrarian" in mode:
            st.info("📖 **Filosofi: Warren Buffett & Baron Rothschild**\n\n'Be fearful when others are greedy, and be greedy when others are fearful.' (Takutlah saat orang lain serakah, dan serakah lah saat orang lain takut/panik).")
        elif "Golden" in mode:
            st.info("📖 **Filosofi: John J. Murphy (Technical Analysis Bible)**\n\n'Trend is your friend. Golden Cross (MA50 memotong MA200) adalah sinyal objektif dimulainya tren bullish jangka panjang.'")
        elif "Akumulasi" in mode:
            st.info("📖 **Filosofi: Richard Wyckoff (The Composite Man)**\n\n'Pasar digerakkan oleh Smart Money. Jika harga datar tapi Volume meledak, itu tanda Paus sedang makan (Akumulasi). Ikutilah jejak Paus.'")
        elif "Volatilitas" in mode:
            st.info("📖 **Filosofi: Jesse Livermore (The Boy Plunger)**\n\n'Ada waktu untuk investasi, ada waktu untuk spekulasi. Saham yang bergerak liar dengan volume besar adalah tempat uang cepat dibuat (dan hilang).'")
        
        if mode != st.session_state['mode']:
            st.session_state['scan'] = None; st.session_state['mode'] = mode; st.rerun()
    
    with col_rad2:
        st.write(""); st.write("")
        if st.button("🚀 SCAN SEKARANG", type="primary", use_container_width=True):
            res = []
            bar = st.progress(0)
            for i, t in enumerate(IDX_TICKERS):
                bar.progress((i+1)/len(IDX_TICKERS))
                df, inf = get_hybrid_data(t)
                if df is not None:
                    C = df['Close'].iloc[-1]; C1 = df['Close'].iloc[-2]
                    O = df['Open'].iloc[-1]
                    H = df['High'].iloc[-1]; L = df['Low'].iloc[-1]
                    rsi = ta.rsi(df['Close'], 14).iloc[-1]
                    rsi_val = rsi if pd.notna(rsi) else 50
                    
                    # FUNDAMENTAL
                    roe = inf.get('returnOnEquity', 0) * 100 if inf else 0
                    per = inf.get('trailingPE', 999) if inf else 999
                    pbv = inf.get('priceToBook', 999) if inf else 999
                    if roe > 10: funda_stat = "🟢 PRIME"
                    elif roe > 0: funda_stat = "🟡 STD"
                    else: funda_stat = "🔴 JUNK"
                    if per < 15 or pbv < 1: val_stat = "🟢 MURAH"
                    elif per < 25: val_stat = "🟡 WAJAR"
                    else: val_stat = "🔴 MAHAL"

                    # TECHNICAL
                    vol_now = df['Volume'].iloc[-1]
                    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                    is_spike = (pd.notna(vol_avg) and vol_now > vol_avg * 1.25)
                    ma20 = df['Close'].rolling(20).mean().iloc[-1]
                    ma50 = df['Close'].rolling(50).mean().iloc[-1]
                    ma200 = df['Close'].rolling(200).mean().iloc[-1]
                    std = df['Close'].rolling(20).std().iloc[-1]
                    lower_bb = ma20 - (2 * std)
                    high_20 = df['High'].rolling(20).max().iloc[-1]

                    # SCORING
                    score = 0; rank_msg = "⚪ NEUTRAL"
                    
                    if "Swing" in mode: 
                        if pd.notna(ma50) and C > ma50:
                            if rsi_val < 60:
                                score = 2; rank_msg = "✅ BUY WEAKNESS"
                                if abs(C - ma20)/ma20 < 0.02 or is_spike: score = 3; rank_msg = "💎 PERFECT SWING"
                            else: score = 1; rank_msg = "⚡ EARLY TREND"

                    elif "Contrarian" in mode: 
                        if C < lower_bb:
                            score = 2; rank_msg = "✅ OVERSOLD"
                            if rsi_val < 30:
                                score = 3; rank_msg = "💎 REVERSAL"
                                if is_spike: score = 4; rank_msg = "🦈 SNIPER"
                        elif rsi_val < 30: score = 1; rank_msg = "⚡ RSI MURAH"

                    elif "SUPER" in mode:
                        is_uptrend = (pd.notna(ma50) and C > ma50)
                        if roe > 10: score += 1
                        if per < 20: score += 1
                        if rsi_val < 45: score += 1 
                        if is_uptrend: score += 1   
                        if is_spike: score += 2 
                        if score >= 5: rank_msg = "💎 DIAMOND"
                        elif score >= 4: rank_msg = "✅ GOLD"
                        elif score < 3: score = 0 

                    elif "Golden" in mode: 
                        if pd.notna(ma50) and pd.notna(ma200) and ma50 > ma200:
                            ma50_prev = df['Close'].rolling(50).mean().iloc[-5]
                            ma200_prev = df['Close'].rolling(200).mean().iloc[-5]
                            if ma50_prev <= ma200_prev: 
                                score = 2; rank_msg = "✅ GOLD FRESH"
                                if is_spike: score = 3; rank_msg = "💎 DIAMOND"
                            elif C > ma50: score = 1; rank_msg = "⚡ STRONG"

                    elif "Akumulasi" in mode:
                        price_change = abs((C - C1)/C1)
                        if is_spike:
                            if price_change < 0.02: 
                                score = 2; rank_msg = "✅ SILENT"
                                if vol_now > vol_avg * 2.0: score = 3; rank_msg = "💎 WHALE"
                            elif C > O: score = 1; rank_msg = "⚡ VOL FLOW"

                    elif "Volatilitas" in mode:
                        daily_range = ((H - L) / L) * 100
                        if daily_range > 2.0:
                            score = daily_range 
                            if daily_range > 4.0 and is_spike: rank_msg = "💎 LIAR+VOL"
                            elif daily_range > 4.0: rank_msg = "✅ LIAR"
                            elif daily_range > 3.0: rank_msg = "⚡ AKTIF"
                            else: score = 1; rank_msg = "⚪ GERAK"

                    elif "Turtle" in mode:
                        if C >= high_20:
                            score = 2; rank_msg = "✅ BREAKOUT 20D"
                            if is_spike: score = 3; rank_msg = "💎 STRONG BREAK"
                        elif C >= (high_20 * 0.98): score = 1; rank_msg = "⚡ NEAR HIGH"

                    if score > 0: 
                        chg = ((C-C1)/C1)*100
                        res.append({
                            "Stock": t.replace(".JK",""), 
                            "Price": int(C), 
                            "Chg%": chg,
                            "RSI": int(rsi_val),
                            "Funda": funda_stat, 
                            "Valuasi": val_stat,
                            "STATUS": rank_msg,
                            "Score": score
                        })
                        
            bar.empty()
            if res: 
                df_res = pd.DataFrame(res).sort_values(by="Score", ascending=False)
                df_res.reset_index(drop=True, inplace=True)
                df_res.index = df_res.index + 1 
                df_res['🏆 Peringkat'] = df_res.index.map(lambda x: "🥇 JUARA 1" if x==1 else ("🥈 JUARA 2" if x==2 else ("🥉 JUARA 3" if x==3 else f"#{x}")))
                
                cols = ['🏆 Peringkat', 'Stock', 'Price', 'Chg%', 'STATUS', 'Funda', 'Valuasi']
                st.session_state['scan'] = df_res[cols]
                
                csv = df_res.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Laporan (Excel/CSV)",
                    data=csv,
                    file_name=f'laporan_saham_{mode.split(" ")[0]}_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv',
                    type='secondary'
                )
            else: st.warning("Tidak ada saham sesuai kriteria.")

    # INTERACTIVE TABLE & EXECUTION BRIDGE
    if st.session_state.get('scan') is not None:
        event = st.dataframe(
            st.session_state['scan'], 
            column_config={
                "Chg%": st.column_config.NumberColumn("Chg%", format="%.2f%%"),
                "STATUS": st.column_config.TextColumn("Sinyal Teknikal", width="medium"),
                "Funda": st.column_config.TextColumn("🏢 Kualitas"),
                "Valuasi": st.column_config.TextColumn("🏷️ Valuasi")
            }, 
            hide_index=True, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        if len(event.selection["rows"]) > 0:
            selected_idx = event.selection["rows"][0]
            selected_ticker = st.session_state['scan'].iloc[selected_idx]['Stock']
            selected_price = st.session_state['scan'].iloc[selected_idx]['Price']
            if st.session_state['xray_ticker'] != selected_ticker:
                st.session_state['xray_ticker'] = selected_ticker
                st.rerun()

            st.markdown("---")
            c_btn1, c_btn2 = st.columns([1, 4])
            with c_btn1:
                if st.button(f"🧮 KIRIM {selected_ticker} KE KALKULATOR MM", type="primary"):
                    st.session_state['mm_ticker'] = selected_ticker
                    st.session_state['mm_price'] = selected_price
                    st.success(f"✅ {selected_ticker} masuk ke Tab EXECUTION! Silakan buka Tab 2.")

# --- TAB 2: EXECUTION (MM CALCULATOR) ---
with tab2:
    st.header("⚡ Money Management Calculator")
    st.caption("Pilar Terpenting: 2% Rule (Jangan pernah rugi >2% modal dalam 1 transaksi).")
    
    with st.container(border=True):
        col_in1, col_in2 = st.columns(2)
        
        def_ticker = st.session_state.get('mm_ticker', 'BBCA')
        def_price = st.session_state.get('mm_price', 10000)
        
        with col_in1:
            st.subheader("1. Setup Modal")
            modal = st.number_input("Modal Trading (Rp):", value=100_000_000, step=1_000_000, format="%d")
            risk_pct = st.slider("Resiko per Trade (%):", 1.0, 5.0, 2.0, 0.5)
            max_risk_rp = modal * (risk_pct / 100)
            st.info(f"🛡️ Batas Rugi Maksimal: **Rp {int(max_risk_rp):,}**")
            
        with col_in2:
            st.subheader(f"2. Setup Trade ({def_ticker})")
            entry = st.number_input("Harga Beli (Entry):", value=int(def_price), step=50)
            sl = st.number_input("Stop Loss (Cut Loss):", value=int(def_price * 0.95), step=50)
            sl_distance = entry - sl
            sl_pct = (sl_distance / entry) * 100 if entry > 0 else 0
            if sl >= entry: st.error("⚠️ Stop Loss harus di bawah Harga Beli!")
            else: st.write(f"📉 Jarak Stop Loss: **{int(sl_distance)} perak ({sl_pct:.1f}%)**")
                
        st.markdown("---")
        if sl < entry:
            max_shares = max_risk_rp / sl_distance
            max_lot = math.floor(max_shares / 100)
            total_modal_buy = max_lot * 100 * entry
            
            st.subheader("🏁 HASIL PERHITUNGAN (PLAN):")
            r1, r2, r3 = st.columns(3)
            with r1: st.metric("Jumlah Lot", f"{max_lot} Lot", f"Volume: {max_lot*100:,.0f} Lembar")
            with r2: st.metric("Modal Diperlukan", f"Rp {total_modal_buy:,.0f}", f"{ (total_modal_buy/modal)*100:.1f}% dari Modal")
            with r3: st.metric("Resiko Jika Cutloss", f"- Rp {int(max_lot * 100 * sl_distance):,.0f}", f"Tepat {risk_pct}% Modal")
            target_price = entry + (sl_distance * 2) 
            st.success(f"🎯 Target Profit (RR 1:2) disarankan di harga: **Rp {int(target_price):,}** (+Rp {int(max_lot * 100 * sl_distance * 2):,.0f})")

# --- TAB 3: PORTFOLIO ---
with tab3:
    st.header("🔐 Portfolio"); st.info("Fitur pencatatan portfolio (Coming Soon).")
