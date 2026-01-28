import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. INISIALISASI DATABASE ---
st.set_page_config(page_title="EDU-VEST ALL-IN-ONE V128", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar saham Syariah Bapak (ANTM, BRIS, TLKM, dll)
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA ---
def get_detailed_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 50: return "Data Kurang", "⚪", 0, "0%", 0, 0
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        if last_p < ma200: status, reco = "Trend Rusak (Below MA200)", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Fase Konsolidasi", "⚪ TUNGGU"
            
        gl_str, tp, ts = "0%", 0, 0
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            tp, ts = int(entry_price * 1.15), int(last_p * 0.95)
            if gl_val <= -7.0: reco = "🚨 SELL (Cut Loss)"
            elif gl_val >= 15.0: reco = "🔵 TAKE PROFIT"
            elif gl_val >= 5.0: reco = "🟢 HOLD (TS Active)"
            else: reco = "🟡 HOLD (Wait)"
            
        return status, reco, last_p, gl_str, tp, ts
    except: return "Error", "❌", 0, "0%", 0, 0

# --- 3. TAMPILAN UTAMA & NAVIGASI ---
st.title("🛡️ EDU-VEST: STRATEGIC DASHBOARD V128")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("🚀 Scanner Reversal Syariah")
    if st.button("JALANKAN SCANNER SEKARANG"):
        with st.spinner("Memproses data market Syariah..."):
            scan_results = []
            for t in SYARIAH_TICKERS:
                status, reco, pr, _, _, _ = get_detailed_analysis(t)
                if reco == "🟢 BAGUS":
                    scan_results.append({"Stock": t.replace(".JK",""), "Price": pr, "Status": status, "Action": reco})
            
            if scan_results:
                st.table(pd.DataFrame(scan_results))
            else:
                st.warning("Tidak ada saham syariah yang memenuhi kriteria Strong Momentum saat ini.")

with tab2:
    st.subheader("📊 Analisa Watchlist")
    new_s = st.text_input("Tambah Kode:").upper()
    if st.button("➕ Simpan ke Watchlist"):
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

with tab3:
    st.subheader("📊 Monitoring Porto (Hapus Manual Aktif)")
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for index, row in df_p.iterrows():
            _, reco, last, gl, tp, ts = get_detailed_analysis(row['Stock'], True, row['Entry'])
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])
            col1.write(f"**{row['Stock']}**")
            col2.write(f"G/L: {gl}")
            col3.write(f"Action: {reco}")
            col4.write(f"TP: {tp} | TS: {ts}")
            # Fitur Hapus Manual per baris
            if col5.button(f"🗑️", key=f"del_{row['Stock']}"):
                df_p = df_p.drop(index)
                df_p.to_csv(DB_FILE, index=False)
                st.rerun()
            st.divider()
    else: st.info("Portfolio Kosong.")

with tab4:
    st.subheader("➕ Tambah Transaksi Manual")
    with st.form("manual_form"):
        c1, c2 = st.columns(2)
        s_in = c1.text_input("Kode:").upper()
        p_in = c2.number_input("Harga Beli:", step=1)
        if st.form_submit_button("Simpan ke Porto"):
            df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
            new_data = pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Stock": s_in, "Entry": p_in}])
            pd.concat([df_p, new_data], ignore_index=True).to_csv(DB_FILE, index=False)
            st.success("Berhasil disimpan!")
