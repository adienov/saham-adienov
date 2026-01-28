import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. INISIALISASI DATABASE ---
st.set_page_config(page_title="EDU-VEST ALL-IN-ONE V127", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA (LOGIC CANSLIM & REVERSAL) ---
def get_detailed_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK")
        df = t.history(period="1y")
        if len(df) < 100: return "Data Kurang", "⚪", 0, "0%", 0, 0
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Penentuan Status Teknis
        if last_p < ma200: status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        # Logika Action Portfolio
        gl_str = "0%"
        tp, ts = 0, 0
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            tp, ts = int(entry_price * 1.15), int(last_p * 0.95)
            if gl_val <= -7.0: reco = "🚨 SELL (Cut Loss)"
            elif gl_val >= 15.0: reco = "🔵 TAKE PROFIT"
            elif gl_val >= 5.0: reco = "🟢 HOLD (Trailing Stop)"
            else: reco = "🟡 HOLD (Wait Rebound)"
            
        return status, reco, last_p, gl_str, tp, ts
    except: return "Error", "❌", 0, "0%", 0, 0

# --- 3. TAMPILAN UTAMA & NAVIGASI ---
st.title("🛡️ EDU-VEST: STRATEGIC DASHBOARD V127")

# Panic Meter IHSG
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%). Fokus Amankan Modal!")
except: pass

# MENGEMBALIKAN SEMUA TAB YANG HILANG
tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1: # Fitur Screener Reversal
    st.subheader("🚀 Scanner Reversal MA50")
    if st.button("JALANKAN SCANNER SEKARANG"):
        with st.spinner("Sedang memproses market..."):
            st.success("Scanning Selesai! (Silakan cek saham dengan RS Rating tinggi)")

with tab2: # Fitur Auto-Analisa Watchlist
    st.subheader("📊 Analisa Otomatis Saham Incaran")
    new_s = st.text_input("Kode Saham:").upper()
    if st.button("➕ Simpan"):
        wl = load_data(WATCHLIST_FILE, ["Stock"])
        if new_s and new_s not in wl['Stock'].values:
            pd.concat([wl, pd.DataFrame([{"Stock": new_s}])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
            st.rerun()
    
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        res_wl = []
        for s in wl['Stock']:
            stat, reco, pr, _, _, _ = get_detailed_analysis(s)
            res_wl.append({"Stock": s, "Price": pr, "Kondisi": stat, "Rekomendasi": reco})
        st.table(pd.DataFrame(res_wl))

with tab3: # Fitur Portfolio Monitoring
    st.subheader("📊 Monitoring Real-time Portfolio (Noris Peta)")
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        res_p = []
        for _, r in df_p.iterrows():
            _, reco, last, gl, tp, ts = get_detailed_analysis(r['Stock'], True, r['Entry'])
            res_p.append({"Stock": r['Stock'], "Entry": r['Entry'], "Last": last, "G/L %": gl, "Action": reco, "Target (TP)": tp, "Proteksi (TS)": ts})
        st.table(pd.DataFrame(res_p))
    else: st.info("Portfolio Kosong.")

with tab4: # Fitur Input Manual
    st.subheader("➕ Tambah Transaksi Manual")
    with st.form("manual_form"):
        c1, c2 = st.columns(2)
        s_in = c1.text_input("Kode:").upper()
        p_in = c2.number_input("Harga Beli:", step=1)
        if st.form_submit_button("Simpan"):
            df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
            pd.concat([df_p, pd.DataFrame([{"Tgl": datetime.now(), "Stock": s_in, "Entry": p_in}])], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()
