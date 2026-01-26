import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Noris Trading System V68", layout="wide", initial_sidebar_state="expanded")

# --- 2. DATABASE SESSION (PENYIMPAN HASIL SCAN) ---
if 'history_db' not in st.session_state:
    # Tabel untuk menyimpan saham yang pernah direkomendasikan scanner
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])

# --- 3. SIDEBAR PARAMETER (BASIS V59) ---
st.sidebar.title("⚙️ Parameter & Database")
modal_jt = st.sidebar.number_input("Modal (Juta Rp)", value=100)
st.sidebar.divider()

# Tombol Clear Database jika ingin reset histori
if st.sidebar.button("🗑️ Reset Histori Scanner"):
    st.session_state.history_db = pd.DataFrame(columns=["Tanggal", "Emiten", "Harga_Awal", "SL_Awal", "Status_Awal"])
    st.sidebar.success("Histori berhasil dihapus.")

# ... (Daftar Ticker LQ45/Kompas100 sesuai V59 Bapak tetap di sini) ...
lq45_tickers = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK", "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK", "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK", "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK", "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "GOTO.JK"]

# --- 4. ENGINE SCANNER (BASIS V59) ---
@st.cache_data(ttl=300)
def scan_market(ticker_list):
    results = []
    try:
        data_batch = yf.download(ticker_list, period="1y", progress=False)['Close']
        rs_map = (data_batch.iloc[-1]/data_batch.iloc[0]-1).rank(pct=True).to_dict()
    except: rs_map = {}

    for ticker in ticker_list:
        try:
            df = yf.Ticker(ticker).history(period="1y")
            close = df['Close'].iloc[-1]
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma150 = df['Close'].rolling(150).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            rs_rating = int(rs_map.get(ticker, 0.5) * 99)
            
            # Kriteria Stage 2 V59
            if close > ma150 and ma150 > ma200 and close > ma50 and rs_rating >= 70:
                red_line = ta.sma((df['High']+df['Low'])/2, 8).iloc[-1]
                if close > red_line:
                    results.append({
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Emiten": ticker.replace(".JK",""),
                        "Harga_Awal": int(close),
                        "SL_Awal": int(red_line),
                        "Status_Awal": "🚀 BREAKOUT" if close > df['High'].rolling(20).max().shift(1).iloc[-1] else "🟢 REVERSAL"
                    })
        except: continue
    return pd.DataFrame(results)

# --- 5. TAMPILAN UTAMA ---
st.title("📈 Noris Trading System V68")

tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 PERFORMANCE TRACKER (DATABASE)"])

with tab1:
    if st.button("🚀 JALANKAN SCANNER HARI INI"):
        df_today = scan_market(lq45_tickers)
        if not df_today.empty:
            st.subheader("📋 Saham Lolos Kriteria Hari Ini")
            st.dataframe(df_today, use_container_width=True, hide_index=True)
            
            if st.button("💾 SIMPAN SEMUA HASIL KE DATABASE"):
                st.session_state.history_db = pd.concat([st.session_state.history_db, df_today], ignore_index=True).drop_duplicates(subset=['Emiten'], keep='last')
                st.success("Data berhasil disimpan! Cek Tab Performance Tracker untuk melihat kenaikannya.")
        else:
            st.warning("Tidak ada saham lolos kriteria hari ini.")

with tab2:
    st.subheader("📈 Day-by-Day Performance Tracker")
    st.caption("Memantau kenaikan/penurunan saham sejak pertama kali direkomendasikan oleh scanner.")
    
    if not st.session_state.history_db.empty:
        db = st.session_state.history_db.copy()
        
        # Ambil Harga Live untuk Tracking
        live_results = []
        for index, row in db.iterrows():
            try:
                ticker_live = yf.Ticker(f"{row['Emiten']}.JK")
                current_price = ticker_live.history(period="1d")['Close'].iloc[-1]
                pnl_pct = ((current_price - row['Harga_Awal']) / row['Harga_Awal']) * 100
                
                live_results.append({
                    "Tgl Rekom": row['Tanggal'],
                    "Emiten": row['Emiten'],
                    "Harga Entry": f"Rp {row['Harga_Awal']:,}",
                    "Harga Saat Ini": f"Rp {current_price:,.0f}",
                    "% Profit/Loss": round(pnl_pct, 2),
                    "Status": "✅ CUAN" if pnl_pct > 0 else "❌ LOSS"
                })
            except: continue
            
        df_track = pd.DataFrame(live_results)
        
        # Styling Warna
        def color_pnl(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}; font-weight: bold'
        
        st.dataframe(df_track.style.applymap(color_pnl, subset=['% Profit/Loss']), use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong. Silakan jalankan scanner dan klik 'Simpan' di Tab Live Scanner.")
