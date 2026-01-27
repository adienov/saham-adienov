import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V76", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. ENGINE SCANNER (LIVE & HISTORICAL) ---
@st.cache_data(ttl=300)
def scan_engine(ticker_list, rs_threshold, target_date=None):
    results = []
    # Jika target_date diisi, end_date adalah tanggal backtest tersebut
    end_date = datetime.now() if target_date is None else datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
    
    # Download batch untuk efisiensi
    data_batch = yf.download(ticker_list, start=end_date - timedelta(days=365), end=end_date, progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()

    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(start=end_date - timedelta(days=365), end=end_date)
            if len(df) < 200: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                results.append({
                    "Tanggal": end_date.strftime("%Y-%m-%d") if target_date is None else target_date,
                    "Emiten": t.replace(".JK",""),
                    "Harga_Awal": int(close),
                    "SL_Awal": int(red_line),
                    "Status": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V76")

tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER", "⏮️ HISTORICAL BACKTEST"])

# ... (Tab 1 & 2 tetap menggunakan logika V75 yang stabil) ...

with tab3:
    st.subheader("⏮️ Historical Backtest (Mundur Tanggal)")
    back_date = st.date_input("Pilih Tanggal Mundur:", datetime.now() - timedelta(days=30))
    
    if st.button("⏪ SCAN TANGGAL TERPILIH"):
        with st.spinner(f"Menganalisa data per {back_date}..."):
            df_hist = scan_engine(["ANTM.JK", "BRIS.JK", "TLKM.JK", "ASII.JK", "PGAS.JK", "MDKA.JK", "EXCL.JK"], 70, target_date=back_date.strftime("%Y-%m-%d"))
            
            if not df_hist.empty:
                # --- KALKULASI G/L% UNTUK BACKTEST ---
                bt_results = []
                for _, row in df_hist.iterrows():
                    try:
                        # Ambil harga SEKARANG untuk dibandingkan dengan harga tanggal terpilih
                        curr_data = yf.Ticker(f"{row['Emiten']}.JK").history(period="1d")
                        if not curr_data.empty:
                            last_p = curr_data['Close'].iloc[-1]
                            diff_pct = ((last_p - row['Harga_Awal']) / row['Harga_Awal']) * 100
                            
                            bt_results.append({
                                "Tanggal": row['Tanggal'],
                                "Emiten": row['Emiten'],
                                "Harga Dulu": row['Harga_Awal'],
                                "Harga Kini": int(last_p),
                                "% G/L": round(diff_pct, 2),
                                "Status Kini": "🟢 CUAN" if diff_pct > 0 else "🔴 LOSS",
                                "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{row['Emiten']}"
                            })
                    except: continue
                
                st.write(f"### Performa Saham yang Lolos Scan pada {back_date}:")
                st.dataframe(pd.DataFrame(bt_results), column_config={
                    "TV": st.column_config.LinkColumn("Chart", display_text="📈 Buka"),
                    "% G/L": st.column_config.NumberColumn(format="%.2f%%")
                }, use_container_width=True, hide_index=True)
            else:
                st.warning("Tidak ada saham lolos kriteria pada tanggal tersebut.")
