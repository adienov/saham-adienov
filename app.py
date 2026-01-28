import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING UTAMA ---
st.set_page_config(page_title="EDU-VEST V146: EXECUTION", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK", "MYOR.JK", "JPFA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE HYBRID (SCREENER) ---
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

# --- 3. ENGINE TEKNIKAL DETIL (WATCHLIST) ---
def get_technical_detail(ticker):
    try:
        t = yf.Ticker(f"{ticker}.JK" if ".JK" not in ticker else ticker)
        df = t.history(period="1y")
        if len(df) < 200: return None
        
        close = int(df['Close'].iloc[-1])
        ma50 = int(df['Close'].rolling(50).mean().iloc[-1])
        ma200 = int(df['Close'].rolling(200).mean().iloc[-1])
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        if close > ma50 and ma50 > ma200: trend = f"🚀 Strong (>MA50 {ma50})"
        elif close > ma200: trend = f"📈 Uptrend (>MA200 {ma200})"
        elif close < ma200: trend = f"📉 Downtrend (<MA200 {ma200})"
        else: trend = "➡️ Sideways"
        
        timing = "Wait"
        if close > ma50:
            dist = abs(close - ma50)/ma50
            if dist < 0.05: timing = f"🟢 BUY AREA: {ma50}-{close}"
            else: timing = f"⏳ TUNGGU di {ma50}"
        elif close < ma200 and rsi < 35: timing = "👀 WATCH REVERSAL"

        # Hitung Support & Resist sederhana untuk Kalkulator
        support = int(df['Low'].tail(20).min())
        resistance = int(df['High'].tail(20).max())

        return {
            "Stock": ticker.replace(".JK",""),
            "Price": close,
            "Trend": trend,
            "RSI": int(rsi),
            "Timing": timing,
            "Support": support,
            "Resistance": resistance,
            "TV": f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"
        }
    except: return None

# --- ENGINE PORTO ---
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
st.title("💎 EDU-VEST: EXECUTION BRIDGE V146")

# Panic Meter
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2, tab3 = st.tabs(["1️⃣ SCREENER", "2️⃣ WATCHLIST & EKSEKUSI", "3️⃣ PETA PORTO"])

# --- TAB 1: SCREENER (SAMA SEPERTI V145) ---
with tab1:
    st.subheader("Langkah 1: Cari Kandidat Saham")
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
                    results.append({"Pilih": False, "Stock": t.replace(".JK",""), "Price": int(close), "Kualitas": f_stat, "ROE (%)": round(roe, 1), "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"})
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

# --- TAB 2: WATCHLIST & EKSEKUSI (INTI PERUBAHAN) ---
with tab2:
    st.subheader("Langkah 2: Perencanaan & Eksekusi")
    wl = load_data(WATCHLIST_FILE, ["Stock"])
    
    if wl.empty:
        st.info("Watchlist Kosong. Silakan pilih saham dari Tab 1.")
    else:
        # Tampilkan setiap saham dalam kartu (Expander)
        for idx, row in wl.iterrows():
            d = get_technical_detail(row['Stock'])
            if d:
                # Judul Kartu: Nama Saham + Harga + Sinyal
                with st.expander(f"📊 {d['Stock']} | Rp {d['Price']} | {d['Timing']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Tren:** {d['Trend']}")
                    c2.write(f"**RSI:** {d['RSI']}")
                    c3.write(f"[Lihat Chart TV]({d['TV']})")
                    
                    st.divider()
                    
                    # FITUR KALKULATOR LOT (MONEY MANAGEMENT)
                    st.write("🧮 **Kalkulator & Eksekusi**")
                    col_input1, col_input2, col_input3 = st.columns(3)
                    
                    modal_trading = col_input1.number_input("Modal Siap (Rp):", value=10000000, key=f"mod_{d['Stock']}")
                    risiko_persen = col_input2.number_input("Risiko Max (%):", value=2.0, key=f"ris_{d['Stock']}")
                    stop_loss_price = col_input3.number_input("Titik Cut Loss:", value=d['Support'], key=f"sl_{d['Stock']}")
                    
                    # Hitung Lot Aman
                    if stop_loss_price < d['Price']:
                        risiko_rupiah = modal_trading * (risiko_persen / 100)
                        jarak_sl = d['Price'] - stop_loss_price
                        max_lembar = risiko_rupiah / jarak_sl
                        max_lot = int(max_lembar / 100)
                        
                        st.info(f"💡 Agar risiko maksimal **Rp {int(risiko_rupiah):,}**, beli maksimal: **{max_lot} Lot**.")
                    else:
                        st.warning("Harga Cut Loss harus di bawah harga sekarang.")
                    
                    st.divider()
                    
                    # TOMBOL EKSEKUSI
                    # Jika ditekan: Simpan ke Porto, Hapus dari WL
                    col_btn1, col_btn2 = st.columns([1, 4])
                    if col_btn2.button(f"✅ BELI {d['Stock']} SEKARANG", type="primary", key=f"buy_{d['Stock']}"):
                        # 1. Simpan ke Portfolio
                        porto_db = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
                        new_porto = pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Stock": d['Stock'], "Entry": d['Price']}])
                        pd.concat([porto_db, new_porto], ignore_index=True).to_csv(DB_FILE, index=False)
                        
                        # 2. Hapus dari Watchlist
                        wl = wl[wl.Stock != d['Stock']]
                        wl.to_csv(WATCHLIST_FILE, index=False)
                        
                        st.success(f"{d['Stock']} berhasil dibeli dan dipindah ke Peta Porto!")
                        st.rerun()

                    if col_btn1.button("🗑️ Hapus", key=f"del_{d['Stock']}"):
                        wl = wl[wl.Stock != d['Stock']]
                        wl.to_csv(WATCHLIST_FILE, index=False)
                        st.rerun()

# --- TAB 3: PETA PORTO (SIMPLE & JELAS) ---
with tab3:
    st.subheader("Langkah 3: Peta Portfolio (Monitoring)")
    df_p = load_data(DB_FILE, ["Tgl", "Stock", "Entry"])
    
    if df_p.empty:
        st.info("Portfolio Kosong. Belum ada aset.")
    else:
        # Ringkasan Total
        st.metric("Total Posisi Terbuka", f"{len(df_p)} Saham")
        
        st.write("---")
        for idx, row in df_p.iterrows():
            last, gl, act = get_porto_analysis(row['Stock'], row['Entry'])
            
            # Visualisasi Kartu Porto
            cols = st.columns([2, 2, 2, 1])
            cols[0].write(f"### {row['Stock']}")
            cols[0].caption(f"Beli: {row['Entry']}")
            
            # Warna Profit/Loss
            if "Profit" in act: cols[1].markdown(f"<h3 style='color:green'>{gl}</h3>", unsafe_allow_html=True)
            elif "CUT" in act: cols[1].markdown(f"<h3 style='color:red'>{gl}</h3>", unsafe_allow_html=True)
            else: cols[1].markdown(f"<h3>{gl}</h3>", unsafe_allow_html=True)
            
            cols[2].info(f"Saran: {act}")
            
            if cols[3].button("Jual/Hapus", key=f"sold_{idx}"):
                df_p.drop(idx).to_csv(DB_FILE, index=False)
                st.rerun()
            st.divider()
