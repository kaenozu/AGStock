import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES, MARKETS
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy, MLStrategy, LightGBMStrategy, DeepLearningStrategy, EnsembleStrategy, load_custom_strategies
from src.backtester import Backtester
from src.portfolio import PortfolioManager
from src.paper_trader import PaperTrader
from src.live_trading import PaperBroker, LiveTradingEngine
from src.llm_analyzer import LLMAnalyzer
from src.agents import TechnicalAnalyst, FundamentalAnalyst, MacroStrategist, RiskManager, PortfolioManager
from src.cache_config import install_cache

# Design System Imports
from src.design_tokens import Colors, RISK_LEVELS, ACTION_TYPES
from src.formatters import (
    format_currency, format_percentage, format_number, 
    get_risk_level, get_sentiment_label
)
from src.ui_components import (
    display_risk_badge, display_action_badge, display_sentiment_gauge,
    display_stock_card, display_best_pick_card, display_error_message,
    display_loading_skeleton
)

# Install cache
install_cache()

# Initialize Strategies
strategies = [
    SMACrossoverStrategy(),
    RSIStrategy(),
    BollingerBandsStrategy(),
    CombinedStrategy(),
    MLStrategy(),
    LightGBMStrategy(),
    LightGBMStrategy(),
    DeepLearningStrategy(),
    EnsembleStrategy()
]
strategies.extend(load_custom_strategies())

st.set_page_config(page_title="AI Stock Predictor", layout="wide")

st.title("🌍 グローバル株式 AI 予測アナライザー (Pro)")
st.markdown("日本・米国・欧州の主要株式を対象とした、プロ仕様のバックテストエンジン搭載。")

# Load Custom CSS v2 (Improved Design System)
try:
    with open("assets/style_v2.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback to original CSS
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load Mobile Optimizations
try:
    with open("assets/mobile.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass  # モバイルCSSはオプション

# Set Default Plotly Template
import plotly.io as pio
pio.templates.default = "plotly_dark"

# Sidebar
st.sidebar.header("設定")

# Market Selection
selected_market = st.sidebar.selectbox("市場選択 (Market)", ["Japan", "US", "Europe", "Crypto", "All"], index=0)
ticker_group = st.sidebar.selectbox("対象銘柄", [f"{selected_market} 主要銘柄", "カスタム入力"])

custom_tickers = []
if ticker_group == "カスタム入力":
    custom_input = st.sidebar.text_area("銘柄コードを入力 (カンマ区切り)", "7203.T, 9984.T")
    if custom_input:
        custom_tickers = [t.strip() for t in custom_input.split(",")]

period = st.sidebar.selectbox("分析期間", ["1y", "2y", "5y"], index=1)

# Trading Unit Setting
st.sidebar.divider()
st.sidebar.subheader("取引設定")
use_fractional_shares = st.sidebar.checkbox("単元未満株 (1株〜) で取引", value=False, help="ONにすると、1株単位（S株/ミニ株）でシミュレーションします。少額資金での運用に適しています。")
trading_unit = 1 if use_fractional_shares else 100

# Notification Settings
st.sidebar.divider()
with st.sidebar.expander("📢 通知設定"):
    st.write("スキャン完了後に自動通知を送信します。")
    
    # Load current config
    import json
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except:
        config = {"notifications": {"line": {"enabled": False, "token": ""}, "discord": {"enabled": False, "webhook_url": ""}}}
    
    # LINE Notify
    line_enabled = st.checkbox("LINE Notify を有効化", value=config.get("notifications", {}).get("line", {}).get("enabled", False))
    line_token = st.text_input("LINE Notify Token", value=config.get("notifications", {}).get("line", {}).get("token", ""), type="password", help="https://notify-bot.line.me/ja/ からトークンを取得してください")
    
    # Discord
    discord_enabled = st.checkbox("Discord Webhook を有効化", value=config.get("notifications", {}).get("discord", {}).get("enabled", False))
    discord_webhook = st.text_input("Discord Webhook URL", value=config.get("notifications", {}).get("discord", {}).get("webhook_url", ""), type="password", help="Discordサーバー設定からWebhook URLを取得してください")
    
    # Save button
    if st.button("設定を保存", key="save_notification_config"):
        config["notifications"]["line"]["enabled"] = line_enabled
        config["notifications"]["line"]["token"] = line_token
        config["notifications"]["discord"]["enabled"] = discord_enabled
        config["notifications"]["discord"]["webhook_url"] = discord_webhook
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        st.success("✅ 通知設定を保存しました！")

# Risk Management
st.sidebar.divider()
st.sidebar.subheader("リスク管理")
allow_short = st.sidebar.checkbox("空売りを許可", value=False)
position_size = st.sidebar.slider("ポジションサイズ (%)", min_value=10, max_value=100, value=100, step=10) / 100

# Fundamental Filters
st.sidebar.divider()
st.sidebar.subheader("ファンダメンタルズ (財務)")
enable_fund_filter = st.sidebar.checkbox("財務フィルタを有効化", value=False)
max_per = st.sidebar.number_input("PER (倍) 以下", value=15.0, step=1.0, disabled=not enable_fund_filter)
max_pbr = st.sidebar.number_input("PBR (倍) 以下", value=1.5, step=0.1, disabled=not enable_fund_filter)
min_roe = st.sidebar.number_input("ROE (%) 以上", value=8.0, step=1.0, disabled=not enable_fund_filter)

# Live Mode
st.sidebar.divider()
if st.sidebar.checkbox("🔄 自動更新 (Live Mode)", value=False, help="60秒ごとにページを自動更新します。"):
    import time
    time.sleep(60)
    st.rerun()

# Create Tabs
tab_auto, tab_dashboard, tab1, tab2, tab3, tab4, tab5, tab_perf = st.tabs([
    "🚀 フルオート",
    "🏠 ダッシュボード", 
    "📊 市場スキャン", 
    "💼 ポートフォリオ", 
    "📝 ペーパートレード", 
    "📈 詳細分析", 
    "🕰️ 過去検証",
    "📊 パフォーマンス分析"
])

# --- Tab Auto: Fully Automated Trader UI ---
with tab_auto:
    from src.auto_trader_ui import create_auto_trader_ui
    create_auto_trader_ui()

# --- Tab Dashboard: Simple Dashboard ---
with tab_dashboard:
    from src.simple_dashboard import create_simple_dashboard
    create_simple_dashboard()

# --- Tab Performance: Enhanced Performance Dashboard ---
with tab_perf:
    from src.enhanced_performance_dashboard import create_performance_dashboard
    create_performance_dashboard()


with tab1:
    st.header("市場全体スキャン")
    st.write("指定した銘柄群に対して全戦略をバックテストし、有望なシグナルを検出します。")

    # --- Automation Logic ---
    import json
    import os
    import datetime
    
    cached_results = None
    if os.path.exists("scan_results.json"):
        try:
            with open("scan_results.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Check if data is fresh (e.g., from today)
                scan_date = datetime.datetime.strptime(data['scan_date'], '%Y-%m-%d %H:%M:%S')
                if scan_date.date() == datetime.date.today():
                    cached_results = data
                    st.success(f"✅ 最新のスキャン結果を読み込みました ({data['scan_date']})")
        except Exception as e:
            display_error_message(
                "data",
                "スキャン結果の読み込みに失敗しました。ファイルが破損している可能性があります。",
                str(e)
            )

    run_fresh = False
    # Button logic: If cache exists, button says "Re-scan". If not, "Scan".
    # If button clicked, run_fresh becomes True.
    if st.button("市場をスキャンして推奨銘柄を探す (再スキャン)" if cached_results else "市場をスキャンして推奨銘柄を探す", type="primary"):
        run_fresh = True
        cached_results = None # Force fresh scan logic

    if cached_results and not run_fresh:
        sentiment = cached_results['sentiment']
        results_data = cached_results['results']
        
        # === Display Cached Sentiment ===
        with st.expander("📰 市場センチメント分析", expanded=True):
            display_sentiment_gauge(sentiment['score'], sentiment.get('news_count', 0))

            st.subheader("📰 最新ニュース見出し")
            if sentiment.get('top_news'):
                for i, news in enumerate(sentiment['top_news'][:5], 1):
                     st.markdown(f"{i}. [{news['title']}]({news['link']})")

        # === Display Cached Results ===
        results_df = pd.DataFrame(results_data)
        if not results_df.empty:
            actionable_df = results_df[results_df['Action'] != 'HOLD'].copy()
            
            # Apply Fundamental Filters
            if enable_fund_filter:
                original_count = len(actionable_df)
                # Filter logic: Keep if data is missing (NaN) or meets condition?
                # Usually strict filtering: Must meet condition.
                # But if data is missing, maybe keep? Let's be strict for "Quality".
                
                # PER
                if 'PER' in actionable_df.columns:
                    actionable_df = actionable_df[
                        (actionable_df['PER'].notna()) & (actionable_df['PER'] <= max_per)
                    ]
                
                # PBR
                if 'PBR' in actionable_df.columns:
                    actionable_df = actionable_df[
                        (actionable_df['PBR'].notna()) & (actionable_df['PBR'] <= max_pbr)
                    ]
                    
                # ROE
                if 'ROE' in actionable_df.columns:
                    actionable_df = actionable_df[
                        (actionable_df['ROE'].notna()) & (actionable_df['ROE'] >= min_roe / 100.0) # ROE is usually 0.08 for 8%
                    ]
                
                filtered_count = len(actionable_df)
                if original_count > filtered_count:
                    st.info(f"財務フィルタにより {original_count} 件中 {original_count - filtered_count} 件が除外されました。")

            actionable_df = actionable_df.sort_values(by="Return", ascending=False)

            # 1. Today's Best Pick
            if not actionable_df.empty:
                best_pick = actionable_df.iloc[0]
                
                # リスクレベル判定（統一版）
                risk_level = get_risk_level(best_pick.get('Max Drawdown', -0.15))
                
                # 追加情報の準備
                additional_info = {}
                if 'PER' in best_pick and pd.notna(best_pick['PER']):
                    additional_info['PER'] = best_pick['PER']
                if 'PBR' in best_pick and pd.notna(best_pick['PBR']):
                    additional_info['PBR'] = best_pick['PBR']
                if 'ROE' in best_pick and pd.notna(best_pick['ROE']):
                    additional_info['ROE'] = best_pick['ROE']
                
                # 注文コールバック
                def handle_best_pick_order(ticker, action, price):
                    pt = PaperTrader()
                    trade_action = "BUY" if "BUY" in action else "SELL"
                    if pt.execute_trade(ticker, trade_action, trading_unit, price, reason=f"Best Pick: {best_pick['Strategy']}"):
                        st.balloons()
                        st.success(f"{best_pick['Name']} を {trading_unit}株 {trade_action} しました！")
                    else:
                        display_error_message(
                            "permission",
                            "注文に失敗しました。資金不足または保有株式が不足しています。",
                            f"Ticker: {ticker}, Action: {trade_action}, Unit: {trading_unit}"
                        )
                
                # 改善版コンポーネントで表示
                display_best_pick_card(
                    ticker=best_pick['Ticker'],
                    name=best_pick['Name'],
                    action=best_pick['Action'],
                    price=best_pick['Last Price'],
                    explanation=best_pick.get('Explanation', ''),
                    strategy=best_pick['Strategy'],
                    risk_level=risk_level,
                    on_order_click=handle_best_pick_order,
                    additional_info=additional_info if additional_info else None
                )

            # 1.5. AI Robo-Advisor Portfolio
            if 'portfolio' in cached_results and cached_results['portfolio']:
                portfolio = cached_results['portfolio']
                st.markdown("---")
                with st.expander("💰 AIロボアドバイザー・ポートフォリオ", expanded=False):
                    st.write(f"**推奨銘柄数**: {portfolio['total_assets']}銘柄")
                    st.write("AIが最適なリスク・リターン比率で配分を計算しました。")
                    
                    # Display weights as pie chart
                    weights_df = pd.DataFrame([
                        {"銘柄": TICKER_NAMES.get(t, t), "配分比率": w * 100}
                        for t, w in portfolio['weights'].items()
                    ])
                    
                    fig_pie = px.pie(
                        weights_df,
                        values='配分比率',
                        names='銘柄',
                        title='推奨ポートフォリオ配分'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Display as table
                    st.dataframe(weights_df, use_container_width=True)
                    
                    # Apply to Paper Trading button
                    if st.button("📝 このポートフォリオで一括注文（バーチャル）", key="portfolio_order"):
                        pt = PaperTrader()
                        total_capital = 1000000  # 100万円を想定
                        success_count = 0
                        
                        for ticker, weight in portfolio['weights'].items():
                            # Find the price from results
                            ticker_result = next((r for r in cached_results['results'] if r['Ticker'] == ticker and r['Action'] == 'BUY'), None)
                            if ticker_result:
                                allocated_amount = total_capital * weight
                                if use_fractional_shares:
                                    # Fractional shares (1 share unit)
                                    shares = int(allocated_amount / ticker_result['Last Price'])
                                else:
                                    # Standard lot (100 share unit)
                                    shares = int(allocated_amount / (ticker_result['Last Price'] * 100)) * 100
                                
                                if shares > 0:
                                    if pt.execute_trade(ticker, "BUY", shares, ticker_result['Last Price'], reason="Robo-Advisor Portfolio"):
                                        success_count += 1
                        
                        if success_count > 0:
                            st.balloons()
                            st.success(f"✅ {success_count}銘柄の注文が完了しました！")

            # 1.6. High Dividend Strategy
            if 'high_dividend' in cached_results and cached_results['high_dividend']:
                st.markdown("---")
                with st.expander("💰 高配当・積立", expanded=True):
                    st.write("長期保有・積立投資に適した高配当銘柄です（利回り3%以上、配当性向80%以下）。")
                    
                    hd_df = pd.DataFrame(cached_results['high_dividend'])
                    
                    # Format columns for display (統一版フォーマット使用)
                    display_df = hd_df.copy()
                    display_df['Yield'] = display_df['Yield'].apply(lambda x: format_percentage(x, decimals=2))
                    display_df['PayoutRatio'] = display_df['PayoutRatio'].apply(lambda x: format_percentage(x, decimals=2))
    
    # Selection
    if ticker_group == "カスタム入力":
        available_tickers = custom_tickers
    else:
        available_tickers = NIKKEI_225_TICKERS
        
    selected_portfolio = st.multiselect("ポートフォリオに組み入れる銘柄を選択 (3つ以上推奨)", 
                                      options=available_tickers,
                                      default=available_tickers[:5] if len(available_tickers) >=5 else available_tickers,
                                      format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}")
    
    initial_capital = st.number_input("初期投資額 (円)", value=10000000, step=1000000)
    
    if st.button("ポートフォリオを分析する"):
        if len(selected_portfolio) < 2:
            st.error("少なくとも2つの銘柄を選択してください。")
        else:
            with st.spinner("ポートフォリオ分析を実行中..."):
                pm = PortfolioManager(initial_capital=initial_capital)
                data_map_pf = fetch_stock_data(selected_portfolio, period=period)
                
                # 1. Correlation Matrix
                st.subheader("相関行列 (Correlation Matrix)")
                st.write("銘柄間の値動きの連動性を示します。1に近いほど同じ動き、-1に近いほど逆の動きをします。分散投資には相関が低い（色が薄い）組み合わせが有効です。")
                corr_matrix = pm.calculate_correlation(data_map_pf)
                
                if not corr_matrix.empty:
                    fig_corr = px.imshow(corr_matrix, 
                                       text_auto=True, 
                                       color_continuous_scale='RdBu_r', 
                                       zmin=-1, zmax=1,
                                       title="Correlation Matrix")
                    st.plotly_chart(fig_corr, use_container_width=True)
                
                # 2. Portfolio Backtest
                st.subheader("ポートフォリオ資産推移")
                
                # Assign strategies
                st.subheader("戦略の選択")
                pf_strategies = {}
                
                # Create a container for strategy selectors
                cols = st.columns(3)
                for i, ticker in enumerate(selected_portfolio):
                    with cols[i % 3]:
                        # Default to CombinedStrategy (index 3 in our list)
                        strat_names = [s.name for s in strategies]
                        selected_strat_name = st.selectbox(
                            f"{TICKER_NAMES.get(ticker, ticker)}", 
                            strat_names, 
                            index=3,
                            key=f"strat_{ticker}"
                        )
                        # Find the strategy instance
                        pf_strategies[ticker] = next(s for s in strategies if s.name == selected_strat_name)
                
                st.divider()
                
                # Weight Optimization
                weight_mode = st.radio("配分比率 (Weights)", ["均等配分 (Equal)", "最適化 (Max Sharpe)"], horizontal=True)
                
                weights = {}
                if weight_mode == "均等配分 (Equal)":
                    weight = 1.0 / len(selected_portfolio)
                    weights = {t: weight for t in selected_portfolio}
                else:
                    with st.spinner("シャープレシオ最大化ポートフォリオを計算中..."):
                        weights = pm.optimize_portfolio(data_map_pf)
                        st.success("最適化完了")
                        
                        # Display Weights
                        st.write("推奨配分比率:")
                        w_df = pd.DataFrame.from_dict(weights, orient='index', columns=['Weight'])
                        w_df['Weight'] = w_df['Weight'].apply(lambda x: f"{x*100:.1f}%")
                        st.dataframe(w_df.T)

                pf_res = pm.simulate_portfolio(data_map_pf, pf_strategies, weights)
                
                if pf_res:
                    col1, col2 = st.columns(2)
                    col1.metric("トータルリターン", f"{pf_res['total_return']*100:.1f}%")
                    col2.metric("最大ドローダウン", f"{pf_res['max_drawdown']*100:.1f}%")
                    
                    fig_pf = go.Figure()
                    fig_pf.add_trace(go.Scatter(x=pf_res['equity_curve'].index, y=pf_res['equity_curve'], mode='lines', name='Portfolio', line=dict(color='gold', width=2)))
                    
                    # Add individual components (optional, maybe too messy)
                    # for t, res in pf_res['individual_results'].items():
                    #     fig_pf.add_trace(go.Scatter(x=res['equity_curve'].index, y=res['equity_curve'] * (initial_capital * weights[t]), mode='lines', name=t, opacity=0.3))
                        
                    fig_pf.update_layout(title="ポートフォリオ全体の資産推移", xaxis_title="Date", yaxis_title="Total Equity (JPY)")
                    st.plotly_chart(fig_pf, use_container_width=True)
                else:
                    st.error("シミュレーションに失敗しました。データが不足している可能性があります。")

# --- Tab 3: Paper Trading ---
with tab3:
    from src.ui_renderers import render_paper_trading_tab
    render_paper_trading_tab()
    history = pt.get_trade_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("取引履歴はありません。")

# --- Tab 4: Dashboard ---
with tab4:
    from src.ui_renderers import render_performance_tab
    render_performance_tab(ticker_group, selected_market, custom_tickers)
    
    st.divider()
    
    st.divider()
    
    # Performance Tracking
    st.subheader("📈 パフォーマンス追跡")
    st.write("Paper Tradingの運用成績を可視化します。")
    
    pt_perf = PaperTrader()
    balance = pt_perf.get_current_balance()
    equity_history = pt_perf.get_equity_history()
    
    # Current Status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総資産", format_currency(balance['total_equity']))
    with col2:
        profit = balance['total_equity'] - pt_perf.initial_capital
        profit_pct = (profit / pt_perf.initial_capital) * 100
        st.metric("損益", format_currency(profit, decimals=0), f"{profit_pct:+.2f}%")
    with col3:
        st.metric("現金", format_currency(balance['cash']))
    
    # Equity Curve
    if not equity_history.empty:
        st.subheader("資産推移")
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=equity_history['date'],
            y=equity_history['total_equity'],
            mode='lines',
            name='Total Equity',
            line=dict(color='gold', width=2)
        ))
        fig_equity.add_hline(
            y=pt_perf.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="初期資金"
        )
        fig_equity.update_layout(
            title="資産推移（Paper Trading）",
            xaxis_title="日付",
            yaxis_title="資産 (円)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_equity, use_container_width=True)
        
        # Monthly Performance
        if len(equity_history) > 1:
            equity_history['month'] = pd.to_datetime(equity_history['date']).dt.to_period('M')
            monthly_returns = equity_history.groupby('month').agg({
                'total_equity': ['first', 'last']
            })
            monthly_returns['return'] = (
                (monthly_returns[('total_equity', 'last')] - monthly_returns[('total_equity', 'first')]) / 
                monthly_returns[('total_equity', 'first')]
            )
            
            if len(monthly_returns) > 0:
                st.subheader("月次リターン")
                monthly_returns_display = monthly_returns['return'].apply(lambda x: f"{x*100:+.2f}%")
                st.dataframe(monthly_returns_display.to_frame(name='リターン'), use_container_width=True)
    else:
        st.info("まだ取引履歴がありません。Paper Tradingタブで取引を開始してください。")
    
    st.divider()
    
    # Alert Configuration
    st.subheader("🔔 アラート設定")
    st.write("価格変動アラートを設定できます（将来実装予定）。")
    
    alert_ticker = st.selectbox(
        "監視する銘柄",
        options=MARKETS[selected_market][:10],
        format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        alert_type = st.selectbox("アラートタイプ", ["価格上昇", "価格下落"])
    with col2:
        threshold = st.number_input("閾値 (%)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)
    
    if st.button("アラートを設定"):
        st.success(f"✓ {alert_ticker} の{alert_type}アラート（{threshold}%）を設定しました（デモ）")
        st.info("実際のアラートは `src/notifier.py` を使用して実装できます。")

# --- Tab 5: Historical Validation ---
with tab5:
    st.header("🕰️ 過去検証 (Historical Validation)")
    st.write("過去10年間のデータを使用して、戦略の長期的な有効性を検証します。")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        hist_ticker = st.selectbox("検証銘柄", MARKETS[selected_market], format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}", key="hist_ticker")
    with col2:
        hist_strategy = st.selectbox("戦略", ["RSIStrategy", "BollingerBandsStrategy", "CombinedStrategy", "DividendStrategy"], key="hist_strategy")
    with col3:
        hist_years = st.slider("検証期間 (年)", 1, 10, 10, key="hist_years")
        
    if st.button("検証開始", type="primary", key="run_hist_btn"):
        with st.spinner(f"{hist_ticker} の過去{hist_years}年間のデータを取得・検証中..."):
            try:
                from src.backtest_engine import HistoricalBacktester
                from src.strategies import RSIStrategy, BollingerBandsStrategy, CombinedStrategy, DividendStrategy
                
                strategy_map = {
                    "RSIStrategy": RSIStrategy,
                    "BollingerBandsStrategy": BollingerBandsStrategy,
                    "CombinedStrategy": CombinedStrategy,
                    "DividendStrategy": DividendStrategy
                }
                
                hb = HistoricalBacktester()
                results = hb.run_test(hist_ticker, strategy_map[hist_strategy], years=hist_years)
                
                if "error" in results:
                    st.error(f"エラー: {results['error']}")
                else:
                    # Metrics
                    st.markdown("### 📊 検証結果")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("CAGR (年平均成長率)", f"{results['cagr']:.2%}", help="複利計算による年平均リターン")
                    m2.metric("総リターン", f"{results['total_return']:.2%}")
                    m3.metric("最大ドローダウン", f"{results['max_drawdown']:.2%}", help="資産の最大下落率")
                    m4.metric("勝率", f"{results['win_rate']:.1%}")
                    
                    # Benchmark Comparison
                    bh_cagr = results['buy_hold_cagr']
                    delta_cagr = results['cagr'] - bh_cagr
                    st.info(f"参考: Buy & Hold (ガチホ) の CAGR は {bh_cagr:.2%} です。戦略による改善効果: {delta_cagr:+.2%}")
                    
                    # Equity Curve
                    st.subheader("資産推移")
                    equity_curve = results['equity_curve']
                    equity_df = equity_curve.to_frame(name="Strategy")
                    st.line_chart(equity_df, use_container_width=True)
                    
                    # Annual Returns
                    st.subheader("年次リターン")
                    annual_returns = pd.Series(results['annual_returns'])
                    # Format index as string for better chart labels
                    annual_returns.index = annual_returns.index.astype(str)
                    
                    # Color positive green, negative red (Streamlit bar chart doesn't support conditional color easily, so just bar chart)
                    st.bar_chart(annual_returns, use_container_width=True)
                    
                    # Trade List
                    with st.expander("取引履歴詳細"):
                        trades_df = pd.DataFrame(results['trades'])
                        if not trades_df.empty:
                            st.dataframe(trades_df)
                        else:
                            st.write("取引なし")
                    
            except Exception as e:
                st.error(f"検証エラー: {e}")

# === AI Investment Committee ===
st.header("🏛️ AI Investment Committee")  
st.write("専門AIエージェントの「会議」により投資判断を下します。")

committee_ticker = st.selectbox(
    "分析対象銘柄",
    MARKETS.get("Japan", NIKKEI_225_TICKERS),
    format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}",
    key="committee_ticker"
)

if st.button("🏛️ 投資委員会を召集", type="primary", key="run_committee"):
    with st.spinner(f"{committee_ticker} の分析中..."):
        # Fetch data
        stock_data_dict = fetch_stock_data([committee_ticker], period="1y")
        stock_df = stock_data_dict.get(committee_ticker)
        
        # news_data = fetch_news(committee_ticker)  # 未実装
        news_data = None
        
        # Prepare data bundle
        data = {
            "stock_data": stock_df,
            "news_data": news_data,
            "macro_data": None  # Can be fetched if needed
        }
        
        # Initialize Agents
        tech_agent = TechnicalAnalyst()
        fund_agent = FundamentalAnalyst()
        macro_agent = MacroStrategist()
        risk_agent = RiskManager()
        pm_agent = PortfolioManager()
        
        # Collect Votes
        votes = []
        votes.append(tech_agent.vote(committee_ticker, data))
        votes.append(fund_agent.vote(committee_ticker, data))
        votes.append(macro_agent.vote(committee_ticker, data))
        votes.append(risk_agent.vote(committee_ticker, data))
       
        # Final Decision
        decision = pm_agent.make_decision(committee_ticker, votes)
        
        # Display Results
        st.markdown("---")
        st.subheader(f"🎯 最終判断: {decision['decision']}")
        st.metric("Decision Score", f"{decision['score']:.2f}")
        
        if decision['decision'] == "BUY":
            st.success("✅ 委員会は「買い」を推奨します。")
        elif decision['decision'] == "SELL":
            st.error("❌ 委員会は「売り」を推奨します。")
        else:
            st.info("⚪ 委員会は「様子見」を推奨します。")
        
        st.markdown("---")
        st.subheader("🗣️ エージェント別の意見")
        
        for vote in votes:
            with st.container():
                icon = "🟢" if vote.decision == "BUY" else "🔴" if vote.decision == "SELL" else "⚪"
                st.markdown(f"{icon} **{vote.agent_name}**: {vote.decision} (信頼度: {vote.confidence:.2f})")
                st.caption(vote.reasoning)
                st.divider()
        
        st.markdown("---")
        st.subheader("📋 会議議事録")
        for line in decision['summary']:
            st.markdown(line)

# === Broker Control Panel & Emergency Stop ===
st.markdown("---")
st.header("🎛️ Broker Control Panel")

# Load config
import json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except:
    config = {"broker": {"default_mode": "paper"}, "risk_guard": {"enabled": True}}

col_broker1, col_broker2 = st.columns([2, 1])

with col_broker1:
    st.subheader("Broker Selection")
    broker_mode = st.radio(
        "Select Broker Mode",
        ["Paper (Simulator)", "IBKR Paper", "IBKR Live"],
        index=0 if config.get("broker", {}).get("default_mode") == "paper" else 1,
        help="⚠️ IBKR Live uses REAL MONEY. Only enable after thorough Paper Trading validation."
    )
    
    if broker_mode.startswith("IBKR"):
        st.warning("⚠️ IBKR mode requires TWS/IB Gateway running and `ib_insync` installed.")
        st.caption(f"Host: {config.get('broker', {}).get('ibkr', {}).get('host', '127.0.0.1')}")
        
        port = config.get('broker', {}).get('ibkr', {}).get('paper_port' if 'Paper' in broker_mode else 'live_port', 7497)
        st.caption(f"Port: {port}")
        
        # Connection status (placeholder - would need actual connection check)
        connection_status = st.empty()
        connection_status.info("🔴 Not Connected")

with col_broker2:
    st.subheader("Safety Controls")
    
    # Emergency Stop Button
    if st.button("🚨 EMERGENCY STOP", type="primary", help="Immediately halt all trading"):
        st.session_state.emergency_stop = True
        st.error("⛔ EMERGENCY STOP ACTIVATED")
        st.balloons()  # Alert sound
    
    # Status display
    if st.session_state.get("emergency_stop", False):
        st.error("⛔ TRADING HALTED")
        if st.button("Reset Emergency Stop"):
            st.session_state.emergency_stop = False
            st.success("✅ Emergency stop reset")
    else:
        st.success("✅ Trading Active")

st.markdown("---")

# RiskGuard Dashboard
st.subheader("🛡️ Risk Guard Status")

risk_config = config.get("risk_guard", {})
col_risk1, col_risk2, col_risk3 = st.columns(3)

with col_risk1:
    st.metric("Daily Loss Limit", f"{risk_config.get('daily_loss_limit_pct', -5.0)}%")
with col_risk2:
    st.metric("Max Position Size", f"{risk_config.get('max_position_size_pct', 10.0)}%")
with col_risk3:
    st.metric("Max VIX", risk_config.get('max_vix', 40.0))

# Daily P&L Progress (placeholder - would show actual data)
st.caption("Daily P&L Monitor")
pnl_pct = 0.0  # Placeholder
st.progress(max(0, min(1, (pnl_pct + 10) / 20)), text=f"P&L: {pnl_pct:+.2f}%")

if abs(pnl_pct) >= abs(risk_config.get('daily_loss_limit_pct', -5.0)):
    st.error(f"⚠️ Daily loss limit reached: {pnl_pct:.2f}%")
