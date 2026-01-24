
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

st.set_page_config(page_title="Adienov Trading", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        div[data-testid="stSidebar"] { background-color: #F8F9FA; }
        h1, h2, h3, p, span, div, li { color: #212529 !important; }
        div[data-testid="stDataFrame"] { font-size: 14px; }
        div.stButton > button { background-color: #007BFF; color: white !important; font-weight: bold; }
        div[data-testid="stAlert"] { padding: 10px; border-radius: 5px; }
        div[data-testid="stExpander"] { background-color: #E9ECEF; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Adienov Trading System")
st.caption("Personalized Screener: Alligator + Risk Management")

with st.expander("📖 PANDUAN: CARA BACA & TINDAKAN (Klik Disini)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Arti Status")
        st.markdown("* **🟢 EARLY (Aman):** Jarak < 5%. **BUY.**\n* **⚠️ EXTENDED (Rawan):** Jarak > 5%. **WAIT.**\n* **🔴 DOWN (Bahaya):** Harga di bawah Garis Merah. **CASH.**")
    with c2:
        st.subheader("2. SOP Harian")
        st.markdown("1. Scan malam hari.\n2. Catat saham **EARLY**.\n3. Cek chart TradingView besok pagi.")

st.divider()

with st.sidebar:
    st.header("⚙️ Filter")
    min_trans = st.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
    risk_tol = st.slider("Batas Early Trend (%)", 1.0, 10.0, 5.0)

tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK", "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"]

def scan_market(min_val_m, risk_pct):
    results = []
    progress_bar = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, period="3mo", progress=False)
            if df.empty or len(df) < 20: continue
            try:
                if isinstance(df.columns, pd.MultiIndex): df = df.xs(ticker, level=1, axis=1)
            except: pass
            df['HL2'] = (df['High'] + df['Low']) / 2
            df['Teeth_Raw'] = df.ta.sma(close='HL2', length=8)
            if pd.isna(df['Teeth_Raw'].iloc[-6]) or pd.isna(df['Close'].iloc[-1]): continue
            current_close = float(df['Close'].iloc[-1])
            red_line = float(df['Teeth_Raw'].iloc[-6])
            avg_val = (current_close * df['Volume'].mean()) / 1000000000 
            if avg_val < min_val_m: continue
            status = ""
            if current_close > red_line:
                diff = ((current_close - red_line) / current_close) * 100
                if diff <= risk_pct: status = "🟢 EARLY"
                else: status = "⚠️ EXTENDED"
            else:
                diff = ((red_line - current_close) / current_close) * 100
                status = "🔴 DOWN"
            results.append({ "Saham": ticker.replace(".JK", ""), "Harga": int(current_close), "Garis Merah": int(red_line), "Status": status, "Jarak (%)": round(diff, 1), "Val (M)": round(avg_val, 1) })
        except: continue
        progress_bar.progress((i + 1) / len(tickers))
    progress_bar.empty()
    return pd.DataFrame(results)

if st.button("🔍 MULAI SCAN SEKARANG", type="primary"):
    with st.spinner('Sedang memindai pasar...'):
        waktu_skrg = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %B %Y, Pukul %H:%M:%S WIB")
        df = scan_market(min_trans, risk_tol)
        if not df.empty:
            st.success(f"✅ **DATA VALID & TERBARU** | Di-scan pada: **{waktu_skrg}**")
            st.subheader("🔥 Rekomendasi: EARLY BUY")
            df_early = df[df['Status'].str.contains("EARLY")]
            if not df_early.empty: st.dataframe(df_early.style.background_gradient(subset=['Jarak (%)'], cmap="Greens").format({"Harga": "{:.0f}", "Garis Merah": "{:.0f}", "Jarak (%)": "{:.1f}", "Val (M)": "{:.1f} M"}), use_container_width=True, hide_index=True)
            else: st.info("Belum ada saham Early Trend.")
            st.subheader("⚠️ Waspada: EXTENDED")
            df_ext = df[df['Status'].str.contains("EXTENDED")]
            if not df_ext.empty: st.dataframe(df_ext.style.format({"Harga": "{:.0f}", "Garis Merah": "{:.0f}", "Jarak (%)": "{:.1f}", "Val (M)": "{:.1f} M"}), use_container_width=True, hide_index=True)
        else: st.error("Data tidak ditemukan.")
    
