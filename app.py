import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE PERMANEN ---
st.set_page_config(page_title="Noris Trading System V70", layout="wide")

# File CSV untuk menyimpan data secara permanen
DB_FILE = "trading_history.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Memuat data ke session state saat aplikasi dijalankan
if 'history_db' not in st.session_state:
    st.session_state.history_db = load_data()

# --- 2. HEADER & IKON ---
st.title("📈 Noris Trading System V70")

# --- 3. SIDEBAR PARAMETER & DATABASE ---
st.sidebar.title("⚙️ Parameter & Database")
if st.sidebar.button("🗑️ Reset Database Permanen"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])
    st.sidebar.success("Database telah dikosongkan secara permanen.")
    st.rerun()

# --- 4. ENGINE SCANNER (BASIS V59) ---
@st.cache_data(ttl=300)
def scan_market_v59(ticker_list):
    results = []
    # (Logika download & Filter RS tetap seperti V59 Bapak)
    # ... 
    return pd.DataFrame(results)

# --- 5. TAMPILAN UTAMA ---
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER"])

with tab1:
    if st.button("🚀 JALANKAN SCANNER"):
        # Misal tickers lq45
        tickers = ["ANTM.JK", "BRIS.JK", "PGAS.JK", "MDKA.JK"]
        df_today = scan_market_v59(tickers)
        
        if not df_today.empty:
            st.subheader("📋 Hasil Scan Hari Ini")
            st.dataframe(df_today, use_container_width=True, hide_index=True)
            
            if st.button("💾 SIMPAN KE DATABASE PERMANEN"):
                # Gabungkan data lama dan baru
                new_db = pd.concat([st.session_state.history_db, df_today], ignore_index=True)
                # Hapus duplikat emiten (ambil yang terbaru)
                new_db = new_db.drop_duplicates(subset=['Emiten'], keep='last')
                st.session_state.history_db = new_db
                save_data(new_db) # Simpan ke file CSV
                st.success("Berhasil Disimpan secara Permanen!")
        else:
            st.info("Jalankan scanner untuk melihat hasil.")

with tab2:
    st.subheader("📈 Day-by-Day Tracking")
    db = st.session_state.history_db
    
    if not db.empty:
        track_list = []
        for _, row in db.iterrows():
            try:
                # Ambil harga live saat ini
                live = yf.Ticker(f"{row['Emiten']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((live - row['Harga_Awal']) / row['Harga_Awal']) * 100
                
                track_list.append({
                    "Tgl Rekom": row['Tanggal'],
                    "Emiten": row['Emiten'],
                    "Entry": int(row['Harga_Awal']),
                    "Current": int(live),
                    "% G/L": round(gain, 2),
                    "Status": "✅ PROFIT" if gain > 0 else "❌ LOSS",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{row['Emiten']}"
                })
            except: continue
            
        df_track = pd.DataFrame(track_list)
        st.dataframe(df_track, column_config={
            "Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka TV"),
            "% G/L": st.column_config.NumberColumn(format="%.2f%%")
        }, use_container_width=True, hide_index=True)
    else:
        st.warning("Database masih kosong. Silakan simpan hasil scan terlebih dahulu.")
