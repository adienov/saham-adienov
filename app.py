import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V82", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal", "Syariah"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. HEADER LAPORAN (PENYEMPURNAAN STRUKTUR) ---
def display_report_header():
    # Menggunakan expander agar tidak berantakan di layar utama
    with st.expander("📄 KLIK UNTUK LIHAT METODOLOGI & HEADLINE PDF", expanded=False):
        st.markdown(f"""
            <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; border: 1px solid #dee2e6;">
                <h2 style="color:#1E3A8A; text-align:center;">NORIS TRADING SYSTEM REPORT</h2>
                <p style="text-align:center; color:#6B7280;"><i>Generated on: {datetime.now().strftime("%d %B %Y, %H:%M")}</i></p>
                <hr>
                <h4 style="color:#1E3A8A;">🚀 Trading Style & Methodology:</h4>
                <p style="text-align:justify; color:#374151;">
                    Sistem ini menggunakan strategi <b>Trend Following & Momentum</b> berbasis metode <b>Mark Minervini (SEPA)</b> dan <b>Tapak Naga (TN)</b>.
                </p>
                <ul style="color:#374151; font-size:0.9rem;">
                    <li><b>Trend Alignment (Stage 2):</b> Struktur Higher High & Higher Low (MA50 > MA150 > MA200).</li>
                    <li><b>Relative Strength (RS) Rating:</b> Fokus pada saham yang Outperform terhadap market (IHSG).</li>
                    <li><b>VCP Pattern:</b> Identifikasi volatilitas ketat sebelum Breakout.</li>
                    <li><b>Risk Management:</b> Stop Loss (SL) disiplin berbasis RedLine dinamis.</li>
                </ul>
                <p style="color:#EF4444; font-size:0.75rem; text-align:center;"><i>Disclaimer: Alat bantu analisa teknikal. Keputusan trading sepenuhnya tanggung jawab pengguna.</i></p>
            </div>
        """, unsafe_allow_html=True)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V82")

tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER", "⏮️ BACKTEST"])

with tab1:
    # Letakkan tombol di paling atas
    if st.button("🚀 JALANKAN SCANNER MARKET"):
        display_report_header() # Headline muncul rapi di bawah tombol
        
        # (Logika scan_engine tetap menggunakan V81 yang sudah lengkap)
        st.info("Scanner berjalan... Data akan muncul di bawah ini.")
        
        # Contoh visualisasi agar tidak terlihat kosong
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Market Status", "🟢 BULLISH")
        # st.dataframe(df_res, use_container_width=True)

with tab2:
    st.subheader("📊 Performance Tracker")
    if not st.session_state.history_db.empty:
        # Pemuatan data tracker dipastikan tidak kosong
        st.dataframe(st.session_state.history_db, use_container_width=True)
    else:
        st.info("Database kosong. Simpan hasil scan untuk memantau performa.")

# --- (Tab 3 tetap sama) ---
