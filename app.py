import streamlit as st
import pandas as pd
import yfinance as yf

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Adienov Super Scanner", page_icon="📈", layout="wide")

# --- 2. DATABASE SAHAM (50+ SAHAM) ---
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

# A. FILTER UMUM
min_transaksi = st.sidebar.number_input("Min. Transaksi (Miliar)", value=1.0, step=0.5)

# B. SETTING KHUSUS
if strategi == "🟢 Reversal (Early Buy)":
    st.sidebar.info("Mencari saham yang baru mantul dari Garis Merah (Alligator).")
    toleransi = st.sidebar.slider("Jarak Toleransi (%)", 1.0, 15.0, 8.0) 
else:
    st.sidebar.info("Mencari saham Uptrend yang menembus harga tertinggi.")
    lookback = st.sidebar.slider("Periode Breakout (Hari)", 5, 60, 20)

# --- 4. FUNGSI ANALISA ---
def analyze_stock(ticker, strategy_mode):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 60: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ambil Data
        last_close = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        last_vol   = float(df['Volume'].iloc[-1])
        
        avg_vol_20 = df['Volume'].rolling(20).mean().iloc[-1]
        transaksi_m = (last_close * avg_vol_20) / 1_000_000_000
        
        if transaksi_m < min_transaksi: return None
        
        signal = False
        info_text = ""
        
        # LOGIKA STRATEGI
        if strategy_mode == "🟢 Reversal (Early Buy)":
            ma_red = df['Close'].rolling(window=13).mean().iloc[-1]
            if last_close > ma_red:
                jarak = ((last_close - ma_red) / last_close) * 100
                if jarak <= toleransi:
                    signal = True
                    info_text = f"Jarak aman: {jarak:.1f}%"
        
        elif strategy_mode == "🚀 Breakout (Uptrend)":
            highest_prev = df['High'].iloc[-lookback-1:-1].max()
            if last_close > highest_prev:
                signal = True
                pct_break = ((last_close - highest_prev) / highest_prev) * 100
                info_text = f"Breakout +{pct_break:.1f}%"

        if signal:
            # BERSIHKAN KODE SAHAM UNTUK LINK
            clean_ticker = ticker.replace(".JK", "")
            # BUAT LINK TRADINGVIEW
            tv_link = f"https://www.tradingview.com/chart/?symbol=IDX:{clean_ticker}"
            
            return {
                "Saham": clean_ticker,
                "Harga": int(last_close),
                "Chg%": f"{((last_close - prev_close)/prev_close)*100:.2f}%",
                "Vol (xAvg)": f"{last_vol/avg_vol_20:.1f}x",
                "Keterangan": info_text,
                "Link": tv_link  # Kolom ini nanti kita ubah jadi tombol
            }
            
    except Exception as e:
        return None
    return None

# --- 5. TAMPILAN UTAMA ---
st.title(f"Adienov Scanner V3: Auto-Link")

if st.button("🔍 MULAI SCAN SEKARANG"):
    with st.status("Sedang mencari peluang...", expanded=True) as status:
        results = []
        progress_bar = st.progress(0)
        
        for i, tick in enumerate(tickers):
            res = analyze_stock(tick, strategi)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(tickers))
            
        status.update(label="Selesai!", state="complete", expanded=False)

    if len(results) > 0:
        st.success(f"Ditemukan {len(results)} Saham Potensial!")
        df_hasil = pd.DataFrame(results)
        
        # --- KONFIGURASI TABEL AGAR BISA DIKLIK ---
        st.dataframe(
            df_hasil,
            column_config={
                "Harga": st.column_config.NumberColumn(format="Rp %d"),
                "Link": st.column_config.LinkColumn(
                    "Chart", 
                    display_text="Buka Chart ↗️" # Tulisan yang muncul di tombol
                )
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(f"Belum ada saham yang masuk kriteria '{strategi}' saat ini.")
        st.info("Tips: Pasar mungkin sedang koreksi/sepi. Coba ubah filter di sebelah kiri.")

st.markdown("---")
st.caption("Klik 'Buka Chart' untuk langsung analisa di TradingView.")
