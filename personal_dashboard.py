#!/usr/bin/env python3
"""
AGStock Personal Edition Dashboard
個人投資家向け分かりやすいダッシュボード
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ページ設定
st.set_page_config(
    page_title="AGStock Personal",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSS（個人向けデザイン）
st.markdown(
    """
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    color: white;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.safe-card {
    background: #E8F5E8;
    border: 2px solid #4CAF50;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.warning-card {
    background: #FFF3E0;
    border: 2px solid #FF9800;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.danger-card {
    background: #FFEBEE;
    border: 2px solid #F44336;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
}
.info-box {
    background: #E3F2FD;
    border-left: 4px solid #2196F3;
    padding: 15px;
    margin: 15px 0;
    border-radius: 5px;
}
.large-number {
    font-size: 2.5rem;
    font-weight: bold;
    line-height: 1;
}
.medium-number {
    font-size: 1.8rem;
    font-weight: bold;
    line-height: 1;
}
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}
.status-good { background-color: #4CAF50; }
.status-warning { background-color: #FF9800; }
.status-danger { background-color: #F44336; }
.quick-action-button {
    background: linear-gradient(45deg, #2196F3, #21CBF3);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 25px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.quick-action-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}
.goal-progress {
    background: #F5F5F5;
    border-radius: 10px;
    padding: 2px;
    margin: 10px 0;
}
.goal-progress-bar {
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    height: 20px;
    border-radius: 8px;
    transition: width 0.5s ease;
}
</style>
""",
    unsafe_allow_html=True,
)

# タイトルとヘッダー
st.title("🏠 AGStock Personal - 個人投資ダッシュボード")
st.markdown("---")

# サイドバー - 基本設定
st.sidebar.header("⚙️ 基本設定")

# リスクプロファイル設定
st.sidebar.subheader("リスクプロファイル")
risk_profile = st.sidebar.selectbox(
    "投資スタイル", ["安定型", "バランス型", "成長型", "積極型"], index=1
)

# 表示期間設定
period = st.sidebar.selectbox(
    "表示期間", ["今日", "今週", "今月", "過去3ヶ月"], index=0
)

# ダークモード設定
dark_mode = st.sidebar.checkbox("🌙 ダークモード", value=False)

# メインコンテンツ
if not dark_mode:
    st.markdown(
        "<style>body { background-color: #F5F5F5; }</style>", unsafe_allow_html=True
    )

# ポートフォリオ概要セクション
st.header("📊 今日のポジション")

# メイン指標（大きく表示）
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    # 資産評価額
    st.markdown(
        """
    <div class="metric-card">
        <div style="font-size: 1.2rem; margin-bottom: 10px;">💰 資産評価額</div>
        <div class="large-number">¥1,245,678</div>
        <div style="font-size: 1rem; margin-top: 5px;">+ ¥34,567 (今日)</div>
        <div style="font-size: 0.9rem; color: #E8F5E8;">▼ 普通高で評価</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    # 本日の損益
    pnl = 34567
    pnl_percent = 2.85
    color = "#4CAF50" if pnl > 0 else "#F44336"

    st.markdown(
        f"""
    <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {color}CC 100%);">
        <div style="font-size: 1.2rem; margin-bottom: 10px;">📈 本日の損益</div>
        <div class="large-number">{"+" if pnl > 0 else ""}¥{pnl:,}</div>
        <div style="font-size: 1rem; margin-top: 5px;">{"+" if pnl_percent > 0 else ""}{pnl_percent:.2f}%</div>
        <div style="font-size: 0.9rem;">全取引中の{len([1, 2, 3, 4, 5])}件が利益</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    # 勝率
    win_rate = 80
    st.markdown(
        f"""
    <div class="metric-card">
        <div style="font-size: 1.2rem; margin-bottom: 10px;">🎯 今日の勝率</div>
        <div class="large-number">{win_rate}%</div>
        <div style="font-size: 1rem; margin-top: 5px;">4勝1敗</div>
        <div style="font-size: 0.9rem;">過去7日平均: 72%</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# リスク状態インジケータ
st.markdown("---")
st.subheader("🛡️ リスク状態")

risk_level = "低"
if risk_profile in ["積極型", "成長型"]:
    risk_level = "中高"
elif risk_profile == "バランス型":
    risk_level = "中"

risk_colors = {"低": "#4CAF50", "中": "#FF9800", "中高": "#F44336"}

risk_messages = {
    "低": "安定運用中です。無理な取引は避けましょう。",
    "中": "バランスの取れた運用です。分散投資を心がけましょう。",
    "中高": "積極的な運用ですが、リスク管理を忘れずに。",
}

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        f"""
    <div class="{("safe-card" if risk_level == "低" else "warning-card" if risk_level == "中" else "danger-card")}">
        <span class="status-indicator status-{"good" if risk_level == "低" else "warning" if risk_level == "中" else "danger"}"></span>
        <strong>現在のリスクレベル: {risk_level}</strong>
        <br><br>{risk_messages[risk_level]}
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    # 簡単な円グラフ
    risk_data = {
        "低リスク": 60
        if risk_profile == "安定型"
        else 40
        if risk_profile == "バランス型"
        else 20,
        "中リスク": 30
        if risk_profile == "安定型"
        else 40
        if risk_profile == "バランス型"
        else 40,
        "高リスク": 10
        if risk_profile == "安定型"
        else 20
        if risk_profile == "バランス型"
        else 40,
    }

    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(risk_data.keys()),
                values=list(risk_data.values()),
                hole=0.3,
                marker_colors=["#4CAF50", "#FF9800", "#F44336"],
            )
        ]
    )

    fig.update_layout(
        title="資産配分", font=dict(size=12), height=300, showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# 投資目標進捗
st.markdown("---")
st.subheader("🎯 投資目標")

goals_data = [
    {
        "title": "老後資金(2,000万円)",
        "current": 5000000,
        "target": 20000000,
        "deadline": "2045-12-31",
        "priority": "high",
    },
    {
        "title": "住宅資金(1,500万円)",
        "current": 8000000,
        "target": 15000000,
        "deadline": "2035-12-31",
        "priority": "high",
    },
    {
        "title": "教育資金(500万円)",
        "current": 2000000,
        "target": 5000000,
        "deadline": "2030-12-31",
        "priority": "medium",
    },
]

for i, goal in enumerate(goals_data):
    progress = (goal["current"] / goal["target"]) * 100

    # 残り日数計算
    try:
        deadline = datetime.fromisoformat(goal["deadline"].replace("Z", "+00:00"))
        days_remaining = (deadline - datetime.now()).days
        days_text = f"残り{days_remaining}日" if days_remaining > 0 else "達成済み"
    except:
        days_text = "未設定"

    # 優先度マーク
    priority_mark = "🔴" if goal["priority"] == "high" else "🟡"

    # 進捗バー
    progress_color = (
        "#4CAF50" if progress >= 75 else "#FF9800" if progress >= 50 else "#F44336"
    )

    st.markdown(
        f"""
    <div class="info-box">
        <strong>{priority_mark} {goal["title"]}</strong><br>
        <small>現在: ¥{goal["current"]:,} / 目標: ¥{goal["target"]:,}</small>
        <div class="goal-progress">
            <div class="goal-progress-bar" style="width: {min(progress, 100)}%; background: {progress_color};">
                <span style="text-align: center; color: white; font-size: 12px; line-height: 20px;">
                    {progress:.1f}%
                </span>
            </div>
        </div>
        <small>⏰ {days_text}</small>
    </div>
    """,
        unsafe_allow_html=True,
    )

# クイック操作ボタン
st.markdown("---")
st.subheader("⚡ クイック操作")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💰 資産追加", use_container_width=True):
        st.success("資産追加画面を準備中...")

with col2:
    if st.button("📊 詳細分析", use_container_width=True):
        st.success("分析画面を準備中...")

with col3:
    if st.button("⚠️ リスク設定", use_container_width=True):
        st.success("設定画面を準備中...")

# 重要通知
st.markdown("---")
st.subheader("📢 重要通知")

notifications = [
    {
        "type": "success",
        "title": "目標達成おめ！",
        "message": "住宅資金の目標の80%を達成しました！",
        "time": "2時間前",
    },
    {
        "type": "warning",
        "title": "市場変動注意",
        "message": "米国市場が3%下落。リスク管理を徹底してください。",
        "time": "4時間前",
    },
    {
        "type": "info",
        "title": "新機能追加",
        "message": "音声操作機能が追加されました。マイクで取引できます。",
        "time": "1日前",
    },
]

for notif in notifications:
    icon = (
        "✅"
        if notif["type"] == "success"
        else "⚠️"
        if notif["type"] == "warning"
        else "ℹ️"
    )
    bg_color = (
        "#E8F5E8"
        if notif["type"] == "success"
        else "#FFF3E0"
        if notif["type"] == "warning"
        else "#E3F2FD"
    )

    st.markdown(
        f"""
    <div style="background: {bg_color}; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <strong>{icon} {notif["title"]}</strong>
        <br><small>{notif["message"]}</small>
        <br><small style="color: #666;">{notif["time"]}</small>
    </div>
    """,
        unsafe_allow_html=True,
    )

# AIアドバイス
st.markdown("---")
st.subheader("🤖 AIアドバイス")

advice_data = {
    "安定型": "現在の安定型投資は順調です。景気変動に強い債券を増やし、リスク分散を徹底しましょう。",
    "バランス型": "バランス型として素晴らしいです。50%株式、50%債券の割合を維持しながら、定期的なリバランスをお勧めします。",
    "成長型": "成長型投資家として、より大きなリターンが期待できますが、その分リスクも高まります。分散投資と損切りルールを徹底してください。",
    "積極型": "積極的な投資は高いリターン可能性がありますが、大きなリスクも伴います。ポートフォリオ全体の5%以上を失ったら即座に見直しましょう。",
}

st.info(f"💡 {advice_data.get(risk_profile, '')}")

# 簡単なチャート表示
st.markdown("---")
st.subheader("📈 資産推移")

# ダミーデータ
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="M")
values = [
    1000000 + i * 120000 + np.random.randint(-50000, 50000)
    for i in range(1, len(dates) + 1)
]

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        name="資産評価額",
        line=dict(color="#2196F3", width=3),
        marker=dict(size=6),
    )
)

fig.update_layout(
    title="2024年 資産推移",
    xaxis_title="月",
    yaxis_title="評価額 (円)",
    height=400,
    showlegend=True,
    yaxis=dict(tickformat=","),
    xaxis=dict(tickformat="%Y-%m"),
)

st.plotly_chart(fig, use_container_width=True)

# 学習コンテンツ推薦
st.markdown("---")
st.subheader("📚 おすすめ学習コンテンツ")

learning_content = [
    {
        "level": "初級",
        "title": "投資の基本",
        "duration": "15分",
        "topics": ["リスクとは", "分散投資", "長期投資のメリット"],
        "recommendation": "まずここから！",
    },
    {
        "level": "中級",
        "title": "テクニカル分析入門",
        "duration": "20分",
        "topics": ["ローソク足", "移動平均線", "RSI"],
        "recommendation": "おすすめ",
    },
    {
        "level": "上級",
        "title": "オプション取引",
        "duration": "30分",
        "topics": ["プット/コール", "プレミアム", "権利行使"],
        "recommendation": "上級者向け",
    },
]

for content in learning_content:
    level_color = (
        "#4CAF50"
        if content["level"] == "初級"
        else "#FF9800"
        if content["level"] == "中級"
        else "#F44336"
    )

    st.markdown(
        f"""
    <div style="border: 2px solid {level_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
        <span style="background: {level_color}; color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px;">
            {content["level"]}
        </span>
        <strong> {content["title"]}</strong> ({content["duration"]})
        <br><small>📝 {", ".join(content["topics"])}</small>
        <br><span style="color: {level_color};">★ {content["recommendation"]}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

# フッター情報
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <strong>AGStock Personal Edition</strong><br>
    最終更新: {} | 設定: {} | データ: デモンストレーション
</div>
""".format(datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"), risk_profile),
    unsafe_allow_html=True,
)

# ヘルプセクション（アコーディオン）
with st.expander("🆘 ヘルプ・よくある質問"):
    st.markdown("""
    ### 💡 基本的な使い方
    
    1. **リスクプロファイル設定**: あなたの投資スタイルを選択してください
    2. **目標設定**: 退職、住宅、教育などの目標を設定
    3. **資産管理**: 現在の保有状況を確認
    4. **AIアドバイス**: 個人に合わせた投資アドバイスを受け取る
    
    ### ❓ よくある質問
    
    **Q: データはリアルタイムですか？**  
    A: 現在はデモデータですが、実装時にはリアルタイム対応予定です。
    
    **Q: 音声操作はできますか？**  
    A: モバイルアプリで音声操作対応予定です。
    
    **Q: 税務計算はできますか？**  
    A: はい、確定申告用の計算機能を実装予定です。
    """)
