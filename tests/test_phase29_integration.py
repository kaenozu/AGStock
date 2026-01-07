"""
Phase 29 統合テストスクリプト

Phase 29で実装した機能が正常に動作するか確認します。
"""

import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_advanced_features():
    """Phase 29-1: 特徴量エンジニアリングのテスト"""
    print("=" * 60)
    print("Phase 29-1: 特徴量エンジニアリングのテスト")
    print("=" * 60)

    try:
        import numpy as np
        import pandas as pd

        from src.advanced_features import generate_phase29_features

        # サンプルデータ作成
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "Open": np.random.randn(100).cumsum() + 100,
                "High": np.random.randn(100).cumsum() + 102,
                "Low": np.random.randn(100).cumsum() + 98,
                "Close": np.random.randn(100).cumsum() + 100,
                "Volume": np.random.randint(1000000, 10000000, 100),
            },
            index=dates,
        )

        # 特徴量生成
        df_features = generate_phase29_features(df)

        # 検証
        expected_features = [
            "Lag_Close_1",
            "Lag_Close_3",
            "Lag_Close_5",
            "Rolling_Std_5",
            "Rolling_Std_10",
            "Price_Change_1d",
            "Price_Change_3d",
            "ADX",
            "ADX_Trend_Direction",
            "Volatility_Regime",
            "ROC_5",
            "Stochastic_K",
            "Williams_R",
        ]

        missing_features = [f for f in expected_features if f not in df_features.columns]

        if missing_features:
            print(f"❌ 失敗: 以下の特徴量が見つかりません: {missing_features}")
            return False

        print(f"✅ 成功: {len(df_features.columns)}個の特徴量を生成")
        print(f"   サンプル特徴量: {list(df_features.columns[:10])}")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_stacking_ensemble():
    """Phase 29-2: スタッキングアンサンブルのテスト"""
    print("\n" + "=" * 60)
    print("Phase 29-2: スタッキングアンサンブルのテスト")
    print("=" * 60)

    try:
        import numpy as np

        from src.stacking_ensemble import StackingEnsemble

        # サンプルデータ
        X = np.random.randn(100, 10)
        y = np.random.randint(0, 2, 100)

        # アンサンブル作成
        ensemble = StackingEnsemble()

        # ダミーモデルを追加
        class DummyModel:
            def fit(self, X, y):
                return self

            def predict_proba(self, X):
                return np.random.rand(len(X), 2)

        ensemble.add_base_model("dummy1", DummyModel())
        ensemble.add_base_model("dummy2", DummyModel())

        # 訓練
        ensemble.fit(X, y)

        # 予測
        predictions = ensemble.predict(X)

        if len(predictions) != len(X):
            print(f"❌ 失敗: 予測数が一致しません（期待: {len(X)}, 実際: {len(predictions)}）")
            return False

        print("✅ 成功: アンサンブル予測を生成")
        print(f"   ベースモデル数: {len(ensemble.base_models)}")
        print(f"   予測サンプル: {predictions[:5]}")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_hyperparameter_tuning():
    """Phase 29-3: ハイパーパラメータ最適化のテスト"""
    print("\n" + "=" * 60)
    print("Phase 29-3: ハイパーパラメータ最適化のテスト")
    print("=" * 60)

    try:
        import numpy as np
        import pandas as pd

        from src.hyperparameter_tuning import HyperparameterTuner

        # サンプルデータ
        X = pd.DataFrame(np.random.randn(100, 10))
        y = pd.Series(np.random.randint(0, 2, 100))

        # チューナー作成
        tuner = HyperparameterTuner("lightgbm", n_splits=3)

        # 最適化実行（試行回数を少なくして高速化）
        print("   最適化実行中（5試行）...")
        best_params = tuner.optimize(X, y, n_trials=5, timeout=30)

        if not best_params:
            print("❌ 失敗: 最適パラメータが取得できませんでした")
            return False

        print("✅ 成功: ハイパーパラメータ最適化完了")
        print(f"   最適パラメータ: {best_params}")
        print(f"   最良Sharpe Ratio: {tuner.study.best_value:.4f}")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_performance_monitor():
    """パフォーマンス監視システムのテスト"""
    print("\n" + "=" * 60)
    print("パフォーマンス監視システムのテスト")
    print("=" * 60)

    try:
        import os
        import tempfile

        from src.trading_performance_monitor import TradingPerformanceMonitor

        # 一時DBファイル
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            monitor = TradingPerformanceMonitor(db_path)

            # 日次パフォーマンス記録
            monitor.record_daily_performance(
                "2025-11-29",
                {
                    "total_assets": 10000000,
                    "cash": 5000000,
                    "stock_value": 5000000,
                    "daily_return": 0.02,
                    "num_positions": 3,
                    "num_trades": 2,
                    "realized_pnl": 50000,
                    "unrealized_pnl": 100000,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -0.05,
                },
            )

            # 取引記録
            monitor.record_trade("2025-11-29", "AAPL", "BUY", 100, 150.0, 0, "LightGBM")

            # レポート生成
            daily_report = monitor.generate_daily_report("2025-11-29")

            if "10,000,000" not in daily_report:
                print("❌ 失敗: レポートに期待される内容が含まれていません")
                return False

            print("✅ 成功: パフォーマンス監視システムが正常動作")
            print("   日次レポート生成: OK")
            print("   取引記録: OK")
            return True

        finally:
            # クリーンアップ
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("\n" + "🚀" * 30)
    print("Phase 29 統合テスト開始")
    print("🚀" * 30 + "\n")

    results = {
        "Phase 29-1: 特徴量エンジニアリング": test_advanced_features(),
        "Phase 29-2: スタッキングアンサンブル": test_stacking_ensemble(),
        "Phase 29-3: ハイパーパラメータ最適化": test_hyperparameter_tuning(),
        "パフォーマンス監視システム": test_performance_monitor(),
    }

    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "=" * 60)
    print(f"総合結果: {passed}/{total} テスト成功")
    print("=" * 60)

    if passed == total:
        print("\n🎉 すべてのテストが成功しました！")
        print("Phase 29の実装は正常に動作しています。")
        return 0
    else:
        print(f"\n⚠️ {total - passed}個のテストが失敗しました。")
        print("上記のエラーメッセージを確認してください。")
        return 1


if __name__ == "__main__":
    exit(main())
