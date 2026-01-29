# --- TAB 1: SCREENER (AUTO-CLEAR FIXED) ---
with tab1:
    st.header("🔍 Radar Saham")
    
    # Simpan mode sebelumnya untuk mendeteksi perubahan
    if 'last_mode' not in st.session_state:
        st.session_state['last_mode'] = "Radar Diskon (Market Crash)"
        
    mode = st.radio("Pilih Strategi:", ["Radar Diskon (Market Crash)", "Reversal (Pantulan)", "Breakout (Tren Naik)", "Swing (Koreksi Sehat)"], horizontal=True)
    
    # --- LOGIKA PEMBERSIH OTOMATIS (AUTO-CLEAR) ---
    # Jika User mengganti pilihan strategi (Radio Button berubah)
    if mode != st.session_state['last_mode']:
        st.session_state['scan_results'] = None # HAPUS HASIL LAMA
        st.session_state['last_mode'] = mode    # Update mode terakhir
        st.rerun() # Refresh halaman agar tabel hilang seketika
    
    if 'scan_results' not in st.session_state: st.session_state['scan_results'] = None

    if st.button("🚀 SCAN MARKET SEKARANG", type="primary"):
        st.write(f"⏳ Memindai data market untuk: **{mode}**...")
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(SYARIAH_TICKERS):
            progress_bar.progress((i + 1) / len(SYARIAH_TICKERS))
            df, info = get_hybrid_data(t)
            if df is not None and info is not None:
                # --- A. PERSIAPAN DATA ---
                O = df['Open'].iloc[-1]; H = df['High'].iloc[-1]; L = df['Low'].iloc[-1]; C = df['Close'].iloc[-1]
                O_prev = df['Open'].iloc[-2]; C_prev = df['Close'].iloc[-2]
                body = abs(C - O); upper_shadow = H - max(C, O); lower_shadow = min(C, O) - L
                rsi_series = ta.rsi(df['Close'], length=14); rsi_now = rsi_series.iloc[-1]
                vol_now = df['Volume'].iloc[-1]; vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                
                # --- B. DETEKSI POLA CANDLE ---
                pola_candle = ""; is_valid_reversal = False
                if rsi_now < 45: 
                    if (lower_shadow > body * 2) and (upper_shadow < body): pola_candle = "🔨 HAMMER"; is_valid_reversal = True
                    elif (C > O) and (C_prev < O_prev) and (C > O_prev) and (O < C_prev): pola_candle = "🔥 ENGULFING"; is_valid_reversal = True
                
                # --- C. FILTER LOGIC ---
                lolos = False
                roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                per = info.get('trailingPE', 999) if info.get('trailingPE') else 999
                f_stat = "⚠️ Mahal"; 
                if roe > 10 and per < 20: f_stat = "✅ Sehat"
                if roe > 15 and per < 15: f_stat = "💎 Super"

                if "Radar Diskon" in mode: lolos = True
                elif "Reversal" in mode:
                    if is_valid_reversal: lolos = True
                    elif rsi_now < 32 and C > df['High'].iloc[-2]: lolos = True; pola_candle = "↗️ REBOUND" 
                elif "Breakout" in mode:
                     high_20 = df['High'].rolling(20).max().iloc[-2]
                     if C > high_20 and vol_now > vol_avg: lolos = True
                elif "Swing" in mode:
                    ma50 = df['Close'].rolling(50).mean().iloc[-1]
                    if C > ma50 and L <= (ma50 * 1.05) and C > C_prev: lolos = True

                if lolos:
                    vol_ratio = vol_now / vol_avg
                    if vol_ratio < 0.6: v_txt = "😴 Sepi"
                    elif vol_ratio < 1.3: v_txt = "😐 Normal"
                    elif vol_ratio < 3.0: v_txt = "⚡ Ramai"
                    else: v_txt = "🔥 MELEDAK"
                    vol_display = f"{v_txt} ({vol_ratio:.1f}x)"
                    
                    if rsi_now < 30: rsi_txt = "🔥 DISKON"
                    elif rsi_now < 45: rsi_txt = "✅ MURAH"
                    else: rsi_txt = "😐 NORMAL"
                    rsi_display = f"{int(rsi_now)} ({rsi_txt})"
                    
                    if roe > 15: roe_txt = "🚀 ISTIMEWA"
                    elif roe > 10: roe_txt = "✅ BAGUS"
                    else: roe_txt = "⚠️ KURANG"
                    roe_display = f"{roe:.1f}%"

                    signal_final = f_stat
                    if "Reversal" in mode and pola_candle != "": signal_final = f"{pola_candle}" 
                    elif "Breakout" in mode: signal_final = "🚀 BREAKOUT"
                    elif "Swing" in mode: signal_final = "🔄 SWING"

                    tv_link = f"https://www.tradingview.com/chart/{TV_CHART_ID}/?symbol=IDX:{t.replace('.JK','')}"
                    
                    results.append({"Pilih": False, "Stock": t.replace(".JK",""), "Price": int(C), "Chg%": ((C - C_prev)/C_prev)*100, "Vol": vol_display, "Signal": signal_final, "ROE": roe_display, "RSI": rsi_display, "Chart": tv_link})
        progress_bar.empty()
        
        if results:
            df_res = pd.DataFrame(results)
            if "Reversal" in mode: df_res = df_res.sort_values(by="Signal", ascending=True) 
            elif "Radar" in mode: df_res = df_res.sort_values(by="ROE", ascending=False)
            st.session_state['scan_results'] = df_res
        else: st.warning("Tidak ada saham yang sesuai kriteria.")

    # TAMPILKAN HASIL JIKA ADA
    if st.session_state['scan_results'] is not None:
        edited_df = st.data_editor(st.session_state['scan_results'], column_config={"Pilih": st.column_config.CheckboxColumn("Add", width=50), "Stock": st.column_config.TextColumn("Kode", width=60), "Price": st.column_config.NumberColumn("Harga", format="Rp %d", width=80), "Chg%": st.column_config.NumberColumn("Chg%", format="%.2f%%", width=70), "Vol": st.column_config.TextColumn("Volume", width=120), "Signal": st.column_config.TextColumn("SINYAL", width=130), "ROE": st.column_config.TextColumn("ROE", width=70), "RSI": st.column_config.TextColumn("RSI", width=110), "Chart": st.column_config.LinkColumn("View", display_text="📈 Chart", width=70)}, hide_index=True, use_container_width=True)
        
        if st.button("💾 MASUKKAN KE WATCHLIST"):
            selected = edited_df[edited_df["Pilih"] == True]["Stock"].tolist()
            if selected:
                wl = load_data(WATCHLIST_FILE, ["Stock"])
                new = [s for s in selected if s not in wl["Stock"].values]
                if new: 
                    pd.concat([wl, pd.DataFrame([{"Stock": s} for s in new])], ignore_index=True).to_csv(WATCHLIST_FILE, index=False)
                    st.success(f"✅ Berhasil! {len(new)} saham ditambahkan.")
                    time.sleep(1.5); st.rerun()
                else: st.warning("⚠️ Saham sudah ada di Watchlist.")
            else: st.warning("⚠️ Belum ada saham yang dicentang.")
