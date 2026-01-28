import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASHBOARD ---
st.set_page_config(page_title="EDU-VEST V136: SMART LOADER", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham Syariah
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA UMUM ---
def get_general_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 60: return None
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        if last_p < ma200: status, reco = "Trend Rusak", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Konsolidasi", "⚪ TUNGGU"
            
        gl_str, action = "0%", reco
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: action = "🚨 CUT LOSS"
            elif gl_val >= 15.0: action = "🔵 TAKE PROFIT"
            elif gl_val >= 5.0: action = "🟢 HOLD"
            else: action = "🟡 HOLD"
            
        return {"Price": last_p, "Status": status, "Action": action, "GL": gl_str}
    except: return None

# --- 3. ENGINE SCREENER SPESIFIK ---
def run_specific_screener(mode):
    results = []
    for t in SYARIAH_TICKERS:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="6mo")
            if len(df) < 50: continue
            
            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            vol_now = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
            high_20 = df['High'].rolling(20).max().iloc[-2]
            
            match = False
            note = ""
            
            # LOGIC REVERSAL
            if mode == "Reversal (Pantulan)":
                if rsi < 40 and close > prev_close:
                    match = True
                    note = f"RSI Jenuh ({int(rsi)}) + Rebound Candle"
            
            # LOGIC BREAKOUT
            elif mode == "Breakout (Ledakan)":
                if close > high_20 and vol_now > vol_avg:
                    match = True
                    note = "New High 20 Hari + Volume Spike"
            
            # LOGIC SWING
            elif mode == "Swing (Santai)":
                if close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.05) and close > prev_close:
                    match = True
                    note = "Pantulan Sehat di Support MA50"

            if match:
                results.append({
                    "Stock": t.replace(".JK",""), "Price": int(close), 
                    "Mode": mode.split()[0], "Alasan Teknis": note,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: SMART LOADER V136")

try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%) - Cash is King!")
    elif chg <= -1.0: st.warning(f"⚠️ MARKET MERAH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER SPESIFIK", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("🚀 Cari Saham Sesuai Strategi")
    mode = st.radio("Pilih Strategi:", ["Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    
    if st.button("JALANKAN SCANNER"):
        # --- LOGIC TEXT EDUKATIF DI SINI ---
        if mode == "Reversal (Pantulan)":
            msg = "🔍 Sedang mencari saham Jenuh Jual (RSI < 40) yang mulai melawan naik..."
        elif mode == "Breakout (Ledakan)":
            msg = "🚀 Sedang mendeteksi saham yang menembus High 20 Hari Terakhir dengan Volume Tinggi..."
        else:
            msg = "🌊 Sedang memindai saham Uptrend (di atas MA50) yang koreksi sehat ke Support..."
            
        with st.spinner(msg): # Pesan loading berubah sesuai strategi
            df_res = run_specific_screener(mode)
            if not df_res.empty:
                st.success(f"Ditemukan {len(df_res)} saham sesuai kriteria {mode}!")
                st.data_editor(df_res, column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
            else:
                st.warning(f"Tidak ada saham yang lolos. (Artinya: Belum ada saham yang memenuhi syarat '{msg}')")

with tab2:
    st.subheader("📊 Analisa Watchlist")
    if st.button("🗑️ HAPUS WATCHLIST", type="secondary"):
        if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()
            
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        res = [get_general_analysis(s) for s in wl['Stock']]
        st.table(pd.DataFrame([r for r in res if r]))

with tab3:
    st.subheader("📊 Portfolio Monitor")
    if st.button("🚨 RESET PORTO", type="primary"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()
            
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            d = get_general_analysis(row['Stock'], True, row['Entry'])
            if d:
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                c1.write(f"**{row['Stock']}**"); c2.write(f"G/L: {d['GL']}"); c3.write(f"Saran: {d['Action']}")
                if c4.button("🗑️", key=f"d{idx}"): df_p.drop(idx).to_csv(DB_FILE, index=False); st.rerun()
                st.divider()

with tab4:
    st.subheader("➕ Input Data")
    with st.form("in"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Kode:").upper()
        p = c2.number_input("Harga:", step=1)
        if st.form_submit_button("Simpan Porto"):
            pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now(), "Stock": s, "Entry": p}])], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()
