import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Adienov Super Scanner", page_icon="📈", layout="wide")

# --- 2. DATABASE SAHAM (DIPERLUAS KE 50+ SAHAM LIQUID) ---
# Kombinasi Bluechip, Second Liner, dan Saham Volatil
tickers = [
    # PERBANKAN
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "BBTN.JK", "ARTO.JK", "BNGA.JK",
    # TAMBANG & ENERGI
    "ADRO.JK", "PTBA.JK", "ITMG.JK", "PGAS.JK", "ANTM.JK", "INCO.JK", "MDKA.JK", "HRUM.JK",
    "MEDC.JK", "AKRA.JK", "AMMN.JK", "BREN.JK", "CUAN.JK", "PTRO.JK", "PANI.JK", "TPIA.JK",
    # KONSUMER & RITEL
    "ICBP.JK", "INDF.JK", "UNVR.JK", "MYOR.JK", "AMRT.JK", "MIDI.JK", "ACES.JK", "MAPI.JK",
    # TELCO & TECH
    "TLKM.JK", "ISAT.JK", "EXCL.JK", "GOTO.JK", "BUKA.JK", "EMTK.JK", 
    # OTOMOTIF & PROPERTI
    "ASII.JK", "UNTR.JK", "SMRA.JK", "BSDE.JK", "CTRA.JK", "PWON.JK",
    # KESEHATAN & LAINNYA
    "KLBF.JK", "MIKA.JK", "HEAL.JK", "SIDO.JK", "BRPT.JK", "INKP.JK", "TKIM.JK", "JPFA.JK", "CPIN.JK"
]

# --- 3. SIDEBAR (PENGATURAN) ---
st.sidebar.header("⚙️ PENGATURAN ROBOT")

strategi = st.sidebar.selectbox(
    "PILIH STRATEGI:",
    ("🟢 Reversal (Early Buy)", "🚀 Breakout (Uptrend)")
)

st.sidebar.divider()

# A. FILTER UMUM (Default diturunkan jadi 1M biar lebih banyak hasil)
min_transaksi = st.sidebar.number_input("Min. Transaksi (Miliar)", value=1.0, step=0.5)

# B. SETTING KHUSUS
if strategi == "🟢 Reversal (Early Buy)":
    st.sidebar.info("Mencari saham yang baru mantul dari Garis Merah (Alligator).")
    # Default dinaikkan jadi 10% agar lebih longgar
    toleransi = st.sidebar.slider("Jarak Toleransi (%)", 1.0, 15.0, 8.0) 
else:
    st.sidebar.info("Mencari saham Uptrend yang menembus harga tertinggi.")
    lookback = st.sidebar.slider("Periode Breakout (Hari)", 5, 60, 20)

# --- 4. FUNGSI ANALISA ---
def analyze_stock(ticker, strategy_mode):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 60: return None
        
        # Bersihkan Multi-Index jika ada (Masalah umum yfinance baru)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ambil Data
        last_close = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        last_vol   = float(df['Volume'].iloc[-1])
        
        # Hitung Transaksi (Miliar)
        avg_vol_20 = df['Volume'].rolling(20).mean().iloc[-1]
        transaksi_m = (last_close * avg_vol_20) / 1_000_000_000
        
        # Filter Transaksi
        if transaksi_m < min_transaksi: return None
        
        signal = False
        info_text = ""
        
        # --- LOGIKA 1: REVERSAL (EARLY BUY) ---
        if strategy_mode == "🟢 Reversal (Early Buy)":
            # Kita pakai MA 13 sebagai pendekatan Alligator Lips/Teeth
            ma_red = df['Close'].rolling(window=13).mean().iloc[-1]
            
            # Syarat: Close > MA (Uptrend)
            if last_close > ma_red:
                jarak = ((last_close - ma_red) / last_close) * 100
                
                # Syarat: Jarak tidak boleh kejauhan (Sesuai Slider Toleransi)
                if jarak <= toleransi:
                    signal = True
                    info_text = f"Jarak ke MA: {jarak:.1f}% (Aman)"
        
        # --- LOGIKA 2: BREAKOUT ---
        elif strategy_mode == "🚀 Breakout (Uptrend)":
            # Cari harga tertinggi N hari ke belakang (tidak termasuk hari ini)
            highest_prev = df['High'].iloc[-lookback-1:-1].max()
            
            # Syarat: Close hari ini > Harga Tertinggi Kemarin
            if last_close > highest_prev:
                signal = True
                pct_break = ((last_close - highest_prev) / highest_prev) * 100
                info_text = f"Breakout +{pct_break:.1f}% dari High {lookback} Hari"

        if signal:
            return {
                "Saham": ticker.replace(".JK", ""),
                "Harga": int(last_close),
                "Chg%": f"{((last_close - prev_close)/prev_close)*100:.2f}%",
                "Vol (xAvg)": f"{last_vol/avg_vol_20:.1f}x",
                "Transaksi": f"{transaksi_m:.1f} M",
                "Keterangan": info_text
            }
            
    except Exception as e:
        return None
    return None

# --- 5. TAMPILAN UTAMA ---
st.title(f"Adienov Scanner V2: {strategi}")

if st.button("🔍 MULAI SCAN (LIST LEBIH BANYAK)"):
    with st.status("Memindai 50+ Saham Pilihan... Sabar ya Pak...", expanded=True) as status:
        results = []
        progress_bar = st.progress(0)
        
        for i, tick in enumerate(tickers):
            res = analyze_stock(tick, strategi)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(tickers))
            
        status.update(label="Selesai!", state="complete", expanded=False)

    if len(results) > 0:
        st.success(f"Alhamdulillah! Ditemukan {len(results)} Saham.")
        df_hasil = pd.DataFrame(results)
        # Menampilkan tabel dengan format yang rapi
        st.dataframe(
            df_hasil, 
            column_config={
                "Harga": st.column_config.NumberColumn(format="Rp %d"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(f"Masih Kosong Pak. Pasar lagi sepi atau filter terlalu ketat.")
        st.info("💡 TIPS: Coba geser slider 'Toleransi' ke kanan atau turunkan 'Min. Transaksi'.")

st.markdown("---")
st.caption("Developed by Adienov System | Data by Yahoo Finance")
