import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASHBOARD ---
st.set_page_config(page_title="EDU-VEST V130: Market Wizard", layout="wide")
DB_FILE = "trading_history.csv"

# --- 2. ENGINE WIZARD LOGIC ---
def get_wizard_analysis(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 150: return None
        
        # Indikator Utama
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma150 = df['Close'].rolling(150).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        vol_now = df['Volume'].iloc[-1]
        max_down_vol = df[df['Close'] < df['Open']]['Volume'].tail(10).max()
        
        # A. Trend Template (Minervini)
        # Harga harus > MA150 & MA200, dan MA50 > MA150
        is_uptrend = close > ma150 and ma150 > ma200 and close > ma50
        
        # B. Pocket Pivot (O'Neil/HQ Style)
        # Volume hari ini > volume turun tertinggi dalam 10 hari terakhir
        is_pocket_pivot = vol_now > max_down_vol and close > df['Close'].iloc[-2]
        
        # Penentuan Status
        if is_uptrend and is_pocket_pivot:
            status, reco = "🔥 WIZARD BREAKOUT", "🟢 BUY"
        elif is_uptrend:
            status, reco = "Trend Strong", "🟡 MONITOR"
        else:
            status, reco = "Laggard/Downtrend", "🔴 AVOID"
            
        return {
            "Price": int(close), "Status": status, "Action": reco,
            "TP": int(close * 1.20), "SL": int(close * 0.93),
            "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
        }
    except: return None

# --- 3. UI DASHBOARD ---
st.title("🧙‍♂️ EDU-VEST: MARKET WIZARD SCREENER V130")

tab1, tab2, tab3 = st.tabs(["🔍 WIZARD SCANNER", "⭐ WATCHLIST", "📊 PORTO MONITOR"])

with tab1:
    st.subheader("🚀 Scan Saham 'Super Performance'")
    if st.button("MULAI ANALISA WIZARD"):
        with st.spinner("Mencari jejak kaki Market Wizard..."):
            tickers = ["ANTM.JK", "PGAS.JK", "EXCL.JK", "MDKA.JK", "INCO.JK", "HRUM.JK", "MEDC.JK", "BRIS.JK", "TLKM.JK"]
            results = []
            for t in tickers:
                data = get_wizard_analysis(t)
                if data and data["Action"] != "🔴 AVOID":
                    results.append({
                        "Stock": t.replace(".JK",""), "Price": data["Price"],
                        "Kondisi": data["Status"], "Action": data["Action"],
                        "Target (TP)": data["TP"], "Cut Loss": data["SL"],
                        "Link": data["TV"]
                    })
            if results:
                st.data_editor(pd.DataFrame(results), column_config={"Link": st.column_config.LinkColumn("Chart")}, hide_index=True)
            else:
                st.warning("Belum ada saham yang memenuhi kriteria ketat Market Wizard.")

# (Sisa kode tab2 dan tab3 tetap mengikuti struktur V129 sebelumnya)
