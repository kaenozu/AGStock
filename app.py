import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES, MARKETS
from src.data_loader import fetch_stock_data, get_latest_price, fetch_news
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy, MLStrategy, LightGBMStrategy, DeepLearningStrategy, EnsembleStrategy, load_custom_strategies
from src.backtester import Backtester
from src.portfolio import PortfolioManager
from src.paper_trader import PaperTrader
from src.agents import TechnicalAnalyst, FundamentalAnalyst, MacroStrategist, RiskManager
from src.cache_config import install_cache

# Design System Imports
from src.formatters import (
    format_currency, format_percentage,
    get_risk_level
)
from src.ui_components import (
    display_sentiment_gauge,
    display_stock_card, display_best_pick_card, display_error_message
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
tab_home, tab1, tab2, tab3, tab4, tab5, tab_perf = st.tabs([
    "🏠 ホーム", 
    "📊 市場スキャン", 
    "💼 ポートフォリオ", 
    "📝 ペーパートレード", 
    "📈 ダッシュボード", 
    "🕰️ 過去検証",
    "📊 パフォーマンス分析"  # NEW
])

# --- Tab Home: Simple Dashboard ---
with tab_home:
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
                    display_df['Last Price'] = display_df['Last Price'].apply(lambda x: format_currency(x))
                    
                    # Add growth metrics if available
                    if 'DividendCAGR' in display_df.columns:
                        display_df['成長率 (CAGR)'] = display_df['DividendCAGR'].apply(lambda x: f"{x:.1f}%")
                        display_df['連続増配'] = display_df['ConsecutiveIncreases'].apply(lambda x: f"{x}年" if x > 0 else "-")
                        st.dataframe(display_df[['Name', 'Ticker', 'Yield', 'PayoutRatio', '成長率 (CAGR)', '連続増配', 'Last Price']], use_container_width=True)
                    else:
                        st.dataframe(display_df[['Name', 'Ticker', 'Yield', 'PayoutRatio', 'Last Price']], use_container_width=True)
                    
                    # Show dividend history charts for selected stocks
                    if 'DividendHistory' in hd_df.columns:
                        st.markdown("#### 📈 配当履歴トレンド")
                        # Show top 5 by CAGR
                        top_growers = hd_df.nlargest(min(5, len(hd_df)), 'DividendCAGR') if 'DividendCAGR' in hd_df.columns else hd_df.head(5)
                        
                        for idx, stock in top_growers.iterrows():
                            if stock['DividendHistory'] and len(stock['DividendHistory']) > 0:
                                st.markdown(f"**{stock['Name']} ({stock['Ticker']})** - 増配率: {stock.get('DividendCAGR', 0):.1f}%")
                                history_df = pd.DataFrame(stock['DividendHistory'])
                                history_df = history_df.set_index('year')
                                st.line_chart(history_df['dividend'], use_container_width=True)
                                st.divider()
                    
                    # Accumulate Button
                    if st.button(f"🌱 全銘柄を {trading_unit}株ずつ 積立注文", key="accumulate_btn", type="primary"):
                        pt = PaperTrader()
                        success_count = 0
                        for item in cached_results['high_dividend']:
                            # Order trading_unit shares
                            if pt.execute_trade(item['Ticker'], "BUY", trading_unit, item['Last Price'], reason="High Dividend Accumulation"):
                                success_count += 1
                        
                        if success_count > 0:
                            st.balloons()
                            st.success(f"✅ {success_count}銘柄を {trading_unit}株ずつ 積立注文しました！")

            # 2. Recommended Signals (Cards)
            st.markdown("---")
            st.subheader(f"✨ その他の注目銘柄 ({len(actionable_df) - 1}件)")
            
            if len(actionable_df) > 1:
                for idx, row in actionable_df.iloc[1:].iterrows():
                    # リスクレベル判定
                    risk_level = get_risk_level(row.get('Max Drawdown', -0.15))
                    
                    # 追加情報
                    additional_info = {}
                    if 'PER' in row and pd.notna(row['PER']):
                        additional_info['PER'] = row['PER']
                    if 'PBR' in row and pd.notna(row['PBR']):
                        additional_info['PBR'] = row['PBR']
                    if 'ROE' in row and pd.notna(row['ROE']):
                        additional_info['ROE'] = row['ROE']
                    
                    # 注文コールバック
                    def handle_card_order(ticker, action, price, row_data=row):
                        pt = PaperTrader()
                        t_act = "BUY" if "BUY" in action else "SELL"
                        if pt.execute_trade(ticker, t_act, trading_unit, price, reason=f"Card: {row_data['Strategy']}"):
                            st.toast(f"{row_data['Name']} 注文完了！")
                        else:
                            st.warning("注文に失敗しました。")
                    
                    # 改善版コンポーネントで表示
                    display_stock_card(
                        ticker=row['Ticker'],
                        name=row['Name'],
                        action=row['Action'],
                        price=row['Last Price'],
                        explanation=row.get('Explanation', ''),
                        strategy=row['Strategy'],
                        risk_level=risk_level,
                        on_order_click=handle_card_order,
                        additional_info=additional_info if additional_info else None
                    )

            # 2.5. Pattern Scan
            if 'patterns' in cached_results and cached_results['patterns']:
                st.markdown("---")
                st.subheader("🔍 チャートパターン検出")
                st.write("アルゴリズムが検出したテクニカルパターンです（ダブルボトム、三角持ち合い等）。")
                
                patterns_df = pd.DataFrame(cached_results['patterns'])
                
                # Group by pattern type
                for pattern_type in patterns_df['pattern'].unique():
                    st.markdown(f"#### {pattern_type}")
                    subset = patterns_df[patterns_df['pattern'] == pattern_type]
                    
                    cols = st.columns(min(len(subset), 3))
                    for idx, row in subset.iterrows():
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.info(f"**{row['ticker']}**")
                            st.caption(row['description'])
                            st.metric("信頼度", f"{row['confidence']:.0%}")
                            
                            if st.button(f"チャートで確認 ({row['ticker']})", key=f"pat_{row['ticker']}_{idx}"):
                                st.session_state['pattern_ticker'] = row['ticker']
                                st.session_state['pattern_data'] = row.to_dict()

                # Display Chart for Selected Pattern
                if 'pattern_ticker' in st.session_state and st.session_state['pattern_ticker']:
                    p_ticker = st.session_state['pattern_ticker']
                    p_data = st.session_state['pattern_data']
                    
                    st.markdown(f"### 📉 {p_ticker} - {p_data['pattern']}")
                    
                    # Fetch data for visualization
                    with st.spinner(f"{p_ticker} の詳細データを取得中..."):
                        # Fetch 6 months to show context
                        df_pat = fetch_stock_data([p_ticker], period="6mo")[p_ticker]
                        
                    if df_pat is not None and not df_pat.empty:
                        fig_pat = go.Figure()
                        fig_pat.add_trace(go.Candlestick(
                            x=df_pat.index,
                            open=df_pat['Open'], high=df_pat['High'],
                            low=df_pat['Low'], close=df_pat['Close'],
                            name=p_ticker
                        ))
                        
                        # Annotate points if available
                        if 'points' in p_data and p_data['points']:
                            points = p_data['points']
                            # Filter points that exist in the fetched dataframe
                            valid_points = [p for p in points if pd.to_datetime(p) in df_pat.index]
                            
                            if valid_points:
                                # Draw markers
                                fig_pat.add_trace(go.Scatter(
                                    x=valid_points,
                                    y=[df_pat.loc[pd.to_datetime(p)]['Low'] for p in valid_points], # Assuming Low for bottoms
                                    mode='markers',
                                    marker=dict(color='blue', size=12, symbol='circle-open'),
                                    name='Pattern Points'
                                ))
                                
                                # Draw lines connecting points
                                fig_pat.add_trace(go.Scatter(
                                    x=valid_points,
                                    y=[df_pat.loc[pd.to_datetime(p)]['Low'] for p in valid_points],
                                    mode='lines',
                                    line=dict(color='blue', width=2, dash='dash'),
                                    name='Pattern Line'
                                ))
                        
                        fig_pat.update_layout(xaxis_rangeslider_visible=False, height=400)
                        st.plotly_chart(fig_pat, use_container_width=True)
                        
                        if st.button("閉じる", key="close_pattern_chart"):
                            del st.session_state['pattern_ticker']
                            st.rerun()

            # 3. Advanced Details
            with st.expander("📊 詳細データ・分析ツール (上級者向け)"):
                st.dataframe(actionable_df)
        else:
            st.info("有効なシグナルは見つかりませんでした。")

    elif run_fresh:
        # === Sentiment Analysis Section ===
        with st.expander("📰 市場センチメント分析", expanded=True):
            from src.sentiment import SentimentAnalyzer
            
            # Cache SentimentAnalyzer in session state
            if 'sentiment_analyzer' not in st.session_state:
                st.session_state.sentiment_analyzer = SentimentAnalyzer()
            sa = st.session_state.sentiment_analyzer
            
            with st.spinner("市場センチメントを分析中..."):
                try:
                    sentiment = sa.get_market_sentiment()
                    # Save to database
                    sa.save_sentiment_history(sentiment)
                except Exception as e:
                    display_error_message(
                        "network",
                        "センチメント分析に失敗しました。ネットワーク接続を確認してください。",
                        str(e)
                    )
                    sentiment = {'score': 0, 'label': 'Neutral', 'news_count': 0, 'top_news': []}
            
            # Sentiment Display (統一コンポーネント使用)
            display_sentiment_gauge(sentiment['score'], sentiment.get('news_count', 0))
            
            # Sentiment Timeline
            st.subheader("📈 センチメント推移")
            history_days = st.radio("表示期間", [7, 30], horizontal=True, key="sentiment_history_days")
            history = sa.get_sentiment_history(days=history_days)
            
            if history:
                history_df = pd.DataFrame(history)
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=history_df['timestamp'],
                    y=history_df['score'],
                    mode='lines+markers',
                    name='Sentiment Score',
                    line=dict(color='royalblue', width=2),
                    marker=dict(size=8)
                ))
                fig_timeline.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
                fig_timeline.add_hline(y=0.15, line_dash="dot", line_color="green", annotation_text="Positive Threshold")
                fig_timeline.add_hline(y=-0.15, line_dash="dot", line_color="red", annotation_text="Negative Threshold")
                fig_timeline.update_layout(
                    title=f"過去{history_days}日間のセンチメント推移",
                    xaxis_title="日付",
                    yaxis_title="スコア",
                    yaxis_range=[-1, 1],
                    hovermode='x unified',
                    height=300
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("まだ履歴データがありません。スキャンを繰り返すことで履歴が蓄積されます。")
            
            # Top News Headlines
            st.subheader("📰 最新ニュース見出し")
            if sentiment.get('top_news'):
                for i, news in enumerate(sentiment['top_news'][:5], 1):
                    # Note: Individual news sentiment could be pre-calculated in get_market_sentiment()
                    # but for now we keep it simple
                    news_text = f"{news['title']} {news.get('summary', '')}"
                    news_sentiment = sa.analyze_sentiment(news_text)
                    sentiment_emoji = "🟢" if news_sentiment > 0.1 else "🔴" if news_sentiment < -0.1 else "🟡"
                    st.markdown(f"{i}. {sentiment_emoji} [{news['title']}]({news['link']})")
            else:
                st.info("ニュースが取得できませんでした。")
            
            # Warning if sentiment is bad
            if sentiment['score'] < -0.2:
                st.error("⚠️ 市場センチメントが悪化しています。買いシグナルは抑制されます。")
        
        with st.spinner("データを取得し、全戦略をバックテスト中..."):
            # 1. Fetch Data
            if ticker_group == "カスタム入力":
                tickers = custom_tickers
            else:
                tickers = MARKETS[selected_market]
                
            if not tickers:
                display_error_message(
                    "data",
                    "銘柄が指定されていません。サイドバーで銘柄を選択してください。",
                    None
                )
                st.stop()
            
            try:
                data_map = fetch_stock_data(tickers, period=period)
            except Exception as e:
                display_error_message(
                    "network",
                    "株価データの取得に失敗しました。インターネット接続を確認してください。",
                    str(e)
                )
                st.stop()
            
            results = []
            progress_bar = st.progress(0)
            
            # 2. Run Analysis
            backtester = Backtester(allow_short=allow_short, position_size=position_size)
            
            for i, ticker in enumerate(tickers):
                df = data_map.get(ticker)
                if df is None or df.empty:
                    continue
                    
                for strategy in strategies:
                    # Run with default risk management
                    res = backtester.run(df, strategy, stop_loss=0.05, take_profit=0.10)
                    if res:
                        recent_signals = res['signals'].iloc[-5:]
                        last_signal_date = None
                        action = "HOLD"
                        
                        # Find the most recent non-zero signal
                        for date, signal in recent_signals.items():
                            if signal == 1:
                                action = "BUY"
                                last_signal_date = date
                            elif signal == -1:
                                if allow_short:
                                    action = "SELL (SHORT)"
                                else:
                                    action = "SELL"
                                last_signal_date = date
                                
                        if action != "HOLD":
                            date_str = last_signal_date.strftime('%Y-%m-%d')
                            results.append({
                                "Ticker": ticker,
                                "Name": TICKER_NAMES.get(ticker, ticker),
                                "Strategy": strategy.name,
                                "Return": res['total_return'],
                                "Max Drawdown": res['max_drawdown'],
                                "Action": action,
                                "Signal Date": date_str,
                                "Last Price": get_latest_price(df)
                            })
                
                progress_bar.progress((i + 1) / len(tickers))
                
            results_df = pd.DataFrame(results)
            
            if not results_df.empty:
                actionable_df = results_df[results_df['Action'] != 'HOLD'].copy()
                actionable_df = actionable_df.sort_values(by="Return", ascending=False)
                
                # --- Beginner Friendly UI ---
                
                # 1. Today's Best Pick
                st.markdown("---")
                st.subheader("🏆 今日のイチオシ (Today's Best Pick)")
                
                best_pick = actionable_df.iloc[0]
                best_ticker = best_pick['Ticker']
                best_strat_name = best_pick['Strategy']
                best_strat = next(s for s in strategies if s.name == best_strat_name)
                
                # Calculate Risk Level based on Max Drawdown
                # Low: < 10%, Medium: 10-20%, High: > 20%
                mdd = abs(best_pick['Max Drawdown'])
                if mdd < 0.1:
                    risk_level = "低 (Low)"
                    risk_color = "green"
                elif mdd < 0.2:
                    risk_level = "中 (Medium)"
                    risk_color = "orange"
                else:
                    risk_level = "高 (High)"
                    risk_color = "red"
                
                # Get Explanation
                signal_val = 1 if best_pick['Action'] == "BUY" else -1
                explanation = best_strat.get_signal_explanation(signal_val)
                
                col_best_1, col_best_2 = st.columns([1, 2])
                
                with col_best_1:
                    st.metric("銘柄", f"{best_pick['Name']} ({best_pick['Ticker']})")
                    st.metric("現在価格", f"¥{best_pick['Last Price']:,.0f}")
                    st.markdown(f"**リスクレベル**: :{risk_color}[{risk_level}]")
                    
                with col_best_2:
                    st.success(f"**{best_pick['Action']}** 推奨")
                    st.markdown(f"**理由**: {explanation}")
                    st.caption(f"検知戦略: {best_strat_name}")
                    
                    if st.button("この銘柄を今すぐ注文 (Paper Trading)", key="best_pick_btn", type="primary"):
                         pt = PaperTrader()
                         trade_action = "BUY" if best_pick['Action'] == "BUY" else "SELL"
                         if pt.execute_trade(best_ticker, trade_action, 100, best_pick['Last Price'], reason=f"Best Pick: {best_strat_name}"):
                             st.balloons()
                             st.success(f"{best_pick['Name']} を 100株 {trade_action} しました！")
                         else:
                             st.error("注文に失敗しました。")

                # 2. Recommended Signals (Cards)
                st.markdown("---")
                st.subheader(f"✨ その他の注目銘柄 ({len(actionable_df) - 1}件)")
                
                for idx, row in actionable_df.iloc[1:].iterrows():
                    with st.container():
                        c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
                        
                        # Strategy & Explanation
                        strat = next(s for s in strategies if s.name == row['Strategy'])
                        sig_val = 1 if row['Action'] == "BUY" else -1
                        expl = strat.get_signal_explanation(sig_val)
                        
                        # Risk
                        mdd_val = abs(row['Max Drawdown'])
                        r_level = "低" if mdd_val < 0.1 else "中" if mdd_val < 0.2 else "高"
                        r_color = "🟢" if mdd_val < 0.1 else "🟡" if mdd_val < 0.2 else "🔴"

                        with c1:
                            st.markdown(f"**{row['Name']}**")
                            st.caption(row['Ticker'])
                        with c2:
                            st.markdown(f"**{row['Action']}**")
                            st.caption(f"¥{row['Last Price']:,.0f}")
                        with c3:
                            st.markdown(f"{expl}")
                            st.caption(f"戦略: {row['Strategy']}")
                        with c4:
                            st.markdown(f"リスク: {r_color} {r_level}")
                            if st.button("注文", key=f"btn_{row['Ticker']}_{row['Strategy']}"):
                                pt = PaperTrader()
                                t_act = "BUY" if row['Action'] == "BUY" else "SELL"
                                if pt.execute_trade(row['Ticker'], t_act, 100, row['Last Price'], reason=f"Card: {row['Strategy']}"):
                                    st.toast(f"{row['Name']} 注文完了！")
                        
                        st.divider()

                # 3. Advanced Details (Hidden)
                # 3. Advanced Details (Hidden)
                with st.expander("📊 詳細データ・分析ツール (上級者向け)"):
                    st.subheader("全シグナル一覧")
                    
                    # Fetch Fundamentals for display
                    from src.data_loader import fetch_fundamental_data
                    
                    # Add columns for fundamentals
                    actionable_df['PER'] = "N/A"
                    actionable_df['ROE'] = "N/A"
                    
                    # Fetch data for top results to avoid slow loading
                    for idx, row in actionable_df.iterrows():
                        fund = fetch_fundamental_data(row['Ticker'])
                        if fund:
                            pe = fund.get('trailingPE')
                            roe = fund.get('returnOnEquity')
                            actionable_df.at[idx, 'PER'] = f"{pe:.1f}x" if pe else "N/A"
                            actionable_df.at[idx, 'ROE'] = f"{roe*100:.1f}%" if roe else "N/A"

                    display_df = actionable_df[['Ticker', 'Name', 'Action', 'Signal Date', 'Strategy', 'Return', 'Max Drawdown', 'Win Rate', 'Sharpe Ratio', 'Last Price', 'PER', 'ROE']].copy()
                    display_df['Return'] = display_df['Return'].apply(lambda x: f"{x*100:.1f}%")
                    display_df['Max Drawdown'] = display_df['Max Drawdown'].apply(lambda x: f"{x*100:.1f}%")
                    display_df['Win Rate'] = display_df['Win Rate'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "N/A")
                    display_df['Sharpe Ratio'] = display_df['Sharpe Ratio'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                    display_df['Last Price'] = display_df['Last Price'].apply(lambda x: f"¥{x:,.0f}")
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # One-Click Order Button
                    st.subheader("🚀 アクション")
                    if st.button("推奨シグナルをペーパートレードに反映 (Buy 100株)", type="primary"):
                        pt = PaperTrader()
                        success_count = 0
                        for _, row in actionable_df.iterrows():
                            ticker = row['Ticker']
                            action = row['Action']
                            price = row['Last Price']
                            
                            # Only handle BUY for now for simplicity, or handle SELL if holding
                            trade_action = "BUY" if action == "BUY" else "SELL"
                            
                            # Execute
                            if pt.execute_trade(ticker, trade_action, 100, price, reason=f"Auto-Signal: {row['Strategy']}"):
                                success_count += 1
                        fig_eq.update_layout(title="資産の増減シミュレーション", xaxis_title="Date", yaxis_title="Equity (JPY)")
                        st.plotly_chart(fig_eq, use_container_width=True)
            else:
                st.warning("現在、有効なシグナルが出ている銘柄はありませんでした。")

# --- Tab 2: Portfolio Simulation ---
with tab2:
    st.header("ポートフォリオ・シミュレーション")
    st.write("複数の銘柄を組み合わせた場合のリスクとリターンをシミュレーションします。")
    
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
    st.header("ペーパートレーディング (仮想売買)")
    st.write("リアルタイムの株価データを用いて、仮想資金でトレードの練習ができます。")
    
    pt = PaperTrader()
    
    # Refresh Button
    if st.button("最新価格で評価額を更新"):
        with st.spinner("現在値を更新中..."):
            pt.update_daily_equity()
            st.success("更新完了")
    
    # Dashboard
    balance = pt.get_current_balance()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("現金残高 (Cash)", format_currency(balance['cash']))
    col2.metric("総資産 (Total Equity)", format_currency(balance['total_equity']))
    
    pnl = balance['total_equity'] - pt.initial_capital
    pnl_pct = (pnl / pt.initial_capital) * 100
    col3.metric("全期間損益", format_currency(pnl), delta=f"{pnl_pct:+.1f}%")
    
    st.divider()
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("現在の保有ポジション")
        positions = pt.get_positions()
        if not positions.empty:
            # Format for display
            pos_display = positions.copy()
            pos_display['unrealized_pnl_pct'] = (pos_display['current_price'] - pos_display['entry_price']) / pos_display['entry_price']
            
            # Apply styling
            st.dataframe(pos_display.style.format({
                'entry_price': '¥{:,.0f}',
                'current_price': '¥{:,.0f}',
                'unrealized_pnl': '¥{:,.0f}',
                'unrealized_pnl_pct': '{:.1%}'
            }), use_container_width=True)
        else:
            st.info("現在保有しているポジションはありません。")
            
    with col_right:
        st.subheader("手動注文")
        with st.form("order_form"):
            ticker_input = st.text_input("銘柄コード (例: 7203.T)")
            action_input = st.selectbox("売買", ["BUY", "SELL"])
            qty_input = st.number_input("数量", min_value=100, step=100, value=100)
            
            submitted = st.form_submit_button("注文実行")
            if submitted and ticker_input:
                # Get current price
                price_data = fetch_stock_data([ticker_input], period="1d")
                if ticker_input in price_data and not price_data[ticker_input].empty:
                    current_price = price_data[ticker_input]['Close'].iloc[-1]
                    
                    if pt.execute_trade(ticker_input, action_input, qty_input, current_price, reason="Manual"):
                        st.success(f"{action_input}注文が完了しました: {ticker_input} @ {current_price}")
                        st.rerun()
                    else:
                        st.error("注文に失敗しました（資金不足または保有株不足）。")
                else:
                    st.error("価格データの取得に失敗しました。")

    st.divider()
    st.subheader("取引履歴")
    history = pt.get_trade_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("取引履歴はありません。")

# --- Tab 4: Dashboard ---
with tab4:
    st.header("🎯 パフォーマンス・ダッシュボード")
    st.write("全銘柄のパフォーマンスを一目で確認できます。")
    
    # Performance Analysis Section
    st.markdown("---")
    st.subheader("📈 詳細パフォーマンス分析")
    
    try:
        from src.performance import PerformanceAnalyzer
        
        analyzer = PerformanceAnalyzer()
        
        # Cumulative P&L Chart
        st.markdown("#### 累計損益推移")
        cumulative_pnl = analyzer.get_cumulative_pnl()
        
        if not cumulative_pnl.empty:
            # Benchmark comparison
            benchmark_data = analyzer.compare_with_benchmark(benchmark_ticker="^N225", days=365)
            
            if benchmark_data:
                fig_comparison = go.Figure()
                
                # Portfolio line
                portfolio_df = pd.DataFrame(benchmark_data['portfolio'])
                if not portfolio_df.empty:
                    fig_comparison.add_trace(go.Scatter(
                        x=portfolio_df['date'],
                        y=portfolio_df['portfolio_return'],
                        mode='lines',
                        name='ポートフォリオ',
                        line=dict(color='gold', width=3)
                    ))
                
                # Benchmark line
                benchmark_df = pd.DataFrame(benchmark_data['benchmark'])
                if not benchmark_df.empty:
                    fig_comparison.add_trace(go.Scatter(
                        x=benchmark_df['date'],
                        y=benchmark_df['benchmark_return'],
                        mode='lines',
                        name='日経225',
                        line=dict(color='lightblue', width=2, dash='dash')
                    ))
                
                fig_comparison.update_layout(
                    title="ポートフォリオ vs ベンチマーク (日経225)",
                    xaxis_title="日付",
                    yaxis_title="リターン (%)",
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
            else:
                # Simple P&L chart
                fig_pnl = px.line(cumulative_pnl, x='date', y='cumulative_pnl', 
                                 title='累計損益推移',
                                 labels={'date': '日付', 'cumulative_pnl': '累計損益 (円)'})
                fig_pnl.update_traces(line_color='gold', line_width=3)
                st.plotly_chart(fig_pnl, use_container_width=True)
        else:
            st.info("取引履歴がありません。ペーパートレードを開始してください。")
        
        # Strategy Performance
        st.markdown("#### 戦略別パフォーマンス")
        strategy_perf = analyzer.get_strategy_performance()
        
        if not strategy_perf.empty:
            # Format for display
            display_strat = strategy_perf.copy()
            display_strat['win_rate'] = display_strat['win_rate'].apply(lambda x: f"{x:.1%}")
            display_strat['avg_profit'] = display_strat['avg_profit'].apply(lambda x: f"{x:+.2f}%")
            display_strat['total_pnl'] = display_strat['total_pnl'].apply(lambda x: f"{x:+.2f}%")
            display_strat.columns = ['戦略', '取引回数', '勝率', '平均利益率', '総損益']
            
            st.dataframe(display_strat, use_container_width=True)
        else:
            st.info("戦略別データがありません。")
        
        # Top/Worst Performers
        st.markdown("#### 銘柄別パフォーマンス")
        ticker_perf = analyzer.get_ticker_performance()
        
        if not ticker_perf.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚀 トップ5銘柄**")
                top5 = ticker_perf.nlargest(5, 'total_pnl')[['ticker', 'trades', 'avg_profit', 'total_pnl']]
                top5_display = top5.copy()
                top5_display['avg_profit'] = top5_display['avg_profit'].apply(lambda x: f"{x:+.2f}%")
                top5_display['total_pnl'] = top5_display['total_pnl'].apply(lambda x: f"{x:+.2f}%")
                top5_display.columns = ['銘柄', '取引回数', '平均利益', '総損益']
                st.dataframe(top5_display, use_container_width=True)
            
            with col2:
                st.markdown("**📉 ワースト5銘柄**")
                bottom5 = ticker_perf.nsmallest(5, 'total_pnl')[['ticker', 'trades', 'avg_profit', 'total_pnl']]
                bottom5_display = bottom5.copy()
                bottom5_display['avg_profit'] = bottom5_display['avg_profit'].apply(lambda x: f"{x:+.2f}%")
                bottom5_display['total_pnl'] = bottom5_display['total_pnl'].apply(lambda x: f"{x:+.2f}%")
                bottom5_display.columns = ['銘柄', '取引回数', '平均利益', '総損益']
                st.dataframe(bottom5_display, use_container_width=True)
        
        # Monthly Returns
        st.markdown("#### 月次パフォーマンス")
        monthly_returns = analyzer.get_monthly_returns()
        
        if not monthly_returns.empty:
            # Create month-year labels
            monthly_returns['month_label'] = monthly_returns.apply(
                lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1
            )
            
            fig_monthly = px.bar(monthly_returns, x='month_label', y='monthly_return',
                                title='月次リターン',
                                labels={'month_label': '年月', 'monthly_return': 'リターン (円)'},
                                color='monthly_return',
                                color_continuous_scale='RdYlGn')
            fig_monthly.update_layout(showlegend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)
        
    except Exception as e:
        st.error(f"パフォーマンス分析エラー: {e}")
    
    st.markdown("---")
    
    # Performance Heatmap
    st.subheader("📊 パフォーマンス・ヒートマップ")
    
    if st.button("ヒートマップを生成", type="primary"):
        with st.spinner("データ取得中..."):
            # Get tickers based on selection
            if ticker_group == "カスタム入力":
                heatmap_tickers = custom_tickers[:20]  # Limit for performance
            else:
                heatmap_tickers = MARKETS[selected_market][:20]
            
            data_map_hm = fetch_stock_data(heatmap_tickers, period="1mo")
            
            # Calculate returns
            returns_data = []
            for ticker in heatmap_tickers:
                df = data_map_hm.get(ticker)
                if df is not None and not df.empty and len(df) > 1:
                    daily_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
                    returns_data.append({
                        'Ticker': ticker,
                        'Name': TICKER_NAMES.get(ticker, ticker),
                        'Return': daily_return
                    })
            
            if returns_data:
                returns_df = pd.DataFrame(returns_data)
                
                # Create heatmap
                fig_heatmap = px.treemap(
                    returns_df,
                    path=['Ticker'],
                    values=abs(returns_df['Return']),  # Size by absolute return
                    color='Return',
                    color_continuous_scale='RdYlGn',
                    color_continuous_midpoint=0,
                    title="過去1ヶ月のリターン (緑=上昇、赤=下落)"
                )
                fig_heatmap.update_traces(textinfo="label+value+percent parent")
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Top/Bottom performers
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🚀 トップ5")
                    top5 = returns_df.nlargest(5, 'Return')[['Ticker', 'Name', 'Return']]
                    top5['Return'] = top5['Return'].apply(lambda x: f"{x*100:+.2f}%")
                    st.dataframe(top5, use_container_width=True)
                
                with col2:
                    st.subheader("📉 ワースト5")
                    bottom5 = returns_df.nsmallest(5, 'Return')[['Ticker', 'Name', 'Return']]
                    bottom5['Return'] = bottom5['Return'].apply(lambda x: f"{x*100:+.2f}%")
                    st.dataframe(bottom5, use_container_width=True)
    
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
            y=equity_history['equity'],
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
                'equity': ['first', 'last']
            })
            monthly_returns['return'] = (
                (monthly_returns[('equity', 'last')] - monthly_returns[('equity', 'first')]) / 
                monthly_returns[('equity', 'first')]
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
        
        news_data = fetch_news(committee_ticker)
        
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
