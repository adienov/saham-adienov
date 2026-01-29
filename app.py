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
# ⚙️ KONFIGURASI PENTING
# ==========================================
SECRET_PIN = "2026" 
TV_CHART_ID = "q94KuJTY" 
# 👇 MASUKKAN LINK GRUP WA DI BAWAH INI 👇
LINK_WA = "https://chat.whatsapp.com/IwsFmoVxlNPHy6Sc1vaAqd?mode=gi_t" 
# ==========================================

# FILES
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# UNIVERSE SAHAM (LQ45 + SYARIAH + TECH)
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

        return {"Stock": ticker.replace(".JK",""), "Price": close, "Trend": trend, "RSI": int(rsi), "Timing": timing, "Support": support, "Resistance": resistance, "TV": tv_url}
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

# --- GENERATOR TABEL HTML (PERBAIKAN TOTAL) ---
def render_html_table(df, title, bg_color, text_color, val_col):
    if df.empty: return ""
    
    # Membangun baris tabel satu per satu untuk menghindari error indentasi
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

    # Menyusun container utama
    html_code = f"""
    <div style='background-color:{bg_color}; border-radius:8px; padding:10px; margin-bottom:10px; border:1px solid {text_color};'>
        <div style='text-align:center; font-weight:bold; color:{text_color}; font-size:14px; margin-bottom:5px; text-transform:uppercase;'>{title}</div>
        <table style='width:100%; border-collapse:collapse; font-size:12px; background-color:rgba(255,255,255,0.7); border-radius:5px;'>
            <thead>
                <tr style='border-bottom:2px solid {text_color};'>
                    <th style='padding:5px; text-align:center;'>Emiten</th>
                    <th style='padding:5px; text-align:center;'>Nilai</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return html_code

# --- FETCH DATA ---
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

def generate_outlook_text(price, ma200, rsi):
    if pd.isna(price) or pd.isna(ma200) or pd.isna(rsi): return "Menunggu data teknikal..."
    trend = "**BULLISH (Naik)**" if price > ma200 else "**BEARISH (Turun)**"
    action = "Waspada Profit Taking." if rsi > 70 else "Potensi Rebound." if rsi < 30 else "Pasar Stabil."
    return f"Posisi IHSG saat ini {trend} terhadap MA200. Momentum RSI: {action}"

# --- DASHBOARD DISPLAY ---
def display_market_dashboard():
    ihsg_now, ihsg_chg, usd_now, ma200, rsi, commo, movers = fetch_dashboard_data()
    if ihsg_now is None:
        st.error("Gagal memuat data. Cek koneksi."); return

    c1, c2 = st.columns([2, 1])
    with c1: st.markdown("### 📊 MARKET DASHBOARD")
    with c2: 
        st.markdown(f"<div style='text-align:right; color:gray; font-size:12px;'>📅 {get_indo_date()}<br>⚠️ Data Delayed ~15 Min</div>", unsafe_allow_html=True)

    # METRICS ROW
    k1, k2, k3, k4 = st.columns(4)
    col_ihsg = "#d32f2f" if ihsg_chg < 0 else "#388e3c"
    
    with k1: st.markdown(f"<div style='text-align:center; background:#e3f2fd; padding:10px; border-radius:8px;'><b style='font-size:11px'>🇮🇩 IHSG</b><br><span style='font-size:18px'>{ihsg_now:,.0f}</span><br><span style='color:{col_ihsg}; font-size:12px'>{ihsg_chg:+.2f}%</span></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div style='text-align:center; background:#f1f8e9; padding:10px; border-radius:8px;'><b style='font-size:11px'>🇺🇸 USD/IDR</b><br><span style='font-size:18px'>Rp {usd_now:,.0f}</span><br><span style='color:#555; font-size:12px'>Rate</span></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div style='text-align:center; background:#fff8e1; padding:10px; border-radius:8px;'><b style='font-size:11px'>🥇 GOLD</b><br><span style='font-size:18px'>${commo['Gold']['Price']:,.0f}</span><br><span style='color:#555; font-size:12px'>{commo['Gold']['Chg']:.2f}%</span></div>", unsafe_allow_html=True)
    with k4: st.markdown(f"<div style='text-align:center; background:#eceff1; padding:10px; border-radius:8px;'><b style='font-size:11px'>🛢️ OIL</b><br><span style='font-size:18px'>${commo['Oil']['Price']:,.1f}</span><br><span style='color:#555; font-size:12px'>{commo['Oil']['Chg']:.2f}%</span></div>", unsafe_allow_html=True)

    st.write("")
    st.info(f"📢 **OUTLOOK:** {generate_outlook_text(ihsg_now, ma200, rsi)}")
    st.write("")

    # --- TABLES (FINAL VISUAL FIX) ---
    df_m = pd.DataFrame(movers)
    if not df_m.empty:
        g = df_m.sort_values(by="Chg", ascending=False).head(3)
        l = df_m.sort_values(by="Chg", ascending=True).head(3)
        v = df_m.sort_values(by="Vol", ascending=False).head(3)
        m = df_m.sort_values(by="Val", ascending=False).head(3)
        
        c_g, c_l, c_v, c_m = st.columns(4)
        # Panggil fungsi render_html_table yang sudah diperbaiki
        with c_g: st.markdown(render_html_table(g, "🏆 GAINERS", "#e8f5e9", "#2e7d32", "Chg"), unsafe_allow_html=True)
        with c_l: st.markdown(render_html_table(l, "🔻 LOSERS", "#ffebee", "#c62828", "Chg"), unsafe_allow_html=True)
        with c_v: st.markdown(render_html_table(v, "🔥 VOLUME", "#e3f2fd", "#1565c0", "Vol"), unsafe_allow_html=True)
        with c_m: st.markdown(render_html_table(m, "💰 VALUE", "#fff8e1", "#f9a825", "Val"), unsafe_allow_html=True)
    else: st.warning("Data market belum tersedia.")
    st.write("")

# --- 3. UI UTAMA ---
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

tab1, tab2, tab3 = st.tabs(["🔍 SCREENER", "⚡ EXECUTION", "🔐 PORTFOLIO"])

# TAB 1
with tab1:
    st.header("🕵️ X-Ray Saham")
    with st.container(border=True):
        c_in, c_btn = st.columns([3, 1])
        with c_in: txt_in = st.text_input("Cek Saham (Cth: BBCA, BREN):").upper()
        with c_btn: 
            st.write(""); st.write("")
            btn_cek = st.button("🔍 CEK", type="primary")
        
        if btn_cek and txt_in:
            with st.spinner("Analyzing..."):
                d_s, i_s = get_hybrid_data(txt_in)
                if d_s is not None:
                    cp = d_s['Close'].iloc[-1]; prev = d_s['Close'].iloc[-2]
                    chg = ((cp-prev)/prev)*100
                    ma200 = d_s['Close'].rolling(200).mean().iloc[-1]
                    tr = "UPTREND 🚀" if cp > ma200 else "DOWNTREND 📉"
                    st.metric(txt_in, f"Rp {int(cp):,}", f"{chg:.2f}%")
                    st.info(f"Trend: **{tr}** (vs MA200)")
                    st.markdown(f"[Chart TradingView]({TV_CHART_ID}/?symbol=IDX:{txt_in})")
                else: st.error("Saham tidak ditemukan.")
    
    st.markdown("---")
    st.header("📡 Radar Market")
    
    if 'mode' not in st.session_state: st.session_state['mode'] = "Radar Diskon (Market Crash)"
    mode = st.radio("Strategi:", ["Radar Diskon (Market Crash)", "Reversal (Pantulan)", "Breakout (Tren Naik)", "Swing (Koreksi Sehat)"], horizontal=True)
    
    if mode != st.session_state['mode']:
        st.session_state['scan'] = None; st.session_state['mode'] = mode; st.rerun()
    
    if st.button("🚀 SCAN SEKARANG", type="primary"):
        res = []
        bar = st.progress(0)
        for i, t in enumerate(IDX_TICKERS):
            bar.progress((i+1)/len(IDX_TICKERS))
            df, inf = get_hybrid_data(t)
            if df is not None:
                C = df['Close'].iloc[-1]; C1 = df['Close'].iloc[-2]
                rsi = ta.rsi(df['Close'], 14).iloc[-1]
                ok = False
                if "Diskon" in mode: ok = True
                elif "Reversal" in mode:
                    if rsi < 45 and C > df['Open'].iloc[-1]: ok = True
                elif "Breakout" in mode:
                    if C == df['High'].rolling(20).max().iloc[-1]: ok = True
                elif "Swing" in mode:
                    ma50 = df['Close'].rolling(50).mean().iloc[-1]
                    if C > ma50 and C > C1: ok = True
                
                if ok:
                    chg = ((C-C1)/C1)*100
                    roe = inf.get('returnOnEquity',0)*100 if inf else 0
                    tv = f"https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{t.replace('.JK','')}"
                    res.append({"Pilih":False, "Stock":t.replace(".JK",""), "Price":int(C), "Chg%":chg, "ROE":f"{roe:.1f}%", "RSI":int(rsi), "Chart":tv})
        bar.empty()
        if res: st.session_state['scan'] = pd.DataFrame(res)
        else: st.warning("Tidak ada saham sesuai kriteria.")

    if st.session_state.get('scan') is not None:
        edf = st.data_editor(st.session_state['scan'], column_config={"Chart": st.column_config.LinkColumn("View", display_text="📈")}, hide_index=True, use_container_width=True)
        if st.button("Simpan ke Watchlist"): st.success("Tersimpan!")

# TAB 2 & 3 DEFAULT
with tab2: st.header("⚡ Execution"); st.info("Fitur kalkulator lot.")
with tab3: st.header("🔐 Portfolio"); st.info("Fitur portfolio admin.")
