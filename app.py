import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING UTAMA ---
st.set_page_config(page_title="EDU-VEST V145: TRANSPARENT WL", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE HYBRID (TAB 1) ---
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

# --- 3. ENGINE DETAIL TEKNIKAL & TIMING (TAB 2 - DIPERJELAS) ---
def get_technical_detail(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 200: return None
        
        close = int(df['Close'].iloc[-1])
        high_yest = int(df['High'].iloc[-2]) # High Kemarin (Untuk Reversal)
        ma50 = int(df['Close'].rolling(50).mean().iloc[-1])
        ma200 = int(df['Close'].rolling(200).mean().iloc[-1])
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        # A. ANALISA TREND (MA50 & MA200)
        if close > ma50 and ma50 > ma200: trend = f"🚀 Strong (>MA50 {ma50})"
        elif close > ma200: trend = f"📈 Uptrend (>MA200 {ma200})"
        elif close < ma200: trend = f"📉 Downtrend (<MA200 {ma200})"
        else: trend = "➡️ Sideways"
        
        # B. ANALISA MOMENTUM (RSI 14)
        if rsi < 30: mom = f"🔥 Oversold ({int(rsi)})"
        elif rsi > 70: mom = f"⚠️ Overbought ({int(rsi)})"
        else: mom = f"Netral ({int(rsi)})"
        
        # C. LOGIKA TIMING BELI (KONKRET)
        timing = "⚪ Wait & See"
        
        # Skenario 1: Buy on Support (Trend Naik)
        if close > ma50:
            dist = abs(close - ma50)/ma50
            if dist < 0.05:
                timing = f"🟢 BUY: Antri dekat {ma50}"
            else:
                timing = f"⏳ Tunggu koreksi ke {ma50}"
                
        # Skenario 2: Catch Reversal (Trend Turun tapi Murah)
        elif close < ma200 and rsi < 35:
             # Syarat Reversal: Harus tembus High kemarin
             if close > high_yest:
                 timing = "🟢 BUY: Sudah Rebound!"
             else:
                 timing = f"⏳ Tunggu Tembus {high_yest}"

        return {
            "Stock": ticker.replace(".JK",""),
            "Price": close,
            "Trend (MA50/200)": trend,      # Jelas MA-nya
            "Momentum (RSI 14)": mom,       # Jelas Indikatornya
            "Timing Beli": timing,          # Jelas Angkanya
            "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
        }
    except: return None

# --- ENGINE PORTO (SIMPLE) ---
def get_porto_analysis(ticker, entry_price):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        last_p = int(t.history(period="1d")['Close'].iloc[-1])
        gl_val = ((last_p - entry_price) / entry_price) * 100
        action = "Hold"
        if gl_val <= -7: action = "🚨 CUT LOSS"
        elif gl_val >= 15: action = "🔵 TAKE PROFIT"
        return last_p, f"{gl_val:+.2f}%", action
    except: return 0, "0%", "-"

# --- 4. TAMPILAN DASHBOARD ---
st.title("💎 EDU-VEST: V145 (DETAIL TIMING)")

try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2, tab3, tab4 = st.tabs(["🔍 SCREENER", "⭐ WATCHLIST (DETAIL)", "📊 PORTO", "➕ INPUT"])

# --- TAB 1: SCREENER (LOGIC V143) ---
with tab1:
    st.subheader("Cari Saham Bagus")
    mode = st.radio("Strategi:", ["Radar Krisis (Lihat Semua)", "Reversal (Pantulan)", "Breakout (Ledakan)", "Swing (Santai)"], horizontal=True)
    
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
        else: st.warning("Kosong.")

    if st.session_state['scan_results'] is not None:
        edited_df = st.data_editor(st.session_state['scan_results'], column_config={"Pilih": st.column_config.CheckboxColumn("Add WL?"), "Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
        if st.button("💾 SIMPAN KE WATCHLIST"):
            selected = edited_df[edited_df["Pilih"] == True]["Stock"].tolist()
            if selected:
                wl = load_data(WATCHLIST_FILE, ["Stock"])
                new = [s for s in selected if s not in wl["Stock"].values]
                if new: pd.concat([wl, pd.DataFrame([{"Stock": s} for s in new])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False); st.success("Disimpan!"); st.rerun()

# --- TAB 2: WATCHLIST (TAMPILAN BARU V145) ---
with tab2:
    st.subheader("📋 Saringan 2: Pantauan Eksekusi")
    st.caption("Fokus pada **Timing Beli**. Pastikan harga sesuai rencana sebelum eksekusi.")
    
    if st.button("🗑️ HAPUS SEMUA", type="secondary"):
        if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()
            
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    if not wl.empty:
        wl_data = []
        for s in wl['Stock']:
            d = get_technical_detail(s)
            if d: wl_data.append(d)
        
        # Menampilkan Tabel dengan Kolom yang Diminta
        st.data_editor(
            pd.DataFrame(wl_data),
            column_config={
                "Price": st.column_config.NumberColumn("Harga Last"),
                "Trend (MA50/200)": st.column_config.TextColumn("Tren Utama", help="Menggunakan MA50 dan MA200"),
                "Momentum (RSI 14)": st.column_config.TextColumn("Tenaga (RSI 14)", help="RSI 14 Hari. <30 Murah, >70 Mahal"),
                "Timing Beli": st.column_config.TextColumn("Rencana Aksi (SOP)", help="Sinyal konkret kapan harus masuk"),
                "TV": st.column_config.LinkColumn("Chart")
            },
            hide_index=True,
            use_container_width=True
        )
    else: st.info("Watchlist Kosong. Ambil dari Screener dulu.")

# --- TAB 3: PORTO (SIMPLE) ---
with tab3:
    st.subheader("Monitoring Portfolio")
    if st.button("🚨 RESET PORTO"): os.remove(DB_FILE) if os.path.exists(DB_FILE) else None; st.rerun()
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    if not df_p.empty:
        for idx, row in df_p.iterrows():
            last, gl, act = get_porto_analysis(row['Stock'], row['Entry'])
            c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
            c1.write(f"**{row['Stock']}**"); c2.write(f"G/L: {gl}"); c3.write(f"Saran: {act}")
            if c4.button("🗑️", key=f"del_{idx}"): df_p.drop(idx).to_csv(DB_FILE, index=False); st.rerun()
            st.divider()

# --- TAB 4: INPUT (SIMPLE) ---
with tab4:
    with st.form("manual"):
        c1, c2 = st.columns(2)
        s = c1.text_input("Kode:").upper(); p = c2.number_input("Harga:", step=1)
        if st.form_submit_button("Simpan"):
             pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now(), "Stock": s, "Entry": p}])], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()
