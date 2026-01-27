import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST HYBRID V109", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE HYBRID DENGAN FILTER VOLUME ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_hybrid_v109(ticker_list, rs_min):
    results = []
    # Download data batch untuk RS Rating [cite: 34]
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 150: continue
            
            close = df['Close'].iloc[-1]
            # Logika Volume: Supply & Demand 
            vol_now = df['Volume'].iloc[-1]
            vol_ma20 = df['Volume'].rolling(20).mean().iloc[-1]
            
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # KRITERIA: RS 80+ (Leaders) [cite: 21] + Pullback (Price < MA20) + Vol Mengering
            if rs_val >= rs_min and close > ma200 and close > ma50 and close < ma20:
                if vol_now < vol_ma20: # Hanya koreksi dengan volume rendah
                    red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                    s_name = t.replace(".JK","")
                    results.append({
                        "Pilih": False,
                        "Tgl": datetime.now().strftime("%Y-%m-%d"),
                        "Stock": s_name,
                        "Syariah": "✅" if s_name in SYARIAH_LIST else "❌",
                        "Entry": int(close),
                        "RSI": round(rsi, 2),
                        "Vol Stat": "Mengering ✅",
                        "SL/TS": int(red_line),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                    })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 EDU-VEST HYBRID V109 (Volume Filter)")
st.caption("Kriteria: RS 80+ | Pullback (Price < MA20) | Volume Mengering (Vol < Vol MA20)")

tab1, tab2 = st.tabs(["🔍 HYBRID SCANNER", "📊 PORTFOLIO"])

with tab1:
    rs_threshold = st.sidebar.slider("Min. RS Rating (Standard CANSLIM = 80)", 0, 99, 80)
    
    if st.button("🚀 JALANKAN SCANNER HYBRID"):
        with st.spinner("Mencari Leaders dengan volume mengering..."):
            df_res = run_hybrid_v109(ALL_TICKERS, rs_threshold)
            if not df_res.empty:
                st.session_state.current_scan = df_res
            else:
                st.warning("Tidak ada saham Leader yang sedang pullback sehat dengan volume rendah.")

    if 'current_scan' in st.session_state:
        st.write("### 📋 Hasil Incaran (Volume Filtered):")
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")
            },
            disabled=["Tgl", "Stock", "Syariah", "Entry", "RSI", "Vol Stat", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN KE PORTFOLIO"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RSI", "Vol Stat"])
            if not to_save.empty:
                updated = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Berhasil disimpan!")

with tab2:
    st.subheader("📊 Portfolio EDU-VEST")
    if not st.session_state.history_db.empty:
        # Menampilkan tabel portfolio dengan G/L% real-time
        db_show = st.session_state.history_db
        track_list = []
        for _, row in db_show.iterrows():
            try:
                curr_p = yf.Ticker(f"{row['Stock']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr_p - row['Entry']) / row['Entry']) * 100
                track_list.append({
                    "Tgl": row['Tgl'], "Stock": row['Stock'], "Syariah": row['Syariah'],
                    "Entry": row['Entry'], "Last": int(curr_p),
                    "G/L%": f"{'🟢' if gain >= 0 else '🔴'} {gain:+.2f}%", "SL/TS": row['SL/TS']
                })
            except: pass
        st.dataframe(pd.DataFrame(track_list), use_container_width=True, hide_index=True)
    else: st.info("Portfolio masih kosong.")
        
