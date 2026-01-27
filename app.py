import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V83", layout="wide")

# --- 2. FUNGSI DISPLAY LAPORAN TERINTEGRASI ---
def display_integrated_report(df_results):
    # Headline dan Metodologi menyatu dengan tabel
    st.markdown(f"""
        <div style="border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; background-color: #ffffff;">
            <h2 style="color: #1E3A8A; text-align: center; margin-top: 0;">NORIS TRADING SYSTEM - STOCK SCANNER REPORT</h2>
            <p style="text-align: center; color: #6B7280; margin-bottom: 20px;">
                Generated on: {datetime.now().strftime("%d %B %Y, %H:%M")}
            </p>
            <div style="background-color: #f1f5f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h4 style="color: #1E3A8A; margin-top: 0;">🚀 Strategi & Metodologi Teknikal:</h4>
                <p style="font-size: 0.95rem; color: #334155; line-height: 1.6;">
                    Daftar saham di bawah ini dipilih menggunakan kombinasi metode <b>Trend Following Mark Minervini (SEPA)</b> 
                    dan <b>Tapak Naga (TN)</b>. Kriteria utama meliputi:
                </p>
                <ul style="font-size: 0.9rem; color: #334155;">
                    <li><b>Stage 2 Uptrend:</b> Konfirmasi struktur <i>Higher High & Higher Low</i> (Harga > MA50 > MA150 > MA200).</li>
                    <li><b>Relative Strength:</b> Memilih emiten yang bergerak lebih kuat dibandingkan IHSG.</li>
                    <li><b>VCP & Breakout:</b> Deteksi penyempitan harga sebelum ledakan volume (Buy on Breakout).</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Menampilkan Tabel Tepat di Bawah Penjelasan
    st.subheader("📋 DAFTAR SAHAM LOLOS KRITERIA")
    st.dataframe(
        df_results, 
        column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")},
        use_container_width=True, 
        hide_index=True
    )
    st.markdown("<p style='color:red; font-size:0.8rem;'>*Disiplin Stop Loss (SL) adalah kunci utama keselamatan modal.</p>", unsafe_allow_html=True)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V83")

# Tombol Eksekusi
if st.button("🚀 JALANKAN SCANNER MARKET"):
    # (Logika scan_engine Bapak tetap digunakan di sini)
    # Misal kita simulasikan hasil scan df_res
    # df_res = scan_engine(selected_tickers, min_rs)
    
    if not df_res.empty:
        # Panggil fungsi laporan yang menyatu
        display_integrated_report(df_res)
    else:
        st.warning("Belum ada saham yang memenuhi kriteria breakout hari ini.")
