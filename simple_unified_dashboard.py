#!/usr/bin/env python3
"""
AGStock Simple Unified Dashboard
統合ダッシュボードの簡易版
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import os
import random

# 多言語対応
translations = {
    "ja": {
        "title": "AGStock 統合ダッシュボード",
        "portfolio": "ポートフォリオ",
        "performance": "パフォーマンス監視",
        "ai_prediction": "AI予測",
        "community": "コミュニティ",
        "mobile": "モバイル機能",
        "total_assets": "総資産",
        "pnl": "損益",
        "success_rate": "成功率",
        "cpu_usage": "CPU使用率",
        "memory_usage": "メモリ使用率",
        "welcome": "🎉 AGStockにようこそ！すべての新機能をご覧ください",
        "language": "言語",
    },
    "en": {
        "title": "AGStock Unified Dashboard",
        "portfolio": "Portfolio",
        "performance": "Performance Monitor",
        "ai_prediction": "AI Prediction",
        "community": "Community",
        "mobile": "Mobile Features",
        "total_assets": "Total Assets",
        "pnl": "P&L",
        "success_rate": "Success Rate",
        "cpu_usage": "CPU Usage",
        "memory_usage": "Memory Usage",
        "welcome": "🎉 Welcome to AGStock! All new features available",
        "language": "Language",
    },
}


def t(key, lang="ja"):
    return translations.get(lang, {}).get(key, key)


def create_demo_portfolio():
    """デモポートフォリオデータ作成"""
    return {"total_value": 1050000, "pnl": 50000, "pnl_pct": 5.0, "positions_count": 12}


def create_demo_performance():
    """デモパフォーマンスデータ作成"""
    return {
        "cpu_percent": random.randint(20, 80),
        "memory_percent": random.randint(30, 70),
        "disk_percent": random.randint(40, 60),
        "process_count": random.randint(150, 250),
        "uptime_hours": 24.5,
    }


def create_demo_ai_prediction():
    """デモAI予測データ作成"""
    return {
        "prediction": random.uniform(0.3, 0.8),
        "confidence": random.uniform(0.6, 0.95),
        "models": {
            "Random Forest": random.uniform(0.4, 0.7),
            "XGBoost": random.uniform(0.3, 0.8),
            "LSTM": random.uniform(0.5, 0.9),
        },
        "recommendation": "BUY" if random.random() > 0.5 else "HOLD",
    }


def create_gauge_chart(value, title, max_val=100):
    """ゲージチャート作成"""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            gauge={
                "axis": {"range": [None, max_val]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 80], "color": "yellow"},
                    {"range": [80, max_val], "color": "lightcoral"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 80,
                },
            },
        )
    )
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def main():
    # ページ設定
    st.set_page_config(
        page_title="AGStock Unified Dashboard", page_icon="🚀", layout="wide"
    )

    # 言語選択
    lang = st.sidebar.selectbox(
        t("language"),
        ["ja", "en"],
        format_func=lambda x: "日本語" if x == "ja" else "English",
    )

    # タイトル
    st.title(f"🚀 {t('title', lang)}")
    st.success(t("welcome", lang))
    st.markdown("---")

    # タブ作成
    tabs = [
        t("portfolio", lang),
        t("performance", lang),
        t("ai_prediction", lang),
        t("community", lang),
        t("mobile", lang),
    ]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs)

    with tab1:
        st.subheader(f"💼 {t('portfolio', lang)}")

        portfolio = create_demo_portfolio()

        # メトリクス
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                t("total_assets", lang),
                f"¥{portfolio['total_value']:,}",
                f"+{portfolio['pnl_pct']:.1f}%",
            )

        with col2:
            st.metric(
                t("pnl", lang),
                f"¥{portfolio['pnl']:,}",
                f"+{portfolio['pnl_pct']:.1f}%",
            )

        with col3:
            st.metric("保有銘柄", portfolio["positions_count"])

        with col4:
            st.metric("本日変動", "+¥12,345", "+1.2%")

        # 資産推移チャート
        dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
        values = [1000000 + i * 1000 + (i % 30) * 5000 for i in range(len(dates))]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines",
                name="総資産",
                line=dict(color="blue", width=2),
            )
        )
        fig.update_layout(
            title="資産価値の推移",
            xaxis_title="日付",
            yaxis_title="価値 (円)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader(f"📊 {t('performance', lang)}")

        perf = create_demo_performance()

        # リアルタイムメトリクス
        col1, col2, col3 = st.columns(3)

        with col1:
            fig_cpu = create_gauge_chart(perf["cpu_percent"], t("cpu_usage", lang))
            st.plotly_chart(fig_cpu, use_container_width=True)

        with col2:
            fig_mem = create_gauge_chart(
                perf["memory_percent"], t("memory_usage", lang)
            )
            st.plotly_chart(fig_mem, use_container_width=True)

        with col3:
            fig_disk = create_gauge_chart(perf["disk_percent"], "ディスク使用率")
            st.plotly_chart(fig_disk, use_container_width=True)

        # 詳細情報
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("プロセス数", perf["process_count"])

        with col2:
            st.metric("稼働時間", f"{perf['uptime_hours']} 時間")

        with col3:
            st.metric("取引実行", "1,234 回")

        with col4:
            st.metric("エラー数", "0 件")

    with tab3:
        st.subheader(f"🤖 {t('ai_prediction', lang)}")

        if st.button("🔮 AI予測実行"):
            with st.spinner("AI予測を実行中..."):
                time.sleep(2)  # デモ用遅延
                st.session_state.ai_prediction = create_demo_ai_prediction()

        if "ai_prediction" in st.session_state:
            pred = st.session_state.ai_prediction

            # 予測結果
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "買いシグナル強さ",
                    f"{pred['prediction']:.3f}",
                    pred["recommendation"],
                )

            with col2:
                st.metric(
                    "予測信頼度",
                    f"{pred['confidence']:.3f}",
                    "高信頼度" if pred["confidence"] > 0.8 else "中信頼度",
                )

            # 各モデルの予測
            st.subheader("📊 各モデルの予測")

            model_data = []
            for model, value in pred["models"].items():
                model_data.append(
                    {
                        "モデル": model,
                        "予測値": f"{value:.3f}",
                        "信頼度": "High"
                        if value > 0.6
                        else "Medium"
                        if value > 0.4
                        else "Low",
                    }
                )

            df_models = pd.DataFrame(model_data)
            st.dataframe(df_models, use_container_width=True)

            # 予測トレンド
            st.subheader("📈 予測トレンド")

            predictions = [0.3, 0.45, 0.6, 0.55, pred["prediction"]]
            timestamps = [datetime.now() - timedelta(hours=4 - i) for i in range(5)]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=predictions,
                    mode="lines+markers",
                    name="予測値",
                    line=dict(color="green", width=3),
                )
            )
            fig.add_hline(y=0.5, line_dash="dash", line_color="red")
            fig.update_layout(
                title="AI予測の時間推移",
                xaxis_title="時刻",
                yaxis_title="予測値",
                yaxis=dict(range=[0, 1]),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader(f"👥 {t('community', lang)}")

        # コミュニティ統計
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("👤 ユーザー数", "156")

        with col2:
            st.metric("📈 戦略数", "42")

        with col3:
            st.metric("💬 コメント数", "128")

        with col4:
            st.metric("🗳️ 総投票数", "1,234")

        # 最新戦略
        st.subheader("🌟 最新の戦略")

        strategies = [
            {
                "title": "RSIとMACDを組み合わせた戦略",
                "author": "Trader123",
                "upvotes": 45,
                "category": "テクニカル分析",
            },
            {
                "title": "AIドリブン予測モデル",
                "author": "AIMaster",
                "upvotes": 38,
                "category": "AI機械学習",
            },
        ]

        for i, strategy in enumerate(strategies, 1):
            with st.expander(f"{i}. {strategy['title']} (by {strategy['author']})"):
                st.write(f"**カテゴリ:** {strategy['category']}")
                st.write(f"**いいね数:** {strategy['upvotes']}")
                st.write(
                    "**説明:** この戦略はテクニカル指標を組み合わせた効果的なアプローチです..."
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.button("👍 いいね", key=f"upvote_{i}")
                with col2:
                    st.button("📖 詳細を見る", key=f"detail_{i}")

        # コミュニティ活動グラフ
        activity_data = pd.DataFrame(
            {
                "日付": pd.date_range(start="2024-01-01", periods=30, freq="D"),
                "投稿数": [5, 8, 12, 6, 9] * 6,
                "コメント数": [15, 22, 18, 25, 20] * 6,
            }
        )

        fig = px.line(
            activity_data,
            x="日付",
            y=["投稿数", "コメント数"],
            title="コミュニティ活動の推移",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader(f"📱 {t('mobile', lang)}")

        st.info("""
        **📱 モバイル対応機能:**
        - ✅ レスポンシブUIデザイン
        - ✅ タッチ操作最適化
        - ✅ プッシュ通知対応
        - ✅ モバイルブラウザ最適化
        - ✅ オフライン機能（一部）
        """)

        # モバイルプレビュー
        st.subheader("📱 モバイルプレビュー")

        mobile_html = """
        <div style="
            max-width: 375px;
            margin: 0 auto;
            border: 2px solid #333;
            border-radius: 20px;
            padding: 20px;
            background: #f8f9fa;
            font-family: Arial, sans-serif;
        ">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>📱 AGStock Mobile</h3>
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 10px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-size: 18px; font-weight: bold; color: #007bff;">💰 ¥1,050,000</div>
                <div style="color: #28a745; font-size: 14px;">+5.0% (本日)</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <button style="padding: 15px; border: none; background: #007bff; color: white; border-radius: 8px; font-weight: bold;">
                    📊 分析
                </button>
                <button style="padding: 15px; border: none; background: #28a745; color: white; border-radius: 8px; font-weight: bold;">
                    💼 取引
                </button>
            </div>
            
            <div style="margin-top: 20px; padding: 10px; background: white; border-radius: 8px;">
                <div style="font-weight: bold; margin-bottom: 5px;">🔔 通知</div>
                <div style="font-size: 12px; color: #666;">AI予測: 買いシグナル (信頼度 85%)</div>
                <div style="font-size: 10px; color: #999; margin-top: 5px;">5分前</div>
            </div>
            
            <div style="margin-top: 20px; text-align: center; color: #666; font-size: 12px;">
                最終更新: 12:34:56
            </div>
        </div>
        """

        st.markdown(mobile_html, unsafe_allow_html=True)

        # プッシュ通知デモ
        st.subheader("🔔 プッシュ通知")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**通知設定**")
            if st.button("テスト通知送信"):
                st.success("🔔 テスト通知を送信しました！")

            enable_notifications = st.checkbox("プッシュ通知を有効にする", value=True)

        with col2:
            st.write("**通知履歴**")
            notifications = [
                "AI予測: 買いシグナル (5分前)",
                "ポートフォリオ: +2.3% (1時間前)",
                "コミュニティ: 新しい戦略 (2時間前)",
            ]

            for notif in notifications:
                st.write(f"• {notif}")

    # サイドバー情報
    with st.sidebar:
        st.markdown("---")
        st.subheader("🚀 新機能一覧")

        features = [
            "✅ パフォーマンス監視",
            "✅ モバイル対応",
            "✅ AI予測強化",
            "✅ コミュニティ機能",
            "✅ 多言語対応",
            "✅ 拡張テスト",
        ]

        for feature in features:
            st.write(feature)

        st.markdown("---")
        st.subheader("📊 システム情報")
        st.write(f"言語: {'日本語' if lang == 'ja' else 'English'}")
        st.write(f"バージョン: v2.0.0")
        st.write(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # フッター
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <strong>🚀 AGStock Unified Dashboard v2.0</strong><br>
        Real-time Performance Monitoring • AI-Powered Predictions • Community Features • Mobile Optimized<br>
        <i>Built with ❤️ using Streamlit</i>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
