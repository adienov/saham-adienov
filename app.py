import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING TAMPILAN PROFESIONAL ---
st.set_page_config(
    page_title="ADIENOV TRADING PRO",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# File Database
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham Universe
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE LOGIC (TETAP SAMA - V148) ---
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

    # Penamaan Mode di Logic disesuaikan dengan UI baru
    if "Radar Diskon" in mode: return True, fund_status, roe, per
    elif "Reversal" in mode:
        if rsi < 40 and close > prev_close: return True, fund_status, roe, per
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

        return {
            "Stock": ticker.replace(".JK",""), "Price": close, "Trend": trend, "RSI": int(rsi), "Timing": timing, "Support": support, "Resistance": resistance, "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
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

# --- 3. UI DASHBOARD (RE-DESIGNED) ---

st.title("📈 ADIENOV PRO: Trading Assistant")
st.markdown("---")

# Panic Meter dengan Bahasa Lebih Halus
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 KONDISI PASAR: CRASH ({chg:.2f}%) - Fokus cari saham diskon (Reversal).")
    elif chg <= -1.0: st.warning(f"⚠️ KONDISI PASAR: KOREKSI ({chg:.2f}%) - Hati-hati, kurangi porsi.")
    else: st.success(f"🟢 KONDISI PASAR: KONDUSIF ({chg:.2f}%) - Strategi Breakout & Swing aman.")
except: pass

# Navigasi Step-by-Step
tab1, tab2, tab3 = st.tabs(["🔍 STEP 1: PENCARIAN", "⚡ STEP 2: EKSEKUSI", "💼 STEP 3: PORTFOLIO"])

# --- TAB 1: SCREENER (PENCARIAN) ---
with tab1:
    st.header("🔍 Pencarian Saham Potensial")
    st.caption("Pilih strategi trading yang sesuai dengan kondisi pasar hari ini.")
    
    # Pilihan Mode dengan Bahasa yang Jelas
    mode = st.radio(
        "Pilih Gaya Trading:", 
        [
            "Radar Diskon (Tampilkan Semua - Market Crash)", 
            "Reversal (Tangkap Pisau Jatuh)", 
            "Breakout (Ikut Tren Naik)", 
            "Swing (Beli Saat Koreksi)"
        ], 
        horizontal=True
    )
    
    if 'scan_results' not in st.session_state: st.session_state['scan_results'] = None

    if st.button("🚀 MULAI SCANNING MARKET", type="primary"):
        st.write(f"⏳ Sedang memindai pasar dengan strategi: **{mode}**...")
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
                        "Pilih": False, 
                        "Stock": t.replace(".JK",""), 
                        "Price": int(close), 
                        "Kualitas": f_stat, 
                        "ROE (%)": round(roe, 1),
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"
                    })
        progress_bar.empty()
        
        if results:
            df_res = pd.DataFrame(results)
            # Sorting Cerdas berdasarkan Mode
            if "Radar" in mode: 
                df_res = df_res.sort_values(by="ROE (%)", ascending=False)
                st.info("💡 **Tips:** Mode Radar menampilkan saham berfundamental bagus (ROE Tinggi) yang sedang turun.")
            
            st.session_state['scan_results'] = df_res
        else: 
            st.warning("Belum ada saham yang cocok dengan kriteria strategi ini.")

    # Tabel Hasil Scan
    if st.session_state['scan_results'] is not None:
        st.write("### 📋 Hasil Analisa")
        edited_df = st.data_editor(
            st.session_state['scan_results'], 
            column_config={
                "Pilih": st.column_config.CheckboxColumn("Add WL?", help="Centang untuk memantau saham ini"),
                "Chart": st.column_config.LinkColumn("Buka Grafik"),
                "Kualitas": st.column_config.TextColumn("Status Fundamental", help="Hijau = Bagus, Kuning = Hati-hati"),
                "ROE (%)": st.column_config.NumberColumn("Profitabilitas (ROE)", format="%.1f%%", help="Semakin tinggi semakin bagus (>15% Super)")
            }, 
            hide_index=True,
            use_container_width=True
        )
        
        col_act1, col_act2 = st.columns([4, 1])
        if col_act1.button("💾 SIMPAN YANG DICENTANG KE WATCHLIST"):
            selected = edited_df[edited_df["Pilih"] == True]["Stock"].tolist()
            if selected:
                wl = load_data(WATCHLIST_FILE, ["Stock"])
                new = [s for s in selected if s not in wl["Stock"].values]
                if new: 
                    pd.concat([wl, pd.DataFrame([{"Stock": s} for s in new])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
                    st.success(f"✅ Berhasil menyimpan: {', '.join(new)}")
                    st.rerun()
                else:
                    st.toast("Saham sudah ada di Watchlist.")
            else:
                st.toast("⚠️ Belum ada saham yang dicentang.")

# --- TAB 2: WATCHLIST & EKSEKUSI (PERENCANAAN) ---
with tab2:
    st.header("⚡ Perencanaan & Eksekusi Trading")
    st.caption("Hitung lot aman sebelum membeli agar psikologis tenang.")
    
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    
    if wl.empty:
        st.info("📭 Watchlist kosong. Silakan cari saham di Step 1 dulu.")
    else:
        for idx, row in wl.iterrows():
            d = get_technical_detail(row['Stock'])
            if d:
                # Kartu Saham yang Informatif
                with st.expander(f"📊 {d['Stock']} | Harga: Rp {d['Price']:,} | Sinyal: {d['Timing']}"):
                    
                    # Baris Informasi Utama
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Tren Utama:**\n{d['Trend']}")
                    c2.markdown(f"**Tenaga (RSI):**\n{d['RSI']}")
                    c3.markdown(f"**Analisa Grafik:**\n[Buka TradingView]({d['TV']})")
                    
                    st.divider()
                    
                    # Area Kalkulator
                    st.subheader("💰 Manajemen Modal (Money Management)")
                    
                    col_in1, col_in2, col_in3 = st.columns(3)
                    
                    # Input Modal
                    modal = col_in1.number_input(
                        "Modal Trading Siap Pakai (Rp):", 
                        value=10000000, 
                        step=1000000, 
                        help="Masukkan total uang cash yang ada di RDN.",
                        key=f"mod_{d['Stock']}"
                    )
                    col_in1.caption(f"💵 Terbaca: **Rp {int(modal):,}**")
                    
                    # Input Risiko
                    risiko = col_in2.number_input(
                        "Batas Risiko per Transaksi (%):", 
                        value=2.0, 
                        help="Berapa persen Anda rela rugi jika analisa salah? (Disarankan max 2%)",
                        key=f"ris_{d['Stock']}"
                    )
                    
                    # Input Cut Loss
                    sl_price = col_in3.number_input(
                        "Titik Cut Loss (Stop Loss):", 
                        value=d['Support'], 
                        step=10, 
                        help="Di harga berapa Anda akan menyerah/jual rugi?",
                        key=f"sl_{d['Stock']}"
                    )
                    col_in3.caption(f"🔻 Terbaca: **Rp {int(sl_price):,}**")

                    # Logika Hitung
                    if sl_price < d['Price']:
                        risiko_rp = modal * (risiko / 100)
                        jarak = d['Price'] - sl_price
                        max_lembar = risiko_rp / jarak
                        max_lot = int(max_lembar / 100)
                        
                        # Tampilan Hasil Hitung yang Menarik
                        st.info(f"""
                        🛡️ **RENCANA TRADING AMAN:**
                        * Jika harga turun ke **{sl_price}**, kerugian Anda hanya **Rp {int(risiko_rp):,}**.
                        * Untuk menjaga risiko itu, beli maksimal: **{max_lot} LOT**.
                        """)
                    else:
                        st.warning("⚠️ Harga Cut Loss harus lebih rendah dari harga pasar saat ini.")
                    
                    st.divider()
                    
                    # Tombol Aksi
                    col_btn1, col_btn2 = st.columns([1, 3])
                    
                    if col_btn1.button("🗑️ Hapus Pantauan", key=f"del_{d['Stock']}"):
                        wl = wl[wl.Stock != d['Stock']]
                        wl.to_csv(WATCHLIST_FILE, index=False)
                        st.rerun()
                        
                    if col_btn2.button(f"🛒 EKSEKUSI BELI {d['Stock']} SEKARANG", type="primary", key=f"buy_{d['Stock']}"):
                        # Pindah ke Porto
                        pd.concat([load_data(DB_FILE, ["Tgl", "Stock", "Entry"]), pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Stock": d['Stock'], "Entry": d['Price']}])], ignore_index=True).to_csv(DB_FILE, index=False)
                        # Hapus dari Watchlist
                        wl = wl[wl.Stock != d['Stock']]
                        wl.to_csv(WATCHLIST_FILE, index=False)
                        st.balloons() # Efek perayaan kecil
                        st.success("Transaksi berhasil dicatat! Cek Tab Portfolio.")
                        st.rerun()

# --- TAB 3: PORTFOLIO (MONITORING) ---
with tab3:
    st.header("💼 Monitor Portfolio Saya")
    
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    
    if df_p.empty:
        st.info("Belum ada saham di portfolio.")
    else:
        # Ringkasan Aset
        total_saham = len(df_p)
        st.metric("Total Posisi Terbuka", f"{total_saham} Emiten")
        st.write("---")
        
        for idx, row in df_p.iterrows():
            last, gl, act = get_porto_analysis(row['Stock'], row['Entry'])
            
            # Kartu Portfolio
            col_card = st.container()
            with col_card:
                c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
                
                c1.markdown(f"### {row['Stock']}")
                c1.caption(f"Harga Beli: Rp {row['Entry']:,}")
                
                # Warna Profit/Loss Dinamis
                if "Profit" in act: 
                    c2.markdown(f"<h3 style='color:#00C853'>{gl}</h3>", unsafe_allow_html=True)
                elif "CUT" in act: 
                    c2.markdown(f"<h3 style='color:#D50000'>{gl}</h3>", unsafe_allow_html=True)
                else: 
                    c2.markdown(f"<h3>{gl}</h3>", unsafe_allow_html=True)
                
                c3.info(f"**Saran Sistem:** {act}")
                
                if c4.button("✅ Jual/Done", key=f"sell_{idx}", help="Klik jika saham sudah dijual"):
                    df_p.drop(idx).to_csv(DB_FILE, index=False)
                    st.success("Posisi ditutup.")
                    st.rerun()
                
                st.markdown("---")
