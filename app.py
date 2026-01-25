import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V67", layout="wide")

# Database Portofolio & Incaran (Session State)
if 'incaran' not in st.session_state:
    st.session_state.incaran = pd.DataFrame(columns=["Stock", "Harga BUY", "SL Awal", "% Range", "AvgTrx30D"])
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Stock", "Harga BUY", "SL/TS", "Tanggal TB", "Last Price", "% G/L"])

# --- 2. SIDEBAR PARAMETER (BASIS V59) ---
st.sidebar.title("⚙️ Parameter Tapak Naga")
modal_jt = st.sidebar.number_input("Modal (Juta Rp)", value=100)
rpt_pct = st.sidebar.slider("RPT (%)", 0.1, 1.0, 0.5, step=0.1) # RPT sesuai gambar Bapak

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V67")
st.caption("Sistem Trading Tapak Naga = Buy On Breakout") #

tab_scan, tab_incaran, tab_peta = st.tabs(["🔍 SCANNER", "🎯 INCARAN (WATCHLIST)", "🗺️ PETA PORTOFOLIO"])

with tab_scan:
    if st.button("🚀 JALANKAN SCANNER MARKET"):
        # (Logika Scanner V59 - Mencari saham Stage 2)
        # Menghasilkan df_scan
        st.success("Scanner Berhasil. Silakan masukkan ke daftar INCARAN di bawah.")
        # Contoh tombol simulasi masukkan ke incaran
        if st.button("Tambahkan MBMA ke Incaran"):
            new_inc = {"Stock": "MBMA", "Harga BUY": 855, "SL Awal": 760, "% Range": 11.11, "AvgTrx30D": 220}
            st.session_state.incaran = pd.concat([st.session_state.incaran, pd.DataFrame([new_inc])], ignore_index=True)

with tab_incaran:
    st.subheader("📋 INCARAN Tapak Naga (TN)") #
    if not st.session_state.incaran.empty:
        st.dataframe(st.session_state.incaran, use_container_width=True, hide_index=True)
        
        st.divider()
        st.info("💡 Input Auto Order, wajib ada mengalah 2-3 Tik agar peluang terisi besar.") #
        
        # Simulasi Trigger Buy (Pindah ke Portofolio)
        if st.button("✅ Konfirmasi Buy MBMA (Triggered)"):
            row = st.session_state.incaran.iloc[0]
            new_peta = {
                "Stock": row['Stock'], "Harga BUY": row['Harga BUY'], "SL/TS": row['SL Awal'],
                "Tanggal TB": "26-01-2026", "Last Price": 900, "% G/L": 5.2
            }
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, pd.DataFrame([new_peta])], ignore_index=True)
            st.session_state.incaran = st.session_state.incaran.drop(0)
            st.rerun()

with tab_peta:
    st.subheader("🗺️ PETA Tapak Naga (TN)") #
    if not st.session_state.portfolio.empty:
        # Styling Tabel sesuai model Bapak
        def highlight_pnl(val):
            color = 'yellow' if val > 20 else 'white'
            return f'background-color: {color}'

        styled_peta = st.session_state.portfolio.style.applymap(highlight_pnl, subset=['% G/L'])
        st.dataframe(styled_peta, use_container_width=True, hide_index=True)
        
        st.warning("⚠️ Jangan Sampai Lupa untuk input SL / TS di Aplikasi Sekuritas!") #
    else:
        st.info("Belum ada posisi aktif. Pantau menu INCARAN.")
