import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING UTAMA ---
st.set_page_config(page_title="EDU-VEST V142: SMART GUIDE", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA HYBRID ---
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

    # Fundamental
    roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
    per = info.get('trailingPE', 999) if info.get('trailingPE') else 999
    
    fund_status = "⚠️ Mahal/Rugi"
    if roe > 10 and per < 20: fund_status = "✅ Sehat"
    if roe > 15 and per < 15: fund_status = "💎 Super (Murah & Bagus)"

    # Filter Logic
    if mode == "Radar Krisis (Lihat Semua)": return True, fund_status, roe, per
    elif mode == "Reversal (Pantulan)":
        if rsi < 40 and close > prev_close: return True, fund_status, roe, per
    elif mode == "Breakout (Ledakan)":
        if close > high_20 and vol_now > vol_avg: return True, fund_status, roe, per
    elif mode == "Swing (Santai)":
        if close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.05) and close > prev_close: return True, fund_status, roe, per

    return False, "", 0, 0

# --- 3. ENGINE SIMPLE (WATCHLIST & PORTO) ---
def get_simple_analysis(ticker, is_portfolio=False, entry_price=0):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="6mo")
        if len(df) < 50: return None
        
        last_p = int(df['Close'].iloc[-1])
        ma50 = df['Close'].rolling(50).mean().iloc[-1]
        ma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        if last_p < ma200: status, reco = "Trend Rusak", "🔴 JAUHI"
        elif last_p > ma50: status, reco = "Strong Momentum", "🟢 BAGUS"
        else: status, reco = "Konsolidasi", "⚪ TUNGGU"
            
        gl_str, action = "0%", reco
        if is_portfolio and entry_price > 0:
            gl_val = ((last_p - entry_price) / entry_price) * 100
            gl_str = f"{gl_val:+.2f}%"
            if gl_val <= -7.0: action = "🚨 CUT LOSS"
            elif gl_val >= 15.0: action = "🔵 TAKE PROFIT"
            elif gl_val >= 5.0: action = "🟢 HOLD (Profit)"
            else: action = "🟡 HOLD"
            
        return {"Price": last_p, "Status": status, "Action": action, "GL": gl_str, "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"}
    except: return None

# --- 4. TAMPILAN DASHBOARD ---
st.title("💎 EDU-VEST: SMART GUIDE V142")

try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2, tab3, tab4 = st.tabs(["🔍 HYBRID SCREENER", "⭐ WATCHLIST", "📊 PORTO MONITOR", "➕ INPUT MANUAL"])

with tab1:
    st.subheader("Cari Saham Bagus (Teknikal + Fundamental)")
    mode = st.radio("Pilih Strategi:", ["Radar Krisis (Lihat Semua)", "Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    
    if st.button("JALANKAN ANALISA"):
        st.write(f"⏳ Mengambil data Teknikal & Fundamental untuk mode: **{mode}**...")
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
                        "Stock": t.replace(".JK",""), "Price": int(close), "RSI": round(rsi, 1),
                        "Kualitas": f_stat, "ROE (%)": round(roe, 1), "PER (x)": round(per, 1),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                    })
        progress_bar.empty()
        
        if results:
            df_res = pd.DataFrame(results)
            if mode == "Radar Krisis (Lihat Semua)": df_res = df_res.sort_values(by="ROE (%)", ascending=False)
            st.success(f"✅ Selesai! Ditemukan {len(df_res)} saham.")
            st.data_editor(df_res, column_config={"Chart": st.column_config.LinkColumn("Buka TV"), "Kualitas": st.column_config.TextColumn("Kualitas", help="Super = ROE>15 & PER<15")}, hide_index=True)
            
            # --- BAGIAN BARU: PANDUAN EKSEKUSI (SOP) ---
            st.divider()
            st.subheader("💡 PANDUAN EKSEKUSI & SINYAL")
            
            if mode == "Radar Krisis (Lihat Semua)" or mode == "Reversal (Pantulan)":
                st.warning("""
                **⚠️ STRATEGI: MENANGKAP PISAU JATUH (COUNTER TREND)**
                Saham di atas (seperti BRIS/ANTM) muncul karena **Fundamental Bagus** tapi **Harga Sedang Hancur**.
                
                **⛔ JANGAN LAKUKAN:**
                * Jangan langsung Hajar Kanan (HAKA) jika chart masih merah tebal.
                * Jangan All-in (Gunakan Money Management ketat).
                
                **✅ TUNGGU SINYAL INI (ENTRY TRIGGER):**
                1.  **Candle Hijau Pertama:** Tunggu hari besok, apakah harga ditutup hijau?
                2.  **Pola Hammer:** Muncul candle dengan ekor bawah panjang (seperti palu).
                3.  **Tindakan:** Masukkan ke WATCHLIST dulu. Cicil beli HANYA JIKA harga mulai memantul naik.
                """)
            
            elif mode == "Breakout (Ledakan)":
                st.info("""
                **🚀 STRATEGI: MENUNGGANGI OMBAK (FOLLOW TREND)**
                Saham di atas sedang kuat menembus atap (Resistance).
                
                **✅ SINYAL VALID:**
                1.  **Volume Tinggi:** Kenaikan harga disertai volume batang hijau yang tinggi.
                2.  **Tindakan:** Boleh HAKA (Beli di harga offer) atau antri di harga penutupan kemarin.
                3.  **Stop Loss:** Pasang ketat di bawah garis Breakout (3-5%).
                """)
                
            elif mode == "Swing (Santai)":
                st.success("""
                **🌊 STRATEGI: MEMBELI SAAT DISKON (PULLBACK)**
                Saham ini tren utamanya NAIK, tapi sedang istirahat sebentar.
                
                **✅ SINYAL MASUK:**
                1.  **Pantulan MA50:** Harga menyentuh garis rata-rata 50 hari lalu mental naik.
                2.  **Tindakan:** Cicil beli (Buy on Weakness) di area merah.
                """)
                
        else: st.warning("Belum ada saham yang lolos kriteria gabungan saat ini.")

# (Tab 2, 3, 4 tetap sama dengan V141)
with tab2: # Watchlist
    st.subheader("📊 Analisa Watchlist Anda")
    if st.button("🗑️ HAPUS WATCHLIST", type="secondary"):
        if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        res_wl = []
        for s in wl['Stock']:
            d = get_simple_analysis(s)
            if d: res_wl.append({"Stock": s, "Price": d["Price"], "Status": d["Status"], "Rekomendasi": d["Action"], "Chart": d["TV"]})
        st.data_editor(pd.DataFrame(res_wl), column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
    else: st.info("Watchlist Kosong.")

with tab3: # Porto
    st.subheader("📊 Portfolio & Action Plan")
    if st.button("🚨 RESET PORTO", type="primary"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            d = get_simple_analysis(row['Stock'], True, row['Entry'])
            if d:
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                c1.write(f"**{row['Stock']}**"); c2.write(f"G/L: {d['GL']}"); c3.write(f"Saran: {d['Action']}")
                if c4.button("🗑️", key=f"del_{idx}"): df_p.drop(idx).to_csv(DB_FILE, index=False); st.rerun()
                st.divider()
    else: st.info("Portfolio Kosong.")

with tab4: # Input
    st.subheader("➕ Tambah Data Manual")
    with st.form("manual"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Kode:").upper(); p = c2.number_input("Harga:", step=1)
        if st.form_submit_button("Simpan"):
             pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now(), "Stock": s, "Entry": p}])], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()
