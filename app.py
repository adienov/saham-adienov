import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING UTAMA ---
st.set_page_config(page_title="EDU-VEST V144: TECHNICAL WATCHLIST", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE HYBRID (TAB 1 - TETAP SAMA) ---
def get_hybrid_data(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="6mo")
        info = t.info 
        if len(df) < 50: return None, None
        return df, info
    except: return None, None

def analyze_hybrid_logic(df, info, mode):
    close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
    vol_now = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
    high_20 = df['High'].rolling(20).max().iloc[-2]

    roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
    per = info.get('trailingPE', 999) if info.get('trailingPE') else 999
    
    fund_status = "⚠️ Mahal/Rugi"
    if roe > 10 and per < 20: fund_status = "✅ Sehat"
    if roe > 15 and per < 15: fund_status = "💎 Super (Murah & Bagus)"

    if mode == "Radar Krisis (Lihat Semua)": return True, fund_status, roe, per
    elif mode == "Reversal (Pantulan)":
        if rsi < 40 and close > prev_close: return True, fund_status, roe, per
    elif mode == "Breakout (Ledakan)":
        if close > high_20 and vol_now > vol_avg: return True, fund_status, roe, per
    elif mode == "Swing (Santai)":
        if close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.05) and close > prev_close: return True, fund_status, roe, per

    return False, "", 0, 0

# --- 3. ENGINE DETAIL TEKNIKAL (KHUSUS TAB 2 - BARU!) ---
def get_technical_detail(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 200: return None
        
        close = df['Close'].iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        vol_now = df['Volume'].iloc[-1]
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        
        # A. ANALISA TREND (MA)
        if close > ma50 and ma50 > ma200: trend = "🚀 Strong Uptrend"
        elif close > ma200: trend = "📈 Uptrend (Koreksi)"
        elif close < ma200: trend = "📉 Downtrend (Bearish)"
        else: trend = "➡️ Sideways"
        
        # B. ANALISA RSI (TIMING)
        if rsi < 30: rsi_stat = f"🔥 {int(rsi)} (Diskon)"
        elif rsi > 70: rsi_stat = f"⚠️ {int(rsi)} (Mahal)"
        else: rsi_stat = f"{int(rsi)} (Netral)"
        
        # C. ANALISA VOLUME (BANDAR)
        vol_ratio = vol_now / vol_avg
        if vol_ratio > 1.5: vol_stat = f"Ramai ({vol_ratio:.1f}x)"
        elif vol_ratio < 0.6: vol_stat = "Sepi"
        else: vol_stat = "Normal"
        
        # D. ACTION CALL
        action = "⚪ WAIT"
        
        # Skenario 1: Buy on Support (Trend Naik, Harga Dekat MA50)
        dist_ma50 = abs(close - ma50)/ma50
        if "Uptrend" in trend and dist_ma50 < 0.03:
             action = "🟢 BUY ON SUPPORT"
             
        # Skenario 2: Catch the Bottom (Trend Turun, tapi RSI Murah Banget)
        elif "Downtrend" in trend and rsi < 30:
             action = "👀 WATCH REVERSAL"
             
        # Skenario 3: Breakout (Volume Meledak)
        elif vol_ratio > 2.0 and close > df['Open'].iloc[-1]:
             action = "🔥 POTENTIAL BREAKOUT"

        return {
            "Price": int(close),
            "Trend": trend,
            "RSI Status": rsi_stat,
            "Volume": vol_stat,
            "Sinyal": action,
            "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
        }
    except: return None

# --- ENGINE PORTO (SEDERHANA) ---
def get_porto_analysis(ticker, entry_price):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1mo")
        last_p = int(df['Close'].iloc[-1])
        gl_val = ((last_p - entry_price) / entry_price) * 100
        action = "Hold"
        if gl_val <= -7: action = "🚨 CUT LOSS"
        elif gl_val >= 15: action = "🔵 TAKE PROFIT"
        return last_p, f"{gl_val:+.2f}%", action
    except: return 0, "0%", "-"

# --- 4. TAMPILAN DASHBOARD ---
st.title("💎 EDU-VEST: TECHNICAL WATCHLIST V144")

# Panic Meter
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER (HYBRID)", "⭐ WATCHLIST (TEKNIKAL)", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

# --- TAB 1: SCREENER (LOGIC V143 - TETAP) ---
with tab1:
    st.subheader("Saringan 1: Cari Saham Bagus")
    mode = st.radio("Pilih Strategi:", ["Radar Krisis (Lihat Semua)", "Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    
    if 'scan_results' not in st.session_state: st.session_state['scan_results'] = None

    if st.button("JALANKAN ANALISA"):
        st.write(f"⏳ Scanning...")
        results = []
        progress_bar = st.progress(0)
        for i, t in enumerate(SYARIAH_TICKERS):
            progress_bar.progress((i + 1) / len(SYARIAH_TICKERS))
            df, info = get_hybrid_data(t)
            if df is not None and info is not None:
                lolos, f_stat, roe, per = analyze_hybrid_logic(df, info, mode)
                if lolos:
                    close = df['Close'].iloc[-1]
                    rsi = ta.rsi(df['Close'], length=14).iloc[-1]
                    results.append({
                        "Pilih": False, "Stock": t.replace(".JK",""), "Price": int(close),
                        "Kualitas": f_stat, "ROE (%)": round(roe, 1), "PER (x)": round(per, 1),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                    })
        progress_bar.empty()
        if results:
            df_res = pd.DataFrame(results)
            if mode == "Radar Krisis (Lihat Semua)": df_res = df_res.sort_values(by="ROE (%)", ascending=False)
            st.session_state['scan_results'] = df_res
        else: st.warning("Belum ada saham yang lolos.")

    if st.session_state['scan_results'] is not None:
        edited_df = st.data_editor(st.session_state['scan_results'], column_config={"Pilih": st.column_config.CheckboxColumn("Add WL?"), "Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
        if st.button("💾 SIMPAN KE WATCHLIST"):
            selected = edited_df[edited_df["Pilih"] == True]["Stock"].tolist()
            if selected:
                wl = load_data(WATCHLIST_FILE, ["Stock"])
                new = [s for s in selected if s not in wl["Stock"].values]
                if new: pd.concat([wl, pd.DataFrame([{"Stock": s} for s in new])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False); st.success("Disimpan!"); st.rerun()

# --- TAB 2: WATCHLIST (LOGIC BARU - TEKNIKAL MURNI) ---
with tab2:
    st.subheader("Saringan 2: Pantauan Teknikal & Timing")
    st.caption("Saham di sini sudah lolos seleksi fundamental. Fokus kita sekarang adalah: Tren, Tenaga (RSI), dan Volume.")
    
    if st.button("🗑️ BERSIHKAN WATCHLIST", type="secondary"):
        if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()
            
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        wl_data = []
        for s in wl['Stock']:
            d = get_technical_detail(s) # Panggil Logic Baru
            if d:
                wl_data.append({
                    "Stock": s,
                    "Price": d['Price'],
                    "Tren (MA)": d['Trend'],     # Kolom Baru
                    "RSI (Tenaga)": d['RSI Status'], # Kolom Baru
                    "Volume": d['Volume'],       # Kolom Baru
                    "Sinyal Action": d['Sinyal'], # Kolom Baru
                    "Chart": d['TV']
                })
        
        # Tampilkan Tabel Teknikal Lengkap
        st.data_editor(
            pd.DataFrame(wl_data),
            column_config={
                "Chart": st.column_config.LinkColumn("Buka TV"),
                "Sinyal Action": st.column_config.TextColumn("Rekomendasi", help="Saran teknikal berdasarkan posisi harga"),
                "RSI (Tenaga)": st.column_config.TextColumn("Momentum", help="<30 = Diskon, >70 = Mahal"),
            },
            hide_index=True
        )
    else: st.info("Watchlist Kosong. Silakan pilih saham dari Tab Screener.")

# --- TAB 3: PORTO (SIMPLE) ---
with tab3:
    st.subheader("Monitoring Portfolio")
    if st.button("🚨 RESET PORTO"): os.remove(DB_FILE) if os.path.exists(DB_FILE) else None; st.rerun()
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            last, gl, act = get_porto_analysis(row['Stock'], row['Entry'])
            c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
            c1.write(f"**{row['Stock']}**"); c2.write(f"G/L: {gl}"); c3.write(f"Action: {act}")
            if c4.button("🗑️", key=f"del_{idx}"): df_p.drop(idx).to_csv(DB_FILE, index=False); st.rerun()
            st.divider()

# --- TAB 4: INPUT (SIMPLE) ---
with tab4:
    with st.form("manual"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Kode:").upper(); p = c2.number_input("Harga:", step=1)
        if st.form_submit_button("Simpan"):
             pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now(), "Stock": s, "Entry": p}])], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()
