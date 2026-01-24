import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Adienov Plan", layout="wide", initial_sidebar_state="collapsed")

# CSS: Tampilan Center & Rapi
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        h1 { font-size: 1.6rem !important; padding-top: 10px !important; }
        div[data-testid="stCaptionContainer"] { font-size: 0.8rem; }
        div.stButton > button { width: 100%; border-radius: 20px; background-color: #007BFF; color: white !important; font-weight: bold;}
        
        /* Memaksa Teks Tabel Rata Tengah */
        .dataframe { text-align: center !important; }
        th { text-align: center !important; }
        td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER & INPUT ---
st.title("📱 Adienov Trading Plan")
st.caption("Auto-Calculate: Entry, Stop Loss, Take Profit (1:1.5)")
st.info("⚙️ **SETTING:** Klik panah **( > )** di kiri atas.")

with st.sidebar:
    st.header("⚙️ Filter Scanner")
    min_trans = st.number_input("Min. Transaksi (Miliar)", value=2.0, step=0.5)
    risk_tol = st.slider("Toleransi Alligator (%)", 1.0, 10.0, 5.0)
    turtle_day = st.slider("Periode Turtle (Hari)", 10, 50, 20)
    rr_ratio = st.number_input("Rasio Risk:Reward", value=1.5, step=0.1, help="Target Profit berapa kali lipat dari resiko?")
    st.markdown("---")

# --- 3. DATABASE SAHAM ---
tickers = [
    "ANTM.JK", "BRIS.JK", "TLKM.JK", "ICBP.JK", "INDF.JK", "UNTR.JK", "ASII.JK",
    "ADRO.JK", "PTBA.JK", "PGAS.JK", "EXCL.JK", "ISAT.JK", "KLBF.JK", "SIDO.JK",
    "MDKA.JK", "INCO.JK", "MBMA.JK", "AMRT.JK", "ACES.JK", "HRUM.JK",
    "AKRA.JK", "MEDC.JK", "ELSA.JK", "BRMS.JK", "DEWA.JK", "BUMI.JK",
    "UNVR.JK", "MYOR.JK", "CPIN.JK", "JPFA.JK", "SMGR.JK", "INTP.JK", "TPIA.JK"
]

# --- 4. FUNGSI SCANNER LENGKAP ---
@st.cache_data(ttl=60)
def scan_market(min_val_m, risk_pct, turtle_window, reward_ratio):
    results = []
    text_progress = st.empty()
    bar_progress = st.progress(0)
    
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        text_progress.text(f"Menganalisa {ticker.replace('.JK','')}... ({i+1}/{total})")
        try:
            df = yf.download(ticker, period="6mo", progress=False)
            if df.empty or len(df) < turtle_window + 5: continue
            try:
                if isinstance(df.columns, pd.MultiIndex): df = df.xs(ticker, level=1, axis=1)
            except: pass

            # Indikator
            df['HL2'] = (df['High'] + df['Low']) / 2
            df['Teeth_Raw'] = df.ta.sma(close='HL2', length=8)
            
            # Data Terakhir
            current_close = float(df['Close'].iloc[-1])
            red_line = float(df['Teeth_Raw'].iloc[-6]) if not pd.isna(df['Teeth_Raw'].iloc[-6]) else 0
            
            # Turtle Breakout Logic
            high_rolling = df['High'].rolling(window=turtle_window).max().shift(1)
            breakout_level = float(high_rolling.iloc[-1])

            # Filter Volume
            avg_val = (current_close * df['Volume'].mean()) / 1000000000 
            if avg_val < min_val_m: continue

            # HITUNG PLAN (SL & TP)
            # Stop Loss selalu di Garis Merah (dibulatkan ke bawah)
            stop_loss = int(red_line)
            risk_amt = current_close - stop_loss
            
            # Take Profit = Harga + (Resiko x Rasio Reward)
            # Contoh: Resiko 100 perak, Rasio 1.5, maka TP = Harga + 150 perak
            take_profit = int(current_close + (risk_amt * reward_ratio))

            status = ""
            priority = 0

            # Cek Status
            if current_close > breakout_level:
                status = "🐢 TURTLE"
                priority = 1
                diff = ((current_close - breakout_level) / breakout_level) * 100
            elif current_close > red_line:
                diff_alli = ((current_close - red_line) / current_close) * 100
                if diff_alli <= risk_pct:
                    status = "🟢 EARLY"
                    priority = 2
                    diff = diff_alli
                else:
                    status = "⚠️ EXTENDED"
                    priority = 3
                    diff = diff_alli
            else:
                status = "🔴 DOWN"
                priority = 4
                diff = ((red_line - current_close) / current_close) * 100

            # Link Chart
            tv_link = f"https://www.tradingview.com/chart/?symbol=IDX:{ticker.replace('.JK','')}"

            results.append({
                "Emiten": ticker.replace(".JK", ""),
                "Status": status,
                "Buy": int(current_close),    # Kolom Baru
                "SL": stop_loss,              # Kolom Baru
                "TP": take_profit,            # Kolom Baru
                "Risk%": round(diff, 1),
                "Chart": tv_link,
                "Priority": priority
            })

        except: continue
        bar_progress.progress((i + 1) / total)
    
    bar_progress.empty()
    text_progress.empty()
    
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by=["Priority", "Risk%"], ascending=[True, True])
    
    return df_res

# --- 5. TAMPILAN TABEL ---
if st.button("🔍 SCAN TRADING PLAN"):
    with st.spinner('Menghitung target harga...'):
        waktu_skrg = datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M WIB")
        df = scan_market(min_trans, risk_tol, turtle_day, rr_ratio)
        
        if not df.empty:
            st.success(f"✅ Update: {waktu_skrg}")
            
            # Konfigurasi Kolom
            column_config = {
                "Chart": st.column_config.LinkColumn("Chart", display_text="📈 Buka"),
                "Buy": st.column_config.NumberColumn("Harga Buy", format="Rp %d"),
                "SL": st.column_config.NumberColumn("Stop Loss", format="Rp %d"),
                "TP": st.column_config.NumberColumn("Take Profit", format="Rp %d"),
                "Risk%": st.column_config.NumberColumn("Jarak SL", format="%.1f %%"),
            }

            # Filter Hanya Sinyal Buy
            df_buy = df[df['Status'].str.contains("TURTLE|EARLY")]
            
            if not df_buy.empty:
                st.subheader("🔥 REKOMENDASI PLAN")
                
                # STYLING TABEL: Rata Tengah + Warna Kolom
                styled_df = (df_buy.drop(columns=['Priority']).style
                    .format({"Buy": "{:.0f}", "SL": "{:.0f}", "TP": "{:.0f}", "Risk%": "{:.1f}"})
                    # Rata Tengah untuk semua sel
                    .set_properties(**{'text-align': 'center'}) 
                    # Warna Header
                    .set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
                    # Warna Kolom Spesifik
                    .background_gradient(subset=['Risk%'], cmap="Greens") # Semakin hijau semakin aman
                    .applymap(lambda x: 'color: red; font-weight: bold;', subset=['SL']) # Angka SL Merah
                    .applymap(lambda x: 'color: green; font-weight: bold;', subset=['TP']) # Angka TP Hijau
                )

                st.dataframe(
                    styled_df,
                    column_config=column_config,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Belum ada sinyal Buy yang aman saat ini.")

            # Tabel Extended (Opsional)
            df_ext = df[df['Status'].str.contains("EXTENDED")]
            if not df_ext.empty:
                with st.expander("⚠️ Saham Extended (Tunggu Koreksi)"):
                    st.dataframe(
                        df_ext.drop(columns=['Priority']).style.set_properties(**{'text-align': 'center'}),
                        column_config=column_config,
                        use_container_width=True,
                        hide_index=True
                    )
        else:
            st.error("Data tidak ditemukan.")
