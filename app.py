import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
import time
from datetime import datetime

# --- 1. SETTING IDENTITAS ---
st.set_page_config(
    page_title="ADIENOV TRADING PRO",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SECRET_PIN = "2026" 
TV_CHART_ID = "q94KuJTY" 

DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE LOGIC ---
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
    prev_high = df['High'].iloc[-2] # Logic V157
    
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

    if "Radar Diskon" in mode: return True, fund_status, roe, per
    elif "Reversal" in mode:
        # Logic V157: RSI < 32 & Close > High Kemarin
        if rsi < 32 and close > prev_high: return True, fund_status, roe, per
    elif "Breakout" in mode:
        if close > high_20 and vol_now > vol_avg: return True, fund_status, roe, per
    elif "Swing" in mode:
        if close > ma50 and df['Low'].iloc[-1] <= (ma50 * 1.05) and close > prev_close: return True, fund_status, roe, per
    return False, "", 0, 0

def get_technical_detail(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 200: return None
        
        close = int(df['Close'].iloc[-1])
        ma50 = int(df['Close'].rolling(50).mean().iloc[-1])
        ma200 = int(df['Close'].rolling(200).mean().iloc[-1])
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        if close > ma50 and ma50 > ma200: trend = f"🚀 Strong Uptrend"
        elif close > ma200: trend = f"📈 Uptrend Normal"
        elif close < ma200: trend = f"📉 Downtrend (Hati-hati)"
        else: trend = "➡️ Sideways"
        
        timing = "Wait"
        if close > ma50:
            dist = abs(close - ma50)/ma50
            if dist < 0.05: timing = f"🟢 BUY AREA: {ma50}-{close}"
            else: timing = f"⏳ TUNGGU KOREKSI: {ma50}"
        elif close < ma200 and rsi < 35: timing = "👀 PANTAU REVERSAL"

        support = int(df['Low'].tail(20).min())
        resistance = int(df['High'].tail(20).max())
        tv_url = f"https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{ticker.replace('.JK','')}"

        return {
            "Stock": ticker.replace(".JK",""), "Price": close, "Trend": trend, "RSI": int(rsi), 
            "Timing": timing, "Support": support, "Resistance": resistance, "TV": tv_url
        }
    except: return None

def get_porto_analysis(ticker, entry_price):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        last_p = int(t.history(period="1d")['Close'].iloc[-1])
        gl_val = ((last_p - entry_price) / entry_price) * 100
        action = "Hold"
        if gl_val <= -7: action = "🚨 CUT LOSS SEGERA"
        elif gl_val >= 15: action = "🔵 TAKE PROFIT"
        return last_p, f"{gl_val:+.2f}%", action
    except: return 0, "0%", "-"

# --- 3. UI DASHBOARD ---

st.title("📈 ADIENOV TRADING PRO")
st.caption("Professional Trading System by Adien Novarisa")
st.markdown("---")

try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 ALERT: CRASH ({chg:.2f}%) - Fokus Reversal & Diskon.")
    elif chg <= -1.0: st.warning(f"⚠️ ALERT: KOREKSI ({chg:.2f}%) - Kurangi agresivitas.")
    else: st.success(f"🟢 MARKET: AMAN ({chg:.2f}%) - Strategi Normal.")
except: pass

tab1, tab2, tab3 = st.tabs(["🔍 STEP 1: SCREENER", "⚡ STEP 2: EXECUTION", "🔐 STEP 3: PORTFOLIO"])

# --- TAB 1: SCREENER (BAHASA MANUSIA) ---
with tab1:
    st.header("🔍 Radar Saham")
    mode = st.radio("Pilih Strategi:", ["Radar Diskon (Market Crash)", "Reversal (Pantulan)", "Breakout (Tren Naik)", "Swing (Koreksi Sehat)"], horizontal=True)
    
    if 'scan_results' not in st.session_state: st.session_state['scan_results'] = None

    if st.button("🚀 SCAN MARKET SEKARANG", type="primary"):
        st.write(f"⏳ Memindai data market untuk: **{mode}**...")
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(SYARIAH_TICKERS):
            progress_bar.progress((i + 1) / len(SYARIAH_TICKERS))
            df, info = get_hybrid_data(t)
            if df is not None and info is not None:
                lolos, f_stat, roe, per = analyze_hybrid_logic(df, info, mode)
                if lolos:
                    # AMBIL DATA RSI & CLOSE TERKINI
                    close = df['Close'].iloc[-1]
                    rsi_series = ta.rsi(df['Close'], length=14)
                    rsi_now = rsi_series.iloc[-1]
                    rsi_prev = rsi_series.iloc[-2] # RSI Kemarin (Untuk perbandingan)
                    
                    # LOGIKA BAHASA MANUSIA (TRANSLATOR)
                    # 1. Tentukan Status Murah/Mahal
                    if rsi_now < 30: rsi_text = "🔥 DISKON PARAH"
                    elif rsi_now < 45: rsi_text = "✅ SUDAH MURAH"
                    elif rsi_now < 60: rsi_text = "😐 NORMAL"
                    else: rsi_text = "⚠️ MULAI MAHAL"
                    
                    # 2. Tentukan Arah (Makin Murah vs Mulai Naik)
                    if rsi_now < rsi_prev:
                        arah = "↘️ Makin Murah"
                    else:
                        arah = "↗️ Mulai Naik"
                    
                    # Gabungkan jadi satu kalimat
                    kondisi_rsi = f"{int(rsi_now)} ({rsi_text}) | {arah}"
                    
                    # URL TV
                    tv_link = f"https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{t.replace('.JK','')}"
                    
                    # Masukkan ke Tabel Hasil (Ganti kolom RSI angka dengan Kondisi Bahasa)
                    results.append({
                        "Pilih": False, 
                        "Stock": t.replace(".JK",""), 
                        "Price": int(close), 
                        "Kualitas": f_stat, 
                        "ROE (%)": round(roe, 1), 
                        "Kondisi Harga (RSI)": kondisi_rsi, # Kolom Baru
                        "Chart": tv_link
                    })
        progress_bar.empty()
        
        if results:
            df_res = pd.DataFrame(results)
            if "Radar" in mode: df_res = df_res.sort_values(by="ROE (%)", ascending=False)
            st.session_state['scan_results'] = df_res
        else: st.warning("Tidak ada saham yang sesuai kriteria saat ini.")

    if st.session_state['scan_results'] is not None:
        # TAMPILKAN TABEL DENGAN KOLOM BAHASA MANUSIA
        edited_df = st.data_editor(
            st.session_state['scan_results'], 
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Pantau"),
                "Chart": st.column_config.LinkColumn("Grafik"),
                "Kualitas": st.column_config.TextColumn("Fundamental"),
                "ROE (%)": st.column_config.NumberColumn("ROE", format="%.1f%%"),
                "Kondisi Harga (RSI)": st.column_config.TextColumn("Status Diskon?", width="medium", help="Membaca indikator RSI dengan bahasa sehari-hari")
            }, 
            hide_index=True, 
            use_container_width=True
        )
        
        if st.button("💾 MASUKKAN KE WATCHLIST"):
            selected = edited_df[edited_df["Pilih"] == True]["Stock"].tolist()
            if selected:
                wl = load_data(WATCHLIST_FILE, ["Stock"])
                new = [s for s in selected if s not in wl["Stock"].values]
                if new: 
                    pd.concat([wl, pd.DataFrame([{"Stock": s} for s in new])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
                    st.success(f"✅ Berhasil! {len(new)} saham ({', '.join(new)}) telah ditambahkan ke Watchlist.")
                    time.sleep(1.5) 
                    st.rerun()
                else: st.warning("⚠️ Semua saham yang dipilih SUDAH ADA di Watchlist Anda sebelumnya.")
            else: st.warning("⚠️ Belum ada saham yang dicentang.")

# --- TAB 2 & 3 (TETAP SAMA DENGAN V154) ---
# (Bagian Tab 2 dan Tab 3 tidak saya tulis ulang agar tidak kepanjangan, 
# karena kodenya sama persis dengan V154. Cukup copy bagian Tab 1 di atas 
# dan gabungkan dengan Tab 2 & 3 dari kode sebelumnya).
with tab2:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.header("⚡ Kalkulator & Eksekusi")
        st.caption("Analisa lot sebelum membeli.")
    with col_h2:
        if st.button("🗑️ RESET WATCHLIST", type="secondary"):
            if os.path.exists(WATCHLIST_FILE): os.remove(WATCHLIST_FILE); st.rerun()

    wl = load_data(WATCHLIST_FILE, ["Stock"])
    
    if wl.empty:
        st.info("📭 Watchlist kosong.")
    else:
        for idx, row in wl.iterrows():
            d = get_technical_detail(row['Stock'])
            if d:
                with st.expander(f"📊 {d['Stock']} | Rp {d['Price']:,} | {d['Timing']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Tren:**\n{d['Trend']}")
                    c2.markdown(f"**RSI:**\n{d['RSI']}")
                    c3.markdown(f"**Grafik:**\n[Buka TradingView]({d['TV']})")
                    st.divider()
                    
                    st.write("💰 **Simulasi Lot**")
                    col_in1, col_in2, col_in3 = st.columns(3)
                    modal = col_in1.number_input("Modal (Rp):", value=10000000, step=1000000, key=f"mod_{d['Stock']}")
                    col_in1.caption(f"💵 Terbaca: **Rp {int(modal):,}**")
                    risiko = col_in2.number_input("Risiko (%):", value=2.0, key=f"ris_{d['Stock']}")
                    sl_price = col_in3.number_input("Cut Loss (Rp):", value=d['Support'], step=10, key=f"sl_{d['Stock']}")
                    col_in3.caption(f"🔻 Terbaca: **Rp {int(sl_price):,}**")

                    if sl_price < d['Price']:
                        risiko_rp = modal * (risiko / 100)
                        max_lot = int((risiko_rp / (d['Price'] - sl_price)) / 100)
                        st.info(f"🛡️ Risiko Max: **Rp {int(risiko_rp):,}**. Beli Max: **{max_lot} LOT**.")
                    else: st.warning("⚠️ Cut Loss harus di bawah harga pasar.")
                    
                    st.divider()
                    col_b1, col_b2 = st.columns([1, 3])
                    
                    if col_b1.button("Hapus", key=f"del_{d['Stock']}"):
                        wl = wl[wl.Stock != d['Stock']]; wl.to_csv(WATCHLIST_FILE, index=False); st.rerun()
                        
                    if col_b2.button(f"🛒 SIMULASI BELI {d['Stock']}", type="primary", key=f"buy_{d['Stock']}"):
                        pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Stock": d['Stock'], "Entry": d['Price']}])], ignore_index=True).to_csv(DB_FILE, index=False)
                        wl = wl[wl.Stock != d['Stock']]; wl.to_csv(WATCHLIST_FILE, index=False)
                        
                        st.success(f"✅ **DATA TERSIMPAN.** {d['Stock']} berhasil dicatat ke Portfolio Admin.")
                        st.warning(f"""
                        🔔 **PENGINGAT EKSEKUSI:**
                        Aplikasi ini hanya alat bantu analisa & pencatatan.
                        
                        👉 **LANGKAH SELANJUTNYA:**
                        Silakan buka aplikasi Sekuritas Anda (IPOT/Stockbit/Ajaib) dan lakukan Order Buy untuk **{d['Stock']}** secara real.
                        """)
                        st.stop() 

with tab3:
    st.header("🔐 Portfolio Administrator")
    
    if 'porto_unlocked' not in st.session_state: st.session_state['porto_unlocked'] = False

    if not st.session_state['porto_unlocked']:
        st.warning("🔒 Halaman ini terkunci. Hanya Admin (Pak Adien) yang bisa mengakses.")
        with st.form("login_form"):
            user_pin = st.text_input("Masukkan PIN Keamanan:", type="password")
            if st.form_submit_button("BUKA AKSES"):
                if user_pin == SECRET_PIN:
                    st.session_state['porto_unlocked'] = True; st.success("Akses Diterima."); st.rerun()
                else: st.error("PIN Salah.")
    else:
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1: st.success("✅ Akses Administrator Terbuka")
        with col_p2:
            if st.button("🔒 KUNCI KEMBALI"): st.session_state['porto_unlocked'] = False; st.rerun()
        
        if st.button("🚨 RESET TOTAL PORTFOLIO", type="primary"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE); st.rerun()
        
        df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
        if df_p.empty: st.info("Belum ada aset.")
        else:
            st.metric("Total Emiten", f"{len(df_p)}")
            st.write("---")
            for idx, row in df_p.iterrows():
                last, gl, act = get_porto_analysis(row['Stock'], row['Entry'])
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
                    c1.markdown(f"### {row['Stock']}")
                    c1.caption(f"Buy: Rp {row['Entry']:,}")
                    if "Profit" in act: c2.markdown(f"<h3 style='color:#00C853'>{gl}</h3>", unsafe_allow_html=True)
                    elif "CUT" in act: c2.markdown(f"<h3 style='color:#D50000'>{gl}</h3>", unsafe_allow_html=True)
                    else: c2.markdown(f"<h3>{gl}</h3>", unsafe_allow_html=True)
                    c3.info(f"**Saran:** {act}")
                    if c4.button("Jual", key=f"sell_{idx}"):
                        df_p.drop(idx).to_csv(DB_FILE, index=False); st.success("Done."); st.rerun()
                    st.markdown("---")
