import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="EDU-VEST REVERSAL V113", layout="wide")

DB_FILE = "trading_history.csv"
if 'history_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.history_db = pd.read_csv(DB_FILE)
    else:
        st.session_state.history_db = pd.DataFrame(columns=["Tgl", "Stock", "Syariah", "Entry", "SL/TS"])

# --- 2. ENGINE MA50 REVERSAL SCANNER ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
ALL_TICKERS = [f"{s}.JK" for s in SYARIAH_LIST] + ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "ADRO.JK"]

@st.cache_data(ttl=60)
def run_ma50_reversal(ticker_list, rs_min):
    results = []
    # Download data batch untuk RS Rating 
    data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
    rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 100: continue
            
            close = df['Close'].iloc[-1]
            low = df['Low'].iloc[-1]
            open_p = df['Open'].iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # --- LOGIKA MA50 REVERSAL ---
            # 1. Leader (CANSLIM): RS Rating >= 75 [cite: 21]
            # 2. Trend: Harga di atas MA200 (Uptrend) [cite: 28]
            # 3. Support: Low hari ini menyentuh atau mendekati MA50 (Toleransi 1%)
            # 4. Reversal: Harga tutup > Harga buka (Candle Hijau) ATAU tutup jauh di atas Low
            
            is_near_ma50 = low <= (ma50 * 1.01) and close >= (ma50 * 0.99)
            is_green_reversal = close > open_p or (close > low and (close-low)/(df['High'].iloc[-1]-low) > 0.5)
            
            if rs_val >= rs_min and close > ma200 and is_near_ma50 and is_green_reversal:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                s_name = t.replace(".JK","")
                results.append({
                    "Pilih": False, "Stock": s_name, "RS": rs_val, 
                    "Dist to MA50": f"{round(((close/ma50)-1)*100, 2)}%",
                    "Entry": int(close), "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{s_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 3. TAMPILAN ---
st.title("🏹 EDU-VEST: MA50 REVERSAL HUNTER V113")
st.info("Mencari Market Leaders yang memantul di Support MA50 (Area Koreksi Sehat).")

tab1, tab2 = st.tabs(["🔍 MA50 REVERSAL", "📊 PORTFOLIO"])

with tab1:
    rs_input = st.sidebar.slider("Min. RS Rating (Leaders)", 0, 99, 75)
    
    if st.button("🚀 SCAN PANTULAN MA50"):
        df_res = run_ma50_reversal(ALL_TICKERS, rs_input)
        if not df_res.empty:
            st.session_state.current_scan = df_res
        else:
            st.warning("Belum ada Leader yang terdeteksi mantul di MA50 saat ini.")

    if 'current_scan' in st.session_state:
        edited_df = st.data_editor(
            st.session_state.current_scan,
            column_config={"Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
                           "Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")},
            disabled=["Stock", "RS", "Dist to MA50", "Entry", "SL/TS"],
            hide_index=True, use_container_width=True
        )
        
        if st.button("💾 SIMPAN PILIHAN"):
            to_save = edited_df[edited_df["Pilih"] == True].drop(columns=["Pilih", "Chart", "RS", "Dist to MA50"])
            if not to_save.empty:
                to_save["Tgl"] = datetime.now().strftime("%Y-%m-%d")
                updated = pd.concat([st.session_state.history_db, to_save], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                updated.to_csv(DB_FILE, index=False)
                st.session_state.history_db = updated
                st.success("Berhasil disimpan ke Portfolio!")
