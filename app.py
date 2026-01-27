import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V90", layout="wide")

# --- 2. DATABASE PERMANEN ---
DB_FILE = "database_tapak_naga.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        # Menggunakan kolom sesuai foto "PETA" Bapak
        st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Stock", "Harga BUY", "SL/TS", "Last Price", "% G/L", "Syariah"])

# --- 3. ENGINE SCANNER (Daftar Syariah Bapak) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V90")
tab1, tab2 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)"])

with tab1:
    # Letakkan tombol di paling atas
    if st.button("🚀 MULAI SCANNER MARKET"):
        with st.spinner("Sedang mencari saham breakout..."):
            # Simulasi Scan Engine V88
            # ... (kode download yfinance di sini) ...
            
            # HEADLINE YANG MENYATU UNTUK SCREENSHOT
            st.markdown(f"""
                <div style="border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; background-color: #ffffff; color: #1E3A8A;">
                    <h2 style="margin-top:0;">NORIS TRADING SYSTEM - INCARAN TN</h2>
                    <p><b>Metode:</b> Stage 2 Minervini & Buy On Breakout Tapak Naga</p>
                    <hr>
                    <p style="font-size: 0.8rem; color: #666;">Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Tampilkan Tabel Hasil Scan (Pastikan data di-download dulu)
            # st.dataframe(df_results, use_container_width=True, hide_index=True)
            st.success("Data berhasil dimuat. Silakan ambil screenshot area ini untuk dibagikan ke member.")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga (Running Portfolio)")
    if not st.session_state.history_db.empty:
        # Pastikan kolom % G/L dihitung ulang
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
    else:
        st.warning("Database PETA masih kosong. Silakan simpan hasil dari tab INCARAN.")
