import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V88", layout="wide")

# --- 2. DATABASE PERMANEN (CSV) ---
DB_FILE = "database_tapak_naga.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    # Kolom sesuai format PETA & INCARAN di WhatsApp Bapak
    return pd.DataFrame(columns=["Tanggal", "Stock", "Harga BUY", "SL/TS", "Last Price", "% G/L", "Syariah"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_data()

# --- 3. FUNGSI CETAK PDF (DENGAN DELAY AGAR TIDAK KOSONG) ---
def add_print_button():
    st.markdown("""
        <style>
        @media print {
            .stButton, .stSidebar, header, footer, [data-testid="stHeader"] { display: none !important; }
            .main .block-container { padding: 0 !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("🖨️ Cetak Laporan (PDF)"):
        # Delay 2 detik agar tabel terisi data sebelum diprint
        st.components.v1.html("<script>setTimeout(function(){ window.print(); }, 2000);</script>", height=0)

# --- 4. ENGINE SCANNER (BASIS V85) ---
# Menggunakan daftar syariah dan logika breakout Bapak
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]

@st.cache_data(ttl=300)
def scan_engine_v88(ticker_list, rs_threshold):
    results = []
    end_date = datetime.now()
    data_batch = yf.download(ticker_list, start=end_date - timedelta(days=365), end=end_date, progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()

    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(period="1y")
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                results.append({
                    "Tanggal": end_date.strftime("%Y-%m-%d"),
                    "Stock": t.replace(".JK",""),
                    "Harga BUY": int(close),
                    "SL/TS": int(red_line),
                    "Last Price": int(close),
                    "% G/L": 0.0,
                    "Syariah": "✅" if t.replace(".JK","") in SYARIAH_LIST else "❌"
                })
        except: continue
    return pd.DataFrame(results)

# --- 5. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V88")
tab1, tab2, tab3 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)", "⏮️ BACKTEST"])

with tab1:
    # TOMBOL UTAMA DI PALING ATAS
    if st.button("🚀 JALANKAN SCANNER LIVE"):
        with st.spinner("Menganalisa Market..."):
            df_res = scan_engine_v88([f"{s}.JK" for s in SYARIAH_LIST], 70)
            if not df_res.empty:
                st.session_state.current_scan = df_res
                st.write("### 📋 Hasil Incaran Tapak Naga Hari Ini:")
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            else:
                st.warning("Tidak ada saham lolos kriteria breakout.")

    if 'current_scan' in st.session_state:
        if st.button("💾 SIMPAN SEMUA HASIL KE PETA (DATABASE)"):
            new_db = pd.concat([st.session_state.history_db, st.session_state.current_scan], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
            new_db.to_csv(DB_FILE, index=False)
            st.session_state.history_db = new_db
            st.success("Tersimpan secara Permanen ke Database CSV!")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga (Running Portfolio)")
    if not st.session_state.history_db.empty:
        # Menampilkan tabel PETA yang tersimpan
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
        add_print_button()
    else:
        st.info("PETA Kosong. Silakan scan dan simpan dari tab INCARAN.")
