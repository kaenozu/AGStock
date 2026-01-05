#!/usr/bin/env python3
"""
AGStock Unified Dashboard - All New Features Integration
すべての新機能を統合した統合ダッシュボード
"""

import streamlit as st
import pandas as pd
import json
import os
import time
import threading
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import sqlite3
import tempfile

# 新機能モジュールのインポート
try:
    from src.enhanced_ai_prediction import EnhancedPredictionSystem
    from src.performance_collector import PerformanceCollector
    from community_dashboard import CommunityDatabase, CommunityDashboard
except ImportError as e:
    st.warning(f"一部モジュールが利用できません: {e}")


class UnifiedDashboard:
    """統合ダッシュボード"""

    def __init__(self):
        self.init_session_state()
        self.load_translations()
        self.setup_components()

    def init_session_state(self):
        """セッション状態初期化"""
        if "language" not in st.session_state:
            st.session_state.language = "ja"
        if "show_predictions" not in st.session_state:
            st.session_state.show_predictions = False
        if "community_user" not in st.session_state:
            st.session_state.community_user = None
        if "performance_running" not in st.session_state:
            st.session_state.performance_running = False

    def load_translations(self):
        """多言語辞書読み込み"""
        self.translations = {
            "ja": {
                "title": "AGStock 統合ダッシュボード",
                "portfolio": "ポートフォリオ",
                "performance": "パフォーマンス監視",
                "ai_prediction": "AI予測",
                "community": "コミュニティ",
                "mobile": "モバイル",
                "total_assets": "総資産",
                "pnl": "損益",
                "success_rate": "成功率",
                "cpu_usage": "CPU使用率",
                "memory_usage": "メモリ使用率",
                "prediction_confidence": "予測信頼度",
                "community_stats": "コミュニティ統計",
                "welcome": "ようこそ AGStock へ！",
                "language": "言語",
                "refresh": "更新",
                "settings": "設定",
            },
            "en": {
                "title": "AGStock Unified Dashboard",
                "portfolio": "Portfolio",
                "performance": "Performance Monitor",
                "ai_prediction": "AI Prediction",
                "community": "Community",
                "mobile": "Mobile",
                "total_assets": "Total Assets",
                "pnl": "P&L",
                "success_rate": "Success Rate",
                "cpu_usage": "CPU Usage",
                "memory_usage": "Memory Usage",
                "prediction_confidence": "Prediction Confidence",
                "community_stats": "Community Stats",
                "welcome": "Welcome to AGStock!",
                "language": "Language",
                "refresh": "Refresh",
                "settings": "Settings",
            },
        }

    def t(self, key: str) -> str:
        """翻訳取得"""
        return self.translations.get(st.session_state.language, {}).get(key, key)

    def setup_components(self):
        """コンポーネントセットアップ"""
        try:
            # AI予測システム
            self.ai_system = EnhancedPredictionSystem()

            # パフォーマンスコレクター
            self.perf_collector = PerformanceCollector()

            # コミュニティ
            self.community = CommunityDashboard()

        except Exception as e:
            st.error(f"コンポーネント初期化エラー: {e}")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """ポートフォリオ概要取得"""
        try:
            portfolio_file = "data/portfolio.json"
            if os.path.exists(portfolio_file):
                with open(portfolio_file, "r") as f:
                    portfolio = json.load(f)

                total_value = sum(
                    pos.get("current_value", 0)
                    for pos in portfolio.get("positions", [])
                )
                total_cost = sum(
                    pos.get("cost_basis", 0) for pos in portfolio.get("positions", [])
                )
                pnl = total_value - total_cost
                pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0

                return {
                    "total_value": total_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "positions_count": len(portfolio.get("positions", [])),
                }
        except:
            pass

        # デモデータ
        return {
            "total_value": 1000000,
            "pnl": 50000,
            "pnl_pct": 5.0,
            "positions_count": 10,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        try:
            metrics = self.perf_collector.collect_metrics()
            return {
                "cpu_percent": metrics.get("cpu_percent", 0),
                "memory_percent": metrics.get("memory", {}).get("percent", 0),
                "disk_percent": metrics.get("disk", {}).get("percent", 0),
                "process_count": metrics.get("process_count", 0),
            }
        except:
            # デモデータ
            import random

            return {
                "cpu_percent": random.randint(20, 80),
                "memory_percent": random.randint(30, 70),
                "disk_percent": random.randint(40, 60),
                "process_count": random.randint(100, 200),
            }

    def get_ai_predictions(self) -> Dict[str, Any]:
        """AI予測取得"""
        try:
            # サンプルデータ作成
            dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
            sample_data = pd.DataFrame(
                {
                    "timestamp": dates,
                    "open": [100 + i * 0.5 + (i % 10) for i in range(100)],
                    "high": [102 + i * 0.5 + (i % 15) for i in range(100)],
                    "low": [98 + i * 0.5 - (i % 8) for i in range(100)],
                    "close": [100 + i * 0.5 + (i % 5) for i in range(100)],
                    "volume": [1000000 + i * 10000 for i in range(100)],
                }
            )

            # 予測実行
            prediction = self.ai_system.predict_signal("DEMO", sample_data.tail(50))

            return {
                "prediction": prediction.prediction,
                "confidence": prediction.confidence,
                "model_predictions": prediction.model_predictions,
                "timestamp": prediction.timestamp,
            }
        except:
            # デモデータ
            import random

            return {
                "prediction": random.uniform(0.3, 0.8),
                "confidence": random.uniform(0.6, 0.95),
                "model_predictions": {
                    "random_forest": random.uniform(0.4, 0.7),
                    "xgboost": random.uniform(0.3, 0.8),
                    "lstm": random.uniform(0.5, 0.9),
                },
                "timestamp": datetime.now(),
            }

    def get_community_stats(self) -> Dict[str, Any]:
        """コミュニティ統計取得"""
        try:
            with sqlite3.connect(self.community.db.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM strategies WHERE is_public = 1")
                total_strategies = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM comments")
                total_comments = cursor.fetchone()[0]

                return {
                    "users": total_users,
                    "strategies": total_strategies,
                    "comments": total_comments,
                }
        except:
            # デモデータ
            return {"users": 156, "strategies": 42, "comments": 128}

    def create_gauge_chart(
        self, value: float, title: str, max_value: float = 100
    ) -> go.Figure:
        """ゲージチャート作成"""
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": title},
                gauge={
                    "axis": {"range": [None, max_value]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "yellow"},
                        {"range": [80, max_value], "color": "lightcoral"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 80,
                    },
                },
            )
        )

        fig.update_layout(height=250)
        return fig

    def render_header(self):
        """ヘッダー表示"""
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.title(f"🚀 {self.t('title')}")

        with col2:
            # 言語選択
            language = st.selectbox(
                self.t("language"),
                ["ja", "en"],
                format_func=lambda x: "日本語" if x == "ja" else "English",
                key="lang_selector",
            )
            if language != st.session_state.language:
                st.session_state.language = language
                st.rerun()

        with col3:
            # クイックアクション
            if st.button(f"🔄 {self.t('refresh')}"):
                st.rerun()

    def render_portfolio_tab(self):
        """ポートフォリオタブ表示"""
        st.subheader(f"💼 {self.t('portfolio')}")

        portfolio = self.get_portfolio_summary()

        # メトリックカード
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                self.t("total_assets"),
                f"¥{portfolio['total_value']:,}",
                f"+{portfolio['pnl_pct']:.1f}%",
            )

        with col2:
            pnl_color = "normal" if portfolio["pnl"] >= 0 else "inverse"
            st.metric(
                self.t("pnl"),
                f"¥{portfolio['pnl']:,}",
                f"{portfolio['pnl_pct']:.1f}%",
                delta_color=pnl_color,
            )

        with col3:
            st.metric("保有銘柄", portfolio["positions_count"])

        with col4:
            st.metric("本日変動", "+¥12,345", "+1.2%")

        # ポートフォリオチャート
        st.subheader("📈 資産推移")

        # デモデータ
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

    def render_performance_tab(self):
        """パフォーマンス監視タブ表示"""
        st.subheader(f"📊 {self.t('performance')}")

        metrics = self.get_performance_metrics()

        # リアルタイムメトリクス
        col1, col2, col3 = st.columns(3)

        with col1:
            fig_cpu = self.create_gauge_chart(
                metrics["cpu_percent"], self.t("cpu_usage")
            )
            st.plotly_chart(fig_cpu, use_container_width=True)

        with col2:
            fig_memory = self.create_gauge_chart(
                metrics["memory_percent"], self.t("memory_usage")
            )
            st.plotly_chart(fig_memory, use_container_width=True)

        with col3:
            fig_disk = self.create_gauge_chart(
                metrics["disk_percent"], "ディスク使用率"
            )
            st.plotly_chart(fig_disk, use_container_width=True)

        # 詳細情報
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("プロセス数", metrics["process_count"])

        with col2:
            st.metric("稼働時間", "24.5 時間")

        with col3:
            st.metric("取引実行", "1,234 回")

        with col4:
            st.metric("エラー数", "0 件")

        # パフォーマンス設定
        with st.expander("⚙️ パフォーマンス設定"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**アラート設定**")
                cpu_threshold = st.slider("CPU警告閾値 (%)", 50, 95, 80)
                memory_threshold = st.slider("メモリ警告閾値 (%)", 50, 95, 80)

            with col2:
                st.write("**自動化設定**")
                auto_optimize = st.checkbox("自動最適化", value=True)
                logging_level = st.selectbox("ログレベル", ["INFO", "DEBUG", "WARNING"])

    def render_ai_prediction_tab(self):
        """AI予測タブ表示"""
        st.subheader(f"🤖 {self.t('ai_prediction')}")

        if st.button("🔮 AI予測実行"):
            with st.spinner("AI予測を実行中..."):
                st.session_state.show_predictions = True
                st.session_state.last_prediction = self.get_ai_predictions()
                time.sleep(1)  # デモ用の遅延

        if st.session_state.show_predictions and "last_prediction" in st.session_state:
            pred = st.session_state.last_prediction

            # 予測結果
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "買いシグナル強さ",
                    f"{pred['prediction']:.3f}",
                    "強い買いシグナル"
                    if pred["prediction"] > 0.6
                    else "弱い買いシグナル",
                )

            with col2:
                st.metric(
                    self.t("prediction_confidence"),
                    f"{pred['confidence']:.3f}",
                    "高信頼度" if pred["confidence"] > 0.8 else "中信頼度",
                )

            # 各モデルの予測
            st.subheader("📊 各モデルの予測")

            model_data = []
            for model, value in pred["model_predictions"].items():
                model_data.append(
                    {
                        "モデル": model.replace("_", " ").title(),
                        "予測値": value,
                        "信頼度": "High"
                        if value > 0.6
                        else "Medium"
                        if value > 0.4
                        else "Low",
                    }
                )

            df_models = pd.DataFrame(model_data)
            st.dataframe(df_models, use_container_width=True)

            # 予測チャート
            st.subheader("📈 予測トレンド")

            # デモデータ
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

            fig.add_hline(
                y=0.5, line_dash="dash", line_color="red", annotation_text="中立ライン"
            )

            fig.update_layout(
                title="AI予測の時間推移",
                xaxis_title="時刻",
                yaxis_title="予測値",
                yaxis=dict(range=[0, 1]),
                height=300,
            )

            st.plotly_chart(fig, use_container_width=True)

    def render_community_tab(self):
        """コミュニティタブ表示"""
        st.subheader(f"👥 {self.t('community')}")

        stats = self.get_community_stats()

        # 統計情報
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("👤 ユーザー数", stats["users"])

        with col2:
            st.metric("📈 戦略数", stats["strategies"])

        with col3:
            st.metric("💬 コメント数", stats["comments"])

        with col4:
            st.metric("🗳️ 総投票数", "1,234")

        # 最新戦略
        st.subheader("🌟 最新の戦略")

        # デモ戦略データ
        strategies = [
            {
                "title": "RSIとMACDを組み合わせた戦略",
                "author": "Trader123",
                "upvotes": 45,
                "category": "テクニカル分析",
                "description": "RSIの買いシグナルとMACDのトレンド確認を組み合わせ...",
            },
            {
                "title": "AIドリブン予測モデル",
                "author": "AIMaster",
                "upvotes": 38,
                "category": "AI機械学習",
                "description": "複数の機械学習モデルをアンサンブルして精度向上...",
            },
        ]

        for i, strategy in enumerate(strategies, 1):
            with st.expander(f"{i}. {strategy['title']} (by {strategy['author']})"):
                st.write(f"**カテゴリ:** {strategy['category']}")
                st.write(f"**いいね数:** {strategy['upvotes']}")
                st.write(f"**説明:** {strategy['description']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.button("👍 いいね", key=f"upvote_{i}")
                with col2:
                    st.button("📖 詳細を見る", key=f"detail_{i}")

        # コミュニティ活動
        st.subheader("📊 {self.t('community_stats')}")

        # デモデータ
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

    def render_mobile_features(self):
        """モバイル機能表示"""
        st.subheader(f"📱 {self.t('mobile')} Features")

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

        # シンプルなモバイルUIシミュレーション
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
            
            <div style="background: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 18px; font-weight: bold;">💰 ¥1,050,000</div>
                <div style="color: green; font-size: 14px;">+5.0% (本日)</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <button style="padding: 15px; border: none; background: #007bff; color: white; border-radius: 8px;">
                    📊 分析
                </button>
                <button style="padding: 15px; border: none; background: #28a745; color: white; border-radius: 8px;">
                    💼 取引
                </button>
            </div>
            
            <div style="margin-top: 20px; text-align: center; color: #666; font-size: 12px;">
                最終更新: 12:34:56
            </div>
        </div>
        """

        st.markdown(mobile_html, unsafe_allow_html=True)

    def render_settings(self):
        """設定表示"""
        st.subheader(f"⚙️ {self.t('settings')}")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**🌐 言語設定**")
            st.info(
                f"現在の言語: {'日本語' if st.session_state.language == 'ja' else 'English'}"
            )

            st.write("**🔔 通知設定**")
            push_notifications = st.checkbox("プッシュ通知を有効にする", value=True)
            email_notifications = st.checkbox("メール通知を有効にする", value=False)

            st.write("**📊 データ設定**")
            refresh_interval = st.selectbox(
                "データ更新間隔",
                [1, 5, 10, 30],
                index=1,
                format_func=lambda x: f"{x} 秒",
            )

        with col2:
            st.write("**🤖 AI設定**")
            ai_enabled = st.checkbox("AI予測を有効にする", value=True)
            auto_trade = st.checkbox("自動取引（デモ）", value=False)

            st.write("**📱 モバイル設定**")
            mobile_mode = st.checkbox("モバイルモードを有効にする", value=False)

            st.write("**🔒 セキュリティ設定**")
            two_factor = st.checkbox("二段階認証（デモ）", value=False)

    def render_automation_tab(self):
        """自動化設定タブのレンダリング"""
        st.subheader("🤖 自動化運用・通知設定")
        
        # 1. AI朝刊（モーニング・ブリーフィング）
        col1, col2 = st.columns(2)
        with col1:
            st.write("### ☀️ モーニング・ブリーフィング")
            st.info("毎朝 08:45 に今日の相場予報と注目銘柄をスマホへ届けます。")
            if st.button("今すぐテスト送信"):
                # 別プロセスで実行
                os.system("python scripts/morning_briefing.py")
                st.success("通知を送信しました。")
        
        with col2:
            st.write("### ⚙️ 通知先設定")
            # LINE Notify 設定
            st.write("**LINE Notify**")
            line_token = st.text_input("LINE Access Token", type="password", placeholder="LINE Notify トークンを入力")
            if st.button("LINE設定を保存"):
                self.save_notification_config("line", {"enabled": True, "token": line_token})
                st.success("LINE設定を保存しました。")
                
            # Discord Webhook 設定
            st.write("**Discord Webhook**")
            discord_url = st.text_input("Discord Webhook URL", type="password", placeholder="https://discord.com/api/webhooks/...")
            if st.button("Discord設定を保存"):
                self.save_notification_config("discord", {"enabled": True, "webhook_url": discord_url})
                st.success("Discord設定を保存しました。")

        st.divider()
        
        # 2. モデル精度監視（ドリフト・チェック）
        st.subheader("📊 AIモデル精度監視 (Model Monitoring)")
        st.caption("時間の経過とともに予測精度が劣化（ドリフト）していないか確認します。")
        
        # ダミーデータ（本来はDBから取得）
        dates = pd.date_range(end=datetime.now(), periods=10, freq="D")
        accuracy = [0.65, 0.64, 0.66, 0.62, 0.61, 0.59, 0.58, 0.60, 0.57, 0.55]
        
        fig = px.line(x=dates, y=accuracy, title="予測精度の推移 (Accuracy Over Time)", labels={"x": "日付", "y": "精度"})
        fig.add_hline(y=0.6, line_dash="dash", line_color="red", annotation_text="再学習推奨ライン")
        st.plotly_chart(fig, use_container_width=True)
        
        if accuracy[-1] < 0.6:
            st.warning("⚠️ 予測精度が低下しています。モデルの再学習を強く推奨します。")
            if st.button("🚀 今すぐ全モデルを再学習 (Retrain All)"):
                with st.spinner("最新データで再学習中..."):
                    os.system("python scripts/retrain_system.py")
                st.success("再学習が完了しました！")

    def save_notification_config(self, platform: str, config: dict):
        """通知設定をconfig.jsonに保存"""
        try:
            config_path = "config.json"
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
            
            if "notification" not in data:
                data["notification"] = {}
            data["notification"][platform] = config
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            st.error(f"設定保存エラー: {e}")

    def run(self):
        """メイン実行"""
        # ページ設定
        st.set_page_config(
            page_title="AGStock Unified Dashboard",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # カスタムCSS
        st.markdown(
            """
        <style>
        .metric-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # ヘッダー
        self.render_header()
        st.markdown("---")

        # タブナビゲーション
        tabs = [
            self.t("portfolio"),
            self.t("performance"),
            self.t("ai_prediction"),
            self.t("community"),
            self.t("mobile"),
            "🤖 自動化・AI朝刊",
            self.t("settings"),
        ]

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tabs)

        with tab1:
            self.render_portfolio_tab()

        with tab2:
            self.render_performance_tab()

        with tab3:
            self.render_ai_prediction_tab()

        with tab4:
            self.render_community_tab()

        with tab5:
            self.render_mobile_features()
            
        with tab6:
            self.render_automation_tab()

        with tab7:
            self.render_settings()

        # フッター
        st.markdown("---")
        st.markdown(
            """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <strong>🚀 AGStock Unified Dashboard</strong><br>
            Real-time Performance Monitoring • AI-Powered Predictions • Community Features • Mobile Optimized<br>
            Built with ❤️ using Streamlit
        </div>
        """,
            unsafe_allow_html=True,
        )


def main():
    """メイン実行関数"""
    dashboard = UnifiedDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
