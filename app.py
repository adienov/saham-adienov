import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING ---
st.set_page_config(page_title="EDU-VEST V138: CRISIS RADAR", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham Syariah Bluechip & Second Liner
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "AMRT.JK", "CPIN.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE RADAR (TANPA FILTER) ---
def run_crisis_radar():
    results = []
    # Progress Bar agar Bapak tahu sistem bekerja
    progress_text = "Memindai kerusakan market..."
    my_bar = st.progress(0, text=progress_text)
    
    total = len(SYARIAH_TICKERS)
    for i, t in enumerate(SYARIAH_TICKERS):
        try:
            # Update progress
            my_bar.progress((i + 1) / total, text=f"Memindai {t}...")
            
            stock = yf.Ticker(t)
            df = stock.history(period="6mo")
            if len(df) < 50: continue
            
            close = df['Close'].iloc[-1]
            change_pct = ((close - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            
            # Indikator
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            bb = ta.bbands(df['Close'], length=20, std=2)
            lower_band = bb['BBL_20_2.0'].iloc[-1]
            
            # Tentukan Status (Hanya Label, Bukan Filter)
            status = "Normal"
            if rsi < 20: status = "🔥 EXTREME OVERSOLD"
            elif rsi < 30: status = "⚠️ Oversold"
            elif close < lower_band: status = "📉 Tembus Bawah BB"
            
            # Rekomendasi Kasar
            if rsi < 30 and close > lower_band: action = "👀 WATCH (Siap Serok)"
            elif close < ma200: action = "⛔ DOWNTREND PARAH"
            else: action = "⚪ WAIT"

            results.append({
                "Stock": t.replace(".JK",""),
                "Price": int(close),
                "Change": f"{change_pct:.2f}%",
                "RSI (14)": round(rsi, 1),
                "Posisi": status,
                "Saran": action,
                "Jarak ke MA200": f"{((close - ma200)/ma200)*100:.1f}%"
            })
        except: continue
        
    my_bar.empty() # Hapus loading bar
    return pd.DataFrame(results)

# --- 3. UI DASHBOARD ---
st.title("☢️ EDU-VEST: CRISIS RADAR V138")

# Panic Meter
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%) - MODE RADAR DIAKTIFKAN.")
    else: st.info(f"Market Status: {chg:.2f}%")
except: pass

st.write("### 📉 Peta Kerusakan Saham (Diurutkan dari RSI Terendah)")
st.write("Fitur ini menampilkan **SEMUA SAHAM** tanpa filter 'Buy Signal', agar Bapak bisa melihat mana yang sudah terlalu murah.")

if st.button("JALANKAN RADAR KRISIS"):
    df_res = run_crisis_radar()
    if not df_res.empty:
        # Urutkan berdasarkan RSI terendah (Paling hancur di atas)
        df_res = df_res.sort_values(by="RSI (14)", ascending=True)
        
        # Tampilkan Data Editor dengan Highlight Warna
        st.data_editor(
            df_res,
            column_config={
                "RSI (14)": st.column_config.NumberColumn(
                    "RSI Score",
                    help="Di bawah 30 = Murah, Di bawah 20 = Sangat Murah",
                    format="%.1f",
                ),
                "Change": st.column_config.TextColumn("Harian %"),
            },
            hide_index=True,
            use_container_width=True
        )
        st.info("💡 **Tips:** Perhatikan saham dengan RSI < 20. Jika besok muncul candle hijau, itu adalah peluang pantulan terbaik.")
    else:
        st.error("Gagal mengambil data market. Cek koneksi internet.")

# Tab Watchlist & Porto tetap ada di bawah
with st.expander("📂 Buka Watchlist & Portfolio"):
    tab1, tab2 = st.tabs(["⭐ Watchlist", "📊 Portfolio"])
    with tab1:
         wl = load_data(WATCHLIST_FILE, ["Stock"])
         st.dataframe(wl) if not wl.empty else st.write("Kosong")
    with tab2:
         pf = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
         st.dataframe(pf) if not pf.empty else st.write("Kosong")
