import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES, MARKETS
from src.data_loader import fetch_stock_data, get_latest_price
from src.strategies import (
    SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy, 
    MLStrategy, LightGBMStrategy, DeepLearningStrategy, EnsembleStrategy, 
    TransformerStrategy, GRUStrategy, AttentionLSTMStrategy, MultiTimeframeStrategy, SentimentStrategy, RLStrategy, load_custom_strategies
)
from src.backtester import Backtester
from src.portfolio import PortfolioManager
from src.paper_trader import PaperTrader
from src.live_trading import PaperBroker, LiveTradingEngine
from src.llm_analyzer import LLMAnalyzer
from src.agents import TechnicalAnalyst, FundamentalAnalyst, MacroStrategist, RiskManager, PortfolioManager as PortfolioManagerAgent
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
    DeepLearningStrategy(),
    EnsembleStrategy(),
    TransformerStrategy(),
    GRUStrategy(),
    AttentionLSTMStrategy(),
    MultiTimeframeStrategy(),
    SentimentStrategy(),
    RLStrategy()
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

# Asset Class Selection
asset_class = st.sidebar.selectbox(
    "資産クラス",
    ["日本株", "暗号資産", "FX"],
    index=0
)

# Market Selection based on Asset Class
if asset_class == "日本株":
    from src.data_loader import JP_STOCKS
    default_tickers = JP_STOCKS
    market_name = "Japan"
elif asset_class == "暗号資産":
    from src.data_loader import CRYPTO_PAIRS
    default_tickers = CRYPTO_PAIRS
    market_name = "Crypto"
else: # FX
    from src.data_loader import FX_PAIRS
    default_tickers = FX_PAIRS
    market_name = "FX"

ticker_group = st.sidebar.selectbox("対象銘柄", [f"{market_name} 主要銘柄", "カスタム入力"])

custom_tickers = []
custom_tickers = []
if ticker_group == "カスタム入力":
    default_input = ", ".join(default_tickers[:5])
    custom_input = st.sidebar.text_area("銘柄コードを入力 (カンマ区切り)", default_input)
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
tab_dashboard, tab_auto, tab_realtime, tab1, tab_risk, tab_ai_report, tab_ai_chat, tab_automation, tab_advanced, tab_monitoring, tab2, tab3, tab4, tab5, tab_perf, tab_export, tab_alerts, tab_social, tab_tax, tab_options, tab_meta = st.tabs([
    "🏠 ダッシュボード", 
    "🚀 フルオート",
    "📡 リアルタイム監視",
    "📊 市場スキャン", 
    "🛡️ リスク管理",
    "📰 AIレポート",
    "💬 AIチャット",
    "🤖 自動化",
    "📊 高度分析",
    "📊 監視",
    "💼 ポートフォリオ", 
    "📝 ペーパートレード", 
    "📈 詳細分析", 
    "🕰️ 過去検証",
    "📊 パフォーマンス分析",
    "📤 エクスポート",
    "🔔 アラート",
    "🏆 ソーシャル",
    "💰 税務",
    "🎲 オプション",
    "🤖 AI進化"
])


# --- Tab Dashboard: Simple Dashboard ---
with tab_dashboard:
    from src.simple_dashboard import create_simple_dashboard
    create_simple_dashboard()

# --- Tab Auto: Fully Automated Trader UI ---
with tab_auto:
    from src.auto_trader_ui import create_auto_trader_ui
    create_auto_trader_ui()

# --- Tab Performance: Enhanced Performance Dashboard ---
# --- Tab Performance: Enhanced Performance Dashboard ---
with tab_perf:
    from src.enhanced_performance_dashboard import create_performance_dashboard
    
    # Determine currency based on asset class
    currency = "USD" if asset_class in ["暗号資産", "FX"] else "JPY"
    
    create_performance_dashboard(currency=currency)

# --- Tab Realtime: Real-time Monitoring ---
with tab_realtime:
    from src.ui_renderers import render_realtime_monitoring_tab
    render_realtime_monitoring_tab(ticker_group, selected_market, custom_tickers)


with tab1:
    from src.ui_renderers import render_market_scan_tab
    render_market_scan_tab(
        ticker_group=ticker_group,
        selected_market=selected_market,
        custom_tickers=custom_tickers,
        period=period,
        strategies=strategies,
        allow_short=allow_short,
        position_size=position_size,
        enable_fund_filter=enable_fund_filter,
        max_per=max_per,
        max_pbr=max_pbr,
        min_roe=min_roe,
        trading_unit=trading_unit
    )

# --- Tab Risk: Risk Management ---
with tab_risk:
    from src.ui_risk_dashboard import render_risk_dashboard
    render_risk_dashboard()

# --- Tab AI Report: AI Market Report ---
with tab_ai_report:
    from src.ui_ai_report import render_ai_report_tab
    render_ai_report_tab()

# --- Tab AI Chat: Interactive AI Chat ---
with tab_ai_chat:
    from src.ui_ai_chat import render_ai_chat
    render_ai_chat()

# --- Tab Automation: Zero-Touch Trading ---
with tab_automation:
    from src.ui_automation import render_automation_tab
    render_automation_tab()

# --- Tab Advanced Analytics ---
with tab_advanced:
    from src.ui_advanced_analytics import render_advanced_analytics_tab
    render_advanced_analytics_tab()

# --- Tab Monitoring ---
with tab_monitoring:
    from src.monitoring_dashboard import render_monitoring_dashboard
    render_monitoring_dashboard()

# --- Tab 2: Portfolio Analysis ---
with tab2:
    st.header("💼 ポートフォリオ分析")
    st.write("複数銘柄の相関分析と最適配分を計算します。")
    
    # Selection
    if ticker_group == "カスタム入力":
        available_tickers = custom_tickers
    else:
        available_tickers = NIKKEI_225_TICKERS
        
    selected_portfolio = st.multiselect("ポートフォリオに組み入れる銘柄を選択 (3つ以上推奨)", 
                                      options=available_tickers,
                                      default=available_tickers[:5] if len(available_tickers) >=5 else available_tickers,
                                      format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}")
    
    # Currency symbol
    currency_symbol = "¥" if asset_class == "日本株" else "$"
    default_capital = 10000000 if asset_class == "日本株" else 100000
    step_capital = 1000000 if asset_class == "日本株" else 10000
    
    initial_capital = st.number_input(f"初期投資額 ({currency_symbol})", value=default_capital, step=step_capital)
    
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

# --- Tab 4: Detailed Analysis (XAI) ---
with tab4:
    st.header("📈 詳細分析 & XAI (説明可能AI)")
    st.write("AIがなぜその予測をしたのか、詳細な根拠を分析します。")
    
    # Analysis Target Selection
    xai_ticker = st.selectbox(
        "分析対象銘柄を選択",
        MARKETS[selected_market],
        format_func=lambda x: f"{x} - {TICKER_NAMES.get(x, '')}",
        key="xai_ticker_select"
    )
    
    if st.button("🔍 詳細分析を実行", type="primary", key="run_xai"):
        with st.spinner(f"{xai_ticker} のデータを分析中..."):
            try:
                # 1. Fetch Data
                from src.data_loader import fetch_stock_data
                from src.features import add_advanced_features
                
                df = fetch_stock_data([xai_ticker], period="2y").get(xai_ticker)
                
                if df is not None and not df.empty:
                    # 2. Feature Engineering
                    df_feat = add_advanced_features(df)
                    
                    # 3. Model Training (Quick LightGBM for explanation)
                    # Note: Ideally we should load a pre-trained model, but for demo we train on the fly
                    from src.strategies import LightGBMStrategy
                    from src.ui_renderers import render_xai_section
                    
                    lgbm = LightGBMStrategy()
                    
                    # Prepare data for training
                    # We need to split data to train a model to explain it
                    # For XAI purpose, we want to explain the *latest* prediction
                    
                    # Train on past data
                    train_size = int(len(df_feat) * 0.8)
                    train_data = df_feat.iloc[:train_size]
                    test_data = df_feat.iloc[train_size:]
                    
                    # Train model (using internal method if available, or just use the strategy)
                    # LightGBMStrategy doesn't expose the model directly easily, 
                    # so we might need to access it or train a fresh one using lightgbm directly
                    
                    import lightgbm as lgb
                    
                    # Simple training for XAI demo
                    feature_cols = [c for c in df_feat.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Target']]
                    # Remove non-numeric
                    feature_cols = df_feat[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
                    
                    X = df_feat[feature_cols]
                    y = (df_feat['Close'].shift(-1) > df_feat['Close']).astype(int) # Binary target
                    
                    # Drop NaN
                    valid_idx = ~X.isna().any(axis=1) & ~y.isna()
                    X = X[valid_idx]
                    y = y[valid_idx]
                    
                    if len(X) > 100:
                        model = lgb.LGBMClassifier(random_state=42, n_estimators=100)
                        model.fit(X, y)
                        
                        # Get prediction probability for the latest data point
                        # We need the latest feature vector
                        latest_X = X.iloc[[-1]]
                        ai_prob = model.predict_proba(latest_X)[0][1] # Probability of class 1 (Up)
                        
                        # 3.5 Render Integrated Signal Analysis
                        from src.ui_renderers import render_integrated_signal
                        render_integrated_signal(df, xai_ticker, ai_prediction=ai_prob)
                        
                        st.markdown("---")
                        
                        # 4. Render XAI Section
                        render_xai_section(model, X, xai_ticker)
                        
                        # 5. Additional Technical Analysis
                        st.markdown("---")
                        st.subheader("📊 テクニカル指標詳細")
                        
                        # MTF Analysis
                        from src.multi_timeframe import get_mtf_analyzer
                        mtf = get_mtf_analyzer()
                        mtf_res = mtf.analyze(df)
                        
                        if mtf_res:
                            st.markdown("##### ⏳ マルチタイムフレーム分析")
                            m_col1, m_col2 = st.columns(2)
                            
                            with m_col1:
                                w_trend = mtf_res['weekly_trend']
                                w_icon = "📈" if w_trend == "UPTREND" else "📉" if w_trend == "DOWNTREND" else "➡️"
                                st.metric("週足トレンド", f"{w_icon} {w_trend}")
                                
                            with m_col2:
                                m_trend = mtf_res['monthly_trend']
                                m_icon = "📈" if m_trend == "UPTREND" else "📉" if m_trend == "DOWNTREND" else "➡️"
                                st.metric("月足トレンド", f"{m_icon} {m_trend}")
                                
                            if w_trend == "UPTREND" and m_trend == "UPTREND":
                                st.success("長期トレンドは非常に強い上昇傾向です。買いエントリーの勝率が高い状態です。")
                            elif w_trend == "DOWNTREND" and m_trend == "DOWNTREND":
                                st.error("長期トレンドは非常に強い下落傾向です。買いエントリーは危険です。")
                        
                        # Candlestick with MA
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=df_feat.index,
                            open=df_feat['Open'],
                            high=df_feat['High'],
                            low=df_feat['Low'],
                            close=df_feat['Close'],
                            name='Price'
                        ))
                        
                        if 'SMA_20' in df_feat.columns:
                            fig.add_trace(go.Scatter(x=df_feat.index, y=df_feat['SMA_20'], name='SMA 20', line=dict(color='orange')))
                        if 'SMA_50' in df_feat.columns:
                            fig.add_trace(go.Scatter(x=df_feat.index, y=df_feat['SMA_50'], name='SMA 50', line=dict(color='blue')))
                            
                        fig.update_layout(title=f"{xai_ticker} Price Chart", xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 6. AI Trade Reasoning (Phase 31-3)
                        st.markdown("---")
                        st.subheader("🤖 AIトレード理由解説")
                        
                        from src.trade_explainer import TradeExplainer
                        from src.regime_detector import MarketRegimeDetector
                        
                        explainer = TradeExplainer()
                        regime_detector = MarketRegimeDetector()
                        
                        if explainer.analyst.enabled:
                            # Get current regime
                            regime = regime_detector.detect_regime(df)
                            
                            # Get latest technical indicators
                            latest_indicators = {}
                            if 'RSI' in df_feat.columns:
                                latest_indicators['RSI'] = df_feat['RSI'].iloc[-1]
                            if 'MACD' in df_feat.columns:
                                latest_indicators['MACD'] = df_feat['MACD'].iloc[-1]
                            if 'SMA_20' in df_feat.columns:
                                latest_indicators['SMA_20'] = df_feat['SMA_20'].iloc[-1]
                            if 'SMA_50' in df_feat.columns:
                                latest_indicators['SMA_50'] = df_feat['SMA_50'].iloc[-1]
                            
                            # Determine hypothetical action based on signal
                            latest_signal = signals.iloc[-1] if not signals.empty else 0
                            action = "BUY" if latest_signal == 1 else "SELL" if latest_signal == -1 else "HOLD"
                            
                            if action != "HOLD":
                                with st.spinner("AIがトレード理由を分析中..."):
                                    explanation = explainer.explain_trade(
                                        ticker=xai_ticker,
                                        action=action,
                                        price=df['Close'].iloc[-1],
                                        technical_indicators=latest_indicators,
                                        market_regime=regime,
                                        strategy_name="LightGBM"
                                    )
                                    st.markdown(explanation)
                            else:
                                st.info("🚦 現在は明確な売買シグナルがありません。様子見モードです。")
                        else:
                            st.warning("⚠️ AIアナリストが無効です。`config.json`でOpenAI APIキーを設定してください。")
                        
                    else:
                        st.error("データ不足のためモデルを学習できませんでした。")
                else:
                    st.error("データの取得に失敗しました。")
                    
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")
                import traceback
                st.text(traceback.format_exc())
    
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
        pm_agent = PortfolioManagerAgent()
        
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
        st.metric("判断スコア (Decision Score)", f"{decision['score']:.2f}")
        
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
st.header("🎛️ ブローカー制御パネル (Broker Control Panel)")

# Load config
import json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except:
    config = {"broker": {"default_mode": "paper"}, "risk_guard": {"enabled": True}}

col_broker1, col_broker2 = st.columns([2, 1])

with col_broker1:
    st.subheader("ブローカー選択")
    broker_mode = st.radio(
        "ブローカーモードを選択",
        ["Paper (シミュレーター)", "IBKR Paper (デモ)", "IBKR Live (本番)"],
        index=0 if config.get("broker", {}).get("default_mode") == "paper" else 1,
        help="⚠️ IBKR Live は実際の資金を使用します。Paper Tradingで十分に検証した後でのみ有効にしてください。"
    )
    
    if broker_mode.startswith("IBKR"):
        st.warning("⚠️ IBKRモードを使用するには、TWSまたはIB Gatewayが起動しており、`ib_insync` がインストールされている必要があります。")
        st.caption(f"Host: {config.get('broker', {}).get('ibkr', {}).get('host', '127.0.0.1')}")
        
        port = config.get('broker', {}).get('ibkr', {}).get('paper_port' if 'Paper' in broker_mode else 'live_port', 7497)
        st.caption(f"Port: {port}")
        
        # Connection status (placeholder - would need actual connection check)
        connection_status = st.empty()
        connection_status.info("🔴 未接続")

with col_broker2:
    st.subheader("安全制御")
    
    # Emergency Stop Button
    if st.button("🚨 緊急停止 (EMERGENCY STOP)", type="primary", help="すべての取引を直ちに停止します"):
        st.session_state.emergency_stop = True
        st.error("⛔ 緊急停止が作動しました")
        st.balloons()  # Alert sound
    
    # Status display
    if st.session_state.get("emergency_stop", False):
        st.error("⛔ 取引停止中")
        if st.button("緊急停止を解除"):
            st.session_state.emergency_stop = False
            st.success("✅ 緊急停止を解除しました")
    else:
        st.success("✅ 取引有効")

st.markdown("---")

# RiskGuard Dashboard
st.subheader("🛡️ リスクガード状態 (Risk Guard Status)")

risk_config = config.get("risk_guard", {})
col_risk1, col_risk2, col_risk3 = st.columns(3)

with col_risk1:
    st.metric("日次損失限度", f"{risk_config.get('daily_loss_limit_pct', -5.0)}%")
with col_risk2:
    st.metric("最大ポジションサイズ", f"{risk_config.get('max_position_size_pct', 10.0)}%")
with col_risk3:
    st.metric("最大VIX指数", risk_config.get('max_vix', 40.0))

# Daily P&L Progress (placeholder - would show actual data)
st.caption("日次損益モニター")
pnl_pct = 0.0  # Placeholder
st.progress(max(0, min(1, (pnl_pct + 10) / 20)), text=f"損益率: {pnl_pct:+.2f}%")

if abs(pnl_pct) >= abs(risk_config.get('daily_loss_limit_pct', -5.0)):
    st.error(f"⚠️ 日次損失限度に達しました: {pnl_pct:.2f}%")
#   A d d   t h i s   t o   t h e   e n d   o f   a p p . p y 
 
 
 
 #   - - -   T a b   E x p o r t :   E x p o r t   M a n a g e r   - - - 
 
 w i t h   t a b _ e x p o r t : 
 
         f r o m   s r c . u i _ e x p o r t   i m p o r t   r e n d e r _ e x p o r t _ t a b 
 
         r e n d e r _ e x p o r t _ t a b ( ) 
 
 
 
 #   - - -   T a b   A l e r t s :   A l e r t   M a n a g e m e n t   - - - 
 
 w i t h   t a b _ a l e r t s : 
 
         f r o m   s r c . u i _ a l e r t s   i m p o r t   r e n d e r _ a l e r t s _ t a b 
 
         r e n d e r _ a l e r t s _ t a b ( ) 
 
 
 
 #   - - -   T a b   S o c i a l :   S o c i a l   T r a d i n g   - - - 
 
 w i t h   t a b _ s o c i a l : 
 
         s t . h e a d e r ( " ^��  g~}�]~|�g~w�]~c�]~k�]~;S�]~|�]~�0E0]~s�g~p�" ) 
 
         
 
         s o c i a l _ t a b 1 ,   s o c i a l _ t a b 2 ,   s o c i a l _ t a b 3   =   s t . t a b s ( [ " ]~j�]~|�]~� ]~|�]~�a�0]~�0,   " g~s�]~�e�0]~;S�]~|�]~�0,   " �f�!�e�]~�i�0g~q�]~�0�0" ] ) 
 
         
 
         w i t h   s o c i a l _ t a b 1 : 
 
                 s t . s u b h e a d e r ( " ^�b  ]~;S�0]~�R�0]~l�]~|�]~� ]~|�" ) 
 
                 
 
                 f r o m   s r c . t r a d e r _ p r o f i l e   i m p o r t   T r a d e r P r o f i l e M a n a g e r 
 
                 m a n a g e r   =   T r a d e r P r o f i l e M a n a g e r ( ) 
 
                 
 
                 #   ]~j�]~|�]~� ]~|�]~�a�0]~Yr�S��0
 
                 l e a d e r b o a r d   =   m a n a g e r . g e t _ l e a d e r b o a r d ( m e t r i c = ' t o t a l _ r e t u r n ' ,   l i m i t = 2 0 ) 
 
                 
 
                 i f   n o t   l e a d e r b o a r d . e m p t y : 
 
                         s t . d a t a f r a m e ( 
 
                                 l e a d e r b o a r d , 
 
                                 c o l u m n _ c o n f i g = { 
 
                                         " t o t a l _ r e t u r n " :   s t . c o l u m n _ c o n f i g . N u m b e r C o l u m n ( " ]~j�g~�]~|�]~s�  ( % ) " ,   f o r m a t = " % . 2 f % % " ) , 
 
                                         " s h a r p e _ r a t i o " :   s t . c o l u m n _ c o n f i g . N u m b e r C o l u m n ( " g~w�]~c�]~|�]~�R�g~w�g~j�" ,   f o r m a t = " % . 2 f " ) , 
 
                                         " m a x _ d r a w d o w n " :   s t . c o l u m n _ c o n f i g . N u m b e r C o l u m n ( " [�� ��g�]~�\�]~|�]~� g~f�]~s�  ( % ) " ,   f o r m a t = " % . 2 f % % " ) , 
 
                                         " w i n _ r a t e " :   s t . c o l u m n _ c o n f i g . N u m b e r C o l u m n ( " 
�If+}  ( % ) " ,   f o r m a t = " % . 2 f % % " ) , 
 
                                         " f o l l o w e r _ c o u n t " :   s t . c o l u m n _ c o n f i g . N u m b e r C o l u m n ( " ]~�K0]~m�]~o�]~|�(�p�" ) 
 
                                 } , 
 
                                 u s e _ c o n t a i n e r _ w i d t h = T r u e 
 
                         ) 
 
                 e l s e : 
 
                         s t . i n f o ( " ]~;S�]~|�]~� ]~|�]~�0�0g~�:~�_`"g~�*":~^S�2~�0) 
 
         
 
         w i t h   s o c i a l _ t a b 2 : 
 
                 s t . s u b h e a d e r ( " ^�-d  g~s�]~�e�0]~;S�]~|�]~��h�m����0) 
 
                 
 
                 f r o m   s r c . c o p y _ t r a d i n g   i m p o r t   C o p y T r a d i n g E n g i n e 
 
                 e n g i n e   =   C o p y T r a d i n g E n g i n e ( ) 
 
                 
 
                 s t . w r i t e ( " * * g~s�]~�e�0��m����0* " ) 
 
                 
 
                 c o l 1 ,   c o l 2   =   s t . c o l u m n s ( 2 ) 
 
                 
 
                 w i t h   c o l 1 : 
 
                         c o p y _ p e r c e n t a g e   =   s t . s l i d e r ( " g~s�]~�e�0H��v+}  ( % ) " ,   1 ,   1 0 0 ,   1 0 ) 
 
                         m a x _ p e r _ t r a d e   =   s t . n u m b e r _ i n p u t ( " 1 ?���|��`":~�nJ�:~n�s�O^R  ( ��e�) " ,   v a l u e = 5 0 0 0 0 ,   s t e p = 1 0 0 0 0 ) 
 
                 
 
                 w i t h   c o l 2 : 
 
                         m a x _ t o t a l   =   s t . n u m b e r _ i n p u t ( " ��WN\Qɖ�0a�:Xx�O^R  ( ��e�) " ,   v a l u e = 1 0 0 0 0 0 ,   s t e p = 1 0 0 0 0 ) 
 
                         m i n _ c o n f i d e n c e   =   s t . s l i d e r ( " [�� ƇN�a��|��f�" ,   0 . 0 ,   1 . 0 ,   0 . 5 ,   0 . 1 ) 
 
                 
 
                 i f   s t . b u t t o n ( " ��m����XR��Ofm��0,   t y p e = " p r i m a r y " ) : 
 
                         s t . s u c c e s s ( " g~s�]~�e�0��m����XR��Ofm�%P �:~~�:~�R�%" ) 
 
         
 
         w i t h   s o c i a l _ t a b 3 : 
 
                 s t . s u b h e a d e r ( " ^�[  �f�!�e�]~�i�0g~q�]~�0�0]~�R�g~d�g~y�" ) 
 
                 
 
                 f r o m   s r c . s t r a t e g y _ m a r k e t p l a c e   i m p o r t   S t r a t e g y M a r k e t p l a c e 
 
                 m a r k e t p l a c e   =   S t r a t e g y M a r k e t p l a c e ( ) 
 
                 
 
                 #   ���at�b�
 
                 s e a r c h _ q u e r y   =   s t . t e x t _ i n p u t ( " �f�!�e�g~HTd��at�b�" ,   p l a c e h o l d e r = " ��0  S M A ,   R S I ,   M A C D " ) 
 
                 c a t e g o r y   =   s t . s e l e c t b o x ( " g~k�]~�0V0]~j�" ,   [ " :~6T":~f�" ,   " t e c h n i c a l " ,   " f u n d a m e n t a l " ,   " m l " ,   " h y b r i d " ] ) 
 
                 
 
                 #   �f�!�e�s�� ��g�
 
                 s t r a t e g i e s   =   m a r k e t p l a c e . s e a r c h _ s t r a t e g i e s ( 
 
                         q u e r y = s e a r c h _ q u e r y   i f   s e a r c h _ q u e r y   e l s e   N o n e , 
 
                         c a t e g o r y = c a t e g o r y   i f   c a t e g o r y   ! =   " :~6T":~f�"   e l s e   N o n e , 
 
                         l i m i t = 2 0 
 
                 ) 
 
                 
 
                 i f   n o t   s t r a t e g i e s . e m p t y : 
 
                         f o r   _ ,   s t r a t e g y   i n   s t r a t e g i e s . i t e r r o w s ( ) : 
 
                                 w i t h   s t . e x p a n d e r ( f " �{�0{ s t r a t e g y [ ' n a m e ' ] }   -   { s t r a t e g y [ ' a u t h o r ' ] } " ) : 
 
                                         s t . w r i t e ( f " * * ��l�O��0* :   { s t r a t e g y [ ' d e s c r i p t i o n ' ] } " ) 
 
                                         s t . w r i t e ( f " * * g~k�]~�0V0]~j�* * :   { s t r a t e g y [ ' c a t e g o r y ' ] } " ) 
 
                                         s t . w r i t e ( f " * * �a�l�|�* * :   ��e�{ s t r a t e g y [ ' p r i c e ' ] : , . 0 f } " ) 
 
                                         s t . w r i t e ( f " * * ��Bz~�a�* * :   { ' �{�0  *   i n t ( s t r a t e g y [ ' r a t i n g ' ] ) }   ( { s t r a t e g y [ ' r a t i n g ' ] : . 1 f } ) " ) 
 
                                         s t . w r i t e ( f " * * ]~� g~f�]~s�]~m�]~|�]~;uq* * :   { s t r a t e g y [ ' d o w n l o a d s ' ] } " ) 
 
                                         
 
                                         i f   s t . b u t t o n ( f " ]~� g~f�]~s�]~m�]~|�]~�0,   k e y = f " d l _ { s t r a t e g y [ ' i d ' ] } " ) : 
 
                                                 s t . s u c c e s s ( " �f�!�e�g~uP�0g~f�]~s�]~m�]~|�]~�\ �:~~�:~�R�%" ) 
 
                 e l s e : 
 
                         s t . i n f o ( " �f�!�e�:~Ztf�]N�%:~]NJ�:~~�:~^S�:~g�:~�R�%2~�0) 
 
 
 
 #   - - -   T a b   T a x :   T a x   O p t i m i z a t i o n   - - - 
 
 w i t h   t a b _ t a x : 
 
         s t . h e a d e r ( " ^�x�  ^�;No[�� U�i����0) 
 
         
 
         t a x _ t a b 1 ,   t a x _ t a b 2 ,   t a x _ t a b 3   =   s t . t a b s ( [ " ^�1ga"����n��0,   " N I S A ��a���0,   " R�z���YO{;��0] ) 
 
         
 
         w i t h   t a x _ t a b 1 : 
 
                 s t . s u b h e a d e r ( " ^��  ^�1ga"g~w�]~�n�]~l�]~|�g~w�]~g�]~s�" ) 
 
                 
 
                 f r o m   s r c . t a x _ c a l c u l a t o r   i m p o r t   T a x C a l c u l a t o r 
 
                 c a l c   =   T a x C a l c u l a t o r ( ) 
 
                 
 
                 p r o f i t   =   s t . n u m b e r _ i n p u t ( " ��i�6��0( ��e�) " ,   v a l u e = 1 0 0 0 0 0 0 ,   s t e p = 1 0 0 0 0 0 ) 
 
                 i s _ n i s a   =   s t . c h e c k b o x ( " N I S A ?�c��g�" ,   v a l u e = F a l s e ) 
 
                 
 
                 t a x _ i n f o   =   c a l c . c a l c u l a t e _ c a p i t a l _ g a i n s _ t a x ( p r o f i t ,   i s _ n i s a ) 
 
                 
 
                 c o l 1 ,   c o l 2 ,   c o l 3   =   s t . c o l u m n s ( 3 ) 
 
                 
 
                 w i t h   c o l 1 : 
 
                         s t . m e t r i c ( " ��i�6��0,   f " ��e�{ t a x _ i n f o [ ' p r o f i t ' ] : , . 0 f } " ) 
 
                 w i t h   c o l 2 : 
 
                         s t . m e t r i c ( " ^�1ga"" ,   f " ��e�{ t a x _ i n f o [ ' t o t a l _ t a x ' ] : , . 0 f } " ) 
 
                 w i t h   c o l 3 : 
 
                         s t . m e t r i c ( " ^�;N|��R~��0,   f " ��e�{ t a x _ i n f o [ ' n e t _ p r o f i t ' ] : , . 0 f } " ) 
 
                 
 
                 s t . w r i t e ( f " * * ���n�g^��[+}* * :   { t a x _ i n f o [ ' e f f e c t i v e _ t a x _ r a t e ' ] : . 2 % } " ) 
 
                 
 
                 #   3��id�q�?��[i�k�
 
                 s t . d i v i d e r ( ) 
 
                 s t . s u b h e a d e r ( " ^�`  3��id�q�?��[i�k�[�� U�i����0) 
 
                 
 
                 f r o m   s r c . p a p e r _ t r a d e r   i m p o r t   P a p e r T r a d e r 
 
                 p t   =   P a p e r T r a d e r ( ) 
 
                 p o s i t i o n s   =   p t . g e t _ p o s i t i o n s ( ) 
 
                 
 
                 i f   n o t   p o s i t i o n s . e m p t y : 
 
                         h a r v e s t   =   c a l c . o p t i m i z e _ l o s s _ h a r v e s t i n g ( p o s i t i o n s ) 
 
                         
 
                         i f   h a r v e s t : 
 
                                 s t . w r i t e ( f " * * �h���h���r�
�t�* * :   { l e n ( h a r v e s t ) } ��v�" ) 
 
                                 
 
                                 f o r   r e c   i n   h a r v e s t : 
 
                                         s t . w r i t e ( f " -   { r e c [ ' t i c k e r ' ] } :   3��id�q���e�{ r e c [ ' u n r e a l i z e d _ l o s s ' ] : , . 0 f } ,   }�� ^��{e�{ r e c [ ' t a x _ b e n e f i t ' ] : , . 0 f } " ) 
 
                         e l s e : 
 
                                 s t . i n f o ( " 3��id�q�?��[i�k�:~n��h���h�:~o�:~�0J�:~~�:~^S�2~�0) 
 
                 e l s e : 
 
                         s t . i n f o ( " ]~4fZ0g~w�]~g�]~s�:~�_`"g~�*":~^S�2~�0) 
 
         
 
         w i t h   t a x _ t a b 2 : 
 
                 s t . s u b h e a d e r ( " ^�X�  N I S A k�����a���0) 
 
                 
 
                 f r o m   s r c . n i s a _ m a n a g e r   i m p o r t   N I S A M a n a g e r ,   N I S A T y p e 
 
                 n i s a _ m g r   =   N I S A M a n a g e r ( ) 
 
                 
 
                 r e m a i n i n g   =   n i s a _ m g r . g e t _ r e m a i n i n g _ l i m i t ( 1 ,   N I S A T y p e . N E W _ N I S A ) 
 
                 
 
                 c o l 1 ,   c o l 2   =   s t . c o l u m n s ( 2 ) 
 
                 
 
                 w i t h   c o l 1 : 
 
                         s t . m e t r i c ( " ��t���x�O^R" ,   f " ��e�{ r e m a i n i n g [ ' t o t a l _ l i m i t ' ] : , . 0 f } " ) 
 
                         s t . m e t r i c ( " ���h���;S)"" ,   f " ��e�{ r e m a i n i n g [ ' t o t a l _ u s e d ' ] : , . 0 f } " ) 
 
                 
 
                 w i t h   c o l 2 : 
 
                         s t . m e t r i c ( " ?�]NJ�k���" ,   f " ��e�{ r e m a i n i n g [ ' t o t a l _ r e m a i n i n g ' ] : , . 0 f } " ) 
 
                         
 
                         p r o g r e s s   =   r e m a i n i n g [ ' t o t a l _ u s e d ' ]   /   r e m a i n i n g [ ' t o t a l _ l i m i t ' ]   i f   r e m a i n i n g [ ' t o t a l _ l i m i t ' ]   >   0   e l s e   0 
 
                         s t . p r o g r e s s ( p r o g r e s s ) 
 
         
 
         w i t h   t a x _ t a b 3 : 
 
                 s t . s u b h e a d e r ( " ^�XX  R�z���YO{;���]��n�0" ) 
 
                 
 
                 f r o m   s r c . t a x _ r e p o r t _ g e n e r a t o r   i m p o r t   T a x R e p o r t G e n e r a t o r 
 
                 g e n e r a t o r   =   T a x R e p o r t G e n e r a t o r ( ) 
 
                 
 
                 y e a r   =   s t . n u m b e r _ i n p u t ( " ��t��f�" ,   v a l u e = 2 0 2 5 ,   s t e p = 1 ) 
 
                 
 
                 i f   s t . b u t t o n ( " ��t��Xp��q�;���]g~$X�Q��0,   t y p e = " p r i m a r y " ) : 
 
                         f r o m   s r c . p a p e r _ t r a d e r   i m p o r t   P a p e r T r a d e r 
 
                         p t   =   P a p e r T r a d e r ( ) 
 
                         
 
                         t r a d e s   =   p t . g e t _ t r a d e _ h i s t o r y ( ) 
 
                         u s e r _ i n f o   =   { 
 
                                 ' n a m e ' :   ' ��q��p���j�[��0, 
 
                                 ' a d d r e s s ' :   ' Z�q���l�[�}�' , 
 
                                 ' b i r t h _ d a t e ' :   ' 1 9 9 0 / 0 1 / 0 1 ' 
 
                         } 
 
                         
 
                         p d f   =   g e n e r a t o r . g e n e r a t e _ a n n u a l _ r e p o r t ( y e a r ,   t r a d e s ,   u s e r _ i n f o ) 
 
                         
 
                         s t . d o w n l o a d _ b u t t o n ( 
 
                                 l a b e l = " ^��  P D F g~uP�0g~f�]~s�]~m�]~|�]~�0, 
 
                                 d a t a = p d f , 
 
                                 f i l e _ n a m e = f " a n n u a l _ r e p o r t _ { y e a r } . p d f " , 
 
                                 m i m e = " a p p l i c a t i o n / p d f " 
 
                         ) 
 
 
 
 #   - - -   T a b   O p t i o n s :   O p t i o n s   P r i c i n g   - - - 
 
 w i t h   t a b _ o p t i o n s : 
 
         s t . h e a d e r ( " ^���  g~j�]~�RY0]~g�]~s�?���|��0) 
 
         
 
         o p t _ t a b 1 ,   o p t _ t a b 2   =   s t . t a b s ( [ " �a�l�|�����n��0,   " �f�!�e�" ] ) 
 
         
 
         w i t h   o p t _ t a b 1 : 
 
                 s t . s u b h e a d e r ( " ^�b  B l a c k - S c h o l e s ����n��0) 
 
                 
 
                 f r o m   s r c . o p t i o n s _ p r i c i n g   i m p o r t   O p t i o n s C a l c u l a t o r 
 
                 c a l c   =   O p t i o n s C a l c u l a t o r ( ) 
 
                 
 
                 c o l 1 ,   c o l 2   =   s t . c o l u m n s ( 2 ) 
 
                 
 
                 w i t h   c o l 1 : 
 
                         S   =   s t . n u m b e r _ i n p u t ( " �~�h�h��a�l�|�  ( ��e�) " ,   v a l u e = 1 5 0 0 . 0 ,   s t e p = 1 0 . 0 ) 
 
                         K   =   s t . n u m b e r _ i n p u t ( " f��_}���a�l�|�  ( ��e�) " ,   v a l u e = 1 5 5 0 . 0 ,   s t e p = 1 0 . 0 ) 
 
                         T   =   s t . n u m b e r _ i n p u t ( " ��� [��n*":~g�:~n�L�e�(�p�" ,   v a l u e = 3 0 ,   s t e p = 1 )   /   3 6 5 
 
                 
 
                 w i t h   c o l 2 : 
 
                         r   =   s t . n u m b e r _ i n p u t ( " ]~j�g~y�g~o�]~��]~|�]~l�]~|�]~�0( % ) " ,   v a l u e = 1 . 0 ,   s t e p = 0 . 1 )   /   1 0 0 
 
                         s i g m a   =   s t . n u m b e r _ i n p u t ( " ]~�a�]~�0E0]~j�]~�0E0  ( % ) " ,   v a l u e = 2 5 . 0 ,   s t e p = 1 . 0 )   /   1 0 0 
 
                         o p t i o n _ t y p e   =   s t . s e l e c t b o x ( " g~j�]~�RY0]~g�]~s�g~�g~d�]~�0,   [ " c a l l " ,   " p u t " ] ) 
 
                 
 
                 i f   s t . b u t t o n ( " ����n��0,   t y p e = " p r i m a r y " ) : 
 
                         p r i c e   =   c a l c . b l a c k _ s c h o l e s ( S ,   K ,   T ,   r ,   s i g m a ,   o p t i o n _ t y p e ) 
 
                         g r e e k s   =   c a l c . c a l c u l a t e _ g r e e k s ( S ,   K ,   T ,   r ,   s i g m a ,   o p t i o n _ t y p e ) 
 
                         
 
                         s t . s u c c e s s ( f " * * g~j�]~�RY0]~g�]~s��a�l�|�* * :   ��e�{ p r i c e : . 2 f } " ) 
 
                         
 
                         s t . w r i t e ( " * * G r e e k s : * * " ) 
 
                         c o l _ g 1 ,   c o l _ g 2 ,   c o l _ g 3 ,   c o l _ g 4 ,   c o l _ g 5   =   s t . c o l u m n s ( 5 ) 
 
                         
 
                         w i t h   c o l _ g 1 : 
 
                                 s t . m e t r i c ( " D e l t a " ,   f " { g r e e k s [ ' d e l t a ' ] : . 4 f } " ) 
 
                         w i t h   c o l _ g 2 : 
 
                                 s t . m e t r i c ( " G a m m a " ,   f " { g r e e k s [ ' g a m m a ' ] : . 4 f } " ) 
 
                         w i t h   c o l _ g 3 : 
 
                                 s t . m e t r i c ( " T h e t a " ,   f " { g r e e k s [ ' t h e t a ' ] : . 4 f } " ) 
 
                         w i t h   c o l _ g 4 : 
 
                                 s t . m e t r i c ( " V e g a " ,   f " { g r e e k s [ ' v e g a ' ] : . 4 f } " ) 
 
                         w i t h   c o l _ g 5 : 
 
                                 s t . m e t r i c ( " R h o " ,   f " { g r e e k s [ ' r h o ' ] : . 4 f } " ) 
 
         
 
         w i t h   o p t _ t a b 2 : 
 
                 s t . s u b h e a d e r ( " ^�]  g~j�]~�RY0]~g�]~s��f�!�e�" ) 
 
                 
 
                 f r o m   s r c . o p t i o n s _ p r i c i n g   i m p o r t   O p t i o n S t r a t e g y 
 
                 
 
                 s t r a t e g y _ t y p e   =   s t . s e l e c t b o x ( 
 
                         " �f�!�e�" , 
 
                         [ " g~k�]~��0]~�\U0]~|�]~k�" ,   " ]~�R�]~�0Q0]~�0E0]~�`�0]~�0�0" ,   " g~y�]~;S�]~�\�" ] 
 
                 ) 
 
                 
 
                 i f   s t r a t e g y _ t y p e   = =   " g~k�]~��0]~�\U0]~|�]~k�" : 
 
                         s t o c k _ p r i c e   =   s t . n u m b e r _ i n p u t ( " l�j��a�" ,   v a l u e = 1 5 0 0 . 0 ) 
 
                         s t o c k _ q u a n t i t y   =   s t . n u m b e r _ i n p u t ( " �Df`l�j�(�p�" ,   v a l u e = 1 0 0 ) 
 
                         c a l l _ s t r i k e   =   s t . n u m b e r _ i n p u t ( " g~s�]~|�]~k�f��_}���a�l�|�" ,   v a l u e = 1 5 5 0 . 0 ) 
 
                         c a l l _ p r e m i u m   =   s t . n u m b e r _ i n p u t ( " g~s�]~|�]~k�]~�R�]~�nD0]~��" ,   v a l u e = 3 0 . 0 ) 
 
                         
 
                         i f   s t . b u t t o n ( " ���0�h" ) : 
 
                                 r e s u l t   =   O p t i o n S t r a t e g y . c o v e r e d _ c a l l ( 
 
                                         s t o c k _ p r i c e ,   s t o c k _ q u a n t i t y ,   c a l l _ s t r i k e ,   c a l l _ p r e m i u m 
 
                                 ) 
 
                                 
 
                                 s t . w r i t e ( f " * * { r e s u l t [ ' s t r a t e g y ' ] } * * " ) 
 
                                 s t . w r i t e ( f " [�� ��g���i�6��0  ��e�{ r e s u l t [ ' m a x _ p r o f i t ' ] : , . 0 f } " ) 
 
                                 s t . w r i t e ( f " [�� ��g�3��id�q�:   ��e�{ r e s u l t [ ' m a x _ l o s s ' ] : , . 0 f } " ) 
 
                                 s t . w r i t e ( f " 3��T�[���0r�CS[0:   ��e�{ r e s u l t [ ' b r e a k e v e n ' ] : , . 0 f } " ) 
 
                                 s t . i n f o ( r e s u l t [ ' d e s c r i p t i o n ' ] ) 
 
 
 
 #   - - -   T a b   M e t a :   M e t a   L e a r n i n g   - - - 
 
 w i t h   t a b _ m e t a : 
 
         s t . h e a d e r ( " ^�d��0A I ��j���q�>�r����0) 
 
         
 
         s t . s u b h e a d e r ( " ^�n  ]~a�g~�ćf��uPJ0]~s�g~x�]~s�" ) 
 
         
 
         f r o m   s r c . m e t a _ l e a r n e r   i m p o r t   M e t a L e a r n e r 
 
         
 
         s t . w r i t e ( " * * A u t o M L   -   ��j�
���]~�0�[�� U�i����0* " ) 
 
         
 
         t i c k e r   =   s t . t e x t _ i n p u t ( " k��Olg~s�]~|�]~�0,   v a l u e = " 7 2 0 3 . T " ) 
 
         n _ t r i a l s   =   s t . s l i d e r ( " [�� U�i����Qi�f�f��`S\(�p�" ,   1 0 ,   1 0 0 ,   2 0 ) 
 
         
 
         i f   s t . b u t t o n ( " �f�!�e�g~�[�0
�Ua1S���0,   t y p e = " p r i m a r y " ) : 
 
                 w i t h   s t . s p i n n e r ( " [�� U�i���}x�m�. . . " ) : 
 
                         f r o m   s r c . d a t a _ l o a d e r   i m p o r t   f e t c h _ s t o c k _ d a t a 
 
                         
 
                         d a t a _ m a p   =   f e t c h _ s t o c k _ d a t a ( [ t i c k e r ] ,   p e r i o d = " 2 y " ) 
 
                         d a t a   =   d a t a _ m a p . g e t ( t i c k e r ) 
 
                         
 
                         i f   d a t a   i s   n o t   N o n e   a n d   n o t   d a t a . e m p t y : 
 
                                 l e a r n e r   =   M e t a L e a r n e r ( n _ t r i a l s = n _ t r i a l s ) 
 
                                 s t r a t e g i e s   =   l e a r n e r . d i s c o v e r _ s t r a t e g i e s ( d a t a ,   m i n _ s h a r p e = 0 . 5 ) 
 
                                 
 
                                 i f   s t r a t e g i e s : 
 
                                         s t . s u c c e s s ( f " ({�0{ l e n ( s t r a t e g i e s ) } ߆]N�0�f�!�e�g~$X1S��]N �:~~�:~�R�%�0�0) 
 
                                         
 
                                         f o r   s t r a t e g y   i n   s t r a t e g i e s : 
 
                                                 w i t h   s t . e x p a n d e r ( f " �{�0{ s t r a t e g y [ ' n a m e ' ] } " ) : 
 
                                                         c o l 1 ,   c o l 2 ,   c o l 3   =   s t . c o l u m n s ( 3 ) 
 
                                                         
 
                                                         w i t h   c o l 1 : 
 
                                                                 s t . m e t r i c ( " g~w�]~c�]~|�]~�R�g~w�g~j�" ,   f " { s t r a t e g y [ ' s h a r p e _ r a t i o ' ] : . 2 f } " ) 
 
                                                         w i t h   c o l 2 : 
 
                                                                 s t . m e t r i c ( " ��o�h�*��g~�]~|�]~s�" ,   f " { s t r a t e g y [ ' c u m u l a t i v e _ r e t u r n ' ] : . 2 % } " ) 
 
                                                         w i t h   c o l 3 : 
 
                                                                 s t . m e t r i c ( " ��~��f�" ,   f " { s t r a t e g y [ ' a c c u r a c y ' ] : . 2 % } " ) 
 
                                                         
 
                                                         s t . w r i t e ( f " * * ]~�N�]~a�]~|�g~�* * :   { s t r a t e g y [ ' p a r a m s ' ] } " ) 
 
                                 e l s e : 
 
                                         s t . w a r n i n g ( " [�Yr�g:~j��f�!�e�:~Ztf�]N�%:~]NJ�:~~�:~^S�:~g�:~�R�%2~�0) 
 
                         e l s e : 
 
                                 s t . e r r o r ( " ]~�0�0g~�:~n�?���~��R�!��q�(��R �:~~�:~�R�%2~�0) 
 
 
 
 s t . s i d e b a r . d i v i d e r ( ) 
 
 s t . s i d e b a r . c a p t i o n ( " A G S t o c k   v 3 . 0   -   P h a s e   0 - 4 0   C o m p l e t e " ) 
 
 


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
