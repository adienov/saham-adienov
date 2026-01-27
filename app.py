import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V104", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        return df.loc[:, ~df.columns.duplicated()]
    return pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=300)
def run_scanner_v104(ticker_list, rs_threshold):
    results = []
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
        for t in ticker_list:
            df = yf.Ticker(t).history(period="1y")
            if len(df) < 200: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1] # Filter Baru
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma150 = df['Close'].rolling(150).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # KRITERIA: Stage 2 + Kekuatan Jangka Pendek (MA20)
            if close > ma20 and close > ma50 and ma150 > ma200 and close > ma150 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False, 
                    "Tgl": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": s_name,
                    "Syariah": "✅" if s_name in SYARIAH_LIST else "❌",
                    "Entry": int(close),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
    except: pass
    return pd.DataFrame(results)

# --- 3. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V104")
tab1, tab2 = st.tabs(["🔍 NORIS INCARAN", "📊 NORIS PETA (PORTFOLIO)"])

with tab1:
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    if st.button("🚀 JALANKAN SCANNER"):
        with st.spinner("Sedang memfilter market dengan MA20..."):
            df_res = run_scanner_v104(TICKERS, min_rs)
            if not df_res.empty:
                st.session_state.current_scan = df_res
            else: st.warning("Tidak ada saham yang memenuhi kriteria (termasuk filter MA20).")

    if 'current_scan' in st.session_state:
        st.write("### 📋 Hasil Incaran (Sudah Filter MA20):")
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                "Chart": st.column_config.LinkColumn("TradingView", display_text="📈 Buka")
            },
            disabled=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"],
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("💾 SIMPAN SAHAM TERPILIH"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart"])
            if not to_save.empty:
                current_db = load_db()
                updated_db = pd.concat([current_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated_db.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated_db
                st.success(f"✅ {len(to_save)} Saham berhasil masuk ke Peta!")
            else: st.warning("Centang saham yang ingin disimpan.")

with tab2:
    st.subheader("📊 Noris Peta (Portfolio)")
    db_show = load_db()
    if not db_show.empty:
        final_list = []
        for _, row in db_show.iterrows():
            try:
                curr_p = yf.Ticker(f"{row['Stock']}.JK").history(period="1d")['Close'].iloc[-1]
                gain = ((curr_p - row['Entry']) / row['Entry']) * 100
                final_list.append({
                    "Tgl": row['Tgl'], "Stock": row['Stock'], "Syariah": row['Syariah'],
                    "Entry": row['Entry'], "Last": int(curr_p),
                    "G/L%": f"{'🟢' if gain >= 0 else '🔴'} {gain:+.2f}%", "SL/TS": row['SL/TS']
                })
            except: pass
        st.dataframe(pd.DataFrame(final_list), use_container_width=True, hide_index=True)
        
        if st.button("🗑️ RESET PETA"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])
            st.rerun()
    else: st.info("Peta Kosong.")
