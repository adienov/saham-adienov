import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING IDENTITAS & KONFIGURASI ---
st.set_page_config(
    page_title="NOVA QUANTUM",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
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
        close = int(df['Close'].iloc[-1])
        ma50 = int(df['Close'].rolling(50).mean().iloc[-1] if pd.notna(df['Close'].rolling(50).mean().iloc[-1]) else 0)
        ma200 = int(df['Close'].rolling(200).mean().iloc[-1] if pd.notna(df['Close'].rolling(200).mean().iloc[-1]) else 0)
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        if ma200 > 0:
            trend = f"🚀 Strong Uptrend" if close > ma50 and ma50 > ma200 else (f"📈 Uptrend" if close > ma200 else "📉 Downtrend")
        else:
            trend = "⚠️ Data Terbatas"

        return {"Stock": ticker.replace(".JK",""), "Price": close, "Trend": trend, "RSI": rsi, "MA200": ma200}
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
    return f"{days[now.strftime('%A')]}, {now.strftime('%d')} {months[now.strftime('%B')]} {now.strftime('%Y')}"

def format_large_number(num):
    if num >= 1_000_000_000_000: return f"{num/1_000_000_000_000:.1f}T"
    if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}M"
    if num >= 1_000_000: return f"{num/1_000_000:.1f}jt"
    return str(int(num))

# --- WIDGET CHART (DENGAN AUTO FIBONACCI) ---
def render_tv_widget(symbol):
    html_code = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 600,
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
        "studies": [
          "MASimple@tv-basicstudies",
          "RSI@tv-basicstudies",
          "AutoFib@tv-basicstudies" 
        ],
        "hide_side_toolbar": false
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=610)

# --- FETCH DASHBOARD DATA ---
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
        
        return ihsg_now, ihsg_chg, usd_now, ma200_ihsg, rsi_ihsg, commo_data
    except: return None, None, None, None, None, None

def generate_outlook_text(price, ma200, rsi):
    if pd.isna(price) or pd.isna(ma200) or pd.isna(rsi): return "Menunggu data teknikal..."
    trend = "**BULLISH (Naik)**" if price > ma200 else "**BEARISH (Turun)**"
    action = "Waspada Profit Taking." if rsi > 70 else "Potensi Rebound." if rsi < 30 else "Pasar Stabil."
    return f"Posisi IHSG saat ini {trend} terhadap MA200. Momentum RSI: {action}"

# --- MAIN UI ---
def display_market_dashboard():
    ihsg_now, ihsg_chg, usd_now, ma200, rsi, commo = fetch_dashboard_data()
    if ihsg_now is None: st.error("Gagal memuat data. Cek koneksi."); return

    c1, c2 = st.columns([2, 1])
    with c1: st.markdown("### 📊 MARKET DASHBOARD")
    with c2: st.markdown(f"<div style='text-align:right; color:gray; font-size:12px;'>📅 {get_indo_date()}<br>⚠️ Data Delayed ~15 Min</div>", unsafe_allow_html=True)

    # ROW 1: METRICS
    k1, k2, k3, k4 = st.columns(4)
    col_ihsg = "#d32f2f" if ihsg_chg < 0 else "#388e3c"
    with k1: st.markdown(f"<div style='text-align:center; background:#e3f2fd; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🇮🇩 IHSG</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{ihsg_now:,.0f}</span><br><span style='color:{col_ihsg}; font-size:16px; font-weight:bold;'>{ihsg_chg:+.2f}%</span></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div style='text-align:center; background:#f1f8e9; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🇺🇸 USD/IDR</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{int(usd_now):,.0f}</span><br><span style='color:#555; font-size:16px;'>Rupiah</span></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div style='text-align:center; background:#fff8e1; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🥇 GOLD</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{int(commo['Gold']['Price']):,.0f}</span><br><span style='color:#555; font-size:16px;'>USD/Oz</span></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div style='text-align:center; background:#eceff1; padding:15px; border-radius:10px;'><b style='font-size:14px; color:#555;'>🛢️ OIL</b><br><span style='font-size:36px; font-weight:bold; color:#000;'>{commo['Oil']['Price']:,.1f}</span><br><span style='color:#555; font-size:16px;'>USD/Bbl</span></div>", unsafe_allow_html=True)

    st.write("")
    st.info(f"📢 **OUTLOOK:** {generate_outlook_text(ihsg_now, ma200, rsi)}")
    st.write("")

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

tab1, tab2, tab3 = st.tabs(["🔍 SCREENER & ANALYST", "⚡ EXECUTION", "🔐 PORTFOLIO"])

# --- TAB 1: CHART + SCANNER (INTERACTIVE) ---
with tab1:
    # 1. KOTAK INPUT (KEMBALI DI ATAS)
    with st.container(border=True):
        col_in, col_btn = st.columns([3, 1])
        with col_in:
            if 'xray_ticker' not in st.session_state: st.session_state['xray_ticker'] = "BBCA"
            txt_in = st.text_input("X-Ray Saham (Ketik Kode Manual):", value=st.session_state['xray_ticker']).upper()
        with col_btn:
            st.write(""); st.write("")
            if st.button("🔍 ANALISA CHART", type="primary", use_container_width=True):
                st.session_state['xray_ticker'] = txt_in

    # 2. CHART SECTION (FULL WIDTH)
    st.markdown(f"### 📈 Chart: {st.session_state['xray_ticker']}")
    render_tv_widget(st.session_state['xray_ticker']) # Chart with AutoFib
    
    # 3. INFO SECTION (DI BAWAH CHART)
    d_s = get_technical_detail(st.session_state['xray_ticker'])
    if d_s is not None:
        cp = d_s['Price']
        rsi_disp = str(int(d_s['RSI'])) if pd.notna(d_s['RSI']) else "N/A"
        ma200_disp = str(int(d_s['MA200'])) if pd.notna(d_s['MA200']) and d_s['MA200'] > 0 else "-"
        st.info(f"**Data {st.session_state['xray_ticker']}:** Harga Rp {int(cp):,} | Trend: **{d_s['Trend']}** | RSI: {rsi_disp} | MA200: {ma200_disp}")
    
    st.markdown("---")
    
    # 4. SCANNER SECTION (INTERACTIVE TABLE)
    st.header("📡 Radar Market (Scanner)")
    st.caption("👇 **KLIK PADA BARIS TABEL** untuk melihat Chart Saham tersebut di atas.")
    
    col_rad1, col_rad2 = st.columns([3, 1])
    with col_rad1:
        if 'mode' not in st.session_state: st.session_state['mode'] = "Radar Diskon (Market Crash)"
        mode = st.radio("Strategi:", ["Radar Diskon (Market Crash)", "Reversal (Pantulan)", "Breakout (Tren Naik)", "Swing (Koreksi Sehat)"], horizontal=True)
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
                    # Basic Data
                    C = df['Close'].iloc[-1]; C1 = df['Close'].iloc[-2]
                    O = df['Open'].iloc[-1]
                    rsi = ta.rsi(df['Close'], 14).iloc[-1]
                    rsi_val = rsi if pd.notna(rsi) else 50
                    
                    # Volume Logic
                    vol_now = df['Volume'].iloc[-1]
                    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                    v_ratio = vol_now/vol_avg if (pd.notna(vol_avg) and vol_avg > 0) else 0
                    v_txt = "🔥 RAMAI" if v_ratio > 1.5 else "😐 NORMAL"
                    
                    # RSI Logic
                    if rsi_val < 30: r_txt = "DISKON"
                    elif rsi_val < 45: r_txt = "MURAH"
                    elif rsi_val > 70: r_txt = "MAHAL"
                    else: r_txt = "NETRAL"

                    ok = False
                    if "Diskon" in mode: ok = True
                    elif "Reversal" in mode:
                        if rsi_val < 45 and C > O: ok = True
                    elif "Breakout" in mode:
                        if C == df['High'].rolling(20).max().iloc[-1]: ok = True
                    elif "Swing" in mode:
                        ma50 = df['Close'].rolling(50).mean().iloc[-1]
                        if pd.notna(ma50) and C > ma50 and C > C1: ok = True
                    
                    if ok:
                        chg = ((C-C1)/C1)*100
                        res.append({
                            "Stock": t.replace(".JK",""), 
                            "Price": int(C), 
                            "Chg%": chg,
                            "Vol": v_txt,
                            "RSI": r_txt,
                            "Signal": mode.split(" ")[0]
                        })
                        
            bar.empty()
            if res: st.session_state['scan'] = pd.DataFrame(res)
            else: st.warning("Tidak ada saham sesuai kriteria.")

    # TAMPILKAN TABEL INTERAKTIF
    if st.session_state.get('scan') is not None:
        event = st.dataframe(
            st.session_state['scan'], 
            column_config={
                "Chg%": st.column_config.NumberColumn("Chg%", format="%.2f%%"),
                "Price": st.column_config.NumberColumn("Harga", format="Rp %d")
            }, 
            hide_index=True, 
            use_container_width=True,
            on_select="rerun", # WAJIB UNTUK INTERAKTIVITAS
            selection_mode="single-row"
        )
        
        # LOGIC GANTI CHART SAAT KLIK
        if len(event.selection["rows"]) > 0:
            selected_idx = event.selection["rows"][0]
            selected_ticker = st.session_state['scan'].iloc[selected_idx]['Stock']
            # Cek agar tidak looping rerun
            if st.session_state['xray_ticker'] != selected_ticker:
                st.session_state['xray_ticker'] = selected_ticker
                st.rerun()

# TAB 2 & 3 DEFAULT
with tab2: st.header("⚡ Execution"); st.info("Fitur kalkulator lot lanjutan & Money Management.")
with tab3: st.header("🔐 Portfolio"); st.info("Fitur portfolio admin.")
