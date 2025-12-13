"""
Phase 30-1 統合テスト

オンライン学習、市場レジーム検出、動的リスク管理の統合テスト
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier


def test_online_learning():
    """オンライン学習のテスト"""
    print("=" * 60)
    print("Test 1: Online Learning")
    print("=" * 60)

    try:
        from src.online_learning import OnlineLearner

        # サンプルデータ
        X = pd.DataFrame(np.random.randn(100, 10))
        y = pd.Series(np.random.randint(0, 2, 100))

        # ベースモデル
        base_model = LGBMClassifier(n_estimators=50, random_state=42, verbose=-1)
        base_model.fit(X[:80], y[:80])

        # オンライン学習
        learner = OnlineLearner(base_model, update_frequency="daily")

        # 新しいデータで更新
        X_new = X[80:]
        y_new = y[80:]
        learner.incremental_fit(X_new, y_new)

        # 性能評価
        result = learner.evaluate_and_update(X_new, y_new)

        print("✅ Online learning test passed")
        print(f"   Performance: {result['performance']}")
        print(f"   Needs update: {result['needs_update']}")

        return True

    except Exception as e:
        print(f"❌ Online learning test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_regime_detector():
    """市場レジーム検出のテスト"""
    print("\n" + "=" * 60)
    print("Test 2: Market Regime Detector")
    print("=" * 60)

    try:
        from src.regime_detector import MarketRegimeDetector

        # サンプルデータ
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

        # レジーム検出
        detector = MarketRegimeDetector()
        regime = detector.detect_regime(df)

        # 戦略パラメータ
        strategy = detector.get_regime_strategy()

        print("✅ Regime detector test passed")
        print(f"   Detected regime: {regime}")
        print(f"   Strategy: {strategy['strategy']}")
        print(f"   Stop loss: {strategy['stop_loss']*100:.2f}%")
        print(f"   Take profit: {strategy['take_profit']*100:.2f}%")

        return True

    except Exception as e:
        print(f"❌ Regime detector test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_dynamic_risk_manager():
    """動的リスク管理のテスト"""
    print("\n" + "=" * 60)
    print("Test 3: Dynamic Risk Manager")
    print("=" * 60)

    try:
        from src.dynamic_risk_manager import DynamicRiskManager

        # サンプルデータ
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

        # 動的リスク管理
        risk_manager = DynamicRiskManager()

        # パラメータ更新
        params = risk_manager.update_parameters(df)

        # ポジションサイズ計算
        position_size = risk_manager.get_position_size(account_balance=1000000, current_price=100, stop_loss_price=98)

        # 損切り・利確価格
        stop_loss = risk_manager.calculate_stop_loss(100, "long")
        take_profit = risk_manager.calculate_take_profit(100, "long")

        print("✅ Dynamic risk manager test passed")
        print(f"   Regime: {params['regime']}")
        print(f"   Position size: {position_size:.2f}")
        print(f"   Stop loss: {stop_loss:.2f}")
        print(f"   Take profit: {take_profit:.2f}")

        return True

    except Exception as e:
        print(f"❌ Dynamic risk manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_integration():
    """統合テスト"""
    print("\n" + "=" * 60)
    print("Test 4: Integration Test")
    print("=" * 60)

    try:
        from src.dynamic_risk_manager import DynamicRiskManager
        from src.online_learning import OnlineLearner
        from src.regime_detector import MarketRegimeDetector

        # サンプルデータ
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

        # 1. レジーム検出
        detector = MarketRegimeDetector()
        regime = detector.detect_regime(df)

        # 2. 動的リスク管理
        risk_manager = DynamicRiskManager(detector)
        params = risk_manager.update_parameters(df)

        # 3. オンライン学習（モデル更新）
        X = pd.DataFrame(np.random.randn(100, 10))
        y = pd.Series(np.random.randint(0, 2, 100))
        base_model = LGBMClassifier(n_estimators=50, random_state=42, verbose=-1)
        base_model.fit(X[:80], y[:80])

        learner = OnlineLearner(base_model)
        learner.incremental_fit(X[80:], y[80:])

        print("✅ Integration test passed")
        print("   Workflow: Regime Detection → Risk Management → Model Update")
        print(f"   Current regime: {regime}")
        print(
            f"   Risk parameters: Stop loss={params['stop_loss']*100:.2f}%, "
            f"Take profit={params['take_profit']*100:.2f}%"
        )

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("\n" + "🚀" * 30)
    print("Phase 30-1 Integration Test")
    print("🚀" * 30 + "\n")

    results = {
        "Online Learning": test_online_learning(),
        "Regime Detector": test_regime_detector(),
        "Dynamic Risk Manager": test_dynamic_risk_manager(),
        "Integration": test_integration(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Phase 30-1 is ready to use.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
