import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V91", layout="wide")

DB_FILE = "database_tapak_naga.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Stock", "Harga BUY", "SL/TS", "Syariah"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. DATABASE EMITEN SYARIAH & LIQUID ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]
NON_SYARIAH = ["BBCA", "BBRI", "BMRI", "BBNI", "ASII", "ADRO", "PTBA", "UNVR"]

# --- 3. ENGINE SCANNER (LOGIKA LENGKAP) ---
def run_full_scan(ticker_list, rs_threshold):
    results = []
    # Download data sekaligus untuk RS Rating
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except:
        rs_map = {}

    for t in ticker_list:
        try:
            df = yf.Ticker(t).history(period="1y")
            if len(df) < 200: continue
            
            close = df['Close'].iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma150 = df['Close'].rolling(150).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            
            # Filter Mark Minervini & Tapak Naga
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                stock_name = t.replace(".JK","")
                results.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                    "Stock": stock_name,
                    "Syariah": "✅" if stock_name in SYARIAH_LIST else "❌",
                    "Harga BUY": int(close),
                    "SL/TS": int(red_line),
                    "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{stock_name}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V91")
tab1, tab2 = st.tabs(["🎯 INCARAN (SCANNER)", "🗺️ PETA (PORTFOLIO)"])

with tab1:
    # Sidebar Filter
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    
    if st.button("🚀 JALANKAN SCANNER LIVE"):
        all_tickers = [f"{s}.JK" for s in (SYARIAH_LIST + NON_SYARIAH)]
        
        with st.spinner("Menganalisa data market..."):
            df_res = run_full_scan(all_tickers, min_rs)
            
            if not df_res.empty:
                st.session_state.current_scan = df_res
                
                # HEADLINE TERINTEGRASI
                st.markdown(f"""
                    <div style="border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; background-color: #ffffff; margin-bottom: 20px;">
                        <h2 style="color: #1E3A8A; text-align: center; margin-top: 0;">NORIS TRADING SYSTEM - INCARAN TN</h2>
                        <p style="text-align: center; color: #6B7280;">Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}</p>
                        <hr>
                        <p style="font-size: 0.9rem; color: #334155;"><b>Metode:</b> Stage 2 Minervini & Buy On Breakout Tapak Naga.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # TABEL HASIL SCAN
                st.dataframe(
                    df_res, 
                    column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")},
                    use_container_width=True, 
                    hide_index=True
                )
                
                if st.button("💾 SIMPAN KE PETA (DATABASE)"):
                    updated_db = pd.concat([st.session_state.history_db, df_res], ignore_index=True).drop_duplicates(subset=['Stock'], keep='last')
                    updated_db.to_csv(DB_FILE, index=False)
                    st.session_state.history_db = updated_db
                    st.success("Tersimpan secara permanen!")
            else:
                st.warning("Tidak ada saham yang memenuhi kriteria breakout hari ini.")

with tab2:
    st.subheader("🗺️ PETA Tapak Naga (Running Portfolio)")
    if not st.session_state.history_db.empty:
        # Menampilkan data PETA yang sudah tersimpan
        st.dataframe(st.session_state.history_db, use_container_width=True, hide_index=True)
        
        # Tombol Download CSV sebagai cadangan
        csv = st.session_state.history_db.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Database (CSV)", data=csv, file_name="peta_tapak_naga.csv", mime="text/csv")
    else:
        st.info("PETA masih kosong. Silakan simpan hasil dari tab INCARAN.")
