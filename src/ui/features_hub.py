"""新機能ハブUI

決算カレンダー、センチメント、セクターローテーション、税金最適化のUI
"""

import streamlit as st
import pandas as pd


def render_features_hub():
    """新機能ハブをレンダリング"""
    st.markdown("### 🚀 新機能センター")

    tabs = st.tabs(
        [
            "📅 決算カレンダー",
            "📊 市場センチメント",
            "🔄 セクターローテーション",
            "💰 税金最適化",
            "🌱 配当再投資",
        ]
    )

    with tabs[0]:
        render_earnings_calendar()

    with tabs[1]:
        render_sentiment_indicators()

    with tabs[2]:
        render_sector_rotation()

    with tabs[3]:
        render_tax_optimizer()

    with tabs[4]:
        render_drip_manager()


def render_earnings_calendar():
    """決算カレンダーUI"""
    st.markdown("#### 📅 決算カレンダー")
    st.caption("決算発表前のポジション調整でサプライズリスクを回避")

    try:
        from src.features.earnings_calendar import get_earnings_calendar
        from src.paper_trader import PaperTrader

        cal = get_earnings_calendar()
        pt = PaperTrader()
        positions = pt.get_positions()

        if not positions:
            st.info("ポジションがありません")
            return

        tickers = list(positions.keys())

        with st.spinner("決算データを取得中..."):
            upcoming = cal.get_upcoming_earnings(tickers)

        if upcoming.empty:
            st.success("✅ 今後14日間に決算発表のある銀柄はありません")
        else:
            # リスクレベルで色分け
            def color_risk(val):
                colors = {
                    "CRITICAL": "background-color: #ef4444; color: white",
                    "HIGH": "background-color: #f59e0b; color: white",
                    "MEDIUM": "background-color: #3b82f6; color: white",
                    "LOW": "background-color: #22c55e; color: white",
                }
                return colors.get(val, "")

            st.dataframe(
                upcoming.style.applymap(color_risk, subset=["risk_level"]),
                use_container_width=True,
            )

            # 推奨アクション
            critical = upcoming[upcoming["risk_level"] == "CRITICAL"]
            if not critical.empty:
                st.warning(f"⚠️ {len(critical)}銀柄が決算直前です。ポジション縮小を検討してください。")

                for _, row in critical.iterrows():
                    ticker = row["ticker"]
                    days = row["days_until"]
                    st.markdown(f"- **{ticker}**: {days}日後に決算")

    except Exception as e:
        st.error(f"エラー: {e}")


def render_sentiment_indicators():
    """市場センチメントUI"""
    st.markdown("#### 📊 市場センチメント")
    st.caption("Fear & Greed Index, VIX, Put/Call Ratioの統合分析")

    try:
        from src.features.sentiment_indicators import get_sentiment_indicators

        indicators = get_sentiment_indicators()

        with st.spinner("センチメントデータを取得中..."):
            rec = indicators.get_trading_recommendation()

        data = rec["sentiment_data"]

        # メトリクス表示
        cols = st.columns(4)

        with cols[0]:
            fg = data.get("fear_greed_index")
            st.metric(
                "Fear & Greed",
                f"{fg:.0f}" if fg else "N/A",
                data.get("fear_greed_label", ""),
            )

        with cols[1]:
            vix = data.get("vix_current")
            st.metric(
                "VIX",
                f"{vix:.2f}" if vix else "N/A",
                f"{data.get('vix_percentile', 0):.0f}パーセンタイル" if vix else "",
            )

        with cols[2]:
            pcr = data.get("put_call_ratio")
            st.metric(
                "Put/Call Ratio",
                f"{pcr:.2f}" if pcr else "N/A",
            )

        with cols[3]:
            sentiment = data.get("overall_sentiment", "Neutral")
            st.metric(
                "統合センチメント",
                sentiment,
            )

        # 推奨アクション
        recommendation = rec["recommendation"]
        action = recommendation["action"]
        reason = recommendation["reason"]
        multiplier = recommendation["position_multiplier"]

        st.markdown("---")
        st.markdown("**🎯 推奨アクション**")

        if action == "BUY_AGGRESSIVE":
            st.success(f"🟢 {action}: {reason}")
        elif action == "BUY":
            st.info(f"🟢 {action}: {reason}")
        elif action == "HOLD":
            st.info(f"⚪ {action}: {reason}")
        elif action == "REDUCE":
            st.warning(f"🟡 {action}: {reason}")
        else:
            st.error(f"🔴 {action}: {reason}")

        st.caption(f"ポジションサイズ係数: {multiplier:.1f}x")

    except Exception as e:
        st.error(f"エラー: {e}")


def render_sector_rotation():
    """セクターローテーションUI"""
    st.markdown("#### 🔄 セクターローテーション")
    st.caption("景気サイクルに応じた最適セクターの提案")

    try:
        from src.features.sector_rotation import get_sector_rotation

        market = st.selectbox("市場選択", ["US", "JP"], index=0)
        sr = get_sector_rotation(market=market)

        with st.spinner("セクターデータを分析中..."):
            recs = sr.get_recommendations()

        # 景気サイクル
        col1, col2 = st.columns(2)
        with col1:
            st.metric("現在の景気サイクル", recs["current_cycle"])
        with col2:
            st.metric("信頼度", f"{recs['cycle_confidence']:.0%}")

        st.info(recs["cycle_description"])

        # トップセクター
        st.markdown("**🏆 推奨セクター TOP3**")
        for i, sec in enumerate(recs["top_sectors"], 1):
            st.markdown(
                f"{i}. **{sec['sector']}** ({sec['etf']}) "
                f"- モメンタム: {sec['momentum_score']:.1f} "
                f"{'⭐' if sec['cycle_recommended'] else ''}"
            )

        # 回避セクター
        st.markdown("**⚠️ 回避推奨セクター**")
        for sec in recs["avoid_sectors"]:
            st.markdown(f"- {sec['sector']} ({sec['etf']}) " f"- モメンタム: {sec['momentum_score']:.1f}")

    except Exception as e:
        st.error(f"エラー: {e}")


def render_tax_optimizer():
    """税金最適化UI"""
    st.markdown("#### 💰 Tax Loss Harvesting")
    st.caption("年末に向けた損益通算シミュレーション")

    try:
        from src.features.tax_optimizer import get_tax_optimizer, HarvestingStrategy
        from src.paper_trader import PaperTrader

        # 戦略選択
        strategy_name = st.selectbox(
            "ハーベスティング戦略",
            ["バランス", "積極的", "保守的"],
            index=0,
        )
        strategy_map = {
            "バランス": HarvestingStrategy.BALANCED,
            "積極的": HarvestingStrategy.AGGRESSIVE,
            "保守的": HarvestingStrategy.CONSERVATIVE,
        }

        optimizer = get_tax_optimizer(strategy=strategy_map[strategy_name])
        pt = PaperTrader()
        positions = pt.get_positions()

        if not positions:
            st.info("ポジションがありません")
            return

        # ポジションデータを整形
        positions_list = []
        for ticker, pos in positions.items():
            positions_list.append(
                {
                    "ticker": ticker,
                    "quantity": pos.get("quantity", 0),
                    "avg_price": pos.get("avg_price", 0),
                    "current_price": pos.get("current_price", pos.get("avg_price", 0)),
                }
            )

        realized_gains = st.number_input(
            "年初来の実現益 (¥)",
            value=0,
            step=10000,
        )

        if st.button("🔍 分析実行"):
            with st.spinner("分析中..."):
                analysis = optimizer.analyze_portfolio(positions_list, realized_gains)

            summary = analysis["summary"]

            # サマリー
            cols = st.columns(4)
            with cols[0]:
                st.metric("未実現利益", f"¥{summary['unrealized_gains']:,.0f}")
            with cols[1]:
                st.metric("未実現損失", f"¥{summary['unrealized_losses']:,.0f}")
            with cols[2]:
                st.metric("推定税金", f"¥{summary['estimated_tax']:,.0f}")
            with cols[3]:
                st.metric("税金削減可能額", f"¥{summary['potential_tax_savings']:,.0f}")

            # 推奨アクション
            recs = analysis["recommendations"]
            if recs:
                st.markdown("**🎯 推奨アクション**")
                for rec in recs:
                    action_icon = "🔴" if rec["action"] == "HARVEST_LOSS" else "🟢"
                    st.markdown(
                        f"{action_icon} **{rec['ticker']}**: {rec['action']} "
                        f"(税金影響: ¥{rec['tax_impact']:,.0f})\n"
                        f"   - {rec['reason']}"
                    )
                    if rec.get("replacement_ticker"):
                        st.caption(f"   → 代替: {rec['replacement_ticker']}")
            else:
                st.success("✅ 現時点でハーベスティング推奨はありません")

    except Exception as e:
        st.error(f"エラー: {e}")


def render_drip_manager():
    """配当再投資UI"""
    st.markdown("#### 🌱 配当再投資 (DRIP)")
    st.caption("配当受領時に自動で再投資")

    try:
        from src.features.drip import get_drip_manager, DRIPStrategy
        from src.paper_trader import PaperTrader

        # 戦略選択
        strategy_name = st.selectbox(
            "再投資戦略",
            ["同じ銀柄", "指定銀柄", "分散投資", "現金蓄積"],
            index=0,
        )
        strategy_map = {
            "同じ銀柄": DRIPStrategy.SAME_STOCK,
            "指定銀柄": DRIPStrategy.TARGET_STOCK,
            "分散投資": DRIPStrategy.DIVERSIFIED,
            "現金蓄積": DRIPStrategy.ACCUMULATE,
        }

        drip = get_drip_manager(strategy=strategy_map[strategy_name])
        pt = PaperTrader()
        positions = pt.get_positions()

        if not positions:
            st.info("ポジションがありません")
            return

        # ポートフォリオを構築
        portfolio = {ticker: pos.get("quantity", 0) for ticker, pos in positions.items()}

        with st.spinner("配当データを取得中..."):
            summary = drip.get_drip_summary(portfolio)

        # サマリー
        st.metric(
            "90日間の予想配当",
            f"¥{summary['total_expected_dividend_90d']:,.0f}",
        )

        # 配当スケジュール
        schedule = summary["dividend_schedule"]
        if schedule:
            st.markdown("**📅 配当スケジュール**")
            df = pd.DataFrame(schedule)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("今後90日間に配当予定の銀柄はありません")

    except Exception as e:
        st.error(f"エラー: {e}")
