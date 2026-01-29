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

# --- MAIN UI ---
def display_market_dashboard():
    ihsg_now, ihsg_chg, usd_now, ma200, rsi, commo, movers = fetch_dashboard_data()
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

    # ROW 3: TABLES
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
    else: st.warning("Data market belum tersedia.")
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

# --- TAB 1: CHART + SCANNER ---
with tab1:
    # 1. CHART SECTION (FULL WIDTH)
    if 'xray_ticker' not in st.session_state: st.session_state['xray_ticker'] = "BBCA"
    
    st.subheader(f"📈 Chart Analisa: {st.session_state['xray_ticker']}")
    render_tv_widget(st.session_state['xray_ticker']) # Chart with AutoFib
    
    # Data Teknikal Singkat di Bawah Chart
    d_s = get_technical_detail(st.session_state['xray_ticker'])
    if d_s is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Harga", f"Rp {int(d_s['Price']):,}")
        c2.metric("RSI (Momentum)", f"{int(d_s['RSI'])}")
        c3.info(f"**{d_s['Trend']}**")
    
    st.markdown("---")
    
    # 2. SCANNER SECTION (INTERACTIVE)
    st.header("📡 Radar Market (Scanner)")
    st.caption("👇 **Klik baris pada tabel di bawah untuk melihat Chart di atas.**")
    
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
                O = df['Open'].iloc[-1]
                rsi = ta.rsi(df['Close'], 14).iloc[-1]
                rsi_val = rsi if pd.notna(rsi) else 50
                
                vol_now = df['Volume'].iloc[-1]
                vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                v_txt = "🔥 RAMAI" if (pd.notna(vol_avg) and vol_now > vol_avg * 1.5) else "😐 NORMAL"
                
                if rsi_val < 30: r_txt = f"{int(rsi_val)} (DISKON)"
                elif rsi_val > 70: r_txt = f"{int(rsi_val)} (MAHAL)"
                else: r_txt = f"{int(rsi_val)} (NETRAL)"

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
                        "RSI": r_txt
                    })
        bar.empty()
        if res: st.session_state['scan'] = pd.DataFrame(res)
        else: st.warning("Tidak ada saham sesuai kriteria.")

    # INTERACTIVE TABLE (KLIK BARIS -> UPDATE CHART)
    if st.session_state.get('scan') is not None:
        event = st.dataframe(
            st.session_state['scan'], 
            column_config={"Chg%": st.column_config.NumberColumn("Chg%", format="%.2f%%")}, 
            hide_index=True, 
            use_container_width=True,
            on_select="rerun", # FITUR KUNCI: RERUN SAAT DIKLIK
            selection_mode="single-row"
        )
        
        # LOGIC UPDATE CHART
        if len(event.selection["rows"]) > 0:
            selected_idx = event.selection["rows"][0]
            selected_ticker = st.session_state['scan'].iloc[selected_idx]['Stock']
            # Cek jika ticker berbeda, baru update (biar gak loop)
            if st.session_state['xray_ticker'] != selected_ticker:
                st.session_state['xray_ticker'] = selected_ticker
                st.rerun()

# TAB 2 & 3 DEFAULT
with tab2: st.header("⚡ Execution"); st.info("Fitur kalkulator lot lanjutan & Money Management.")
with tab3: st.header("🔐 Portfolio"); st.info("Fitur portfolio admin.")
