"""
個人投資家向けシンプルダッシュボード

一目でわかる資産状況とリスク管理画面
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict

from src.paper_trader import PaperTrader

# Design System Imports (optional - will use local functions if not available)
try:
    from src.design_tokens import Colors, RISK_LEVELS
    from src.formatters import format_currency, format_percentage
except ImportError:
    pass  # デザインシステムがなくても動作する

# Design System Imports
from src.design_tokens import Colors, RISK_LEVELS
from src.formatters import format_currency, format_percentage
from src.benchmark_comparator import BenchmarkComparator


def calculate_simple_risk_score(positions: pd.DataFrame, total_equity: float) -> int:
    """
    シンプルなリスクスコアを計算（0-100）
    
    考慮要素:
    - ポジション集中度
    - 現金比率
    - ボラティリティ
    """
    if positions.empty:
        return 10  # ポジションなし = 低リスク
    
    risk_score = 0
    
    # 1. 最大ポジション比率（40点満点）
    max_position_ratio = (positions['market_value'].max() / total_equity) if total_equity > 0 else 0
    if max_position_ratio > 0.3:
        risk_score += 40
    elif max_position_ratio > 0.2:
        risk_score += 25
    elif max_position_ratio > 0.1:
        risk_score += 10
    
    # 2. ポジション数（20点満点）
    num_positions = len(positions)
    if num_positions == 1:
        risk_score += 20  # 1銘柄のみ = 高リスク
    elif num_positions <= 3:
        risk_score += 15
    elif num_positions <= 5:
        risk_score += 5
    
    # 3. 投資比率（40点満点）
    cash_ratio = 1 - (positions['market_value'].sum() / total_equity) if total_equity > 0 else 1
    if cash_ratio < 0.1:
        risk_score += 40  # 現金10%未満 = 高リスク
    elif cash_ratio < 0.2:
        risk_score += 25
    elif cash_ratio < 0.3:
        risk_score += 10
    
    return min(risk_score, 100)


def get_risk_message(risk_score: int) -> tuple[str, str, str]:
    """
    リスクスコアに応じたメッセージを返す
    
    Returns:
        (emoji, level, message)
    """
    if risk_score < 30:
        return "🟢", "低い（安全）", "✅ リスク管理が適切です"
    elif risk_score < 70:
        return "🟡", "中程度", "⚠️ バランスに注意しましょう"
    else:
        return "🔴", "高い（注意！）", "🚨 リスク調整を推奨します"


def format_currency_jp(amount: float) -> str:
    """
    日本円を万円・億円形式で表示
    
    Args:
        amount: 金額（円）
        
    Returns:
        フォーマットされた文字列
    """
    if amount >= 100000000:  # 1億以上
        return f"¥{amount/100000000:.2f}億"
    elif amount >= 10000:  # 1万以上
        return f"¥{amount/10000:.1f}万"
    else:
        return f"¥{amount:,.0f}"


def get_trend_indicator(value: float) -> tuple[str, str]:
    """
    値に基づいてトレンドインジケーターを返す
    
    Args:
        value: 損益などの値
        
    Returns:
        (emoji, color)
    """
    if value > 0:
        return "📈", "green"
    elif value < 0:
        return "📉", "red"
    else:
        return "➡️", "gray"


def create_simple_dashboard():
    """シンプルダッシュボードを表示"""
    
    # カスタムCSS
    st.markdown("""
    <style>
    /* メトリクスのスタイル改善 */
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* ボタンのホバー効果 */
    .stButton button {
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,217,255,0.3);
    }
    
    /* dividerのスタイル */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid rgba(0,217,255,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("💼 マイポートフォリオ")
    
    # データ取得
    pt = PaperTrader()
    balance = pt.get_current_balance()
    positions = pt.get_positions()
    history = pt.get_trade_history()
    equity_history = pt.get_equity_history()
    
    total_equity = balance['total_equity']
    cash = balance['cash']
    invested = balance['invested_amount']
    unrealized_pnl = balance['unrealized_pnl']

    # 日次損益計算
    if len(equity_history) >= 2:
        today_equity = equity_history.iloc[-1]['total_equity']
        yesterday_equity = equity_history.iloc[-2]['total_equity'] if len(equity_history) > 1 else today_equity
        daily_pnl = today_equity - yesterday_equity
        daily_change_pct = (daily_pnl / yesterday_equity) if yesterday_equity > 0 else 0
    else:
        daily_pnl = 0
        daily_change_pct = 0
    
    # 月次損益計算
    one_month_ago = datetime.now() - timedelta(days=30)
    monthly_history = equity_history[equity_history['date'] >= one_month_ago]
    if len(monthly_history) >= 2:
        monthly_start = monthly_history.iloc[0]['total_equity']
        monthly_pnl = total_equity - monthly_start
    else:
        monthly_pnl = 0
    
    # 勝率計算
    if not history.empty:
        # realized_pnlカラムが存在するかチェック（後方互換性）
        if 'realized_pnl' in history.columns:
            closed_trades = history[history['realized_pnl'] != 0]
            if len(closed_trades) > 0:
                wins = len(closed_trades[closed_trades['realized_pnl'] > 0])
                win_rate = wins / len(closed_trades)
            else:
                win_rate = 0
        else:
            # 古いDBスキーマの場合は勝率0
            win_rate = 0
    else:
        win_rate = 0
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 0. AI Command Center (AI指令室)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("🤖 AI Command Center")
    ai_col1, ai_col2 = st.columns([2, 1])

    with ai_col1:
        # Latest Committee Decision (Simulation)
        # In a real scenario, this would fetch from a database or a shared state
        st.info("💡 **AI委員会からの最新メッセージ**")
        st.markdown("""
        > "現在の市場は**強気(Bullish)**傾向ですが、ボラティリティの上昇に注意が必要です。
        > ポートフォリオの現金比率を30%以上に保つことを推奨します。"
        > *(Investment Committee, 10 mins ago)*
        """)

    with ai_col2:
        # Quick Launch
        st.write("**クイックアクセス**")
        if st.button("💬 AIに質問する (Chat)", use_container_width=True, type="primary"):
             # Switch to generic chat
             st.session_state["chat_target_ticker"] = None
             # st.query_params["tab"] = "chat" # Removed due to compatibility issue
             st.info("「💬 AIチャット」タブへ移動してください ↗")

    st.divider()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 重要指標（4列）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 総資産", 
            value=format_currency_jp(total_equity),
            delta=f"{daily_change_pct:+.2%}"
        )
    
    with col2:
        trend_emoji, trend_color = get_trend_indicator(daily_pnl)
        st.metric(
            label="📊 今日の損益", 
            value=format_currency_jp(abs(daily_pnl)) if daily_pnl != 0 else "¥0",
            delta=None
        )
        st.markdown(f":{trend_color}[{trend_emoji} トレンド]")
    
    with col3:
        monthly_trend_emoji, monthly_trend_color = get_trend_indicator(monthly_pnl)
        st.metric(
            label="📅 今月の損益", 
            value=format_currency_jp(abs(monthly_pnl)) if monthly_pnl != 0 else "¥0",
            delta=None
        )
        st.markdown(f":{monthly_trend_color}[{monthly_trend_emoji} トレンド]")
    
    with col4:
        st.metric(
            label="🎯 勝率",
            value=f"{win_rate:.0%}",
            delta=None
        )
    
    st.divider()
    
    # クイックアクション
    st.subheader("⚡ クイックアクション")
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("📊 市場スキャン", use_container_width=True, type="secondary"):
            st.info("市場スキャンタブに移動してください")
    
    with action_col2:
        if st.button("💼 ポートフォリオ", use_container_width=True, type="secondary"):
            st.info("ポートフォリオタブに移動してください")
    
    with action_col3:
        if st.button("📝 取引履歴", use_container_width=True, type="secondary"):
            st.info("ペーパートレードタブに移動してください")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. ポートフォリオ診断 (Risk Radar)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("🛡️ ポートフォリオ診断 (Risk Radar)")
    
    # --- 指標計算 ---
    # 1. 集中度スコア (100 = 完全に分散, 0 = 一点集中)
    num_positions = len(positions)
    if num_positions == 0:
        diversity_score = 0
    elif num_positions == 1:
        diversity_score = 20
    elif num_positions <= 3:
        diversity_score = 50
    elif num_positions <= 5:
        diversity_score = 80
    else:
        diversity_score = 100
        
    # 2. 資金効率 (100 = 適切に投資中, 0 = 現金過多orカツカツ)
    cash_ratio = cash / total_equity if total_equity > 0 else 0
    if 0.1 <= cash_ratio <= 0.4:
         efficiency_score = 100 # 理想的
    elif cash_ratio < 0.1:
         efficiency_score = 60 # リスク取りすぎ
    else:
         # 現金多すぎなほどスコア低下
         efficiency_score = max(0, 100 - (cash_ratio - 0.4) * 200)

    # 3. AI期待値 (仮定: 上昇トレンド銘柄の割合)
    # 本来はSentiment分析結果を使うが、ここでは含み益銘柄の割合で代用
    if not positions.empty and 'unrealized_pnl' in positions.columns:
        profitable_positions = len(positions[positions['unrealized_pnl'] > 0])
        sentiment_score = (profitable_positions / num_positions) * 100
    else:
        sentiment_score = 50 # 中立

    # 4. 安定性 (仮定: ボラティリティの逆数などだが簡略化)
    # ここでは「大きな含み損がないか」で判定
    if not positions.empty and 'unrealized_pnl_pct' in positions.columns:
        min_pnl_pct = positions['unrealized_pnl_pct'].min()
        if min_pnl_pct < -0.1: # -10%以下の銘柄がある
            stability_score = 40
        elif min_pnl_pct < -0.05:
            stability_score = 70
        else:
            stability_score = 95
    else:
        stability_score = 100 # ポジションなしは安定

    # --- レーダーチャート描画 ---
    radar_data = pd.DataFrame(dict(
        r=[diversity_score, efficiency_score, sentiment_score, stability_score],
        theta=['分散力', '資金効率', 'AI期待値', '安定性']
    ))
    
    col_risk1, col_risk2 = st.columns([1, 1])
    
    with col_risk1:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_data['r'],
            theta=radar_data['theta'],
            fill='toself',
            name='Portfolio Stats',
            line_color='#00D9FF',
            fillcolor='rgba(0, 217, 255, 0.2)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    tickfont=dict(color='gray')
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=False,
            height=300,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_risk2:
        # 総合スコア計算
        total_score = int((diversity_score + efficiency_score + sentiment_score + stability_score) / 4)
        
        # ランク判定
        if total_score >= 80:
            rank = "S (Professional)"
            rank_color = "#00ff9d" # Green
            comment = "素晴らしいバランスです。AIの推奨運用に非常に近いです。"
        elif total_score >= 60:
            rank = "A (Advanced)"
            rank_color = "#00D9FF" # Cyan
            comment = "良好な状態です。弱点パラメーターを補強するとさらに良くなります。"
        elif total_score >= 40:
            rank = "B (Batalance Needed)"
            rank_color = "#FFA500" # Orange
            comment = "少しバランスが崩れています。分散投資や現金比率を見直してください。"
        else:
            rank = "C (Caution)"
            rank_color = "#FF4444" # Red
            comment = "リスクが高い状態です。早急なポートフォリオの再構築を推奨します。"

        st.markdown(f"""
        ### 総合ランク: <span style='color:{rank_color}'>{rank}</span>
        **スコア: {total_score}/100**
        
        {comment}
        
        ---
        - **分散力**: {diversity_score} - 銘柄数の適切さ
        - **資金効率**: {efficiency_score} - 現金比率のバランス
        - **AI期待値**: {sentiment_score:.0f} - 含み益銘柄の割合
        - **安定性**: {stability_score} - 大きな損失の回避度
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. アラート
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    alerts = []
    
    # 大きな損失
    if daily_pnl < -total_equity * 0.03:
        alerts.append("⚠️ 本日の資産が3%以上減少しています")
    
    # 集中リスク  
    if not positions.empty:
        max_position_ratio = positions['market_value'].max() / total_equity
        if max_position_ratio > 0.3:
            alerts.append("⚠️ 特定銘柄への投資が30%を超えています")
    
    # 現金不足
    if cash_ratio < 0.1:
        alerts.append("💰 現金余力が少なくなっています（追加入金を検討）")
    
    # 含み損
    if unrealized_pnl < -total_equity * 0.05:
        alerts.append("📉 含み損が資産の5%を超えています")
    
    if alerts:
        st.subheader("🚨 アラート")
        for alert in alerts:
            st.warning(alert)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. ポジション一覧（簡易版）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not positions.empty:
        st.subheader("📋 保有ポジション")
        
        # 表示用データ整形
        display_df = positions.copy()
        display_df['銘柄'] = display_df['ticker']
        display_df['株数'] = display_df['quantity']
        display_df['平均取得単価'] = display_df['entry_price'].apply(lambda x: f"¥{x:,.0f}")
        display_df['最終価格'] = display_df['current_price'].apply(lambda x: f"¥{x:,.0f}")
        display_df['損益'] = display_df['unrealized_pnl'].apply(lambda x: f"¥{x:+,.0f}")
        display_df['損益率'] = display_df['unrealized_pnl_pct'].apply(lambda x: f"{x:+.2%}")
        display_df['投資額'] = display_df['market_value'].apply(lambda x: f"¥{x:,.0f}")
        
        st.dataframe(
            display_df[['銘柄', '株数', '平均取得単価', '最終価格', '投資額', '損益', '損益率']],
            use_container_width=True
        )
    else:
        st.info("現在ポジションはありません")
    
    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5. 資産推移チャート
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not equity_history.empty:
        st.subheader("📈 資産推移（直近30日）")
        
        recent_equity = equity_history.tail(30)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_equity['date'],
            y=recent_equity['total_equity'],
            mode='lines+markers',
            name='総資産',
            line=dict(color='#00D9FF', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 217, 255, 0.1)'
        ))
        
        fig.update_layout(
            height=400,
            xaxis_title="日付",
            yaxis_title="総資産 (円)",
            hovermode='x unified',
            template='plotly_dark'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. 今日のアドバイス
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("💡 今日のアドバイス")
    
    advice = []
    
    if daily_pnl > 0:
        advice.append("✅ 本日はプラスです。このまま継続しましょう。")
    elif daily_pnl < -total_equity * 0.02:
        advice.append("⚠️ 本日の損失が大きいです。ポジションを見直しましょう。")
    
    if risk_score > 70:
        advice.append("🚨 リスクが高めです。ポジションを減らすか、現金比率を上げましょう。")
    elif risk_score < 30:
        advice.append("✅ リスク管理は良好です。")
    
    if cash_ratio > 0.5:
        advice.append("💰 現金比率が高いです。投資機会があれば検討しましょう。")
        st.metric(
            label="📅 今月の損益", 
            value=format_currency_jp(abs(monthly_pnl)) if monthly_pnl != 0 else "¥0",
            delta=None
        )
        st.markdown(f":{monthly_trend_color}[{monthly_trend_emoji} トレンド]")
    
    with col4:
        st.metric(
            label="🎯 勝率",
            value=f"{win_rate:.0%}",
            delta=None
        )
    
    st.divider()
    
    # クイックアクション
    st.subheader("⚡ クイックアクション")
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("📊 市場スキャン", use_container_width=True, type="secondary", key="home_btn_market_scan"):
            st.info("市場スキャンタブに移動してください")
    
    with action_col2:
        if st.button("💼 ポートフォリオ", use_container_width=True, type="secondary", key="home_btn_portfolio"):
            st.info("ポートフォリオタブに移動してください")
    
    with action_col3:
        if st.button("📝 取引履歴", use_container_width=True, type="secondary", key="home_btn_trade_history"):
            st.info("ペーパートレードタブに移動してください")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. リスクメーター
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("🛡️ リスク状況")
    
    risk_score = calculate_simple_risk_score(positions, total_equity)
    emoji, level, message = get_risk_message(risk_score)
    
    col_risk1, col_risk2 = st.columns([1, 2])
    
    with col_risk1:
        # リスクゲージ
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "リスクスコア"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 30], 'color': "#00D9FF"},    # ブランドカラー（シアン）
                    {'range': [30, 70], 'color': "#FFA500"},   # オレンジ
                    {'range': [70, 100], 'color': "#FF4444"}   # 明るい赤
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': risk_score
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_risk2:
        st.markdown(f"### {emoji} リスク: {level}")
        st.info(message)
        
        # 詳細情報
        cash_ratio = cash / total_equity if total_equity > 0 else 0
        invested_ratio = invested / total_equity if total_equity > 0 else 0
        num_positions = len(positions)
        
        diversification_score = min(num_positions * 20, 100) if num_positions > 0 else 0
        
        st.markdown(f"""
**詳細:**
- 📊 現金比率: {cash_ratio:.0%} 
  {'✅ 適切' if 0.2 <= cash_ratio <= 0.5 else '⚠️ 調整を検討'}
- 💼 投資比率: {invested_ratio:.0%}
- 🎲 分散度: {diversification_score}/100 
  {'✅ 十分' if diversification_score >= 60 else '⚠️ もう少し分散を'}
- 🏢 保有銘柄数: {num_positions}銘柄
""")
    
    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. アラート
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    alerts = []
    
    # 大きな損失
    if daily_pnl < -total_equity * 0.03:
        alerts.append("⚠️ 本日の資産が3%以上減少しています")
    
    # 集中リスク  
    if not positions.empty:
        max_position_ratio = positions['market_value'].max() / total_equity
        if max_position_ratio > 0.3:
            alerts.append("⚠️ 特定銘柄への投資が30%を超えています")
    
    # 現金不足
    if cash_ratio < 0.1:
        alerts.append("💰 現金余力が少なくなっています（追加入金を検討）")
    
    # 含み損
    if unrealized_pnl < -total_equity * 0.05:
        alerts.append("📉 含み損が資産の5%を超えています")
    
    if alerts:
        st.subheader("🚨 アラート")
        for alert in alerts:
            st.warning(alert)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. ポジション一覧（簡易版）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not positions.empty:
        st.subheader("📋 保有ポジション")
        
        # 表示用データ整形
        display_df = positions.copy()
        display_df['銘柄'] = display_df['ticker']
        display_df['株数'] = display_df['quantity']
        display_df['平均取得単価'] = display_df['entry_price'].apply(lambda x: f"¥{x:,.0f}")
        display_df['最終価格'] = display_df['current_price'].apply(lambda x: f"¥{x:,.0f}")
        display_df['損益'] = display_df['unrealized_pnl'].apply(lambda x: f"¥{x:+,.0f}")
        display_df['損益率'] = display_df['unrealized_pnl_pct'].apply(lambda x: f"{x:+.2%}")
        display_df['投資額'] = display_df['market_value'].apply(lambda x: f"¥{x:,.0f}")
        
        st.dataframe(
            display_df[['銘柄', '株数', '平均取得単価', '最終価格', '投資額', '損益', '損益率']],
            use_container_width=True
        )
    else:
        st.info("現在ポジションはありません")
    
    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5. 資産推移チャート
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not equity_history.empty:
        st.subheader("📈 資産推移（直近30日）")
        
        recent_equity = equity_history.tail(30)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_equity['date'],
            y=recent_equity['total_equity'],
            mode='lines+markers',
            name='総資産',
            line=dict(color='#00D9FF', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 217, 255, 0.1)'
        ))
        
        fig.update_layout(
            height=400,
            xaxis_title="日付",
            yaxis_title="総資産 (円)",
            hovermode='x unified',
            template='plotly_dark'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. 今日のアドバイス
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.subheader("💡 今日のアドバイス")
    
    advice = []
    
    if daily_pnl > 0:
        advice.append("✅ 本日はプラスです。このまま継続しましょう。")
    elif daily_pnl < -total_equity * 0.02:
        advice.append("⚠️ 本日の損失が大きいです。ポジションを見直しましょう。")
    
    if risk_score > 70:
        advice.append("🚨 リスクが高めです。ポジションを減らすか、現金比率を上げましょう。")
    elif risk_score < 30:
        advice.append("✅ リスク管理は良好です。")
    
    if cash_ratio > 0.5:
        advice.append("💰 現金比率が高いです。投資機会があれば検討しましょう。")
    
    if diversification_score < 60 and num_positions > 0:
        advice.append("🎲 分散が不足しています。複数の銘柄に分散投資しましょう。")
    
    if not advice:
        advice.append("✅ 現状維持で問題ありません。")
    
    for item in advice:
        st.markdown(f"- {item}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7. データエクスポート機能（新機能）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.divider()
    st.subheader("📥 データエクスポート")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # ポジションCSVダウンロード
        if not positions.empty:
            csv = positions.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📊 ポジション（CSV）",
                data=csv,
                file_name=f"positions_{datetime.now():%Y%m%d_%H%M}.csv",
                mime="text/csv",
                help="現在のポジション一覧をCSV形式でダウンロード"
            )
        else:
            st.button("📊 ポジション（CSV）", disabled=True, help="ポジションがありません")
    
    with col2:
        # 取引履歴CSVダウンロード
        trade_history = pt.get_trade_history()
        if not trade_history.empty:
            csv = trade_history.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📜 取引履歴（CSV）",
                data=csv,
                file_name=f"trades_{datetime.now():%Y%m%d_%H%M}.csv",
                mime="text/csv",
                help="全取引履歴をCSV形式でダウンロード"
            )
        else:
            st.button("📜 取引履歴（CSV）", disabled=True, help="取引履歴がありません")
    
    with col3:
        # 全データJSONダウンロード
        import json
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "balance": balance,
            "positions": positions.to_dict('records') if not positions.empty else [],
            "trade_history": trade_history.tail(100).to_dict('records') if not trade_history.empty else [],
            "equity_history": equity_history.tail(30).to_dict('records') if not equity_history.empty else []
        }
        
        json_str = json.dumps(export_data, default=str, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 全データ（JSON）",
            data=json_str,
            file_name=f"portfolio_data_{datetime.now():%Y%m%d_%H%M}.json",
            mime="application/json",
            help="全データをJSON形式でダウンロード"
        )


if __name__ == "__main__":
    # Streamlitアプリとして直接実行する場合
    create_simple_dashboard()
