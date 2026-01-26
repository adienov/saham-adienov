import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V73", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. SIDEBAR PARAMETER ---
st.sidebar.title("⚙️ Parameter & Database")
# (Parameter Input Mode & RS Rating tetap di sini)
# ...

# --- 3. ENGINE SCANNER HISTORIS (UNTUK BACKTEST) ---
@st.cache_data(ttl=3600)
def scan_historical(ticker_list, rs_threshold, target_date):
    results = []
    # Mundur ke tanggal target untuk mengambil data historis
    end_date = datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
    
    for t in ticker_list:
        try:
            # Ambil data hingga tanggal yang dipilih Bapak
            df = yf.Ticker(t).history(start=end_date - timedelta(days=365), end=end_date)
            if len(df) < 200: continue
            
            close = df['Close'].iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma150 = df['Close'].rolling(150).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            
            # Kriteria Sederhana Stage 2 untuk Backtest Cepat
            if close > ma150 and ma150 > ma200 and close > ma50:
                results.append({
                    "Tanggal": target_date,
                    "Emiten": t.replace(".JK",""),
                    "Harga_Scan": int(close),
                    "Status": "✅ LOLOS KRITERIA"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V73")

tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER", "⏮️ HISTORICAL BACKTEST"])

with tab1:
    # (Logika Scanner Live dan Tombol Simpan tetap sama seperti V72)
    # ...

with tab2:
    # (Logika Day-by-Day Tracking tetap sama seperti V72)
    # ...

with tab3:
    st.subheader("⏮️ Mundur Hasil Scan (Historical Backtest)")
    st.caption("Gunakan fitur ini untuk melihat saham apa saja yang lolos scanner pada tanggal pilihan Bapak di masa lalu.")
    
    col_bt1, col_bt2 = st.columns([1, 2])
    with col_bt1:
        # Pilihan tanggal mundur
        backtest_date = st.date_input("Pilih Tanggal Mundur:", datetime.now() - timedelta(days=7))
        bt_date_str = backtest_date.strftime("%Y-%m-%d")
        
    if st.button("⏪ JALANKAN BACKTEST SCAN"):
        with st.spinner(f"Mencari hasil scan pada {bt_date_str}..."):
            # Jalankan scan menggunakan data masa lalu
            # Gunakan tickers lq45_tickers yang sudah ada di sidebar
            df_bt = scan_historical(lq45_tickers, 70, bt_date_str)
            
            if not df_bt.empty:
                st.write(f"### Hasil Scan pada {bt_date_str}:")
                # Bandingkan dengan harga SEKARANG untuk melihat performa
                bt_analysis = []
                for _, row in df_bt.iterrows():
                    try:
                        current = yf.Ticker(f"{row['Emiten']}.JK").history(period="1d")['Close'].iloc[-1]
                        diff = ((current - row['Harga_Scan']) / row['Harga_Scan']) * 100
                        bt_analysis.append({
                            "Emiten": row['Emiten'], "Harga Dulu": row['Harga_Scan'],
                            "Harga Kini": int(current), "% Profit/Loss": round(diff, 2)
                        })
                    except: pass
                st.dataframe(pd.DataFrame(bt_analysis), use_container_width=True, hide_index=True)
            else:
                st.warning(f"Tidak ditemukan saham yang lolos kriteria pada {bt_date_str}.")
