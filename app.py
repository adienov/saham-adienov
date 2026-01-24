import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Adienov Super Scanner", page_icon="📈", layout="wide")

# --- 2. LIST SAHAM (Bisa ditambah manual) ---
# Contoh 20 Saham Liquid (Bisa Bapak tambah jadi 100 atau semua Kompas100)
tickers = [
    "BBRI.JK", "BBCA.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "UNTR.JK", "ICBP.JK", 
    "INDF.JK", "KLBF.JK", "BRIS.JK", "ANTM.JK", "MDKA.JK", "PGAS.JK", "PTBA.JK", "ADRO.JK",
    "INKP.JK", "TPIA.JK", "GOTO.JK", "AMMN.JK", "BREN.JK", "CUAN.JK", "PTRO.JK", "PANI.JK"
]

# --- 3. SIDEBAR (PENGATURAN) ---
st.sidebar.header("⚙️ PENGATURAN ROBOT")

# A. PILIHAN STRATEGI (FITUR BARU)
strategi = st.sidebar.selectbox(
    "PILIH STRATEGI:",
    ("🟢 Reversal (Early Buy)", "🚀 Breakout (Uptrend)")
)

st.sidebar.divider()

# B. FILTER UMUM
min_transaksi = st.sidebar.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)

# C. SETTING KHUSUS
if strategi == "🟢 Reversal (Early Buy)":
    st.sidebar.info("Mencari saham yang baru mantul dari Garis Merah (Alligator).")
    toleransi = st.sidebar.slider("Jarak Toleransi (%)", 1.0, 10.0, 5.0)
else:
    st.sidebar.info("Mencari saham Uptrend yang menembus harga tertinggi 20 hari.")
    lookback = st.sidebar.slider("Periode Breakout (Hari)", 10, 60, 20) # Default 20 Hari (Turtle)

# --- 4. FUNGSI ANALISA ---
def analyze_stock(ticker, strategy_mode):
    try:
        # Ambil data agak panjang untuk hitung MA dan Breakout
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        if len(df) < 60: return None # Skip jika data kurang
        
        # Data Terakhir
        last_close = float(df['Close'].iloc[-1])
        last_open  = float(df['Open'].iloc[-1])
        last_vol   = float(df['Volume'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        
        # Hitung Transaksi Harian (Miliar)
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        transaksi_m = (last_close * avg_vol) / 1_000_000_000
        
        if transaksi_m < min_transaksi: return None
        
        # --- LOGIKA STRATEGI ---
        signal = False
        info_text = ""
        
        if strategy_mode == "🟢 Reversal (Early Buy)":
            # Rumus Alligator Simple (SMA 8 digeser)
            # Kita simulasi manual: Ambil SMA 8 dari data yang digeser 5 hari lalu
            # Agar sederhana di python, kita pakai SMA 13 sebagai pendekatan garis merah
            ma_red = df['Close'].rolling(window=13).mean().iloc[-1] 
            
            # Syarat: Harga di atas Garis Merah TAPI jaraknya dekat
            if last_close > ma_red:
                jarak = ((last_close - ma_red) / last_close) * 100
                if jarak <= toleransi:
                    signal = True
                    info_text = f"Jarak: {jarak:.1f}%"
                    
        elif strategy_mode == "🚀 Breakout (Uptrend)":
            # 1. Cek Uptrend (Harga di atas MA 50)
            ma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
            is_uptrend = last_close > ma_50
            
            # 2. Cek Breakout High (Harga Tertinggi N hari terakhir, exclude hari ini)
            # Kita pakai iloc[:-1] untuk melihat High H-1 ke belakang
            highest_price = df['High'].iloc[-lookback-1:-1].max()
            
            # Syarat: Uptrend DAN Harga Close Hari Ini > Highest Price Kemarin
            # DAN Volume meledak (> Rata2)
            is_breakout = last_close > highest_price
            is_volume   = last_vol > avg_vol
            
            if is_uptrend and is_breakout and is_volume:
                signal = True
                pct_break = ((last_close - highest_price) / highest_price) * 100
                info_text = f"Breakout +{pct_break:.1f}%"

        if signal:
            return {
                "Saham": ticker.replace(".JK", ""),
                "Harga": int(last_close),
                "Perubahan": f"{((last_close - prev_close)/prev_close)*100:.2f}%",
                "Volume (xAvg)": f"{last_vol/avg_vol:.1f}x",
                "Info Signal": info_text
            }
            
    except Exception as e:
        return None
    return None

# --- 5. TAMPILAN UTAMA ---
st.title(f"Adienov Scanner: {strategi}")
st.write("Robot pencari saham otomatis berdasarkan algoritma pilihan.")

if st.button("🔍 MULAI SCAN SEKARANG"):
    with st.status("Sedang memindai pasar... Mohon tunggu...", expanded=True) as status:
        results = []
        progress_bar = st.progress(0)
        
        for i, tick in enumerate(tickers):
            res = analyze_stock(tick, strategi)
            if res:
                results.append(res)
            # Update progress
            progress_bar.progress((i + 1) / len(tickers))
            
        status.update(label="Selesai!", state="complete", expanded=False)

    if len(results) > 0:
        st.success(f"Ditemukan {len(results)} Saham Potensial!")
        df_hasil = pd.DataFrame(results)
        st.dataframe(df_hasil, use_container_width=True)
    else:
        st.warning("Tidak ada saham yang memenuhi kriteria saat ini.")

# Footer
st.markdown("---")
st.caption("Developed by Adienov System")
