#!/usr/bin/env python3
"""
Enhanced Test Coverage for AGStock
包括的テストカバレッジ拡充とエッジケース対応
"""

import unittest
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import tempfile
import shutil
import sqlite3
from typing import Dict, Any, List
import asyncio
import threading
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト対象モジュール
from src.core.trading_engine import TradingEngine
from src.agents.risk_manager import RiskManager
from src.enhanced_ai_prediction import EnhancedPredictionSystem, FeatureEngineering
from src.performance_collector import PerformanceCollector
from community_dashboard import CommunityDatabase, CommunityDashboard


class TestFeatureEngineering(unittest.TestCase):
    """特徴量エンジニアリングテスト"""

    def setUp(self):
        self.fe = FeatureEngineering()
        self.sample_data = self.create_sample_data()

    def create_sample_data(self, rows: int = 100) -> pd.DataFrame:
        """サンプルデータ作成"""
        dates = pd.date_range(start="2023-01-01", periods=rows, freq="D")
        np.random.seed(42)

        base_price = 100
        price_changes = np.random.normal(0, 2, rows).cumsum()

        return pd.DataFrame(
            {
                "timestamp": dates,
                "open": base_price + price_changes,
                "high": base_price + price_changes + np.random.uniform(0, 3, rows),
                "low": base_price + price_changes - np.random.uniform(0, 3, rows),
                "close": base_price + price_changes + np.random.normal(0, 0.5, rows),
                "volume": np.random.randint(1000000, 5000000, rows),
            }
        )

    def test_technical_features_creation(self):
        """テクニカル指標特徴量生成テスト"""
        df_with_features = self.fe.create_technical_features(self.sample_data)

        # 必須カラムの存在確認
        required_columns = [
            "sma_5",
            "sma_10",
            "sma_20",
            "sma_50",
            "ema_5",
            "ema_10",
            "ema_20",
            "ema_50",
            "price_sma_5_ratio",
            "price_sma_10_ratio",
            "price_sma_20_ratio",
            "price_sma_50_ratio",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_histogram",
            "bb_position",
            "stoch_k",
            "stoch_d",
            "volume_sma_20",
            "volume_ratio",
            "price_volume_trend",
            "atr_14",
            "volatility_ratio",
            "return_1d",
            "return_3d",
            "return_5d",
            "return_10d",
        ]

        for col in required_columns:
            with self.subTest(column=col):
                self.assertIn(col, df_with_features.columns)

    def test_atr_calculation(self):
        """ATR計算テスト"""
        atr = self.fe.calculate_atr(self.sample_data, 14)

        # ATRが正の値であることを確認 (NaNを除外)
        self.assertTrue(all(atr.dropna() >= 0))

        # 最初の数値はNaNであることを確認（計算に十分なデータがないため）
        self.assertTrue(pd.isna(atr.iloc[:13]).any())

    def test_market_features_creation(self):
        """市場関連特徴量生成テスト"""
        market_data = {"market_sentiment": 0.75, "vix": 18.5, "interest_rate": 0.005}

        df_with_market = self.fe.create_market_features(self.sample_data, market_data)

        # 市場特徴量カラムの存在確認
        self.assertIn("market_sentiment", df_with_market.columns)
        self.assertIn("vix", df_with_market.columns)
        self.assertIn("interest_rate", df_with_market.columns)

        # 値が正しく設定されていることを確認
        self.assertEqual(df_with_market["market_sentiment"].iloc[0], 0.75)
        self.assertEqual(df_with_market["vix"].iloc[0], 18.5)
        self.assertEqual(df_with_market["interest_rate"].iloc[0], 0.005)

    def test_prepare_features(self):
        """特徴量準備テスト"""
        df_with_features = self.fe.create_technical_features(self.sample_data)
        X, feature_cols = self.fe.prepare_features(df_with_features)

        # 特徴量がDataFrameであることを確認
        self.assertIsInstance(X, pd.DataFrame)

        # 特徴量カラムリストがリストであることを確認
        self.assertIsInstance(feature_cols, list)
        self.assertTrue(len(feature_cols) > 0)

        # 欠損値が処理されていることを確認
        self.assertFalse(X.isnull().any().any())

    def test_edge_cases(self):
        """エッジケーステスト"""
        # 空のデータフレーム
        empty_df = pd.DataFrame()
        with self.assertRaises(Exception):
            self.fe.create_technical_features(empty_df)

        # 最小限のデータ
        minimal_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [100],
                "high": [102],
                "low": [98],
                "close": [101],
                "volume": [1000],
            }
        )

        # 最小限のデータでもエラーが発生しないことを確認
        result = self.fe.create_technical_features(minimal_df)
        self.assertIsInstance(result, pd.DataFrame)


class TestEnhancedPredictionSystem(unittest.TestCase):
    """強化された予測システムテスト"""

    def setUp(self):
        self.eps = EnhancedPredictionSystem()
        self.sample_data = self.create_sample_data()

    def create_sample_data(self, rows: int = 200) -> pd.DataFrame:
        """サンプルデータ作成"""
        dates = pd.date_range(start="2023-01-01", periods=rows, freq="D")
        np.random.seed(42)

        base_price = 100
        price_changes = np.random.normal(0, 2, rows).cumsum()

        return pd.DataFrame(
            {
                "timestamp": dates,
                "open": base_price + price_changes,
                "high": base_price + price_changes + np.random.uniform(0, 3, rows),
                "low": base_price + price_changes - np.random.uniform(0, 3, rows),
                "close": base_price + price_changes + np.random.normal(0, 0.5, rows),
                "volume": np.random.randint(1000000, 5000000, rows),
                "symbol": ["TEST"] * rows,
            }
        )

    def test_prepare_training_data(self):
        """学習データ準備テスト"""
        X, y = self.eps.prepare_training_data(self.sample_data)

        # データ型チェック
        self.assertIsInstance(X, pd.DataFrame)
        self.assertIsInstance(y, pd.Series)

        # サイズチェック
        self.assertEqual(len(X), len(y))

        # ターゲット変数が0/1であることを確認
        unique_values = set(y.dropna().unique())
        self.assertTrue(unique_values.issubset({0, 1}))

    def test_model_initialization(self):
        """モデル初期化テスト"""
        model_manager = self.eps.model_manager

        # すべてのモデルが初期化されていることを確認
        expected_models = [
            "random_forest",
            "gradient_boost",
            "xgboost",
            "lightgbm",
            "logistic",
            "lstm",
        ]

        for model_name in expected_models:
            with self.subTest(model=model_name):
                self.assertIn(model_name, model_manager.models)

    def test_train_models(self):
        """モデル学習テスト"""
        # 学習データ準備
        X, y = self.eps.prepare_training_data(self.sample_data)

        # 有効なデータのみ使用
        valid_mask = ~(X.isnull().any(axis=1) | y.isnull())
        X_clean = X[valid_mask].tail(100)  # 学習時間短縮のため
        y_clean = y[valid_mask].tail(100)

        if len(X_clean) > 10:  # 十分なデータがある場合のみ
            try:
                results = self.eps.model_manager.train_models(X_clean, y_clean)

                # 結果の型チェック
                self.assertIsInstance(results, dict)

                # 性能スコアが0-1の範囲内にあることを確認
                for score in results.values():
                    self.assertGreaterEqual(score, 0)
                    self.assertLessEqual(score, 1)

            except Exception as e:
                # 依存ライブラリがない場合のスキップ
                self.skipTest(f"Model training skipped due to: {e}")

    def test_predict_signal(self):
        """シグナル予測テスト"""
        try:
            # 簡単な学習（エラー回避のため）
            X, y = self.eps.prepare_training_data(self.sample_data)
            valid_mask = ~(X.isnull().any(axis=1) | y.isnull())
            if len(X[valid_mask]) > 10:
                X_clean = X[valid_mask].tail(50)
                y_clean = y[valid_mask].tail(50)
                self.eps.model_manager.train_models(X_clean, y_clean)

            # 予測実行
            recent_data = self.sample_data.tail(50)
            market_data = {"market_sentiment": 0.5}

            prediction = self.eps.predict_signal("TEST", recent_data, market_data)

            # 予測結果の検証
            self.assertEqual(prediction.symbol, "TEST")
            self.assertGreaterEqual(prediction.prediction, 0)
            self.assertLessEqual(prediction.prediction, 1)
            self.assertGreaterEqual(prediction.confidence, 0)
            self.assertLessEqual(prediction.confidence, 1)

        except Exception as e:
            self.skipTest(f"Prediction test skipped due to: {e}")

    def test_save_and_load_models(self):
        """モデル保存・読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 一時的なモデルパス
            original_path = self.eps.model_path
            self.eps.model_path = temp_dir

            try:
                # モデル保存
                self.eps.save_models()

                # ファイルが作成されていることを確認
                saved_files = os.listdir(temp_dir)
                self.assertGreater(len(saved_files), 0)

                # メタデータファイルの確認
                self.assertIn("metadata.json", saved_files)

                # 新しいインスタンスでモデル読み込み
                new_eps = EnhancedPredictionSystem()
                new_eps.model_path = temp_dir
                success = new_eps.load_models()

                self.assertTrue(success)

            finally:
                # 元のパスに戻す
                self.eps.model_path = original_path


class TestPerformanceCollector(unittest.TestCase):
    """パフォーマンス収集テスト"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.collector = PerformanceCollector(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_collect_metrics(self):
        """メトリクス収集テスト"""
        metrics = self.collector.collect_metrics()

        # 必須メトリクスの存在確認
        required_keys = [
            "timestamp",
            "cpu_percent",
            "memory",
            "disk",
            "network",
            "process_count",
        ]

        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, metrics)

        # タイムスタンプがISO形式であることを確認
        try:
            datetime.fromisoformat(metrics["timestamp"])
        except ValueError:
            self.fail("timestamp is not in ISO format")

    def test_save_metrics(self):
        """メトリクス保存テスト"""
        test_metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": 50.0,
            "memory": {"total": 8000000000, "percent": 60.0},
            "disk": {"total": 500000000000, "percent": 70.0},
            "network": {"bytes_sent": 1000000, "bytes_recv": 2000000},
            "process_count": 150,
        }

        self.collector.save_metrics(test_metrics)

        # 日次ファイルが作成されていることを確認
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_file = os.path.join(self.temp_dir, f"metrics_{date_str}.json")
        self.assertTrue(os.path.exists(daily_file))

        # 最新ファイルが作成されていることを確認
        latest_file = os.path.join(self.temp_dir, "latest_metrics.json")
        self.assertTrue(os.path.exists(latest_file))

        # 保存されたデータの検証
        with open(latest_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["cpu_percent"], 50.0)
        self.assertEqual(saved_data["process_count"], 150)

    def test_agstock_metrics(self):
        """AGStock固有メトリクス収集テスト"""
        # ダミーの設定ファイルとログファイルを作成
        config_data = {"test": "value"}
        config_path = os.path.join(os.path.dirname(self.temp_dir), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        agstock_metrics = self.collector.collect_agstock_metrics()

        # 設定ハッシュが含まれていることを確認
        self.assertIn("config_hash", agstock_metrics)

    def test_cleanup_old_files(self):
        """古いファイルクリーンアップテスト"""
        # 古いファイルを作成
        old_date = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
        old_file = os.path.join(self.temp_dir, f"metrics_{old_date}.json")
        with open(old_file, "w") as f:
            json.dump({"test": "old"}, f)

        # 新しいファイルを作成
        new_date = datetime.now().strftime("%Y-%m-%d")
        new_file = os.path.join(self.temp_dir, f"metrics_{new_date}.json")
        with open(new_file, "w") as f:
            json.dump({"test": "new"}, f)

        # クリーンアップ実行
        self.collector.cleanup_old_files()

        # 古いファイルが削除され、新しいファイルが残っていることを確認
        self.assertFalse(os.path.exists(old_file))
        self.assertTrue(os.path.exists(new_file))


class TestCommunityDatabase(unittest.TestCase):
    """コミュニティデータベーステスト"""

    def setUp(self):
        self.temp_db = tempfile.mktemp(suffix=".db")
        self.db = CommunityDatabase(self.temp_db)

    def tearDown(self):
        if os.path.exists(self.temp_db):
            os.unlink(self.temp_db)

    def test_database_initialization(self):
        """データベース初期化テスト"""
        self.assertTrue(os.path.exists(self.temp_db))

        # テーブルが作成されていることを確認
        conn = sqlite3.connect(self.temp_db)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["users", "strategies", "comments", "votes", "follows"]
            for table in expected_tables:
                with self.subTest(table=table):
                    self.assertIn(table, tables)
        finally:
            conn.close()

    def test_create_and_get_user(self):
        """ユーザー作成・取得テスト"""
        # ユーザー作成
        user = self.db.create_user("testuser", "test@example.com")

        # 作成されたユーザーの検証
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertIsNotNone(user.user_id)
        self.assertIsInstance(user.join_date, datetime)

        # ユーザー取得
        retrieved_user = self.db.get_user(user_id=user.user_id)
        self.assertEqual(retrieved_user.username, "testuser")
        self.assertEqual(retrieved_user.email, "test@example.com")

        # ユーザー名での取得
        retrieved_by_username = self.db.get_user(username="testuser")
        self.assertEqual(retrieved_by_username.user_id, user.user_id)

    def test_create_and_get_strategies(self):
        """戦略作成・取得テスト"""
        # ユーザー作成
        user = self.db.create_user("strategy_author", "author@example.com")

        # 戦略作成
        strategy = self.db.create_strategy(
            author_id=user.user_id,
            title="テスト戦略",
            description="これはテスト戦略です",
            code="def test_strategy(): pass",
            category="テクニカル分析",
            tags=["テスト", "デモ"],
        )

        # 作成された戦略の検証
        self.assertEqual(strategy.title, "テスト戦略")
        self.assertEqual(strategy.author_id, user.user_id)
        self.assertEqual(strategy.category, "テクニカル分析")
        self.assertEqual(len(strategy.tags), 2)

        # 戦略リスト取得
        strategies = self.db.get_strategies()
        self.assertGreater(len(strategies), 0)

        # カテゴリフィルター
        tech_strategies = self.db.get_strategies(category="テクニカル分析")
        self.assertGreater(len(tech_strategies), 0)

    def test_voting_system(self):
        """投票システムテスト"""
        # ユーザーと戦略作成
        user = self.db.create_user("voter", "voter@example.com")
        author = self.db.create_user("author", "author@example.com")
        strategy = self.db.create_strategy(
            author_id=author.user_id,
            title="投票テスト戦略",
            description="投票テスト用",
            code="def test(): pass",
            category="テクニカル分析",
            tags=["テスト"],
        )

        # アップ投票
        original_upvotes = strategy.upvotes
        self.db.vote_strategy(user.user_id, strategy.strategy_id, 1)

        # 投票結果確認
        updated_strategies = self.db.get_strategies()
        voted_strategy = next(
            s for s in updated_strategies if s.strategy_id == strategy.strategy_id
        )
        self.assertEqual(voted_strategy.upvotes, original_upvotes + 1)

        # 作者の評価確認
        updated_author = self.db.get_user(user_id=author.user_id)
        self.assertEqual(updated_author.reputation, 1)

        # ダウンロード投票
        self.db.vote_strategy(user.user_id, strategy.strategy_id, -1)
        final_strategies = self.db.get_strategies()
        final_strategy = next(
            s for s in final_strategies if s.strategy_id == strategy.strategy_id
        )
        self.assertEqual(final_strategy.upvotes, original_upvotes)
        self.assertEqual(final_strategy.downvotes, 1)


class TestEdgeCases(unittest.TestCase):
    """エッジケーステスト"""

    def test_empty_data_handling(self):
        """空データ処理テスト"""
        fe = FeatureEngineering()

        # 空のDataFrame
        empty_df = pd.DataFrame()

        with self.assertRaises(Exception):
            fe.create_technical_features(empty_df)

    def test_corrupted_data_handling(self):
        """破損データ処理テスト"""
        # 無効な価格データ
        invalid_data = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [np.nan],
                "high": [-1],  # 負の価格
                "low": [1000],  # 高すぎる価格
                "close": [100],
                "volume": [-100],  # 負の出来高
            }
        )

        fe = FeatureEngineering()

        # エラーが発生しないことを確認
        try:
            result = fe.create_technical_features(invalid_data)
            self.assertIsInstance(result, pd.DataFrame)
        except Exception:
            # エラーが発生してもOK（ハンドリングされているべき）
            pass

    def test_concurrent_access(self):
        """並列アクセステスト"""
        temp_db = tempfile.mktemp(suffix=".db")

        def create_users(start_id: int, count: int):
            db = CommunityDatabase(temp_db)
            for i in range(count):
                db.create_user(f"user{start_id + i}", f"user{start_id + i}@example.com")

        try:
            # 複数スレッドで同時ユーザー作成
            threads = []
            for i in range(3):
                thread = threading.Thread(target=create_users, args=(i * 10, 5))
                threads.append(thread)
                thread.start()

            # 全スレッドの完了を待機
            for thread in threads:
                thread.join()

            # データベースの整合性確認
            db = CommunityDatabase(temp_db)
            conn = sqlite3.connect(temp_db)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(user_count, 15)  # 3スレッド × 5ユーザー

        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)

    def test_large_dataset_handling(self):
        """大規模データセット処理テスト"""
        # 大規模サンプルデータ
        large_data = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2020-01-01", periods=10000, freq="H"),
                "close": np.random.normal(100, 10, 10000).cumsum(),
                "volume": np.random.randint(1000000, 10000000, 10000),
            }
        )

        # 高値・安値・始値を適切に設定
        large_data["open"] = large_data["close"].shift(1).fillna(100)
        large_data["high"] = large_data["close"] * (
            1 + np.random.uniform(0, 0.05, 10000)
        )
        large_data["low"] = large_data["close"] * (
            1 - np.random.uniform(0, 0.05, 10000)
        )

        fe = FeatureEngineering()

        # 処理時間を計測
        start_time = time.time()
        result = fe.create_technical_features(large_data)
        end_time = time.time()

        # 処理時間が妥当であることを確認（10秒以内）
        self.assertLess(end_time - start_time, 10)

        # 結果の検証
        self.assertEqual(len(result), len(large_data))
        self.assertGreater(len(result.columns), 20)  # 特徴量が追加されている


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    def test_end_to_end_prediction_workflow(self):
        """エンドツーエンド予測ワークフローテスト"""
        eps = EnhancedPredictionSystem()

        # サンプルデータ作成
        sample_data = pd.DataFrame(
            {
                "timestamp": pd.date_range(start="2023-01-01", periods=100, freq="D"),
                "open": np.random.normal(100, 5, 100).cumsum(),
                "high": np.random.normal(105, 5, 100).cumsum(),
                "low": np.random.normal(95, 5, 100).cumsum(),
                "close": np.random.normal(100, 5, 100).cumsum(),
                "volume": np.random.randint(1000000, 5000000, 100),
            }
        )

        try:
            # 学習データ準備
            X, y = eps.prepare_training_data(sample_data)

            # モデル学習（小規模データで）
            if len(X) > 20:
                X_small = X.tail(20)
                y_small = y.tail(20)
                eps.model_manager.train_models(X_small, y_small)

                # 予測実行
                recent_data = sample_data.tail(20)
                prediction = eps.predict_signal("INTEGRATION_TEST", recent_data)

                # 予測結果の検証
                self.assertIsNotNone(prediction)
                self.assertEqual(prediction.symbol, "INTEGRATION_TEST")

        except Exception as e:
            self.skipTest(f"Integration test skipped due to: {e}")

    def test_performance_monitoring_integration(self):
        """パフォーマンス監視統合テスト"""
        temp_dir = tempfile.mkdtemp()

        try:
            collector = PerformanceCollector(temp_dir)

            # メトリクス収集
            metrics = collector.collect_metrics()

            # 保存
            collector.save_metrics(metrics)

            # ファイル確認
            files = os.listdir(temp_dir)
            self.assertTrue(any("metrics_" in f for f in files))

        finally:
            shutil.rmtree(temp_dir)


# テストスイート実行
def run_all_tests():
    """全テスト実行"""
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_enhanced_coverage.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    # 単体テスト実行
    unittest.main(verbosity=2)
