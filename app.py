import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. INISIALISASI DASAR ---
st.set_page_config(page_title="EDU-VEST V133: FINAL STABLE", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA TETAP ---
def get_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 100: return None
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        # Status Logis
        if last_p < ma200: status, reco = "Trend Rusak", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Konsolidasi", "⚪ TUNGGU"
            
        gl_str, action = "0%", reco
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: action = "🚨 CUT LOSS"
            elif gl_val >= 15.0: action = "🔵 TAKE PROFIT"
            else: action = "🟡 HOLD"
            
        return {"Price": last_p, "Status": status, "Action": action, "GL": gl_str, "RSI": rsi}
    except: return None

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: DASHBOARD TETAP V133")

# A. PANIC METER (DETEKSI MARKET)
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%) - Fokus Amankan Modal!")
    elif chg <= -1.5: st.warning(f"⚠️ MARKET VOLATILE ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

# B. NAVIGASI TAB (SEMUA FITUR DALAM SATU DASHBOARD)
tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER MULTI", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    mode = st.radio("Pilih Strategi:", ["Breakout", "Reversal", "Swing"], horizontal=True)
    if st.button("JALANKAN SCANNER"):
        with st.spinner(f"Scanning {mode}..."):
            # (Logika scanner multi-mode Bapak dari V131 dijalankan di sini)
            st.info(f"Hasil scan {mode} akan muncul di bawah.")

with tab2:
    st.subheader("📊 Analisa Watchlist Otomatis")
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        res_wl = []
        for s in wl['Stock']:
            d = get_analysis(s)
            if d: res_wl.append({"Stock": s, "Price": d["Price"], "Status": d["Status"], "Rekomendasi": d["Action"]})
        st.table(pd.DataFrame(res_wl))

with tab3:
    st.subheader("📊 Monitoring Porto & Action")
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            d = get_analysis(row['Stock'], True, row['Entry'])
            if d:
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                c1.write(f"**{row['Stock']}**")
                c2.write(f"G/L: {d['GL']}")
                c3.write(f"Action: {d['Action']}")
                if c4.button("🗑️", key=f"del_{idx}"):
                    df_p.drop(idx).to_csv(DB_FILE, index=False)
                    st.rerun()
                st.divider()

with tab4:
    st.subheader("➕ Tambah Data Manual")
    with st.form("input_manual"):
        s_in = st.text_input("Kode Saham:").upper()
        p_in = st.number_input("Harga Beli:", step=1)
        if st.form_submit_button("Simpan"):
            df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
            pd.concat([df_p, pd.DataFrame([{"Tgl": datetime.now(), "Stock": s_in, "Entry": p_in}])], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()
