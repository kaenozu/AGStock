import streamlit as st
import os

from src.ui.ai_chat import render_ai_chat
from src.ui.committee_ui import render_committee_ui
from src.ui.earnings_analyst import render_earnings_analyst  # Phase 28
from src.ui.news_analyst import render_news_analyst
from src.ui.risk_hedge_panel import render_risk_hedge_panel
from src.rag.filing_watcher import FilingWatcher
from src.data.feedback_store import FeedbackStore
from src.data.earnings_history import EarningsHistory
import pandas as pd
import plotly.express as px


def render_ai_hub():
    """Renders the consolidated AI Analyzer Hub"""
    st.header("🧠 AI Intelligence Center")
    st.caption("Access all AI-driven insights, committee debates, and automated market scanning from this central hub.")

    tabs = st.tabs(
        [
            "🏛️ Committee (投資委員会)",
            "📰 News (ニュース分析)",
            "💬 Chat (AI相談)",
            "📑 Earnings (決算分析)",
            "🛡️ Risk (リスク管理)",
            "📡 Filings (適時開示)",
            "📊 Sectors (セクター分析)",
            "⚖️ Governance (ガバナンス)",
        ]
    )

    with tabs[0]:
        render_committee_ui()

    with tabs[1]:
        render_news_analyst()

    with tabs[2]:
        render_ai_chat()

    with tabs[3]:
        render_earnings_analyst()

    with tabs[4]:
        # Portfolio context (mocked for now, normally would come from session state)
        portfolio_mock = {"equity": 1500000.0, "cash": 500000.0}
        # VIX (normally from market data)
        vix_mock = 22.4
        render_risk_hedge_panel(portfolio_mock, vix_mock)

    with tabs[5]:
        _render_filing_watcher_ui()

    with tabs[6]:
        render_sector_heatmap()

    with tabs[7]:
        render_executive_control()


def render_sector_heatmap():
    st.subheader("📊 セクター別決算スコア (Sector Heatmap)")
    st.caption("最近の決算分析結果をセクター別に集計し、市場の『波』を可視化します。")

    history = EarningsHistory().get_history(limit=100)
    if not history:
        st.info("データが不足しています。決算分析を実行してください。")
        return

    # データをDataFrameに変換
    data_list = []
    for item in history:
        analysis = item.get("analysis", {})
        data_list.append(
            {
                "ticker": item.get("ticker", "Unknown"),
                "score": analysis.get("score", 0),
                "sector": analysis.get("sector", "Unknown"),
                "industry": analysis.get("industry", "Unknown"),
                "timestamp": item.get("timestamp"),
            }
        )

    df = pd.DataFrame(data_list)

    if df["sector"].nunique() <= 1 and "Unknown" in df["sector"].unique():
        st.warning("セクター情報が含まれる分析データがまだありません。新しい決算分析を実行してください。")
        return

    # セクター別に集計
    sector_summary = df.groupby("sector").agg({"score": "mean", "ticker": "count"}).reset_index()
    sector_summary.columns = ["Sector", "Avg Score", "Count"]
    sector_summary = sector_summary.sort_values(by="Avg Score", ascending=False)

    # 可視化
    fig = px.bar(
        sector_summary,
        x="Sector",
        y="Avg Score",
        color="Avg Score",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        text="Count",
        labels={"Avg Score": "平均スコア", "Count": "銘柄数"},
        title="セクター別センチメント（直近の決算より）",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(sector_summary, use_container_width=True)

    st.markdown("---")
    render_past_decisions()


def render_past_decisions():
    st.subheader("🧠 AI自己学習：過去の判断と結果")
    st.caption("AIが自身の判断を振り返り、成功・失敗から学習している履歴です。")

    fs = FeedbackStore()
    recent_lessons = fs.get_lessons_for_ticker("%", limit=20)  # Get all recent outcomes

    if not recent_lessons:
        st.info("まだ評価済みの学習データがありません。判断から数日後に結果が自動更新されます。")
        return

    for lesson in recent_lessons:
        with st.expander(
            f"{lesson['timestamp'][:16]} | {lesson['ticker']} | {lesson['decision']} -> {lesson['outcome']}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**当時の価格:** ¥{lesson['initial_price']:,.1f}")
                st.write(f"**1週間後価格:** ¥{lesson['price_1w']:,.1f}" if lesson["price_1w"] else "未更新")
            with col2:
                ret = lesson["return_1w"]
                if ret is not None:
                    st.metric("収益率", f"{ret * 100:+.2f}%")
                else:
                    st.write("結果待ち...")

            st.write(f"**AIの論拠:** {lesson['rationale']}")
            if lesson["lesson_learned"]:
                st.info(f"💡 **学習した教訓:** {lesson['lesson_learned']}")
            else:
                if lesson["outcome"] == "FAILURE":
                    st.warning("このケースは失敗として学習モデルにフィードバックされました。")
                elif lesson["outcome"] == "SUCCESS":
                    st.success("このケースは成功パターンとして学習モデルに強化されました。")


def _render_filing_watcher_ui():
    st.subheader("📡 自動適時開示ウォッチ")
    st.markdown("PCを起動している間、特定のディレクトリを監視し、新しい決算PDFを自動で分析します。")

    col1, col2 = st.columns(2)
    with col1:
        watch_dir = st.text_input("監視ディレクトリ", value="./data/new_filings")
    with col2:
        st.slider("確認間隔(秒)", 10, 300, 60)

    if "filing_watcher_running" not in st.session_state:
        st.session_state.filing_watcher_running = False

    if st.session_state.filing_watcher_running:
        if st.button("🔴 監視を停止", type="secondary"):
            st.session_state.filing_watcher_running = False
            st.rerun()
        st.success("👀 監視実行中... ディレクトリにPDFを入れると自動で分析されます。")
    else:
        if st.button("🟢 監視を開始", type="primary"):
            st.session_state.filing_watcher_running = True
            st.rerun()
        st.info(
            "監視を開始すると、バックグラウンドでのチェックが有効になります（現在の実装ではこのタブを表示している間、または明示的なトリガーで実行されます）。"
        )

    # 手動スキャンの実行ボタン
    if st.button("🔄 今すぐスキャンを実行"):
        watcher = FilingWatcher(watch_dir=watch_dir)
        with st.spinner("スキャン中..."):
            watcher.scan_and_process()
        st.success("スキャン完了。新しいファイルがあれば分析と通知が行われました。")


def render_executive_control():
    """Renders the AI Governance / Executive dashboard."""
    st.subheader("⚖️ 自律型AIガバナンス監視")
    st.caption("システムの『脳』の健康状態と、現在の市場適応戦略を表示します。")

    # --- NIGHTWATCH SECTION ---
    st.write("## 🦁 グローバル・ナイトウォッチ (Morning Memo)")
    from src.data.us_market_monitor import USMarketMonitor
    from src.morning_strategy_memo import MorningStrategyMemo

    col_nw1, col_nw2 = st.columns([1, 2])
    with col_nw1:
        if st.button("🌙 昨晩の米国市場をスキャン", type="primary"):
            monitor = USMarketMonitor()
            night_data = monitor.fetch_nightwatch_data()
            st.session_state.night_data = night_data

            memo_gen = MorningStrategyMemo()
            st.session_state.morning_memo = memo_gen.generate_memo(night_data)

        if "night_data" in st.session_state:
            st.write("### 市場データ概略")
            for k, v in st.session_state.night_data.items():
                if isinstance(v, dict):
                    st.write(f"- **{k}**: {v['value']:,.1f} ({v['change_pct']:+.1f}%)")

    with col_nw2:
        if "morning_memo" in st.session_state:
            st.info(st.session_state.morning_memo)
        else:
            st.info("米国市場のスキャンを実行すると、今日の日本株戦略メモが生成されます。")

    st.divider()

    from src.agents.strategy_arena import StrategyArena
    from src.data.macro_loader import MacroLoader
    from src.execution.adaptive_rebalancer import AdaptiveRebalancer
    from src.utils.tax_optimizer import TaxOptimizer

    col1, col2 = st.columns([1, 1])

    with col1:
        # 1. AI Arena Status
        st.write("### 🧠 AIアリーナ：エージェント権限")
        arena = StrategyArena()
        data = arena.get_weights() or {
            "MarketAnalyst": 1.0,
            "RiskManager": 1.0,
            "MacroStrategist": 1.0,
        }

        # Display as metrics
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Market Analyst", f"x{data.get('MarketAnalyst', 1.0)}")
        m_col2.metric("Risk Manager", f"x{data.get('RiskManager', 1.0)}")
        m_col3.metric("Macro Strategist", f"x{data.get('MacroStrategist', 1.0)}")
        st.info("※ 過去の判断精度に基づき、投票権（ウェイト）が自動調整されています。")

    with col2:
        # 2. Macro State
        st.write("### 🌐 マクロ環境スコア")
        macro = MacroLoader()
        macro_data = macro.fetch_macro_data()
        score = macro_data.get("macro_score", 50)

        st.write(f"**現在の市場安定度:** {score:.1f}/100")
        st.progress(score / 100.0)

        if score < 40:
            st.warning("⚠️ 市場の混乱を検知。防御モードが有効です。")
        else:
            st.success("✅ 市場は概ね安定しています。")

    st.divider()

    # 1.5 Digital Twin Shadow Portfolios
    st.write("### 🧪 デジタルツイン・シミュレーション (もしもの軌跡)")
    from src.simulation.digital_twin import DigitalTwin

    twin = DigitalTwin()
    twin_perf = twin.get_twin_performance()

    perf_df = pd.DataFrame(
        [
            {"Portfolio": "現実 (Real)", "Performance": twin_perf["REAL_WORLD"]},
            {
                "Portfolio": "積極型 (Aggressive)",
                "Performance": twin_perf["AGGRESSIVE"],
            },
            {
                "Portfolio": "保守型 (Conservative)",
                "Performance": twin_perf["CONSERVATIVE"],
            },
        ]
    )

    fig_twin = px.bar(
        perf_df,
        x="Portfolio",
        y="Performance",
        color="Portfolio",
        title="意思決定モデル別・累積リターン比較",
        labels={"Performance": "基準値 (100=開始時)"},
    )
    st.plotly_chart(fig_twin, use_container_width=True)
    st.info("※ AIが現実とは異なる『性格』で運用している場合のシミュレーションと比較しています。")

    st.divider()

    # 3. Rebalance & Hedge Proposals
    st.write("### 🛡️ アクティブ適応戦略（リバランス・ヘッジ）")
    rebalancer = AdaptiveRebalancer()
    # Mock portfolio for UI display
    mock_p = {
        "positions": [
            {"ticker": "7203.T", "profit_pct": 5.2},
            {"ticker": "9984.T", "profit_pct": -3.1},
        ]
    }
    actions = rebalancer.run_rebalance_check(mock_p)

    if actions:
        for act in actions:
            with st.expander(f"【{act['action']}】{act.get('ticker', '全体')} - {act['reason'][:50]}..."):
                st.write(f"**詳細理由:** {act['reason']}")
                st.button(
                    f"実行を承認 ({act['ticker']})",
                    key=f"exec_{act['ticker']}_{act['action']}",
                )
    else:
        st.info("現在、推奨されるリバランス・ヘッジアクションはありません。")

    st.divider()

    # 4. Tax Optimization
    st.write("### 💰 節税・コスト最適化")
    tax_opt = TaxOptimizer()
    mock_p_tax = {
        "realized_gains_ytd": 200000,
        "positions": [{"ticker": "8035.T", "unrealized_pnl": -120000}],
    }
    tax_actions = tax_opt.find_harvesting_opportunities(mock_p_tax)

    if tax_actions:
        for t in tax_actions:
            st.info(
                f"💡 **損出しの提案**: {t['ticker']} で利益を相殺し、約 **¥{t['estimated_tax_savings']:,.0f}** の節税が可能です。"
            )
            st.button(f"節税実行 ({t['ticker']})", key=f"tax_{t['ticker']}")
    else:
        st.write("節税チャンスは現在ありません。")

    st.divider()

    # 5. Strategy Evolution
    st.write("### 🧬 戦略自己進化 (Strategy Evolution)")
    from src.evolution.strategy_generator import StrategyGenerator

    col_ev1, col_ev2 = st.columns([1, 1])
    with col_ev1:
        st.write("過去の失敗から新しい戦略を自動生成します。")
        if st.button("🚀 新戦略を生成・進化させる"):
            gen = StrategyGenerator()
            # In a real app, API key would be in config
            with st.spinner("Geminiが失敗を分析し、新しいコードを執筆中..."):
                gen.evolve_strategies()
            st.success("新しい戦略コードが `src/strategies/evolved/` に生成されました！")

    with col_ev2:
        st.write("#### 進化履歴")
        evolved_files = os.listdir("src/strategies/evolved") if os.path.exists("src/strategies/evolved") else []
        if evolved_files:
            for f in evolved_files[-5:]:  # Show last 5
                st.text(f"📄 {f}")
        else:
            st.info("まだ進化した戦略はありません。")

    st.divider()

    # 6. Live Shock Monitor
    st.write("### 📡 ライブ・ショックモニター (緊急防御)")
    from src.execution.news_shock_defense import NewsShockDefense

    defense = NewsShockDefense()

    # Mock some news for the monitor
    mock_news = [
        {"title": "日経平均株価、一時1000円超の下落", "published": "10分前"},
        {
            "title": "半導体セクターに強い買い、米テック株高を受け",
            "published": "30分前",
        },
    ]

    shock = defense.detect_shock_events(mock_news)
    if shock:
        st.error(f"🚨 **緊急警告検知**: {shock['title']}")
        st.warning(f"推奨アクション: {defense.get_emergency_action(shock)['action']}")
    else:
        st.success("✅ 現在、重大なニュースショックは検知されていません。平時運用を継続中。")

    with st.expander("監視キーワード一覧（ミリ秒反応対象）"):
        st.write(defense.CRITICAL_KEYWORDS)