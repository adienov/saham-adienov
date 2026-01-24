import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. KONFIGURASI HALAMAN (MOBILE FRIENDLY) ---
st.set_page_config(page_title="Adienov Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS: Tampilan Rapi di HP + Judul Kecil
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-top: 10px !important; }
        div[data-testid="stCaptionContainer"] { font-size: 0.8rem; }
        div.stButton > button { width: 100%; border-radius: 20px; background-color: #007BFF; color: white !important; font-weight: bold;}
        div[data-testid="stDataFrame"] { font-size: 12px; }
        /* Warna Status Spesifik */
        .turtle { color: #800080; font-weight: bold; } /* Ungu untuk Turtle */
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER & INPUT ---
st.title("📱 Adienov Scanner V4")
st.caption("Alligator Trend + 🐢 Turtle Breakout")

st.info("⚙️ **SETTING:** Klik panah **( > )** di kiri atas untuk filter.")

with st.sidebar:
    st.header("⚙️ Filter Scanner")
    min_trans = st.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
    risk_tol = st.slider("Toleransi Alligator (%)", 1.0, 10.0, 5.0)
    turtle_day = st.slider("Periode Turtle (Hari)", 10, 50, 20, help="Breakout High selama X hari terakhir")
    st.markdown("---")
    st.caption("Tips: Kolom 'Chart' bisa diklik untuk buka TradingView.")

# --- 3. DATABASE SAHAM ---
tickers = [
    "ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK",
    "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK",
    "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK",
    "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"
]

# --- 4. FUNGSI SCANNER (ALLIGATOR + TURTLE) ---
@st.cache_data(ttl=60)
def scan_market(min_val_m, risk_pct, turtle_window):
    results = []
    text_progress = st.empty()
    bar_progress = st.progress(0)
    
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        text_progress.text(f"Scanning {ticker.replace('.JK','')}... ({i+1}/{total})")
        try:
            # Ambil Data
            df = yf.download(ticker, period="6mo", progress=False) # Period lebih panjang untuk Turtle
            if df.empty or len(df) < turtle_window + 5: continue
            try:
                if isinstance(df.columns, pd.MultiIndex): df = df.xs(ticker, level=1, axis=1)
            except: pass

            # A. LOGIKA ALLIGATOR
            df['HL2'] = (df['High'] + df['Low']) / 2
            df['Teeth_Raw'] = df.ta.sma(close='HL2', length=8)
            current_close = float(df['Close'].iloc[-1])
            red_line = float(df['Teeth_Raw'].iloc[-6]) if not pd.isna(df['Teeth_Raw'].iloc[-6]) else 0
            
            # B. LOGIKA TURTLE BREAKOUT (Harga Tertinggi X Hari Terakhir)
            # Kita geser 1 hari sebelumnya agar breakout dihitung hari ini
            high_rolling = df['High'].rolling(window=turtle_window).max().shift(1)
            breakout_level = float(high_rolling.iloc[-1])

            # C. LOGIKA VOLUME
            avg_val = (current_close * df['Volume'].mean()) / 1000000000 
            if avg_val < min_val_m: continue

            # D. PENENTUAN STATUS
            status = ""
            priority = 0 # Untuk urutan sort

            # Cek Turtle Dulu (Prioritas Tertinggi)
            if current_close > breakout_level:
                status = "🐢 TURTLE BO"
                priority = 1
                diff = ((current_close - breakout_level) / breakout_level) * 100 # Jarak dari titik breakout
            # Cek Alligator Early
            elif current_close > red_line:
                diff_alli = ((current_close - red_line) / current_close) * 100
                if diff_alli <= risk_pct:
                    status = "🟢 EARLY"
                    priority = 2
                    diff = diff_alli
                else:
                    status = "⚠️ EXTENDED"
                    priority = 3
                    diff = diff_alli
            else:
                status = "🔴 DOWN"
                priority = 4
                diff = ((red_line - current_close) / current_close) * 100

            # E. LINK TRADINGVIEW
            tv_link = f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"

            results.append({
                "Emiten": ticker.replace(".JK", ""),
                "Harga": int(current_close),
                "Status": status,
                "Jarak%": round(diff, 1),
                "Val(M)": round(avg_val, 1),
                "Chart": tv_link, # Kolom Link
                "Priority": priority
            })

        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    
    # Sortir: Turtle -> Early -> Extended
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["Priority", "Jarak%"], ascending=[True, True])
    
    return df_res

# --- 5. TAMPILAN UTAMA ---
if st.button("🔍 MULAI SCAN (TURTLE + ALLIGATOR)"):
    with st.spinner('Sedang analisa pasar...'):
        waktu_skrg = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M WIB")
        df = scan_market(min_trans, risk_tol, turtle_day)
        
        if not df.empty:
            st.success(f"✅ Update: {waktu_skrg}")
            
            # FITUR KOLOM LINK (Penting!)
            column_config = {
                "Chart": st.column_config.LinkColumn(
                    "Buka Chart", 
                    help="Klik untuk buka TradingView", 
                    display_text="📈 Buka"
                ),
                "Jarak%": st.column_config.NumberColumn(
                    "Risk/Jarak%",
                    format="%.1f %%"
                )
            }

            # TAMPILKAN HASIL (Semua jadi satu tabel agar rapi, diurutkan prioritas)
            # Kita filter yang layak beli saja (Turtle & Early)
            df_buy = df[df['Status'].str.contains("TURTLE|EARLY")]
            
            if not df_buy.empty:
                st.subheader("🔥 Rekomendasi: BUY")
                st.dataframe(
                    df_buy.drop(columns=['Priority']), # Buang kolom bantuan
                    column_config=column_config,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Tidak ada sinyal Buy (Turtle/Early) saat ini.")

            # MONITORING EXTENDED (Opsional)
            df_ext = df[df['Status'].str.contains("EXTENDED")]
            if not df_ext.empty:
                with st.expander("⚠️ Saham Extended (Rawan)"):
                    st.dataframe(
                        df_ext.drop(columns=['Priority']),
                        column_config=column_config,
                        use_container_width=True,
                        hide_index=True
                    )
        else:
            st.error("Data tidak ditemukan atau koneksi error.")
