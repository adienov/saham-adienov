import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING UTAMA ---
st.set_page_config(page_title="EDU-VEST V140: HYBRID MASTER", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham Syariah (Bisa ditambah)
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE HYBRID (TEKNIKAL + FUNDAMENTAL) ---
def get_hybrid_data(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="6mo")
        info = t.info # Ambil data fundamental
        if len(df) < 50: return None, None
        return df, info
    except: return None, None

def analyze_hybrid_logic(df, info, mode):
    # Data Teknikal
    close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
    vol_now = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
    high_20 = df['High'].rolling(20).max().iloc[-2]

    # Data Fundamental (Kunci V140)
    roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
    per = info.get('trailingPE', 999) if info.get('trailingPE') else 999 # Default 999 jika rugi
    
    # Status Fundamental
    fund_status = "⚠️ Mahal/Rugi"
    if roe > 10 and per < 20: fund_status = "✅ Sehat"
    if roe > 15 and per < 15: fund_status = "💎 Super (Murah & Bagus)"

    # LOGIKA FILTER
    if mode == "Radar Krisis (Lihat Semua)":
        # Tampilkan semua, tapi beri label fundamental
        return True, fund_status, roe, per
        
    elif mode == "Reversal (Pantulan)":
        if rsi < 40 and close > prev_close: 
            return True, fund_status, roe, per
        
    elif mode == "Breakout (Ledakan)":
        if close > high_20 and vol_now > vol_avg: 
            return True, fund_status, roe, per
        
    elif mode == "Swing (Santai)":
        if close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.05) and close > prev_close: 
            return True, fund_status, roe, per

    return False, "", 0, 0 # Tidak lolos

# --- 3. UI DASHBOARD ---
st.title("💎 EDU-VEST: HYBRID MASTER V140")

# Panic Meter
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2, tab3, tab4 = st.tabs(["🔍 HYBRID SCREENER", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("Cari Saham Bagus (Teknikal + Fundamental)")
    mode = st.radio("Pilih Strategi:", ["Radar Krisis (Lihat Semua)", "Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    
    if st.button("JALANKAN ANALISA"):
        st.write(f"⏳ Mengambil data Teknikal & Fundamental untuk mode: **{mode}**...")
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(SYARIAH_TICKERS):
            progress_bar.progress((i + 1) / len(SYARIAH_TICKERS))
            df, info = get_hybrid_data(t)
            
            if df is not None and info is not None:
                lolos, f_stat, roe, per = analyze_hybrid_logic(df, info, mode)
                
                if lolos:
                    close = df['Close'].iloc[-1]
                    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
                    
                    # Tambahkan data Fundamental ke Tabel
                    results.append({
                        "Stock": t.replace(".JK",""), 
                        "Price": int(close),
                        "RSI": round(rsi, 1),
                        "Fundamental": f_stat,
                        "ROE (%)": round(roe, 1),
                        "PER (x)": round(per, 1),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                    })
        
        progress_bar.empty()
        
        if results:
            df_res = pd.DataFrame(results)
            # Sorting cerdas: Jika Radar Krisis, urutkan berdasarkan ROE Tertinggi (Cari mutiara terpendam)
            if mode == "Radar Krisis (Lihat Semua)":
                df_res = df_res.sort_values(by="ROE (%)", ascending=False)
                
            st.success(f"✅ Selesai! Ditemukan {len(df_res)} saham.")
            st.data_editor(
                df_res, 
                column_config={
                    "Chart": st.column_config.LinkColumn("Buka TV"),
                    "Fundamental": st.column_config.TextColumn("Kualitas", help="Super = ROE>15 & PER<15"),
                }, 
                hide_index=True
            )
        else:
            st.warning("Belum ada saham yang lolos kriteria gabungan saat ini.")

# (Bagian Tab 2, 3, 4 tetap menggunakan struktur stabil V139)
with tab2:
    st.info("Fitur Watchlist (Logic V139)")
    # ... (Copy logic Tab 2 dari V139)
with tab3:
    st.info("Fitur Porto (Logic V139)")
    # ... (Copy logic Tab 3 dari V139)
with tab4:
    # ... (Copy logic Tab 4 dari V139)
    with st.form("manual"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Kode:").upper()
        p = c2.number_input("Harga:", step=1)
        if st.form_submit_button("Simpan"):
             pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now(), "Stock": s, "Entry": p}])], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()
