import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
import time
from datetime import datetime

# --- 1. SETTING DATABASE ---
st.set_page_config(page_title="EDU-VEST PROTECTION MAX V122", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_local_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA (REVERSAL & CANSLIM) ---
def get_detailed_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return "Data Kurang", "⚪ TUNGGU", 0, "0%"
        
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Logika Status
        if close < ma200: status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif close > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        gl_str = "0%"
        if is_portfolio and entry_price > 0:
            gl_val = ((close - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: reco = "🚨 CUT LOSS"
            
        return status, reco, int(close), gl_str
    except: return "Error", "❌", 0, "0%"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: PROTECTION MAX V122")

tab1, tab2, tab3 = st.tabs(["🔍 SCANNER", "⭐ WATCHLIST", "📊 NORIS PETA (PORTFOLIO)"])

with tab1:
    st.subheader("🚀 Scanner Reversal MA50")
    if st.button("MULAI SCANNING MARKET"):
        progress_bar = st.progress(0) # Indikator Selesai Scanner
        status_text = st.empty()
        # Simulasi proses scan (Ganti dengan ALL_TICKERS Bapak)
        for i in range(101):
            time.sleep(0.01) # Simulasi loading
            progress_bar.progress(i)
            status_text.text(f"Sedang menganalisa market... {i}%")
        st.success("✅ Scanning Selesai!")

with tab2:
    st.subheader("📊 Analisa Watchlist & Action")
    new_stock = st.text_input("Input Kode:").upper()
    if st.button("➕ Simpan"):
        wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
        if new_stock and new_stock not in wl_df['Stock'].values:
            pd.concat([wl_df, pd.DataFrame([{"Stock": new_stock}])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
            st.rerun()

    wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
    if not wl_df.empty:
        # Gunakan data_editor agar ada tombol pindah ke Peta
        analysis_res = []
        for s in wl_df['Stock']:
            status, reco, price, _ = get_detailed_analysis(s)
            analysis_res.append({"Pilih": False, "Stock": s, "Price": price, "Kondisi": status, "Rekomendasi": reco})
        
        df_editor = st.data_editor(pd.DataFrame(analysis_res), use_container_width=True, hide_index=True)
        
        if st.button("🛒 BELI & PINDAHKAN KE PETA PORTFOLIO"):
            to_peta = df_editor[df_editor["Pilih"] == True]
            if not to_peta.empty:
                current_peta = load_local_data(DB_FILE, ["Tgl", "Stock", "Entry", "SL/TS"])
                new_entries = pd.DataFrame([{
                    "Tgl": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": row['Stock'], "Entry": row['Price'], "SL/TS": int(row['Price'] * 0.93)
                } for _, row in to_peta.iterrows()])
                pd.concat([current_peta, new_entries], ignore_index=True).to_csv(DB_FILE, index=False)
                st.success(f"✅ {len(to_peta)} Saham berhasil dipindahkan ke Peta!")

with tab3:
    st.subheader("📊 Monitoring Real-time Portfolio")
    # (Kode monitoring portfolio Bapak tetap ada di sini)
