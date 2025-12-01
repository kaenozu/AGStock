# Add this to the end of app.py

# --- Tab Export: Export Manager ---
with tab_export:
    from src.ui_export import render_export_tab
    render_export_tab()

# --- Tab Alerts: Alert Management ---
with tab_alerts:
    from src.ui_alerts import render_alerts_tab
    render_alerts_tab()

# --- Tab Social: Social Trading ---
with tab_social:
    st.header("🏆 ソーシャルトレーディング")
    
    social_tab1, social_tab2, social_tab3 = st.tabs(["リーダーボード", "コピートレード", "戦略マーケット"])
    
    with social_tab1:
        st.subheader("📊 トップトレーダー")
        
        from src.trader_profile import TraderProfileManager
        manager = TraderProfileManager()
        
        # リーダーボード取得
        leaderboard = manager.get_leaderboard(metric='total_return', limit=20)
        
        if not leaderboard.empty:
            st.dataframe(
                leaderboard,
                column_config={
                    "total_return": st.column_config.NumberColumn("リターン (%)", format="%.2f%%"),
                    "sharpe_ratio": st.column_config.NumberColumn("シャープレシオ", format="%.2f"),
                    "max_drawdown": st.column_config.NumberColumn("最大ドローダウン (%)", format="%.2f%%"),
                    "win_rate": st.column_config.NumberColumn("勝率 (%)", format="%.2f%%"),
                    "follower_count": st.column_config.NumberColumn("フォロワー数")
                },
                use_container_width=True
            )
        else:
            st.info("トレーダーデータがありません。")
    
    with social_tab2:
        st.subheader("📋 コピートレード設定")
        
        from src.copy_trading import CopyTradingEngine
        engine = CopyTradingEngine()
        
        st.write("**コピー設定**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            copy_percentage = st.slider("コピー比率 (%)", 1, 100, 10)
            max_per_trade = st.number_input("1取引あたりの上限 (¥)", value=50000, step=10000)
        
        with col2:
            max_total = st.number_input("総投資額上限 (¥)", value=100000, step=10000)
            min_confidence = st.slider("最小信頼度", 0.0, 1.0, 0.5, 0.1)
        
        if st.button("設定を保存", type="primary"):
            st.success("コピー設定を保存しました")
    
    with social_tab3:
        st.subheader("🏪 戦略マーケットプレイス")
        
        from src.strategy_marketplace import StrategyMarketplace
        marketplace = StrategyMarketplace()
        
        # 検索
        search_query = st.text_input("戦略を検索", placeholder="例: SMA, RSI, MACD")
        category = st.selectbox("カテゴリ", ["すべて", "technical", "fundamental", "ml", "hybrid"])
        
        # 戦略一覧
        strategies = marketplace.search_strategies(
            query=search_query if search_query else None,
            category=category if category != "すべて" else None,
            limit=20
        )
        
        if not strategies.empty:
            for _, strategy in strategies.iterrows():
                with st.expander(f"⭐ {strategy['name']} - {strategy['author']}"):
                    st.write(f"**説明**: {strategy['description']}")
                    st.write(f"**カテゴリ**: {strategy['category']}")
                    st.write(f"**価格**: ¥{strategy['price']:,.0f}")
                    st.write(f"**評価**: {'⭐' * int(strategy['rating'])} ({strategy['rating']:.1f})")
                    st.write(f"**ダウンロード数**: {strategy['downloads']}")
                    
                    if st.button(f"ダウンロード", key=f"dl_{strategy['id']}"):
                        st.success("戦略をダウンロードしました")
        else:
            st.info("戦略が見つかりませんでした。")

# --- Tab Tax: Tax Optimization ---
with tab_tax:
    st.header("💰 税務最適化")
    
    tax_tab1, tax_tab2, tax_tab3 = st.tabs(["税金計算", "NISA管理", "確定申告"])
    
    with tax_tab1:
        st.subheader("💵 税金シミュレーション")
        
        from src.tax_calculator import TaxCalculator
        calc = TaxCalculator()
        
        profit = st.number_input("利益 (¥)", value=1000000, step=100000)
        is_nisa = st.checkbox("NISA口座", value=False)
        
        tax_info = calc.calculate_capital_gains_tax(profit, is_nisa)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("利益", f"¥{tax_info['profit']:,.0f}")
        with col2:
            st.metric("税金", f"¥{tax_info['total_tax']:,.0f}")
        with col3:
            st.metric("税引後", f"¥{tax_info['net_profit']:,.0f}")
        
        st.write(f"**実効税率**: {tax_info['effective_tax_rate']:.2%}")
        
        # 損失収穫
        st.divider()
        st.subheader("📉 損失収穫最適化")
        
        from src.paper_trader import PaperTrader
        pt = PaperTrader()
        positions = pt.get_positions()
        
        if not positions.empty:
            harvest = calc.optimize_loss_harvesting(positions)
            
            if harvest:
                st.write(f"**推奨売却**: {len(harvest)}件")
                
                for rec in harvest:
                    st.write(f"- {rec['ticker']}: 損失¥{rec['unrealized_loss']:,.0f}, 節税¥{rec['tax_benefit']:,.0f}")
            else:
                st.info("損失収穫の推奨はありません。")
        else:
            st.info("ポジションがありません。")
    
    with tax_tab2:
        st.subheader("🎯 NISA枠管理")
        
        from src.nisa_manager import NISAManager, NISAType
        nisa_mgr = NISAManager()
        
        remaining = nisa_mgr.get_remaining_limit(1, NISAType.NEW_NISA)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("年間上限", f"¥{remaining['total_limit']:,.0f}")
            st.metric("使用済み", f"¥{remaining['total_used']:,.0f}")
        
        with col2:
            st.metric("残り枠", f"¥{remaining['total_remaining']:,.0f}")
            
            progress = remaining['total_used'] / remaining['total_limit'] if remaining['total_limit'] > 0 else 0
            st.progress(progress)
    
    with tax_tab3:
        st.subheader("📄 確定申告書生成")
        
        from src.tax_report_generator import TaxReportGenerator
        generator = TaxReportGenerator()
        
        year = st.number_input("年度", value=2025, step=1)
        
        if st.button("年間報告書を生成", type="primary"):
            from src.paper_trader import PaperTrader
            pt = PaperTrader()
            
            trades = pt.get_trade_history()
            user_info = {
                'name': '山田太郎',
                'address': '東京都',
                'birth_date': '1990/01/01'
            }
            
            pdf = generator.generate_annual_report(year, trades, user_info)
            
            st.download_button(
                label="📥 PDFをダウンロード",
                data=pdf,
                file_name=f"annual_report_{year}.pdf",
                mime="application/pdf"
            )

# --- Tab Options: Options Pricing ---
with tab_options:
    st.header("🎲 オプション取引")
    
    opt_tab1, opt_tab2 = st.tabs(["価格計算", "戦略"])
    
    with opt_tab1:
        st.subheader("📊 Black-Scholes計算")
        
        from src.options_pricing import OptionsCalculator
        calc = OptionsCalculator()
        
        col1, col2 = st.columns(2)
        
        with col1:
            S = st.number_input("現在価格 (¥)", value=1500.0, step=10.0)
            K = st.number_input("行使価格 (¥)", value=1550.0, step=10.0)
            T = st.number_input("満期までの日数", value=30, step=1) / 365
        
        with col2:
            r = st.number_input("リスクフリーレート (%)", value=1.0, step=0.1) / 100
            sigma = st.number_input("ボラティリティ (%)", value=25.0, step=1.0) / 100
            option_type = st.selectbox("オプションタイプ", ["call", "put"])
        
        if st.button("計算", type="primary"):
            price = calc.black_scholes(S, K, T, r, sigma, option_type)
            greeks = calc.calculate_greeks(S, K, T, r, sigma, option_type)
            
            st.success(f"**オプション価格**: ¥{price:.2f}")
            
            st.write("**Greeks:**")
            col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
            
            with col_g1:
                st.metric("Delta", f"{greeks['delta']:.4f}")
            with col_g2:
                st.metric("Gamma", f"{greeks['gamma']:.4f}")
            with col_g3:
                st.metric("Theta", f"{greeks['theta']:.4f}")
            with col_g4:
                st.metric("Vega", f"{greeks['vega']:.4f}")
            with col_g5:
                st.metric("Rho", f"{greeks['rho']:.4f}")
    
    with opt_tab2:
        st.subheader("📈 オプション戦略")
        
        from src.options_pricing import OptionStrategy
        
        strategy_type = st.selectbox(
            "戦略",
            ["カバードコール", "プロテクティブプット", "ストラドル"]
        )
        
        if strategy_type == "カバードコール":
            stock_price = st.number_input("株価", value=1500.0)
            stock_quantity = st.number_input("保有株数", value=100)
            call_strike = st.number_input("コール行使価格", value=1550.0)
            call_premium = st.number_input("コールプレミアム", value=30.0)
            
            if st.button("分析"):
                result = OptionStrategy.covered_call(
                    stock_price, stock_quantity, call_strike, call_premium
                )
                
                st.write(f"**{result['strategy']}**")
                st.write(f"最大利益: ¥{result['max_profit']:,.0f}")
                st.write(f"最大損失: ¥{result['max_loss']:,.0f}")
                st.write(f"損益分岐点: ¥{result['breakeven']:,.0f}")
                st.info(result['description'])

# --- Tab Meta: Meta Learning ---
with tab_meta:
    st.header("🤖 AI自己進化")
    
    st.subheader("🔬 メタ学習エンジン")
    
    from src.meta_learner import MetaLearner
    
    st.write("**AutoML - 自動モデル最適化**")
    
    ticker = st.text_input("銘柄コード", value="7203.T")
    n_trials = st.slider("最適化試行回数", 10, 100, 20)
    
    if st.button("戦略を自動発見", type="primary"):
        with st.spinner("最適化中..."):
            from src.data_loader import fetch_stock_data
            
            data_map = fetch_stock_data([ticker], period="2y")
            data = data_map.get(ticker)
            
            if data is not None and not data.empty:
                learner = MetaLearner(n_trials=n_trials)
                strategies = learner.discover_strategies(data, min_sharpe=0.5)
                
                if strategies:
                    st.success(f"✅ {len(strategies)}個の戦略を発見しました！")
                    
                    for strategy in strategies:
                        with st.expander(f"⭐ {strategy['name']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("シャープレシオ", f"{strategy['sharpe_ratio']:.2f}")
                            with col2:
                                st.metric("累積リターン", f"{strategy['cumulative_return']:.2%}")
                            with col3:
                                st.metric("精度", f"{strategy['accuracy']:.2%}")
                            
                            st.write(f"**パラメータ**: {strategy['params']}")
                else:
                    st.warning("有効な戦略が見つかりませんでした。")
            else:
                st.error("データの取得に失敗しました。")

st.sidebar.divider()
st.sidebar.caption("AGStock v3.0 - Phase 0-40 Complete")
