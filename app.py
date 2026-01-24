import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- KONFIGURASI TEMA ---
st.set_page_config(page_title="Adienov Mobile", layout="wide", initial_sidebar_state="collapsed")

# CSS: TAMPILAN KHUSUS HP (Mobile Friendly)
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        /* Perkecil Judul H1 */
        h1 { font-size: 1.5rem !important; padding-top: 0px !important; }
        /* Perkecil Subjudul */
        div[data-testid="stCaptionContainer"] { font-size: 0.8rem; }
        /* Tombol Scan Lebih Menonjol */
        div.stButton > button { width: 100%; border-radius: 20px; font-weight: bold; background-color: #007BFF; color: white !important;}
        /* Tabel Lebih Kompak */
        div[data-testid="stDataFrame"] { font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER VERSI MOBILE ---
st.title("📱 Adienov Scanner V3")
st.caption("Alligator Strategy • Mobile Optimized")

# --- PETUNJUK TOMBOL TERSEMBUNYI ---
# Ini untuk menjawab keluhan "Fitur ubah screening tersembunyi"
st.info("⚙️ **PENGATURAN:** Klik tanda panah **( > )** di pojok kiri atas layar untuk mengubah Filter (Min Transaksi & Risiko).")

# --- SIDEBAR (INPUT) ---
with st.sidebar:
    st.header("⚙️ Filter Scanner")
    min_trans = st.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
    risk_tol = st.slider("Batas Early Trend (%)", 1.0, 10.0, 5.0)
    st.markdown("---")
    st.caption("Tips: Geser layar ke kanan/kiri pada tabel hasil scan untuk melihat kolom lengkap.")

# --- DATABASE SAHAM ---
tickers = [
    "ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK",
    "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK",
    "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK",
    "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"
]

# --- FUNGSI SCAN ---
@st.cache_data(ttl=60) # Cache 60 detik agar tidak berat di HP
def scan_market(min_val_m, risk_pct):
    results = []
    # Progress Bar Sederhana
    text_progress = st.empty()
    bar_progress = st.progress(0)
    
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        # Update teks progress
        text_progress.text(f"Scanning {ticker.replace('.JK','')}... ({i+1}/{total})")
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

            results.append({
                "Emiten": ticker.replace(".JK", ""), # Nama kolom dipersingkat agar muat di HP
                "Harga": int(current_close),
                "GarisMerah": int(red_line),
                "Status": status,
                "Jarak%": round(diff, 1),
                "Val(M)": round(avg_val, 1)
            })
        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    return pd.DataFrame(results)

# --- TOMBOL UTAMA ---
if st.button("🔍 MULAI SCAN SEKARANG"):
    with st.spinner('Sedang memindai...'):
        waktu_skrg = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M WIB")
        df = scan_market(min_trans, risk_tol)
        
        if not df.empty:
            st.success(f"✅ Update: {waktu_skrg}")
            
            # HASIL 1: EARLY
            df_early = df[df['Status'].str.contains("EARLY")]
            if not df_early.empty:
                st.subheader("🔥 Rekomendasi: BUY")
                st.dataframe(
                    df_early.style.background_gradient(subset=['Jarak%'], cmap="Greens")
                    .format({"Harga": "{:.0f}", "GarisMerah": "{:.0f}", "Jarak%": "{:.1f}", "Val(M)": "{:.1f}"}),
                    use_container_width=True, hide_index=True
                )
            else: st.info("Tidak ada saham Early Trend.")

            # HASIL 2: EXTENDED
            df_ext = df[df['Status'].str.contains("EXTENDED")]
            if not df_ext.empty:
                with st.expander("⚠️ Lihat Saham Extended (Rawan)"):
                    st.dataframe(
                        df_ext.style.format({"Harga": "{:.0f}", "GarisMerah": "{:.0f}", "Jarak%": "{:.1f}", "Val(M)": "{:.1f}"}), 
                        use_container_width=True, hide_index=True
                    )
        else: st.error("Data tidak ditemukan.")
