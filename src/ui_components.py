"""
共通UIコンポーネントライブラリ
アプリケーション全体で再利用可能なUIコンポーネント
"""
import streamlit as st
from typing import Optional, Dict, Any, List
from src.design_tokens import Colors, RISK_LEVELS, ACTION_TYPES
from src.formatters import format_currency, format_percentage


def display_risk_badge(risk_level: str, show_label: bool = True) -> None:
    """
    リスクレベルバッジを表示
    
    Args:
        risk_level: "low", "medium", "high"
        show_label: ラベルを表示するか
    """
    config = RISK_LEVELS.get(risk_level, RISK_LEVELS["medium"])
    
    if show_label:
        st.markdown(
            f"**リスクレベル**: :{config['emoji']} {config['label_ja']} ({config['label_en']})",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"{config['emoji']} {config['label_ja']}")


def display_action_badge(action: str, large: bool = False) -> None:
    """
    アクション（売買）バッジを表示
    
    Args:
        action: "BUY", "SELL", "HOLD"
        large: 大きく表示するか
    """
    action_key = action.upper().replace(" (SHORT)", "").replace("SELL", "SELL")
    if "SHORT" in action.upper():
        action_key = "SELL"
    
    config = ACTION_TYPES.get(action_key, ACTION_TYPES["HOLD"])
    
    if large:
        st.success(f"## {config['icon']} **{config['label_ja']}** ({action})")
    else:
        st.markdown(f"{config['icon']} **{action}**")


def display_sentiment_gauge(score: float, news_count: int = 0) -> None:
    """
    センチメントゲージを表示
    
    Args:
        score: センチメントスコア（-1 ~ 1）
        news_count: ニュース件数
    """
    import plotly.graph_objects as go
    
    # ラベル判定
    if score >= 0.15:
        label = "Positive"
        label_ja = "ポジティブ"
        color = Colors.SUCCESS
    elif score <= -0.15:
        label = "Negative"
        label_ja = "ネガティブ"
        color = Colors.DANGER
    else:
        label = "Neutral"
        label_ja = "中立"
        color = Colors.NEUTRAL
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Market Sentiment"},
            gauge={
                'axis': {'range': [-1, 1]},
                'bar': {'color': color},
                'steps': [
                    {'range': [-1, -0.15], 'color': "rgba(239, 68, 68, 0.2)"},
                    {'range': [-0.15, 0.15], 'color': "rgba(107, 114, 128, 0.2)"},
                    {'range': [0.15, 1], 'color': "rgba(16, 185, 129, 0.2)"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("スコア", f"{score:.2f}", label)
        st.caption(f"{label_ja} ({label})")
        if news_count > 0:
            st.caption(f"📰 {news_count}件のニュース")


def display_stock_card(
    ticker: str,
    name: str,
    action: str,
    price: float,
    explanation: str,
    strategy: str,
    risk_level: str,
    on_order_click: Optional[callable] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    銘柄情報カードを表示
    
    Args:
        ticker: ティッカーコード
        name: 銘柄名
        action: アクション（BUY/SELL/HOLD）
        price: 現在価格
        explanation: シグナルの説明
        strategy: 使用戦略
        risk_level: リスクレベル（low/medium/high）
        on_order_click: 注文ボタンクリック時のコールバック
        additional_info: 追加情報（PER, PBR, ROE等）
    """
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
        
        with col1:
            st.markdown(f"**{name}**")
            st.caption(ticker)
            
        with col2:
            action_config = ACTION_TYPES.get(action.upper().replace(" (SHORT)", ""), ACTION_TYPES["HOLD"])
            st.markdown(f"{action_config['icon']} **{action}**")
            st.caption(format_currency(price))
            
        with col3:
            st.markdown(explanation)
            st.caption(f"戦略: {strategy}")
            
            # 追加情報の表示
            if additional_info:
                info_parts = []
                if 'PER' in additional_info and additional_info['PER']:
                    info_parts.append(f"PER: {additional_info['PER']:.1f}")
                if 'PBR' in additional_info and additional_info['PBR']:
                    info_parts.append(f"PBR: {additional_info['PBR']:.2f}")
                if 'ROE' in additional_info and additional_info['ROE']:
                    info_parts.append(f"ROE: {format_percentage(additional_info['ROE'], decimals=1)}")
                
                if info_parts:
                    st.caption(" | ".join(info_parts))
            
        with col4:
            risk_config = RISK_LEVELS.get(risk_level, RISK_LEVELS["medium"])
            st.markdown(f"リスク: {risk_config['emoji']} {risk_config['label_ja']}")
            
            if on_order_click:
                if st.button("📝 注文", key=f"order_{ticker}_{strategy}", use_container_width=True):
                    on_order_click(ticker, action, price)
        
        st.divider()


def display_best_pick_card(
    ticker: str,
    name: str,
    action: str,
    price: float,
    explanation: str,
    strategy: str,
    risk_level: str,
    on_order_click: Optional[callable] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    「今日のイチオシ」カードを大きく表示
    
    Args:
        （display_stock_cardと同じ）
    """
    st.markdown("---")
    st.subheader("🏆 今日のイチオシ (Today's Best Pick)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("銘柄", f"{name} ({ticker})")
        st.metric("現在価格", format_currency(price))
        
        risk_config = RISK_LEVELS.get(risk_level, RISK_LEVELS["medium"])
        st.markdown(f"**リスクレベル**: {risk_config['emoji']} {risk_config['label_ja']}")
        
        # 追加情報
        if additional_info:
            if 'PER' in additional_info and additional_info['PER']:
                st.caption(f"PER: {additional_info['PER']:.1f}倍")
            if 'PBR' in additional_info and additional_info['PBR']:
                st.caption(f"PBR: {additional_info['PBR']:.2f}倍")
            if 'ROE' in additional_info and additional_info['ROE']:
                st.caption(f"ROE: {format_percentage(additional_info['ROE'], decimals=1)}")
    
    with col2:
        action_config = ACTION_TYPES.get(action.upper().replace(" (SHORT)", ""), ACTION_TYPES["HOLD"])
        st.success(f"**{action_config['icon']} {action}** 推奨")
        st.markdown(f"**理由**: {explanation}")
        st.caption(f"検知戦略: {strategy}")
        
        if on_order_click:
            if st.button("🚀 この銘柄を今すぐ注文 (Paper Trading)", key="best_pick_order", type="primary"):
                on_order_click(ticker, action, price)


def display_loading_skeleton(num_rows: int = 3) -> None:
    """
    ローディング中のスケルトン表示
    
    Args:
        num_rows: 表示する行数
    """
    for i in range(num_rows):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
            with col1:
                st.markdown("⏳ **読み込み中...**")
            with col2:
                st.markdown("---")
            with col3:
                st.markdown("データを取得しています...")
            with col4:
                st.markdown("---")
            st.divider()


def display_error_message(
    error_type: str,
    user_message: str,
    technical_details: Optional[str] = None,
    help_link: Optional[str] = None
) -> None:
    """
    ユーザーフレンドリーなエラーメッセージを表示
    
    Args:
        error_type: エラータイプ（"network", "data", "permission", "unknown"）
        user_message: ユーザー向けメッセージ
        technical_details: 技術的詳細（ログ用）
        help_link: ヘルプドキュメントへのリンク
    """
    icons = {
        "network": "🌐",
        "data": "📊",
        "permission": "🔒",
        "unknown": "⚠️"
    }
    
    icon = icons.get(error_type, "⚠️")
    
    st.error(f"{icon} **エラーが発生しました**\n\n{user_message}")
    
    if help_link:
        st.info(f"💡 詳細は[ヘルプドキュメント]({help_link})をご覧ください。")
    
    # 技術的詳細はexpanderに隠す
    if technical_details:
        with st.expander("🔍 技術的詳細（開発者向け）"):
            st.code(technical_details, language="text")


def responsive_columns(mobile: int = 1, tablet: int = 2, desktop: int = 3):
    """
    レスポンシブカラムを作成（デバイス幅に応じて調整）
    
    Args:
        mobile: モバイル時のカラム数
        tablet: タブレット時のカラム数
        desktop: デスクトップ時のカラム数
        
    Returns:
        st.columns() の結果
    
    Note:
        現在のStreamlitではデバイス検出が困難なため、
        デフォルトでデスクトップレイアウトを返す。
        将来的にJavaScriptと連携して実装可能。
    """
    # TODO: JavaScriptでデバイス幅を検出してst.session_stateに保存
    device_type = st.session_state.get('device_type', 'desktop')
    
    if device_type == 'mobile':
        return st.columns(mobile)
    elif device_type == 'tablet':
        return st.columns(tablet)
    else:
        return st.columns(desktop)


def display_quick_action_bar(actions: List[Dict[str, Any]]) -> None:
    """
    クイックアクションバーを表示
    
    Args:
        actions: アクションのリスト
            [
                {"label": "スキャン", "icon": "🔍", "callback": func},
                ...
            ]
    """
    cols = st.columns(len(actions))
    
    for i, action in enumerate(actions):
        with cols[i]:
            if st.button(
                f"{action.get('icon', '')} {action['label']}",
                key=f"quick_action_{i}",
                use_container_width=True
            ):
                if 'callback' in action and callable(action['callback']):
                    action['callback']()
