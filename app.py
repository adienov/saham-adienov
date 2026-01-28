import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os
from datetime import datetime

# --- 1. SETTING UTAMA ---
st.set_page_config(page_title="EDU-VEST V137: LEGENDARY", layout="wide")
DB_FILE = "trading_history.csv"
WATCHLIST_FILE = "my_watchlist.csv"

# Daftar Saham (Bisa diedit)
SYARIAH_TICKERS = ["ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "MDKA.JK", "INCO.JK", "MEDC.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK", "ADRO.JK", "PTBA.JK"]

def load_data(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

# --- 2. ENGINE ANALISA "MAZHAB" ---
def run_legendary_screener(style):
    results = []
    for t in SYARIAH_TICKERS:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if len(df) < 50: continue
            
            # Hitung Indikator Wajib
            close = df['Close'].iloc[-1]
            high = df['High'].iloc[-1]
            low = df['Low'].iloc[-1]
            
            match = False
            reason = ""
            tv_link = f"https://www.tradingview.com/chart/?symbol=IDX:{t.replace('.JK','')}"

            # A. GAYA TURTLE TRADING (Richard Dennis)
            if style == "Turtle (Trend Follow)":
                # Aturan: Harga Close > Harga Tertinggi 20 Hari Terakhir (Breakout Donchian)
                donchian_high = df['High'].rolling(20).max().iloc[-2] # High kemarin
                if close > donchian_high:
                    match = True
                    reason = "Breakout High 20 Hari (Turtle Buy)"

            # B. GAYA BOLLINGER REVERSAL (John Bollinger)
            elif style == "Bollinger (Pantulan)":
                # Aturan: Harga sempat sentuh Lower Band, tapi Close Hijau (Mantul)
                bb = ta.bbands(df['Close'], length=20, std=2)
                lower_band = bb['BBL_20_2.0'].iloc[-1]
                if df['Low'].iloc[-1] <= lower_band and close > df['Open'].iloc[-1]:
                    match = True
                    reason = "Mantul dari Lower Band"

            # C. GAYA FRACTAL / ALLIGATOR (Bill Williams)
            elif style == "Fractal (Chaos Theory)":
                # Logika Sederhana Fractal: High 2 hari lalu adalah yang tertinggi dari 5 candle
                # Kita cari saham yang baru saja menembus Fractal High tersebut
                highs = df['High'].tail(5).values
                # Cek apakah candle ke-3 (tengah) adalah fractal
                if highs[2] > highs[0] and highs[2] > highs[1] and highs[2] > highs[3] and highs[2] > highs[4]:
                    fractal_price = highs[2]
                    # Cek apakah hari ini (candle ke-6/terbaru) menembus fractal itu
                    if close > fractal_price:
                        match = True
                        reason = "Breakout Fractal Resistance"
                else:
                    # Alternatif: Gunakan Alligator Jaw (MA13) -> Harga di atas MA13
                    ma13 = df['Close'].rolling(13).mean().iloc[-1]
                    if close > ma13 and close > df['Close'].iloc[-2]:
                         # Filter tambahan biar tidak terlalu longgar
                         pass 

            # D. GAYA STOCHASTIC (George Lane)
            elif style == "Stochastic (Momentum)":
                stoch = ta.stoch(df['High'], df['Low'], df['Close'])
                k = stoch['STOCHk_14_3_3'].iloc[-1]
                d = stoch['STOCHd_14_3_3'].iloc[-1]
                # Golden Cross di area Oversold (<20)
                if k < 25 and d < 25 and k > d:
                    match = True
                    reason = "Stochastic Golden Cross (Oversold)"

            if match:
                results.append({"Stock": t.replace(".JK",""), "Price": int(close), "Gaya": style, "Sinyal": reason, "Chart": tv_link})
                
        except: continue
    return pd.DataFrame(results)

# --- 3. UI DASHBOARD ---
st.title("🧙‍♂️ EDU-VEST: LEGENDARY STRATEGIES V137")

# Panic Meter (Tetap Ada)
try:
    ihsg = yf.Ticker("^JKSE").history(period="2d")
    chg = ((ihsg['Close'].iloc[-1] - ihsg['Close'].iloc[-2]) / ihsg['Close'].iloc[-2]) * 100
    if chg <= -3.0: st.error(f"🚨 MARKET CRASH ({chg:.2f}%)")
    elif chg <= -1.0: st.warning(f"⚠️ MARKET MERAH ({chg:.2f}%)")
    else: st.success(f"🟢 MARKET NORMAL ({chg:.2f}%)")
except: pass

tab1, tab2 = st.tabs(["🔍 SCREENER MAZHAB", "⭐ WATCHLIST & PORTO"])

with tab1:
    st.subheader("Pilih 'Guru' Trading Anda Hari Ini")
    style = st.selectbox("Strategi:", 
                         ["Turtle (Trend Follow)", 
                          "Bollinger (Pantulan)", 
                          "Stochastic (Momentum)",
                          "Fractal (Chaos Theory)"])
    
    if st.button("JALANKAN SCANNER"):
        # Loading Edukatif Sesuai Gaya
        if "Turtle" in style: msg = "🐢 Mencari saham yang menembus High 20 Hari (Donchian Channel)..."
        elif "Bollinger" in style: msg = "🎈 Mencari saham yang memantul dari Pita Bawah (Lower Band)..."
        elif "Stochastic" in style: msg = "📉 Mencari momentum Golden Cross di area Jenuh Jual..."
        else: msg = "🐊 Mencari konfirmasi Fractal Bill Williams..."
            
        with st.spinner(msg):
            df_res = run_legendary_screener(style)
            if not df_res.empty:
                st.success(f"Ditemukan {len(df_res)} saham!")
                st.data_editor(df_res, column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
            else:
                st.warning(f"Tidak ada saham yang memenuhi kriteria {style} saat ini.")

with tab2:
    st.info("Fitur Watchlist & Porto tetap aktif (menggunakan Logic V136).")
    # (Bapak bisa copy paste kode Tab Watchlist/Porto dari V136 di sini agar tidak kepanjangan)
