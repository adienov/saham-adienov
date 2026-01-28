import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASHBOARD & DATABASE ---
st.set_page_config(page_title="EDU-VEST V132: Market Detector", layout="wide")
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK"]

# --- 2. FITUR DETEKSI MARKET (PANIC METER) ---
def get_market_status():
    try:
        ihsg = yf.Ticker("^JKSE").history(period="2d")
        last_p = ihsg['Close'].iloc[-1]
        prev_p = ihsg['Close'].iloc[-2]
        chg = ((last_p - prev_p) / prev_p) * 100
        
        if chg <= -3.0:
            return f"🚨 MARKET CRASH ({chg:.2f}%)", "error"
        elif chg <= -1.5:
            return f"⚠️ MARKET VOLATILE ({chg:.2f}%)", "warning"
        else:
            return f"🟢 MARKET NORMAL ({chg:.2f}%)", "success"
    except: return "Data Market N/A", "info"

# --- 3. ENGINE SCREENER MULTI-STRATEGY ---
def run_v132_screener(mode):
    results = []
    for t in SYARIAH_TICKERS:
        try:
            df = yf.Ticker(t).history(period="1y")
            if len(df) < 60: continue
            
            close, prev_close = df['Close'].iloc[-1], df['Close'].iloc[-2]
            vol_now, vol_avg = df['Volume'].iloc[-1], df['Volume'].rolling(20).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            high_20 = df['High'].rolling(20).max().iloc[-2]
            
            match = False
            # Logika Strategi
            if mode == "Breakout" and close > high_20 and vol_now > vol_avg: match = True
            elif mode == "Reversal" and rsi < 35 and close > prev_close: match = True
            elif mode == "Swing" and close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.02): match = True

            if match:
                results.append({
                    "Stock": t.replace(".JK",""), "Price": int(close),
                    "Status": "BAGUS" if close > ma50 else "TUNGGU",
                    "TP": int(close * 1.15), "SL": int(close * 0.93),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("🏹 EDU-VEST: MARKET DETECTOR V132")

# Tampilkan Status Market di Paling Atas
status_msg, status_type = get_market_status()
if status_type == "error": st.error(status_msg + " - Fokus Amankan Modal, Jangan Agresif!")
elif status_type == "warning": st.warning(status_msg)
else: st.success(status_msg)

st.sidebar.header("Pilih Strategi")
mode = st.sidebar.radio("Mode:", ["Breakout", "Reversal", "Swing"])

if st.sidebar.button("JALANKAN SCANNER"):
    with st.spinner(f"Menganalisa mode {mode}..."):
        df_res = run_v132_screener(mode)
        if not df_res.empty:
            st.data_editor(df_res, column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
        else:
            st.warning(f"Belum ada saham yang masuk kriteria {mode} saat market sedang crash.")
