import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V89", layout="wide")

# --- 2. DATABASE PERMANEN ---
DB_FILE = "database_tapak_naga.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Stock", "Harga BUY", "SL/TS", "Last Price", "% G/L", "Syariah"])

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V89")
tab1, tab2 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)"])

with tab1:
    # Tombol Scanner Utama
    if st.button("🚀 JALANKAN SCANNER LIVE"):
        # Headline Metodologi terintegrasi agar masuk dalam tangkapan gambar
        st.markdown("""
            <div style="border: 2px solid #1E3A8A; padding: 15px; border-radius: 10px; background-color: #f8f9fa;">
                <h3 style="color: #1E3A8A; margin-top:0;">NORIS TRADING SYSTEM - INCARAN TN</h3>
                <p style="font-size: 0.9rem;"><b>Metode:</b> Buy On Breakout (Tapak Naga) & Stage 2 Minervini.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # (Logika Scan Engine V88 Bapak)
        # Tampilkan hasil scan dalam dataframe
        st.write("### 📋 Hasil Incaran Hari Ini:")
        # st.dataframe(df_res)
        
        # FITUR DOWNLOAD PNG (Gunakan fitur bawaan Streamlit untuk download dataframe ke CSV/Excel sebagai alternatif cepat)
        # Untuk PNG, Bapak bisa menggunakan fitur 'Fullscreen' lalu Screenshot, atau tombol di bawah:
        st.info("💡 Tips: Untuk hasil gambar terbaik di WhatsApp, gunakan fitur 'Screenshot' pada area tabel di bawah.")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga (Running Portfolio)")
    if not st.session_state.history_db.empty:
        df_peta = st.session_state.history_db.copy()
        
        # Menampilkan Tabel PETA
        st.dataframe(df_peta, use_container_width=True, hide_index=True)
        
        # TOMBOL UNDUH DATA (Jika PNG sulit, CSV adalah yang paling aman untuk data)
        csv = df_peta.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Data PETA (CSV/Excel)",
            data=csv,
            file_name=f'PETA_TN_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
    else:
        st.warning("Database PETA masih kosong.")
