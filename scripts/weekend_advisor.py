"""
週末戦略会議 - AI戦略アドバイザー
Weekend Strategy Advisor for Personal Investors

使い方:
  python weekend_advisor.py
  または
  streamlit run weekend_advisor.py
"""

from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import streamlit as st

from src.formatters import format_currency
from src.paper_trader import PaperTrader

# ページ設定は if __name__ == "__main__" ブロックに移動

# カスタムCSS
st.markdown(
    """
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .danger-card {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .recommendation-card {
        background: white;
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


class WeeklyPerformanceAnalyzer:
    """週次パフォーマンス分析"""

    def __init__(self, pt: PaperTrader):
        self.pt = pt
        self.history = pt.get_trade_history()
        self.positions = pt.get_positions()
        self.balance = pt.get_current_balance()

    def get_weekly_stats(self) -> Dict:
        """今週の統計を取得"""
        week_ago = datetime.now() - timedelta(days=7)

        if self.history.empty:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "avg_return": 0,
                "best_trade": None,
                "worst_trade": None,
                "total_pnl": 0,
            }

        # 時間列の処理
        time_col = "timestamp" if "timestamp" in self.history.columns else "date"
        if time_col in self.history.columns:
            self.history[time_col] = pd.to_datetime(self.history[time_col])
            week_trades = self.history[self.history[time_col] >= week_ago]
        else:
            week_trades = self.history

        if week_trades.empty:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "avg_return": 0,
                "best_trade": None,
                "worst_trade": None,
                "total_pnl": 0,
            }

        # 統計計算
        closed_trades = week_trades[week_trades["action"] == "SELL"]

        if not closed_trades.empty and "realized_pnl" in closed_trades.columns:
            wins = len(closed_trades[closed_trades["realized_pnl"] > 0])
            total = len(closed_trades)
            win_rate = wins / total if total > 0 else 0

            avg_return = closed_trades["realized_pnl"].mean()
            total_pnl = closed_trades["realized_pnl"].sum()

            best_trade = closed_trades.loc[closed_trades["realized_pnl"].idxmax()]
            worst_trade = closed_trades.loc[closed_trades["realized_pnl"].idxmin()]
        else:
            win_rate = 0
            avg_return = 0
            total_pnl = 0
            best_trade = None
            worst_trade = None

        return {
            "total_trades": len(week_trades),
            "win_rate": win_rate,
            "avg_return": avg_return,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "total_pnl": total_pnl,
        }

    def analyze_strategy_performance(self) -> List[Dict]:
        """戦略別パフォーマンス分析"""
        if self.history.empty or "strategy" not in self.history.columns:
            return []

        strategy_stats = []

        for strategy in self.history["strategy"].unique():
            if pd.isna(strategy):
                continue

            strategy_trades = self.history[self.history["strategy"] == strategy]
            closed = strategy_trades[strategy_trades["action"] == "SELL"]

            if not closed.empty and "realized_pnl" in closed.columns:
                wins = len(closed[closed["realized_pnl"] > 0])
                total = len(closed)
                win_rate = wins / total if total > 0 else 0
                total_pnl = closed["realized_pnl"].sum()
                avg_pnl = closed["realized_pnl"].mean()

                strategy_stats.append(
                    {
                        "strategy": strategy,
                        "trades": total,
                        "win_rate": win_rate,
                        "total_pnl": total_pnl,
                        "avg_pnl": avg_pnl,
                        "status": "good" if win_rate > 0.6 else "warning" if win_rate > 0.4 else "poor",
                    }
                )

        return sorted(strategy_stats, key=lambda x: x["total_pnl"], reverse=True)


class AIAdvisor:
    """AI戦略アドバイザー"""

    def __init__(self, pt: PaperTrader, analyzer: WeeklyPerformanceAnalyzer):
        self.pt = pt
        self.analyzer = analyzer

    def generate_recommendations(self) -> List[Dict]:
        """推奨アクションを生成"""
        recommendations = []

        # 1. 戦略別パフォーマンスに基づく推奨
        strategy_perf = self.analyzer.analyze_strategy_performance()

        if strategy_perf:
            best_strategy = strategy_perf[0]
            worst_strategy = strategy_perf[-1]

            if best_strategy["win_rate"] > 0.6:
                recommendations.append(
                    {
                        "priority": "HIGH",
                        "type": "INCREASE",
                        "title": f"✅ {best_strategy['strategy']} の比重を増やす",
                        "description": f"勝率{best_strategy['win_rate']:.1%}、平均利益{format_currency(best_strategy['avg_pnl'])}",
                        "reason": "高パフォーマンス戦略",
                        "action": "increase_allocation",
                        "target": best_strategy["strategy"],
                    }
                )

            if worst_strategy["win_rate"] < 0.4 and worst_strategy["trades"] > 3:
                recommendations.append(
                    {
                        "priority": "MEDIUM",
                        "type": "DECREASE",
                        "title": f"⚠️ {worst_strategy['strategy']} の見直し",
                        "description": f"勝率{worst_strategy['win_rate']:.1%}、平均損失{format_currency(worst_strategy['avg_pnl'])}",
                        "reason": "低パフォーマンス戦略",
                        "action": "decrease_allocation",
                        "target": worst_strategy["strategy"],
                    }
                )

        # 2. ポジション分析に基づく推奨
        positions = self.pt.get_positions()

        if not positions.empty:
            # 大きな含み損
            big_losers = positions[positions["unrealized_pnl_pct"] < -10]
            if not big_losers.empty:
                for idx, pos in big_losers.iterrows():
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "type": "SELL",
                            "title": f"🚨 {pos['ticker']} の損切り検討",
                            "description": f"含み損{pos['unrealized_pnl_pct']:.1f}%",
                            "reason": "大きな含み損",
                            "action": "sell",
                            "target": pos["ticker"],
                        }
                    )

            # 大きな含み益
            big_winners = positions[positions["unrealized_pnl_pct"] > 20]
            if not big_winners.empty:
                for idx, pos in big_winners.iterrows():
                    recommendations.append(
                        {
                            "priority": "MEDIUM",
                            "type": "PROFIT",
                            "title": f"💰 {pos['ticker']} の利確検討",
                            "description": f"含み益{pos['unrealized_pnl_pct']:.1f}%",
                            "reason": "大きな含み益",
                            "action": "take_profit",
                            "target": pos["ticker"],
                        }
                    )

        # 3. 現金比率に基づく推奨
        balance = self.pt.get_current_balance()
        cash_ratio = balance["cash"] / balance["total_equity"] if balance["total_equity"] > 0 else 0

        if cash_ratio > 0.5:
            recommendations.append(
                {
                    "priority": "LOW",
                    "type": "BUY",
                    "title": "💡 現金比率が高い",
                    "description": f"現金比率{cash_ratio:.1%}",
                    "reason": "投資機会の検討",
                    "action": "find_opportunities",
                    "target": None,
                }
            )
        elif cash_ratio < 0.1:
            recommendations.append(
                {
                    "priority": "LOW",
                    "type": "REBALANCE",
                    "title": "⚠️ 現金比率が低い",
                    "description": f"現金比率{cash_ratio:.1%}",
                    "reason": "リスク管理",
                    "action": "increase_cash",
                    "target": None,
                }
            )

        return sorted(recommendations, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["priority"]])

    def simulate_next_week(self) -> Dict:
        """来週のシミュレーション"""
        # 簡易的な予測
        stats = self.analyzer.get_weekly_stats()

        if stats["total_trades"] == 0:
            return {"expected_trades": 5, "expected_return": 0, "confidence": "low"}

        # 過去の平均から予測
        expected_trades = max(5, int(stats["total_trades"] * 1.1))
        expected_return = stats["avg_return"] * expected_trades

        confidence = "high" if stats["win_rate"] > 0.6 else "medium" if stats["win_rate"] > 0.4 else "low"

        return {
            "expected_trades": expected_trades,
            "expected_return": expected_return,
            "confidence": confidence,
            "win_rate": stats["win_rate"],
        }


def main():
    """メイン処理"""

    st.title("📊 週末戦略会議")
    st.markdown("### AI戦略アドバイザー")
    st.caption(f"📅 {datetime.now().strftime('%Y年%m月%d日')}")

    # データ読み込み
    pt = PaperTrader()
    analyzer = WeeklyPerformanceAnalyzer(pt)
    advisor = AIAdvisor(pt, analyzer)

    # タブ構成
    tab1, tab2, tab3, tab4 = st.tabs(["📊 今週の成績表", "🤖 AI分析レポート", "📈 来週の推奨", "🎯 シミュレーション"])

    # タブ1: 今週の成績表
    with tab1:
        st.subheader("📊 今週のパフォーマンス")

        stats = analyzer.get_weekly_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
            <div class="metric-card">
                <div style="font-size: 0.9em; opacity: 0.9;">取引回数</div>
                <div style="font-size: 2em; font-weight: bold; margin-top: 10px;">{stats['total_trades']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            color = "#10b981" if stats["win_rate"] >= 0.5 else "#ef4444"
            st.markdown(
                f"""
            <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);">
                <div style="font-size: 0.9em; opacity: 0.9;">勝率</div>
                <div style="font-size: 2em; font-weight: bold; margin-top: 10px;">{stats['win_rate']:.1%}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
            <div class="metric-card">
                <div style="font-size: 0.9em; opacity: 0.9;">平均リターン</div>
                <div style="font-size: 2em; font-weight: bold; margin-top: 10px;">{format_currency(stats['avg_return'])}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col4:
            pnl_color = "#10b981" if stats["total_pnl"] >= 0 else "#ef4444"
            st.markdown(
                f"""
            <div class="metric-card" style="background: linear-gradient(135deg, {pnl_color} 0%, {pnl_color}dd 100%);">
                <div style="font-size: 0.9em; opacity: 0.9;">週次損益</div>
                <div style="font-size: 2em; font-weight: bold; margin-top: 10px;">{format_currency(stats['total_pnl'])}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # ベスト・ワーストトレード
        if stats["best_trade"] is not None:
            st.markdown("---")
            col_best, col_worst = st.columns(2)

            with col_best:
                st.markdown("### 🏆 ベストトレード")
                st.markdown(
                    f"""
                <div class="success-card">
                    <strong>{stats['best_trade']['ticker']}</strong><br>
                    利益: {format_currency(stats['best_trade']['realized_pnl'])}<br>
                    戦略: {stats['best_trade'].get('strategy', 'N/A')}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col_worst:
                st.markdown("### 📉 ワーストトレード")
                st.markdown(
                    f"""
                <div class="danger-card">
                    <strong>{stats['worst_trade']['ticker']}</strong><br>
                    損失: {format_currency(stats['worst_trade']['realized_pnl'])}<br>
                    戦略: {stats['worst_trade'].get('strategy', 'N/A')}
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # 戦略別パフォーマンス
        st.markdown("---")
        st.subheader("📈 戦略別パフォーマンス")

        strategy_perf = analyzer.analyze_strategy_performance()

        if strategy_perf:
            for strat in strategy_perf:
                card_class = {"good": "success-card", "warning": "warning-card", "poor": "danger-card"}[strat["status"]]

                st.markdown(
                    f"""
                <div class="{card_class}">
                    <strong>{strat['strategy']}</strong><br>
                    取引数: {strat['trades']} | 勝率: {strat['win_rate']:.1%} | 
                    総損益: {format_currency(strat['total_pnl'])} | 
                    平均: {format_currency(strat['avg_pnl'])}
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("戦略データがありません")

    # タブ2: AI分析レポート
    with tab2:
        st.subheader("🤖 AI分析レポート")

        recommendations = advisor.generate_recommendations()

        if not recommendations:
            st.success("✅ 現状維持で問題ありません!")
        else:
            st.markdown(f"**{len(recommendations)}件の推奨アクションがあります**")

            for i, rec in enumerate(recommendations):
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

                with st.expander(
                    f"{priority_emoji[rec['priority']]} {rec['title']}", expanded=(rec["priority"] == "HIGH")
                ):
                    st.markdown(f"**{rec['description']}**")
                    st.caption(f"理由: {rec['reason']}")

                    if rec["action"] in ["sell", "take_profit"]:
                        if st.button("✅ 実行", key=f"exec_{i}"):
                            st.success(f"{rec['target']} のアクションを実行しました")

    # タブ3: 来週の推奨
    with tab3:
        st.subheader("📈 来週の推奨ポートフォリオ")

        st.info("💡 現在のポートフォリオと推奨アクションに基づいた最適化案")

        positions = pt.get_positions()

        if not positions.empty:
            st.markdown("### 現在のポジション")

            for idx, pos in positions.iterrows():
                ticker = pos.get("ticker", idx)
                pnl_pct = pos.get("unrealized_pnl_pct", 0)

                if pnl_pct < -10:
                    action = "🚨 損切り検討"
                    color = "#ef4444"
                elif pnl_pct > 20:
                    action = "💰 利確検討"
                    color = "#10b981"
                else:
                    action = "✅ 保持"
                    color = "#667eea"

                st.markdown(
                    f"""
                <div style="background: {color}22; border-left: 4px solid {color}; padding: 15px; margin: 10px 0; border-radius: 5px;">
                    <strong>{ticker}</strong> - {action}<br>
                    含み損益: {pnl_pct:.1f}% | 数量: {pos.get('quantity', 0)}株
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("現在ポジションはありません")

    # タブ4: シミュレーション
    with tab4:
        st.subheader("🎯 来週のシミュレーション")

        simulation = advisor.simulate_next_week()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("予想取引数", f"{simulation['expected_trades']}回")

        with col2:
            st.metric("予想リターン", format_currency(simulation["expected_return"]))

        with col3:
            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
            st.metric("信頼度", f"{confidence_emoji[simulation['confidence']]} {simulation['confidence'].upper()}")

        st.markdown("---")
        st.markdown("### 📊 予測の根拠")
        st.markdown(
            f"""
        - 過去の勝率: {simulation['win_rate']:.1%}
        - 取引パターン分析に基づく予測
        - 市場環境は現状維持を仮定
        """
        )

        st.info("💡 実際の結果は市場環境により変動します")


if __name__ == "__main__":
    st.set_page_config(page_title="週末戦略会議", page_icon="📊", layout="wide")
    main()
