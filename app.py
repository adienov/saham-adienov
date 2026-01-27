import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
import time
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V87", layout="wide")

# --- 2. DATABASE PERMANEN (CSV) ---
DB_FILE = "database_tapak_naga.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    # Sesuaikan kolom dengan "PETA" di foto Bapak
    return pd.DataFrame(columns=["Stock", "Harga BUY", "SL/TS", "Tanggal TB", "Last Price", "% G/L", "Syariah"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_data()

# --- 3. FUNGSI CETAK PDF DENGAN DELAY (FIX BLANK PAGE) ---
def add_print_button():
    # CSS agar tampilan PDF bersih dari menu navigasi
    st.markdown("""
        <style>
        @media print {
            .stButton, .stSidebar, header, footer, .stTabs [data-baseweb="tab-list"] { display: none !important; }
            .main .block-container { padding: 0 !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("🖨️ Cetak ke PDF (Tunggu 2 Detik)"):
        # Skrip JS dengan delay 2 detik agar tabel ter-render sempurna
        st.components.v1.html("""
            <script>
                setTimeout(function(){ window.print(); }, 2000);
            </script>
        """, height=0)

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V87")

tab1, tab2, tab3 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)", "⏮️ BACKTEST"])

with tab1:
    # (Logika Scanner V85 Bapak yang sudah stabil)
    # ...
    st.info("Setelah Scan, jangan lupa klik 'Simpan ke PETA' agar data tidak hilang.")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga (TN)")
    
    # Penjelasan Metodologi agar muncul di PDF
    st.markdown("""<div style='border:2px solid #1E3A8A; padding:15px; border-radius:10px; margin-bottom:20px;'>
        <h2 style='color:#1E3A8A; margin-top:0;'>NORIS TRADING SYSTEM - PETA TN</h2>
        <p><b>Metodologi:</b> Trend Following Stage 2 & Buy On Breakout.</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.history_db.empty:
        # Tampilkan tabel PETA
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
        # Tambahkan tombol cetak yang sudah diperbaiki
        add_print_button()
    else:
        st.warning("Database PETA masih kosong.")
