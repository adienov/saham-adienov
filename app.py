import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os

# --- 1. SETTING DASHBOARD ---
st.set_page_config(page_title="EDU-VEST V131: Multi-Mode", layout="wide")
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK"]

# --- 2. ENGINE MULTI-STRATEGY ---
def run_screener_v131(mode):
    results = []
    for t in SYARIAH_TICKERS:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 60: continue
            
            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            vol_now = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            high_20 = df['High'].rolling(20).max().iloc[-2]
            
            match = False
            # A. MODE BREAKOUT: Harga tembus High 20 hari & Volume > Rata-rata
            if mode == "Breakout" and close > high_20 and vol_now > vol_avg:
                match = True
            
            # B. MODE REVERSAL: RSI < 35 (Oversold) & Hari ini ditutup hijau
            elif mode == "Reversal" and rsi < 35 and close > prev_close:
                match = True
                
            # C. MODE SWING: Harga di atas MA50 & baru saja memantul (Low dekat MA50)
            elif mode == "Swing" and close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.02):
                match = True

            if match:
                results.append({
                    "Stock": t.replace(".JK",""),
                    "Price": int(close),
                    "RSI": round(rsi, 2),
                    "Target TP": int(close * 1.10),
                    "Stop Loss": int(close * 0.95),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. UI DASHBOARD ---
st.title("🏹 EDU-VEST: MULTI-STRATEGY SCREENER V131")

# Navigasi Mode di Sidebar
st.sidebar.header("Pilih Strategi")
selected_mode = st.sidebar.radio("Mode Trading:", ["Breakout", "Reversal", "Swing"])

if st.sidebar.button("JALANKAN SCANNER"):
    with st.spinner(f"Mencari peluang {selected_mode}..."):
        df_res = run_screener_v131(selected_mode)
        if not df_res.empty:
            st.success(f"Ditemukan {len(df_res)} saham sesuai mode {selected_mode}")
            st.data_editor(df_res, column_config={"Chart": st.column_config.LinkColumn("Link TV")}, hide_index=True)
        else:
            st.warning(f"Belum ada saham yang masuk kriteria {selected_mode} saat ini.")

# Penjelasan Visual untuk Bapak
st.divider()
if selected_mode == "Breakout":
    st.info("💡 **Mode Breakout:** Mencari saham yang 'meledak' keluar dari area konsolidasi.")
    
elif selected_mode == "Reversal":
    st.info("💡 **Mode Reversal:** Mencari saham yang sudah jatuh terlalu dalam dan mulai berbalik arah.")
    
else:
    st.info("💡 **Mode Swing Trading:** Mencari saham yang sedang tren naik dan sedang 'istirahat' di garis MA50.")
