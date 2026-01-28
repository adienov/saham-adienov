import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING DASHBOARD ---
st.set_page_config(page_title="EDU-VEST V134: FINAL CONTROL", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham Syariah Default untuk Screener
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA TERPADU ---
def get_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 60: return None
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Status Teknis
        if last_p < ma200: status, reco = "Trend Rusak", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Konsolidasi", "⚪ TUNGGU"
            
        # Action Portfolio
        gl_str, action = "0%", reco
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: action = "🚨 CUT LOSS"
            elif gl_val >= 15.0: action = "🔵 TAKE PROFIT"
            elif gl_val >= 5.0: action = "🟢 HOLD (Profit)"
            else: action = "🟡 HOLD (Wait)"
            
        return {"Price": last_p, "Status": status, "Action": action, "GL": gl_str, "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"}
    except: return None

# --- 3. TAMPILAN UTAMA ---
st.title("🛡️ EDU-VEST: CONTROL DASHBOARD V134")

# Indikator Panic Meter
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%) - Cash is King!")
    elif chg <= -1.0: st.warning(f"⚠️ MARKET MERAH ({chg:.2f}%) - Hati-hati.")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

# --- 4. NAVIGASI FITUR ---
tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("🚀 Cari Saham Potensial")
    mode = st.radio("Pilih Mode:", ["Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    if st.button("JALANKAN SCANNER"):
        with st.spinner("Sedang memproses market..."):
            res = []
            for t in SYARIAH_TICKERS:
                d = get_analysis(t)
                if d and d["Status"] == "Strong Momentum": # Filter sederhana
                     res.append({"Stock": t.replace(".JK",""), "Price": d["Price"], "Status": d["Status"], "Action": d["Action"], "Chart": d["TV"]})
            if res: st.data_editor(pd.DataFrame(res), column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
            else: st.warning("Belum ada saham yang lolos filter ketat saat ini.")

with tab2:
    st.subheader("📊 Analisa Watchlist Anda")
    # Tombol Reset Watchlist (Fitur Baru)
    if st.button("🗑️ HAPUS SEMUA WATCHLIST", type="secondary"):
        if os.path.exists(WATCHLIST_FILE):
            os.remove(WATCHLIST_FILE)
            st.rerun()
            
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        res_wl = []
        for s in wl['Stock']:
            d = get_analysis(s)
            if d: res_wl.append({"Stock": s, "Price": d["Price"], "Status": d["Status"], "Rekomendasi": d["Action"]})
        st.table(pd.DataFrame(res_wl))
    else: st.info("Watchlist Kosong.")

with tab3:
    st.subheader("📊 Portfolio & Action Plan")
    col_a, col_b = st.columns([4, 1])
    # Tombol Reset Portfolio (Fitur Baru)
    if col_b.button("🚨 RESET TOTAL PORTO", type="primary"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.rerun()
            
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            d = get_analysis(row['Stock'], True, row['Entry'])
            if d:
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                c1.write(f"**{row['Stock']}**")
                c2.write(f"G/L: {d['GL']}")
                c3.write(f"Saran: {d['Action']}")
                # Tombol Hapus Per Baris (Tetap Ada)
                if c4.button("🗑️ Hapus", key=f"del_{idx}"):
                    df_p.drop(idx).to_csv(DB_FILE, index=False)
                    st.rerun()
                st.divider()
    else: st.info("Portfolio Kosong. Belum ada aset yang dicatat.")

with tab4:
    st.subheader("➕ Tambah Manual / Dari Watchlist")
    # Input dari Watchlist
    new_s = st.text_input("Kode Saham (untuk Watchlist):").upper()
    if st.button("Simpan ke Watchlist"):
        wl = load_data(WATCHLIST_FILE, ["Stock"])
        if new_s and new_s not in wl['Stock'].values:
            pd.concat([wl, pd.DataFrame([{"Stock": new_s}])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
            st.rerun()
    
    st.divider()
    
    # Input ke Portfolio
    with st.form("manual_porto"):
        st.write("**Catat Transaksi Beli (Porto)**")
        c1, c2 = st.columns(2)
        s_in = c1.text_input("Kode:").upper()
        p_in = c2.number_input("Harga Beli:", step=1)
        if st.form_submit_button("Masukan ke Portfolio"):
            df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
            pd.concat([df_p, pd.DataFrame([{"Tgl": datetime.now(), "Stock": s_in, "Entry": p_in}])], ignore_index=True).to_csv(DB_FILE, index=False)
            st.success("Tersimpan!")
            st.rerun()
