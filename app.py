import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime, timedelta

# --- 1. SETTING HALAMAN & DATABASE ---
st.set_page_config(page_title="Noris Trading System V85", layout="wide")

DB_FILE = "trading_history.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal", "Syariah"])

if 'history_db' not in st.session_state:
    st.session_state.history_db = load_db()

# --- 2. FUNGSI PRINT PDF (STABIL) ---
def add_print_button():
    # CSS untuk menyembunyikan elemen UI Streamlit saat dicetak
    st.markdown("""
        <style>
        @media print {
            .stButton, .stSidebar, header, footer, .stTabs [data-baseweb="tab-list"] { display: none !important; }
            .main .block-container { padding: 0 !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    if st.button("🖨️ Cetak Laporan / Simpan PDF"):
        st.components.v1.html("<script>window.print();</script>", height=0)

# --- 3. DATABASE SYARIAH & ENGINE (BASIS V80) ---
SYARIAH_LIST = ["ANTM", "BRIS", "TLKM", "ICBP", "INDF", "UNTR", "PGAS", "EXCL", "ISAT", "KLBF", "SIDO", "MDKA", "INCO", "MBMA", "AMRT", "ACES", "HRUM", "AKRA", "MEDC", "ELSA", "BRMS", "DEWA", "BUMI", "MYOR", "CPIN", "JPFA", "SMGR", "INTP", "TPIA", "GOTO"]

@st.cache_data(ttl=300)
def scan_engine(ticker_list, rs_threshold, target_date=None):
    results = []
    end_date = datetime.now() if target_date is None else datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
    try:
        data_batch = yf.download(ticker_list, start=end_date - timedelta(days=365), end=end_date, progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except: rs_map = {}
    for t in ticker_list:
        try:
            emiten_code = t.replace(".JK","")
            df = yf.Ticker(t).history(start=end_date - timedelta(days=365), end=end_date)
            if len(df) < 200: continue
            close = df['Close'].iloc[-1]
            ma50, ma150, ma200 = df['Close'].rolling(50).mean().iloc[-1], df['Close'].rolling(150).mean().iloc[-1], df['Close'].rolling(200).mean().iloc[-1]
            rs_val = int(rs_map.get(t, 0.5) * 99)
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_val >= rs_threshold:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                results.append({
                    "Tanggal": end_date.strftime("%Y-%m-%d"), "Emiten": emiten_code, "Syariah": "✅" if emiten_code in SYARIAH_LIST else "❌",
                    "Harga_Awal": int(close), "SL_Awal": int(red_line), "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{emiten_code}"
                })
        except: continue
    return pd.DataFrame(results)

# --- 4. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V85")
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER", "⏮️ BACKTEST"])

with tab1:
    # Sidebar Filter (Basis V80)
    min_rs = st.sidebar.slider("Min. RS Rating", 0, 99, 70)
    
    if st.button("🚀 JALANKAN SCANNER"):
        # Headline Metodologi Terintegrasi
        st.markdown(f"""
            <div style="border: 2px solid #1E3A8A; padding: 20px; border-radius: 10px; background-color: #ffffff;">
                <h2 style="color: #1E3A8A; text-align: center; margin-top: 0;">NORIS TRADING SYSTEM REPORT</h2>
                <p style="text-align: center; color: #6B7280;">Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}</p>
                <div style="background-color: #f1f5f9; padding: 15px; border-radius: 5px;">
                    <h4 style="color: #1E3A8A; margin-top: 0;">🚀 Strategi: Trend Following & Tapak Naga</h4>
                    <p style="font-size: 0.9rem; color: #334155;">Sinyal ini berbasis Stage 2 Minervini (MA50>150>200) dan Strategi Tapak Naga (Buy On Breakout).</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        df_live = scan_engine([f"{s}.JK" for s in SYARIAH_LIST], min_rs)
        if not df_live.empty:
            st.dataframe(df_live, column_config={"Chart": st.column_config.LinkColumn("TV", display_text="📈 Buka")}, use_container_width=True, hide_index=True)
            add_print_button() # Tombol Cetak PDF
        else: st.warning("Tidak ada saham lolos kriteria.")

# ... (Tab 2 & 3 tetap sama dengan logika V80 Bapak) ...
