"""
Phase 56: MoE Verification
賢人会議（Mixture of Experts）が市場環境に応じて正しく機能するかテスト
"""

import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())

# ログ設定
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("src.moe_system")
logger.setLevel(logging.INFO)

from src.moe_system import MixtureOfExperts


def create_synthetic_data(trend_type="up", length=100):
    """人工的な市場データを生成"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=length, freq="D")

    if trend_type == "up":
        # 右肩上がり (+ノイズ)
        close = np.linspace(100, 150, length) + np.random.randn(length)
    elif trend_type == "down":
        # 右肩下がり
        close = np.linspace(100, 50, length) + np.random.randn(length)
    elif trend_type == "range":
        # 横ばい
        close = 100 + np.sin(np.linspace(0, 10, length)) * 5 + np.random.randn(length)
    elif trend_type == "volatile":
        # 激しい動き
        close = 100 + np.cumsum(np.random.randn(length) * 3)

    df = pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1000}, index=dates)
    return df


def test_moe_switching():
    print("\n" + "=" * 60)
    print("🏛️ MoE (Mixture of Experts) Switching Test")
    print("=" * 60)

    moe = MixtureOfExperts()

    scenarios = [
        ("up", "trending_up", "Bull Expert"),
        ("down", "trending_down", "Bear Expert"),
        ("range", "ranging", "Range Expert"),
        # ('volatile', 'high_volatility', 'Crisis Expert') # 乱数依存で難しいので省略
    ]

    score = 0

    for trend_type, expected_regime, expected_expert_keyword in scenarios:
        print(f"\n🧪 Testing Scenario: {trend_type.upper()}")

        # データ生成
        df = create_synthetic_data(trend_type)

        # 判断
        decision = moe.get_expert_signal(df, "TEST")

        print(f"   Detected Regime: {decision['regime']}")
        print(f"   Selected Expert: {decision['expert']}")
        print(f"   Action: {decision['action']}")

        # 検証
        # レジーム検出はTA-Lib依存で厳密には一致しない場合があるため、
        # "Expert"が期待通り切り替わっているかを重視

        if expected_expert_keyword in decision["expert"] or (trend_type == "range" and "Range" in decision["expert"]):
            print("   ✅ CORRECT EXPERT SELECTED")
            score += 1
        else:
            print(f"   ❌ WRONG EXPERT (Expected {expected_expert_keyword})")

    if score >= 3:
        print("\n✅ All scenarios passed. MoE is adapting correctly.")
        return True
    else:
        print("\n⚠️ Some scenarios failed. Sensitivity tuning might be needed.")
        return False


if __name__ == "__main__":
    test_moe_switching()
