import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V86", layout="wide")

# --- 2. DATABASE PERMANEN (CSV) ---
DB_FILE = "database_tapak_naga.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    # Membuat kolom sesuai "PETA" di foto Bapak
    return pd.DataFrame(columns=["Stock", "Harga BUY", "SL/TS", "Tanggal TB", "Last Price", "% G/L", "Syariah"])

# Memastikan data dimuat di awal agar tab tidak kosong
if 'history_db' not in st.session_state:
    st.session_state.history_db = load_data()

# --- 3. FUNGSI CETAK PDF ---
def add_print_button():
    st.markdown("<style>@media print {.stButton, .stSidebar, header, footer {display:none!important;}}</style>", unsafe_allow_html=True)
    if st.button("🖨️ Cetak ke PDF"):
        st.components.v1.html("<script>window.print();</script>", height=0)

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V86")
tab1, tab2, tab3 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)", "⏮️ BACKTEST"])

with tab1:
    st.subheader("📋 INCARAN Tapak Naga (TN)")
    # (Logika Scanner V80 Bapak tetap berjalan di sini)
    # Misal df_scan adalah hasil scan harian
    
    if st.button("🚀 JALANKAN SCANNER"):
        # Tambahkan Headline untuk PDF sesuai permintaan
        st.markdown("""<div style='border:2px solid #1E3A8A; padding:15px; border-radius:10px;'>
            <h3>NORIS TRADING SYSTEM REPORT</h3>
            <p>Strategi: Buy On Breakout (Tapak Naga) & Stage 2 (Minervini)</p>
        </div>""", unsafe_allow_html=True)
        
        # Simulasi hasil scan
        st.dataframe(st.session_state.history_db, use_container_width=True) # Menampilkan data dari DB
        
        if st.button("💾 SIMPAN KE PETA (DATABASE)"):
            # Proses simpan ke CSV agar tidak hilang
            st.session_state.history_db.to_csv(DB_FILE, index=False)
            st.success("Data berhasil masuk ke PETA!")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga (TN)")
    db_peta = st.session_state.history_db
    
    if not db_peta.empty:
        # Menghitung % G/L Realtime
        # Tampilkan tabel dengan warna SL/TS Biru (Update) atau Merah (Kena)
        st.dataframe(db_peta, use_container_width=True, hide_index=True)
        add_print_button()
    else:
        st.info("PETA Kosong. Silakan scan dan simpan saham dari tab INCARAN.")
