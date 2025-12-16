import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.constants import MARKETS, TICKER_NAMES
from src.performance import PerformanceAnalyzer


@st.cache_data
def get_cached_tickers(market: str):
    return MARKETS.get(market, [])


def render_market_ticker_selector(key: str = "main"):
    """
    Cached Market & Ticker Selector Component
    """
    col1, col2 = st.columns(2)
    with col1:
        market = st.selectbox("市場を選択", list(MARKETS.keys()), key=f"market_sel_{key}")
    
    tickers_list = get_cached_tickers(market)
    with col2:
        tickers = st.multiselect(
            "銘柄を選択 (空欄で全銘柄)", 
            tickers_list, 
            format_func=lambda x: f"{x} {TICKER_NAMES.get(x, '')}",
            key=f"ticker_sel_{key}"
        )
    
    return market, tickers if tickers else tickers_list


def render_performance_tab(ticker_group, selected_market, custom_tickers, currency="JPY"):
    """
    パフォーマンス分析タブのレンダリングロジック

    Args:
        ticker_group (str): 選択された銘柄グループ
        selected_market (str): 選択された市場
        custom_tickers (list): カスタム銘柄リスト
        currency (str): 通貨単位 (JPY, USD, etc.)
    """
    st.header("🎯 パフォーマンス・ダッシュボード")
    st.write("全銘柄のパフォーマンスを一目で確認できます。")

    # Performance Analysis Section
    st.markdown("---")
    st.subheader("📈 詳細パフォーマンス分析")

    try:
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
                portfolio_df = pd.DataFrame(benchmark_data["portfolio"])
                if not portfolio_df.empty:
                    fig_comparison.add_trace(
                        go.Scatter(
                            x=portfolio_df["date"],
                            y=portfolio_df["portfolio_return"],
                            mode="lines",
                            name="ポートフォリオ",
                            line=dict(color="gold", width=3),
                        )
                    )

                # Benchmark line
                benchmark_df = pd.DataFrame(benchmark_data["benchmark"])
                if not benchmark_df.empty:
                    fig_comparison.add_trace(
                        go.Scatter(
                            x=benchmark_df["date"],
                            y=benchmark_df["benchmark_return"],
                            mode="lines",
                            name="日経225",
                            line=dict(color="lightblue", width=2, dash="dash"),
                        )
                    )

                fig_comparison.update_layout(
                    title="ポートフォリオ vs ベンチマーク (日経225)",
                    xaxis_title="日付",
                    yaxis_title="リターン (%)",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
            else:
                # Simple P&L chart
                fig_pnl = px.line(
                    cumulative_pnl,
                    x="date",
                    y="cumulative_pnl",
                    title="累計損益推移",
                    labels={"date": "日付", "cumulative_pnl": "累計損益 (円)"},
                )
                fig_pnl.update_traces(line_color="gold", line_width=3)
                st.plotly_chart(fig_pnl, use_container_width=True)
        else:
            st.info("取引履歴がありません。ペーパートレードを開始してください。")

        # Strategy Performance
        st.markdown("#### 戦略別パフォーマンス")
        strategy_perf = analyzer.get_strategy_performance()

        if not strategy_perf.empty:
            # Format for display
            display_strat = strategy_perf.copy()
            display_strat["win_rate"] = display_strat["win_rate"].apply(lambda x: f"{x:.1%}")
            display_strat["avg_profit"] = display_strat["avg_profit"].apply(lambda x: f"{x:+.2f}%")
            display_strat["total_pnl"] = display_strat["total_pnl"].apply(lambda x: f"{x:+.2f}%")
            display_strat.columns = ["戦略", "取引回数", "勝率", "平均利益率", "総損益"]

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
                top5 = ticker_perf.nlargest(5, "total_pnl")[["ticker", "trades", "avg_profit", "total_pnl"]]
                top5_display = top5.copy()
                top5_display["avg_profit"] = top5_display["avg_profit"].apply(lambda x: f"{x:+.2f}%")
                top5_display["total_pnl"] = top5_display["total_pnl"].apply(lambda x: f"{x:+.2f}%")
                top5_display.columns = ["銘柄", "取引回数", "平均利益", "総損益"]
                st.dataframe(top5_display, use_container_width=True)

            with col2:
                st.markdown("**📉 ワースト5銘柄**")
                bottom5 = ticker_perf.nsmallest(5, "total_pnl")[["ticker", "trades", "avg_profit", "total_pnl"]]
                bottom5_display = bottom5.copy()
                bottom5_display["avg_profit"] = bottom5_display["avg_profit"].apply(lambda x: f"{x:+.2f}%")
                bottom5_display["total_pnl"] = bottom5_display["total_pnl"].apply(lambda x: f"{x:+.2f}%")
                bottom5_display.columns = ["銘柄", "取引回数", "平均利益", "総損益"]
                st.dataframe(bottom5_display, use_container_width=True)

        # Monthly Returns
        st.markdown("#### 月次パフォーマンス")
        monthly_returns = analyzer.get_monthly_returns()

        if not monthly_returns.empty:
            # Create month-year labels
            monthly_returns["month_label"] = monthly_returns.apply(
                lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1
            )

            fig_monthly = px.bar(
                monthly_returns,
                x="month_label",
                y="monthly_return",
                title="月次リターン",
                labels={"month_label": "年月", "monthly_return": "リターン (円)"},
                color="monthly_return",
                color_continuous_scale="RdYlGn",
            )
            fig_monthly.update_layout(showlegend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)

    except Exception as e:
        st.error(f"パフォーマンス分析エラー: {e}")

    st.markdown("---")

    # Performance Heatmap
    st.subheader("📊 パフォーマンス・ヒートマップ")

    if st.button("ヒートマップを生成", type="primary"):
        with st.spinner("データ取得中..."):
            from src.data_loader import fetch_stock_data

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
                    daily_return = (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]
                    returns_data.append(
                        {"Ticker": ticker, "Name": TICKER_NAMES.get(ticker, ticker), "Return": daily_return}
                    )

            if returns_data:
                returns_df = pd.DataFrame(returns_data)

                # Create heatmap
                fig_heatmap = px.treemap(
                    returns_df,
                    path=["Ticker"],
                    values=abs(returns_df["Return"]),  # Size by absolute return
                    color="Return",
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    title="過去1ヶ月のリターン (緑=上昇、赤=下落)",
                )
                fig_heatmap.update_traces(textinfo="label+value+percent parent")
                st.plotly_chart(fig_heatmap, use_container_width=True)

                # Top/Bottom performers
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🚀 トップ5")
                    top5 = returns_df.nlargest(5, "Return")[["Ticker", "Name", "Return"]]
                    top5["Return"] = top5["Return"].apply(lambda x: f"{x*100:+.2f}%")
                    st.dataframe(top5, use_container_width=True)

                with col2:
                    st.subheader("📉 ワースト5")
                    bottom5 = returns_df.nsmallest(5, "Return")[["Ticker", "Name", "Return"]]
                    bottom5["Return"] = bottom5["Return"].apply(lambda x: f"{x*100:+.2f}%")
                    st.dataframe(bottom5, use_container_width=True)


def render_paper_trading_tab():
    """
    ペーパートレーディングタブのレンダリングロジック
    """
    from src.data_loader import fetch_stock_data
    from src.formatters import format_currency
    from src.paper_trader import PaperTrader

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
    col1.metric("現金残高 (Cash)", format_currency(balance["cash"]))
    col2.metric("総資産 (Total Equity)", format_currency(balance["total_equity"]))

    pnl = balance["total_equity"] - pt.initial_capital
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
            pos_display["unrealized_pnl_pct"] = (
                pos_display["current_price"] - pos_display["entry_price"]
            ) / pos_display["entry_price"]

            # Apply styling
            st.dataframe(
                pos_display.style.format(
                    {
                        "entry_price": "¥{:,.0f}",
                        "current_price": "¥{:,.0f}",
                        "unrealized_pnl": "¥{:,.0f}",
                        "unrealized_pnl_pct": "{:.1%}",
                    }
                ),
                use_container_width=True,
            )
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
                    current_price = price_data[ticker_input]["Close"].iloc[-1]

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
        # Format for display
        hist_display = history.copy()
        # timestampカラムがない場合のフォールバック
        if "timestamp" in hist_display.columns:
            hist_display["timestamp"] = pd.to_datetime(hist_display["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        elif "date" in hist_display.columns:
            hist_display["date"] = pd.to_datetime(hist_display["date"]).dt.strftime("%Y-%m-%d %H:%M")

        st.subheader("取引履歴")
    history = pt.get_trade_history()
    if not history.empty:
        # Format for display
        hist_display = history.copy()
        # timestampカラムがない場合のフォールバック
        if "timestamp" in hist_display.columns:
            hist_display["timestamp"] = pd.to_datetime(hist_display["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        elif "date" in hist_display.columns:
            hist_display["date"] = pd.to_datetime(hist_display["date"]).dt.strftime("%Y-%m-%d %H:%M")

        st.dataframe(hist_display, use_container_width=True)
    else:
        st.info("取引履歴はありません。")


def render_market_scan_tab(
    ticker_group,
    selected_market,
    custom_tickers,
    period,
    strategies,
    allow_short,
    position_size,
    enable_fund_filter,
    max_per,
    max_pbr,
    min_roe,
    trading_unit,
):
    """
    市場スキャンタブのレンダリングロジック
    """
    import datetime
    import json
    import os

    from src.backtester import Backtester
    from src.data_loader import (fetch_fundamental_data, fetch_stock_data,
                                 get_latest_price)
    from src.formatters import get_risk_level
    from src.paper_trader import PaperTrader
    from src.sentiment import SentimentAnalyzer
    from src.ui_components import (display_best_pick_card,
                                   display_error_message,
                                   display_sentiment_gauge)

    st.header("市場全体スキャン")
    st.write("指定した銘柄群に対して全戦略をバックテストし、有望なシグナルを検出します。")

    # --- Automation Logic ---
    cached_results = None
    if os.path.exists("scan_results.json"):
        try:
            with open("scan_results.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Check if data is fresh (e.g., from today)
                scan_date = datetime.datetime.strptime(data["scan_date"], "%Y-%m-%d %H:%M:%S")
                if scan_date.date() == datetime.date.today():
                    cached_results = data
                    st.success(f"✅ 最新のスキャン結果を読み込みました ({data['scan_date']})")
        except Exception as e:
            display_error_message(
                "data", "スキャン結果の読み込みに失敗しました。ファイルが破損している可能性があります。", str(e)
            )

    run_fresh = False
    # Button logic: If cache exists, button says "Re-scan". If not, "Scan".
    # If button clicked, run_fresh becomes True.
    if st.button(
        "市場をスキャンして推奨銘柄を探す (再スキャン)" if cached_results else "市場をスキャンして推奨銘柄を探す",
        type="primary",
    ):
        run_fresh = True
        cached_results = None  # Force fresh scan logic

    if cached_results and not run_fresh:
        sentiment = cached_results["sentiment"]
        results_data = cached_results["results"]

        # === Display Cached Sentiment ===
        with st.expander("📰 市場センチメント分析", expanded=True):
            display_sentiment_gauge(sentiment["score"], sentiment.get("news_count", 0))

            st.subheader("📰 最新ニュース見出し")
            if sentiment.get("top_news"):
                for i, news in enumerate(sentiment["top_news"][:5], 1):
                    st.markdown(f"{i}. [{news['title']}]({news['link']})")

        # === Display Macro Indicators ===
        with st.expander("🌍 マクロ経済指標", expanded=True):
            try:
                from src.data_loader import fetch_external_data

                macro_data = fetch_external_data(period="5d")

                m_cols = st.columns(len(macro_data))
                for i, (name, df) in enumerate(macro_data.items()):
                    if not df.empty:
                        current = df["Close"].iloc[-1]
                        prev = df["Close"].iloc[-2]
                        diff = current - prev
                        pct = (diff / prev) * 100

                        with m_cols[i]:
                            st.metric(
                                label=name,
                                value=f"{current:,.2f}",
                                delta=f"{diff:+.2f} ({pct:+.2f}%)",
                                delta_color="inverse" if name == "VIX" else "normal",
                            )
            except Exception as e:
                st.error(f"マクロデータ取得エラー: {e}")

        # === Display Cached Results ===
        results_df = pd.DataFrame(results_data)
        if not results_df.empty:
            actionable_df = results_df[results_df["Action"] != "HOLD"].copy()

            # Apply Fundamental Filters
            if enable_fund_filter:
                original_count = len(actionable_df)

                # PER
                if "PER" in actionable_df.columns:
                    actionable_df = actionable_df[(actionable_df["PER"].notna()) & (actionable_df["PER"] <= max_per)]

                # PBR
                if "PBR" in actionable_df.columns:
                    actionable_df = actionable_df[(actionable_df["PBR"].notna()) & (actionable_df["PBR"] <= max_pbr)]

                # ROE
                if "ROE" in actionable_df.columns:
                    actionable_df = actionable_df[
                        (actionable_df["ROE"].notna()) & (actionable_df["ROE"] >= min_roe / 100.0)
                    ]

                filtered_count = len(actionable_df)
                if original_count > filtered_count:
                    st.info(
                        f"財務フィルタにより {original_count} 件中 {original_count - filtered_count} 件が除外されました。"
                    )

            # Heuristic Confidence Score calculation
            # Base confidence 0.5 + Return contribution + Strategy bonus
            # In production, this should come from the model's probability output.
            def calc_confidence(row):
                base_conf = 0.5
                ret_contr = min(0.4, abs(row["Return"]) * 5) # Up to 0.4 from return
                strat_bonus = 0.1 if "LightGBM" in row["Strategy"] else 0.0
                
                return max(0.0, min(0.99, base_conf + ret_contr + strat_bonus))

            if not results_df.empty:
                results_df["Confidence"] = results_df.apply(calc_confidence, axis=1)
                
                actionable_df = results_df[results_df["Action"] != "HOLD"].copy()

                # Filters UI
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    confidence_threshold = st.slider("信頼度スコア (Confidence)", 0.0, 1.0, 0.6, 0.05, key="conf_slider")
                with col_f2:
                    min_return_filter = st.slider("最小予想リターン", 0.0, 0.2, 0.01, 0.005, key="min_ret_slider")

                # Apply Filters
                actionable_df = actionable_df[
                    (actionable_df["Return"] >= min_return_filter) &
                    (actionable_df["Confidence"] >= confidence_threshold)
                ]
                
                if actionable_df.empty:
                    st.warning(f"フィルタリングの結果、表示できる銘柄がありません。(Confidence >= {confidence_threshold}, Return >= {min_return_filter})")
                
                actionable_df = actionable_df.sort_values(by="Return", ascending=False)

            # 1. Today's Best Pick
            if not actionable_df.empty:
                best_pick = actionable_df.iloc[0]

                # Calculate Kelly (Simplified: W - (1-W)/R, assume WinProb=0.6, R=Ratio)
                # Need estimated risk reward.
                upside = best_pick["Return"]
                downside = abs(best_pick["Max Drawdown"])
                risk_reward = upside / downside if downside > 0 else 1.0
                win_prob = 0.55 # Conservative default
                kelly = win_prob - (1 - win_prob) / risk_reward if risk_reward > 0 else 0
                kelly = max(0, kelly) # No negative Kelly

                # リスクレベル判定（統一版）
                risk_level = get_risk_level(best_pick.get("Max Drawdown", -0.15))

                # 追加情報の準備
                additional_info = {
                    "Kelly": kelly,
                    "RiskRatio": risk_reward
                }
                if "PER" in best_pick and pd.notna(best_pick["PER"]):
                    additional_info["PER"] = best_pick["PER"]
                if "PBR" in best_pick and pd.notna(best_pick["PBR"]):
                    additional_info["PBR"] = best_pick["PBR"]
                if "ROE" in best_pick and pd.notna(best_pick["ROE"]):
                    additional_info["ROE"] = best_pick["ROE"]

                # 注文コールバック
                def handle_best_pick_order(ticker, action, price):
                    pt = PaperTrader()
                    trade_action = "BUY" if "BUY" in action else "SELL"
                    if pt.execute_trade(
                        ticker, trade_action, trading_unit, price, reason=f"Best Pick: {best_pick['Strategy']}"
                    ):
                        st.balloons()
                        st.success(f"{best_pick['Name']} を {trading_unit}株 {trade_action} しました！")
                    else:
                        display_error_message(
                            "permission",
                            "注文に失敗しました。資金不足または保有株式が不足しています。",
                            f"Ticker: {ticker}, Action: {trade_action}, Unit: {trading_unit}",
                        )

                # 改善版コンポーネントで表示
                display_best_pick_card(
                    ticker=best_pick["Ticker"],
                    name=best_pick["Name"],
                    action=best_pick["Action"],
                    price=best_pick["Last Price"],
                    explanation=best_pick.get("Explanation", ""),
                    strategy=best_pick["Strategy"],
                    risk_level=risk_level,
                    on_order_click=handle_best_pick_order,
                    additional_info=additional_info if additional_info else None,
                )

            # 1.5. AI Robo-Advisor Portfolio
            if "portfolio" in cached_results and cached_results["portfolio"]:
                st.markdown("---")
                st.subheader("🤖 AIロボアドバイザー推奨ポートフォリオ")
                st.info("AIがリスク・リターンを考慮して構築した推奨ポートフォリオです。")

                pf_df = pd.DataFrame(cached_results["portfolio"])
                st.dataframe(pf_df)

            # 2. Recommended Signals (Cards)
            st.markdown("---")
            st.subheader(f"✨ その他の注目銘柄 ({len(actionable_df) - 1}件)")

            for idx, row in actionable_df.iloc[1:].iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 2])

                    # Strategy & Explanation
                    # Note: Strategy object might not be available in cached results, only name
                    # So we use name directly
                    strat_name = row["Strategy"]

                    # Risk
                    mdd_val = abs(row["Max Drawdown"])
                    r_level = "低" if mdd_val < 0.1 else "中" if mdd_val < 0.2 else "高"
                    r_color = "🟢" if mdd_val < 0.1 else "🟡" if mdd_val < 0.2 else "🔴"

                    with c1:
                        st.markdown(f"**{row['Name']}**")
                        st.caption(row["Ticker"])
                    with c2:
                        st.markdown(f"**{row['Action']}**")
                        st.caption(f"¥{row['Last Price']:,.0f}")
                    with c3:
                        st.markdown(f"戦略: {strat_name}")
                    with c4:
                        st.markdown(f"リスク: {r_color} {r_level}")
                        if st.button("注文", key=f"btn_{row['Ticker']}_{row['Strategy']}"):
                            pt = PaperTrader()
                            t_act = "BUY" if row["Action"] == "BUY" else "SELL"
                            if pt.execute_trade(
                                row["Ticker"], t_act, trading_unit, row["Last Price"], reason=f"Card: {row['Strategy']}"
                            ):
                                st.toast(f"{row['Name']} 注文完了！")

                    st.divider()

            # 3. Advanced Details
            with st.expander("📊 詳細データ・分析ツール (上級者向け)"):
                st.dataframe(actionable_df)
        else:
            st.info("有効なシグナルは見つかりませんでした。")

    elif run_fresh:
        # === Sentiment Analysis Section ===
        with st.expander("📰 市場センチメント分析", expanded=True):

            # Cache SentimentAnalyzer in session state
            if "sentiment_analyzer" not in st.session_state:
                st.session_state.sentiment_analyzer = SentimentAnalyzer()
            sa = st.session_state.sentiment_analyzer

            with st.spinner("市場センチメントを分析中..."):
                try:
                    sentiment = sa.get_market_sentiment()
                    # Save to database
                    sa.save_sentiment_history(sentiment)
                except Exception as e:
                    display_error_message(
                        "network", "センチメント分析に失敗しました。ネットワーク接続を確認してください。", str(e)
                    )
                    sentiment = {"score": 0, "label": "Neutral", "news_count": 0, "top_news": []}

            # Sentiment Display
            display_sentiment_gauge(sentiment["score"], sentiment.get("news_count", 0))

            # Sentiment Timeline
            st.subheader("📈 センチメント推移")
            history_days = st.radio("表示期間", [7, 30], horizontal=True, key="sentiment_history_days")
            history = sa.get_sentiment_history(days=history_days)

            if history:
                history_df = pd.DataFrame(history)
                history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])

                fig_timeline = go.Figure()
                fig_timeline.add_trace(
                    go.Scatter(
                        x=history_df["timestamp"],
                        y=history_df["score"],
                        mode="lines+markers",
                        name="Sentiment Score",
                        line=dict(color="royalblue", width=2),
                        marker=dict(size=8),
                    )
                )
                fig_timeline.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
                fig_timeline.add_hline(
                    y=0.15, line_dash="dot", line_color="green", annotation_text="Positive Threshold"
                )
                fig_timeline.add_hline(y=-0.15, line_dash="dot", line_color="red", annotation_text="Negative Threshold")
                fig_timeline.update_layout(
                    title=f"過去{history_days}日間のセンチメント推移",
                    xaxis_title="日付",
                    yaxis_title="スコア",
                    yaxis_range=[-1, 1],
                    hovermode="x unified",
                    height=300,
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("まだ履歴データがありません。スキャンを繰り返すことで履歴が蓄積されます。")

            # Top News Headlines
            st.subheader("📰 最新ニュース見出し")
            if sentiment.get("top_news"):
                for i, news in enumerate(sentiment["top_news"][:5], 1):
                    news_text = f"{news['title']} {news.get('summary', '')}"
                    news_sentiment = sa.analyze_sentiment(news_text)
                    sentiment_emoji = "🟢" if news_sentiment > 0.1 else "🔴" if news_sentiment < -0.1 else "🟡"
                    st.markdown(f"{i}. {sentiment_emoji} [{news['title']}]({news['link']})")
            else:
                st.info("ニュースが取得できませんでした。")

            # Warning if sentiment is bad
            if sentiment["score"] < -0.2:
                st.error("⚠️ 市場センチメントが悪化しています。買いシグナルは抑制されます。")

        # === Macro Indicators ===
        with st.expander("🌍 マクロ経済指標", expanded=True):
            try:
                from src.data_loader import fetch_external_data

                macro_data = fetch_external_data(period="5d")

                if macro_data:
                    m_cols = st.columns(len(macro_data))
                    for i, (name, df) in enumerate(macro_data.items()):
                        if not df.empty:
                            current = df["Close"].iloc[-1]
                            prev = df["Close"].iloc[-2]
                            diff = current - prev
                            pct = (diff / prev) * 100

                            with m_cols[i]:
                                st.metric(
                                    label=name,
                                    value=f"{current:,.2f}",
                                    delta=f"{diff:+.2f} ({pct:+.2f}%)",
                                    delta_color="inverse" if name == "VIX" else "normal",
                                )
                else:
                    st.info("マクロデータが取得できませんでした。")
            except Exception as e:
                st.warning(f"マクロデータ表示エラー: {e}")

        with st.spinner("データを取得し、全戦略をバックテスト中..."):
            # 1. Fetch Data with performance measurement
            import time

            fetch_start = time.time()

            if ticker_group == "カスタム入力":
                tickers = custom_tickers
            else:
                tickers = MARKETS[selected_market]

            if not tickers:
                display_error_message("data", "銘柄が指定されていません。サイドバーで銘柄を選択してください。", None)
                st.stop()

            try:
                # 非同期ローダーを使用（3銘柄以上の場合）
                data_map = fetch_stock_data(tickers, period=period, use_async=True)
                fetch_time = time.time() - fetch_start

                # パフォーマンスメトリクスを表示
                perf_col1, perf_col2, perf_col3 = st.columns(3)
                with perf_col1:
                    st.metric("データ取得時間", f"{fetch_time:.2f}秒")
                with perf_col2:
                    st.metric("取得銘柄数", f"{len(data_map)}/{len(tickers)}")
                with perf_col3:
                    avg_time = fetch_time / len(data_map) if data_map else 0
                    st.metric("平均取得時間", f"{avg_time:.2f}秒/銘柄")

            except Exception as e:
                display_error_message(
                    "network", "株価データの取得に失敗しました。インターネット接続を確認してください。", str(e)
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
                        recent_signals = res["signals"].iloc[-5:]
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
                            date_str = last_signal_date.strftime("%Y-%m-%d")
                            results.append(
                                {
                                    "Ticker": ticker,
                                    "Name": TICKER_NAMES.get(ticker, ticker),
                                    "Strategy": strategy.name,
                                    "Return": res["total_return"],
                                    "Max Drawdown": res["max_drawdown"],
                                    "Action": action,
                                    "Signal Date": date_str,
                                    "Last Price": get_latest_price(df),
                                    "Explanation": strategy.get_signal_explanation(1 if action == "BUY" else -1),
                                }
                            )

                progress_bar.progress((i + 1) / len(tickers))

            results_df = pd.DataFrame(results)

            if not results_df.empty:
                actionable_df = results_df[results_df["Action"] != "HOLD"].copy()
                actionable_df = actionable_df.sort_values(by="Return", ascending=False)

                # --- Beginner Friendly UI ---

                # 1. Today's Best Pick
                st.markdown("---")
                st.subheader("🏆 今日のイチオシ (Today's Best Pick)")

                best_pick = actionable_df.iloc[0]
                best_ticker = best_pick["Ticker"]
                best_strat_name = best_pick["Strategy"]

                # Calculate Risk Level based on Max Drawdown
                mdd = abs(best_pick["Max Drawdown"])
                risk_level = get_risk_level(mdd)

                # Get Explanation
                explanation = best_pick.get("Explanation", "")

                # 注文コールバック
                def handle_best_pick_order_fresh(ticker, action, price):
                    pt = PaperTrader()
                    trade_action = "BUY" if "BUY" in action else "SELL"
                    if pt.execute_trade(
                        ticker, trade_action, trading_unit, price, reason=f"Best Pick: {best_strat_name}"
                    ):
                        st.balloons()
                        st.success(f"{best_pick['Name']} を {trading_unit}株 {trade_action} しました！")
                    else:
                        display_error_message(
                            "permission",
                            "注文に失敗しました。資金不足または保有株式が不足しています。",
                            f"Ticker: {ticker}, Action: {trade_action}, Unit: {trading_unit}",
                        )

                # 改善版コンポーネントで表示
                display_best_pick_card(
                    ticker=best_pick["Ticker"],
                    name=best_pick["Name"],
                    action=best_pick["Action"],
                    price=best_pick["Last Price"],
                    explanation=explanation,
                    strategy=best_strat_name,
                    risk_level=risk_level,
                    on_order_click=handle_best_pick_order_fresh,
                    additional_info=None,
                )

                # 2. Recommended Signals (Cards)
                st.markdown("---")
                st.subheader(f"✨ その他の注目銘柄 ({len(actionable_df) - 1}件)")

                for idx, row in actionable_df.iloc[1:].iterrows():
                    with st.container():
                        c1, c2, c3, c4 = st.columns([2, 2, 3, 2])

                        strat_name = row["Strategy"]
                        mdd_val = abs(row["Max Drawdown"])
                        r_level = "低" if mdd_val < 0.1 else "中" if mdd_val < 0.2 else "高"
                        r_color = "🟢" if mdd_val < 0.1 else "🟡" if mdd_val < 0.2 else "🔴"

                        with c1:
                            st.markdown(f"**{row['Name']}**")
                            st.caption(row["Ticker"])
                        with c2:
                            st.markdown(f"**{row['Action']}**")
                            st.caption(f"¥{row['Last Price']:,.0f}")
                        with c3:
                            st.markdown(f"戦略: {strat_name}")
                        with c4:
                            st.markdown(f"リスク: {r_color} {r_level}")
                            if st.button("注文", key=f"btn_fresh_{row['Ticker']}_{row['Strategy']}"):
                                pt = PaperTrader()
                                t_act = "BUY" if row["Action"] == "BUY" else "SELL"
                                if pt.execute_trade(
                                    row["Ticker"],
                                    t_act,
                                    trading_unit,
                                    row["Last Price"],
                                    reason=f"Card: {row['Strategy']}",
                                ):
                                    st.toast(f"{row['Name']} 注文完了！")

                        st.divider()

                # 3. Advanced Details
                with st.expander("📊 詳細データ・分析ツール (上級者向け)"):
                    st.subheader("全シグナル一覧")

                    # Fetch Fundamentals for display
                    # Add columns for fundamentals
                    actionable_df["PER"] = "N/A"
                    actionable_df["ROE"] = "N/A"

                    # Fetch data for top results to avoid slow loading
                    for idx, row in actionable_df.iterrows():
                        fund = fetch_fundamental_data(row["Ticker"])
                        if fund:
                            pe = fund.get("trailingPE")
                            roe = fund.get("returnOnEquity")
                            actionable_df.at[idx, "PER"] = f"{pe:.1f}x" if pe else "N/A"
                            actionable_df.at[idx, "ROE"] = f"{roe*100:.1f}%" if roe else "N/A"

                    display_df = actionable_df[
                        [
                            "Ticker",
                            "Name",
                            "Action",
                            "Signal Date",
                            "Strategy",
                            "Return",
                            "Max Drawdown",
                            "Last Price",
                            "PER",
                            "ROE",
                        ]
                    ].copy()
                    display_df["Return"] = display_df["Return"].apply(lambda x: f"{x*100:.1f}%")
                    display_df["Max Drawdown"] = display_df["Max Drawdown"].apply(lambda x: f"{x*100:.1f}%")
                    display_df["Last Price"] = display_df["Last Price"].apply(lambda x: f"¥{x:,.0f}")

                    st.dataframe(display_df, use_container_width=True)
            else:
                st.warning("現在、有効なシグナルが出ている銘柄はありませんでした。")


def render_realtime_monitoring_tab(ticker_group, selected_market, custom_tickers):
    """
    リアルタイム監視タブのレンダリングロジック
    """
    import time

    import pandas as pd

    from src.constants import MARKETS
    from src.streaming_pipeline import get_streaming_pipeline

    st.header("📡 リアルタイム市場監視")
    st.write("市場データをリアルタイムで監視し、AIが継続的に予測を行います。")

    # 監視対象の選択
    if ticker_group == "カスタム入力":
        target_tickers = custom_tickers
    else:
        target_tickers = MARKETS[selected_market][:10]  # パフォーマンスのため上位10銘柄に制限

    st.info(f"監視対象: {len(target_tickers)} 銘柄 ({', '.join(target_tickers[:5])}...)")

    # コントロール
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("監視を開始", type="primary", key="start_monitoring")
    with col2:
        stop_btn = st.button("監視を停止", key="stop_monitoring")

    # 状態管理
    if "monitoring_active" not in st.session_state:
        st.session_state.monitoring_active = False

    if start_btn:
        st.session_state.monitoring_active = True
    if stop_btn:
        st.session_state.monitoring_active = False

    # 監視ループ
    if st.session_state.monitoring_active:
        st.success("監視中... (停止するには「監視を停止」を押してください)")

        # パイプライン初期化（初回のみ）
        pipeline = get_streaming_pipeline()
        if not pipeline.is_initialized:
            with st.spinner("AIパイプラインを初期化中..."):
                pipeline.initialize(target_tickers)

        # データローダー初期化
        # 注意: Streamlitの再実行モデルとスレッドの相性が悪いため、
        # ここでは簡易的にループ内でデータ取得を行う

        placeholder = st.empty()
        log_placeholder = st.empty()

        logs = []

        try:
            # 簡易ループ (実際にはバックグラウンドスレッド推奨だが、UI更新のためメインスレッドで実行)
            # Streamlitのrerunを使うため、whileループは1回で抜ける構造にするか、
            # あるいはst.empty()を更新し続けるならsleepを使う

            # ここではシンプルに1回実行してsleepしてrerunするパターン

            # 1. データ取得（擬似リアルタイム）
            from src.data_loader import fetch_stock_data

            # 最新データ取得
            current_data = fetch_stock_data(target_tickers, period="1d", interval="1m")

            # パイプライン更新
            results = pipeline.process_update(current_data)

            # UI更新
            with placeholder.container():
                # 予測結果のサマリー表示
                st.subheader(f"最新状況 ({pd.Timestamp.now().strftime('%H:%M:%S')})")

                # 注目すべきシグナル
                signals = []
                for ticker, res in results.items():
                    if res["final_signal"] != "HOLD":
                        # 信頼度取得（安全策）
                        conf = 0.0
                        if "LightGBM" in res["details"]:
                            conf = res["details"]["LightGBM"]["confidence"]

                        signals.append(
                            {
                                "Ticker": ticker,
                                "Signal": res["final_signal"],
                                "Confidence": f"{conf:.2f}",
                                "Price": current_data[ticker]["Close"].iloc[-1],
                            }
                        )

                if signals:
                    st.warning(f"⚠️ {len(signals)}件のシグナルを検知！")
                    st.dataframe(pd.DataFrame(signals))
                else:
                    st.info("現在、強いシグナルは検出されていません。")

                # 全銘柄の状況
                with st.expander("全銘柄ステータス"):
                    status_data = []
                    for ticker, res in results.items():
                        status_data.append(
                            {
                                "Ticker": ticker,
                                "Signal": res["final_signal"],
                                "Buy Votes": res["buy_votes"],
                                "Sell Votes": res["sell_votes"],
                            }
                        )
                    st.dataframe(pd.DataFrame(status_data))

            # 自動リロード
            time.sleep(10)  # 10秒待機
            st.rerun()

        except Exception as e:
            st.error(f"監視中にエラーが発生しました: {e}")
            st.session_state.monitoring_active = False


def render_xai_section(model, X_test, ticker_name):
    """
    XAI（説明可能AI）セクションのレンダリング

    Args:
        model: 学習済みモデル
        X_test: テストデータ（特徴量）
        ticker_name: 銘柄名
    """
    import streamlit as st

    from src.xai import get_xai_manager

    st.markdown("---")
    st.header(f"🔬 AI予測の根拠分析 (XAI) - {ticker_name}")
    st.write("AIがなぜそのような予測をしたのか、SHAP値を用いて解析します。")

    if model is None or X_test is None or X_test.empty:
        st.warning("モデルまたはデータが不足しているため、分析を実行できません。")
        return

    xai = get_xai_manager()

    with st.spinner("AIの思考プロセスを解析中..."):
        # SHAP値計算
        # 計算コスト削減のため、直近のデータ（例えば最新100件）のみを使用
        X_sample = X_test.tail(100)
        shap_values = xai.get_shap_values(model, X_sample)

        if shap_values is not None:
            col1, col2 = st.columns(2)

            with col1:
                # 全体的な特徴量重要度
                fig_imp = xai.plot_feature_importance(shap_values, X_sample)
                st.plotly_chart(fig_imp, use_container_width=True)
                st.caption("モデル全体として、どの指標を重視しているかを示します。")

            with col2:
                # 直近の予測理由
                fig_reason = xai.plot_prediction_reason(shap_values, X_sample, row_index=-1)
                st.plotly_chart(fig_reason, use_container_width=True)
                st.caption("最新の予測において、どの指標がプラス/マイナスに働いたかを示します。")

            # 自然言語による説明
            explanation = xai.generate_explanation_text(shap_values, X_sample, row_index=-1)
            st.info(explanation)

        else:
            st.error("SHAP値の計算に失敗しました。このモデルタイプはサポートされていない可能性があります。")


def render_integrated_signal(df, ticker, ai_prediction=0.0):
    """
    統合シグナル分析結果を表示する
    """
    from src.integrated_signals import get_signal_integrator

    st.subheader("🧩 AI総合判断 (Integrated Signal)")

    integrator = get_signal_integrator()
    result = integrator.analyze(df, ticker, ai_prediction)

    # メインシグナル表示
    col1, col2 = st.columns([1, 2])

    with col1:
        action = result["action"]
        score = result["score"]
        confidence = result["confidence"]

        color = "green" if action == "BUY" else "red" if action == "SELL" else "gray"
        icon = "🚀" if action == "BUY" else "🔻" if action == "SELL" else "⏸️"
        action_jp = "買い" if action == "BUY" else "売り" if action == "SELL" else "様子見"

        st.markdown(
            f"""
        <div style="text-align: center; padding: 20px; background-color: rgba(255,255,255,0.05); border-radius: 10px; border: 2px solid {color};">
            <h2 style="color: {color}; margin: 0;">{icon} {action_jp}</h2>
            <p style="margin: 5px 0;">確信度: {confidence:.0%}</p>
            <p style="font-size: 0.8em; color: #888;">総合スコア: {score:.2f}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("**🔍 判断理由:**")
        for reason in result["reasons"]:
            st.markdown(f"- {reason}")

        if not result["reasons"]:
            st.info("特筆すべき判断材料はありません。")

    # 詳細スコア内訳
    with st.expander("📊 スコア内訳詳細"):
        details = result["details"]

        # バーチャートで表示
        fig = go.Figure()

        categories = ["テクニカル", "AI予測", "長期トレンド", "ニュース感情"]
        values = [details.get("technical", 0), details.get("ai", 0), details.get("mtf", 0), details.get("sentiment", 0)]

        colors = ["green" if v > 0 else "red" for v in values]

        fig.add_trace(
            go.Bar(x=categories, y=values, marker_color=colors, text=[f"{v:.2f}" for v in values], textposition="auto")
        )

        fig.update_layout(
            title="要素別貢献度 (-1.0 to 1.0)", yaxis_range=[-1.1, 1.1], height=300, margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)
