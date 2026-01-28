import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DATABASE ---
st.set_page_config(page_title="EDU-VEST V124: Porto Manager", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_local_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA OTOMATIS ---
def get_stock_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return "Data Kurang", "⚪", 0, "0%"
        
        close = df['Close'].iloc[-1]
        ma50, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
        
        if close < ma200: status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif close > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        gl_str = "0%"
        if is_portfolio and entry_price > 0:
            gl_val = ((close - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: reco = "🚨 CUT LOSS" # Aturan Cut Loss CANSLIM
            
        return status, reco, int(close), gl_str
    except: return "Error", "❌", 0, "0%"

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: PORTO MANAGER V124")
st.error("🚨 MARKET CRASH (-5.24%). Gunakan tombol BELI hanya jika sudah yakin!")

tab1, tab2, tab3 = st.tabs(["🔍 SCANNER", "⭐ WATCHLIST", "📊 NORIS PETA (PORTFOLIO)"])

with tab2:
    st.subheader("📊 Analisa & Eksekusi Watchlist")
    # ... (Gunakan input kode saham Bapak di sini)
    wl_df = load_local_data(WATCHLIST_FILE, ["Stock"])
    if not wl_df.empty:
        results = []
        for s in wl_df['Stock']:
            status, reco, price, _ = get_stock_analysis(s)
            results.append({"Pilih": False, "Stock": s, "Price": price, "Status": status, "Rekomendasi": reco})
        
        # Tabel Interaktif untuk memilih saham yang ingin dipindah ke Porto
        df_edit = st.data_editor(pd.DataFrame(results), use_container_width=True, hide_index=True)
        
        if st.button("🛒 BELI & MASUKKAN PETA PORTO"):
            to_peta = df_edit[df_edit["Pilih"] == True]
            if not to_peta.empty:
                peta_now = load_local_data(DB_FILE, ["Tgl", "Stock", "Entry", "SL/TS"])
                new_rows = pd.DataFrame([{
                    "Tgl": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": row['Stock'], "Entry": row['Price'], "SL/TS": int(row['Price'] * 0.93)
                } for _, row in to_peta.iterrows()])
                pd.concat([peta_now, new_rows], ignore_index=True).to_csv(DB_FILE, index=False)
                st.success(f"✅ {len(to_peta)} Saham berhasil dipindahkan ke Porto!")
                st.rerun()

with tab3:
    st.subheader("📊 Monitoring Real-time Portfolio")
    peta_df = load_local_data(DB_FILE, ["Tgl", "Stock", "Entry", "SL/TS"])
    if not peta_df.empty:
        p_res = []
        for _, r in peta_df.iterrows():
            _, reco, last, gl = get_stock_analysis(r['Stock'], is_portfolio=True, entry_price=r['Entry'])
            p_res.append({"Stock": r['Stock'], "Entry": r['Entry'], "Last": last, "G/L %": gl, "Action": reco})
        st.table(pd.DataFrame(p_res))
    else:
        st.info("Portfolio Kosong. Centang saham di tab WATCHLIST dan klik 'BELI' untuk mengisi Peta.")
