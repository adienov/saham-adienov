import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. INISIALISASI DATABASE ---
st.set_page_config(page_title="EDU-VEST V129: Trading Plan", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

SYARIAH_TICKERS = ["ANTM.JK", "PGAS.JK", "EXCL.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "HRUM.JK", "MEDC.JK", "ELSA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA & TRADING PLAN ---
def get_detailed_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 50: return None
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Penentuan Status
        if last_p < ma200: status, reco = "Trend Rusak", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Konsolidasi", "⚪ TUNGGU"
        
        # Auto Trading Plan (Inspirasi HQ)
        buy_area = f"{int(last_p * 0.98)} - {last_p}"
        tp_target = int(last_p * 1.15)
        sl_exit = int(last_p * 0.93)
            
        gl_str = "0%"
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: reco = "🚨 CUT LOSS"
            elif gl_val >= 15.0: reco = "🔵 TAKE PROFIT"
            
        return {
            "Price": last_p, "Status": status, "Action": reco, 
            "G/L": gl_str, "Buy Area": buy_area, "TP": tp_target, "SL": sl_exit,
            "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
        }
    except: return None

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: TRADING PLAN DASHBOARD V129")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("🚀 Scanner & Trading Plan Syariah")
    if st.button("JALANKAN SCANNER SEKARANG"):
        with st.spinner("Menganalisa Trading Plan..."):
            scan_res = []
            for t in SYARIAH_TICKERS:
                data = get_detailed_analysis(t)
                if data and data["Action"] == "🟢 BAGUS":
                    s_name = t.replace(".JK","")
                    scan_res.append({
                        "Stock": s_name, "Price": data["Price"], "Action": data["Action"],
                        "Buy Area": data["Buy Area"], "Target TP": data["TP"], "Stop Loss": data["SL"],
                        "TV Link": data["TV"]
                    })
            if scan_res:
                st.data_editor(pd.DataFrame(scan_res), column_config={"TV Link": st.column_config.LinkColumn("Chart TV")}, hide_index=True)

with tab2:
    st.subheader("📊 Analisa Watchlist")
    # ... (Gunakan input kode saham Bapak)
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        wl_results = []
        for s in wl['Stock']:
            d = get_detailed_analysis(s)
            if d: wl_results.append({"Stock": s, "Price": d["Price"], "Rekomendasi": d["Action"], "TP": d["TP"], "SL": d["SL"], "TV": d["TV"]})
        st.data_editor(pd.DataFrame(wl_results), column_config={"TV": st.column_config.LinkColumn("Buka TV")}, hide_index=True)

with tab3:
    st.subheader("📊 Monitoring Porto & Action")
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            d = get_detailed_analysis(row['Stock'], True, row['Entry'])
            if d:
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                c1.write(f"**{row['Stock']}**")
                c2.write(f"G/L: {d['G/L']}")
                c3.write(f"Action: {d['Action']} | TP: {d['TP']} | SL: {d['SL']}")
                if c4.button("🗑️", key=f"del_{idx}"):
                    df_p.drop(idx).to_csv(DB_FILE, index=False)
                    st.rerun()
                st.divider()
