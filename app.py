import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V72", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. SIDEBAR PARAMETER ---
st.sidebar.title("⚙️ Parameter & Database")
input_mode = st.sidebar.radio("Sumber Saham:", ["LQ45 (Bluechip)", "Kompas100 (Market Wide)", "Input Manual"])

lq45_tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK", "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "GOTO.JK"]

if input_mode == "LQ45 (Bluechip)": tickers = lq45_tickers
else: tickers = lq45_tickers 

min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)

if st.sidebar.button("🗑️ Reset Database Permanen"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])
    st.rerun()

# --- 3. ENGINE SCANNER ---
@st.cache_data(ttl=300)
def scan_market_v72(ticker_list, rs_threshold):
    results = []
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()

    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(period="1y")
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                if close > red_line:
                    results.append({
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Emiten": t.replace(".JK",""),
                        "Harga_Awal": int(close),
                        "SL_Awal": int(red_line),
                        "Status_Awal": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL"
                    })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V72")

tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER"])

with tab1:
    if st.button("🚀 JALANKAN SCANNER"):
        df_res = scan_market_v72(tickers, min_rs)
        if not df_res.empty:
            st.session_state.temp_scan = df_res # Simpan sementara
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        else: st.warning("Tidak ada saham lolos kriteria.")

    # Tombol Simpan diletakkan di luar tombol scan agar tidak hilang
    if 'temp_scan' in st.session_state:
        if st.button("💾 SIMPAN HASIL SCAN KE DATABASE"):
            new_db = pd.concat([st.session_state.history_db, st.session_state.temp_scan], ignore_index=True).drop_duplicates(subset=['Emiten'], keep='last')
            new_db.to_csv(DB_FILE, index=False)
            st.session_state.history_db = new_db
            st.success(f"Berhasil menyimpan {len(st.session_state.temp_scan)} saham ke database!")

with tab2:
    st.subheader("📈 Day-by-Day Tracking")
    db = st.session_state.history_db
    if not db.empty:
        track_data = []
        for _, row in db.iterrows():
            try:
                curr = yf.Ticker(f"{row['Emiten']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr - row['Harga_Awal']) / row['Harga_Awal']) * 100
                track_data.append({
                    "Tgl Rekom": row['Tanggal'], "Emiten": row['Emiten'], "Entry": int(row['Harga_Awal']),
                    "Last": int(curr), "% G/L": round(gain, 2), "Status": "✅ CUAN" if gain > 0 else "❌ LOSS",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{row['Emiten']}"
                })
            except: pass
        
        # Tampilkan Tabel Performance dengan Link TradingView
        st.dataframe(pd.DataFrame(track_data), column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong. Silakan Scan lalu klik 'Simpan' di tab Live Scanner.")
