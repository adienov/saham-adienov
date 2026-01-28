import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASHBOARD ---
st.set_page_config(page_title="EDU-VEST V139: STABLE MASTER", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham Syariah (Bisa ditambah)
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA (Updated V139) ---
def get_stock_data(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="6mo")
        if len(df) < 50: return None
        return df
    except: return None

def analyze_logic(df, mode):
    close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
    vol_now = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
    high_20 = df['High'].rolling(20).max().iloc[-2]
    
    # 1. RADAR KRISIS (Tampilkan Semua Data Tanpa Filter)
    if mode == "Radar Krisis (Lihat Semua)":
        status = "Normal"
        if rsi < 30: status = "⚠️ Oversold (Murah)"
        if rsi < 20: status = "🔥 Extreme (Sangat Murah)"
        return True, status # Selalu True agar muncul semua
        
    # 2. LOGIC REVERSAL
    elif mode == "Reversal (Pantulan)":
        if rsi < 40 and close > prev_close: return True, f"RSI {int(rsi)} + Mantul"
        
    # 3. LOGIC BREAKOUT
    elif mode == "Breakout (Ledakan)":
        if close > high_20 and vol_now > vol_avg: return True, "New High + Big Vol"
        
    # 4. LOGIC SWING
    elif mode == "Swing (Santai)":
        if close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.05) and close > prev_close: return True, "Pantul Support MA50"

    return False, "" # Tidak lolos filter

# --- 3. UI DASHBOARD ---
st.title("🛡️ EDU-VEST: STABLE MASTER V139")

# Panic Meter
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET STATUS: {chg:.2f}%")
except: pass

# --- 4. NAVIGASI TAB (KEMBALI KE STRUKTUR LAMA YANG BAPAK SUKA) ---
tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER & RADAR", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("Cari Saham Potensial")
    # Pilihan Mode dikembalikan lengkap
    mode = st.radio("Pilih Strategi:", ["Radar Krisis (Lihat Semua)", "Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    
    if st.button("JALANKAN PROSES"):
        st.write(f"⏳ Sedang memproses data dengan mode: **{mode}**...")
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(SYARIAH_TICKERS):
            progress_bar.progress((i + 1) / len(SYARIAH_TICKERS))
            df = get_stock_data(t)
            
            if df is not None:
                lolos, catatan = analyze_logic(df, mode)
                if lolos:
                    close = df['Close'].iloc[-1]
                    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
                    results.append({
                        "Stock": t.replace(".JK",""), 
                        "Price": int(close), 
                        "RSI": round(rsi, 1),
                        "Catatan/Status": catatan,
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                    })
        
        progress_bar.empty() # Hilangkan loading bar setelah selesai
        
        if results:
            # Urutkan berdasarkan RSI terendah jika mode Radar Krisis
            df_res = pd.DataFrame(results)
            if mode == "Radar Krisis (Lihat Semua)":
                df_res = df_res.sort_values(by="RSI", ascending=True)
                
            st.success(f"✅ Selesai! Ditemukan {len(df_res)} data.")
            st.data_editor(df_res, column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
        else:
            st.warning("Tidak ada saham yang memenuhi kriteria strategi ini (Wajar jika market crash). Coba mode 'Radar Krisis' untuk melihat semua data.")

with tab2:
    st.subheader("📊 Analisa Watchlist")
    if st.button("🗑️ Hapus Watchlist", type="secondary"):
        if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()
    
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        wl_data = []
        for s in wl['Stock']:
            df = get_stock_data(s)
            if df is not None:
                ma200 = df['Close'].rolling(200).mean().iloc[-1]
                p = df['Close'].iloc[-1]
                stat = "🟢 BAGUS" if p > df['Close'].rolling(50).mean().iloc[-1] else "🔴 JAUHI"
                if p < ma200: stat = "🔴 TREND RUSAK"
                wl_data.append({"Stock": s, "Price": int(p), "Status": stat})
        st.table(pd.DataFrame(wl_data))
    else: st.info("Watchlist Kosong.")

with tab3:
    st.subheader("📊 Portfolio Monitor")
    if st.button("🚨 Reset Porto", type="primary"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()
            
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            df = get_stock_data(row['Stock'])
            if df is not None:
                curr = df['Close'].iloc[-1]
                gl = ((curr - row['Entry']) / row['Entry']) * 100
                act = "🟡 HOLD"
                if gl <= -7: act = "🚨 CUT LOSS"
                elif gl >= 15: act = "🔵 TAKE PROFIT"
                
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                c1.write(f"**{row['Stock']}**")
                c2.write(f"G/L: {gl:+.2f}%")
                c3.write(f"Saran: {act}")
                if c4.button("🗑️", key=f"d{idx}"): df_p.drop(idx).to_csv(DB_FILE, index=False); st.rerun()
                st.divider()

with tab4:
    st.subheader("➕ Input Manual")
    with st.form("add_manual"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Kode:").upper()
        p = c2.number_input("Harga Beli:", step=1)
        if st.form_submit_button("Simpan"):
            pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now(), "Stock": s, "Entry": p}])], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()
