"""
regime_detectorの包括的なテスト
"""

import numpy as np
import pandas as pd
import pytest

from src.regime_detector import MarketRegimeDetector


@pytest.fixture
def detector():
    """MarketRegimeDetectorインスタンスを提供"""
    return MarketRegimeDetector()


@pytest.fixture
def sample_data():
    """サンプルの価格データを提供"""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    np.random.seed(42)

    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)

    df = pd.DataFrame(
        {
            "Open": prices * 0.99,
            "High": prices * 1.02,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": np.random.randint(1000000, 10000000, 100),
        },
        index=dates,
    )

    return df


def test_init(detector):
    """初期化のテスト"""
    assert detector.regimes is not None
    assert detector.current_regime is None
    assert detector.regime_history == []


def test_detect_regime(detector, sample_data):
    """レジーム検出のテスト"""
    regime = detector.detect_regime(sample_data)

    assert regime in detector.regimes.keys()
    assert detector.current_regime == regime
    assert len(detector.regime_history) == 1


def test_detect_trend_fallback(detector, sample_data):
    """トレンド検出フォールバックのテスト"""
    trend = detector._detect_trend_fallback(sample_data, 20)

    assert trend in ["up", "down", "ranging"]


def test_detect_volatility_fallback(detector, sample_data):
    """ボラティリティ検出フォールバックのテスト"""
    volatility = detector._detect_volatility_fallback(sample_data, 20)

    assert volatility in ["high", "normal", "low"]


def test_classify_regime_high_volatility(detector):
    """高ボラティリティ時のレジーム分類"""
    regime = detector._classify_regime("up", "high")
    assert regime == "high_volatility"


def test_classify_regime_low_volatility(detector):
    """低ボラティリティ時のレジーム分類"""
    regime = detector._classify_regime("down", "low")
    assert regime == "low_volatility"


def test_classify_regime_trending_up(detector):
    """上昇トレンド時のレジーム分類"""
    regime = detector._classify_regime("up", "normal")
    assert regime == "trending_up"


def test_classify_regime_trending_down(detector):
    """下降トレンド時のレジーム分類"""
    regime = detector._classify_regime("down", "normal")
    assert regime == "trending_down"


def test_classify_regime_ranging(detector):
    """レンジ相場時のレジーム分類"""
    regime = detector._classify_regime("ranging", "normal")
    assert regime == "ranging"


def test_get_regime_strategy_trending_up(detector):
    """上昇トレンド戦略のテスト"""
    strategy = detector.get_regime_strategy("trending_up")

    assert strategy["strategy"] == "trend_following"
    assert strategy["stop_loss"] == 0.03
    assert strategy["take_profit"] == 0.15


def test_get_regime_strategy_trending_down(detector):
    """下降トレンド戦略のテスト"""
    strategy = detector.get_regime_strategy("trending_down")

    assert strategy["strategy"] == "counter_trend"
    assert strategy["position_size"] == 0.5


def test_get_regime_strategy_ranging(detector):
    """レンジ相場戦略のテスト"""
    strategy = detector.get_regime_strategy("ranging")

    assert strategy["strategy"] == "mean_reversion"


def test_get_regime_strategy_high_volatility(detector):
    """高ボラティリティ戦略のテスト"""
    strategy = detector.get_regime_strategy("high_volatility")

    assert strategy["strategy"] == "volatility_breakout"
    assert strategy["stop_loss"] == 0.05


def test_get_regime_strategy_low_volatility(detector):
    """低ボラティリティ戦略のテスト"""
    strategy = detector.get_regime_strategy("low_volatility")

    assert strategy["strategy"] == "range_trading"


def test_get_regime_strategy_none(detector, sample_data):
    """現在のレジームに基づく戦略取得"""
    detector.detect_regime(sample_data)
    strategy = detector.get_regime_strategy()

    assert "strategy" in strategy
    assert "stop_loss" in strategy


def test_get_regime_strategy_no_regime(detector):
    """レジーム未検出時のデフォルト戦略"""
    strategy = detector.get_regime_strategy()

    assert strategy["strategy"] == "mean_reversion"


def test_get_regime_history(detector, sample_data):
    """レジーム履歴の取得テスト"""
    detector.detect_regime(sample_data)
    detector.detect_regime(sample_data)
    detector.detect_regime(sample_data)

    history = detector.get_regime_history(n=2)

    assert len(history) == 2


def test_get_regime_history_all(detector, sample_data):
    """全レジーム履歴の取得テスト"""
    for _ in range(5):
        detector.detect_regime(sample_data)

    history = detector.get_regime_history(n=10)

    assert len(history) == 5


def test_get_regime_statistics_empty(detector):
    """空の統計テスト"""
    stats = detector.get_regime_statistics()

    assert "message" in stats


def test_get_regime_statistics(detector, sample_data):
    """レジーム統計の取得テスト"""
    for _ in range(10):
        detector.detect_regime(sample_data)

    stats = detector.get_regime_statistics()

    assert "current_regime" in stats
    assert "total_observations" in stats
    assert "regime_counts" in stats
    assert "regime_percentages" in stats
    assert "most_common_regime" in stats
    assert stats["total_observations"] == 10


def test_multiple_regime_detections(detector, sample_data):
    """複数回のレジーム検出テスト"""
    regimes = []
    for _ in range(5):
        regime = detector.detect_regime(sample_data)
        regimes.append(regime)

    assert len(regimes) == 5
    assert len(detector.regime_history) == 5


def test_regime_history_structure(detector, sample_data):
    """レジーム履歴の構造テスト"""
    detector.detect_regime(sample_data)

    history = detector.regime_history[0]

    assert "timestamp" in history
    assert "regime" in history
    assert "trend" in history
    assert "volatility" in history
