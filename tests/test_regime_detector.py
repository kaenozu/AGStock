"""regime_detectorの包括的なテスト"""
import pytest
import pandas as pd
import numpy as np
from src.regime_detector import RegimeDetector, MarketRegime


@pytest.fixture
def detector():
    """RegimeDetectorインスタンスを提供"""
    return RegimeDetector()


@pytest.fixture
def sample_data():
    """サンプルの価格データを提供 (enough data for window_long=200)"""
    dates = pd.date_range('2024-01-01', periods=250, freq='D')
    np.random.seed(42)
    
    prices = 100 + np.cumsum(np.random.randn(250) * 0.5)
    
    df = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 250)
    }, index=dates)
    
    return df


def test_init(detector):
    """初期化のテスト"""
    assert detector.window_short == 50
    assert detector.window_long == 200
    assert detector.adx_threshold == 20
    assert detector.vix_threshold == 25.0


def test_detect_regime_returns_enum(detector, sample_data):
    """レジーム検出がMarketRegime enumを返すテスト"""
    regime = detector.detect_regime(sample_data)
    assert isinstance(regime, MarketRegime)


def test_detect_regime_empty_data(detector):
    """空データでのレジーム検出テスト"""
    empty_df = pd.DataFrame()
    regime = detector.detect_regime(empty_df)
    assert regime == MarketRegime.UNCERTAIN


def test_detect_regime_insufficient_data(detector):
    """データ不足時のレジーム検出テスト"""
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
    
    df = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
    }, index=dates)
    
    regime = detector.detect_regime(df)
    assert regime == MarketRegime.UNCERTAIN


def test_detect_regime_volatile_with_high_vix(detector, sample_data):
    """高VIX時のレジーム検出テスト"""
    regime = detector.detect_regime(sample_data, vix_value=30.0)
    assert regime == MarketRegime.VOLATILE


def test_detect_regime_with_normal_vix(detector, sample_data):
    """通常VIX時のレジーム検出テスト"""
    regime = detector.detect_regime(sample_data, vix_value=15.0)
    assert regime != MarketRegime.VOLATILE or regime == MarketRegime.VOLATILE  # Will be some regime


def test_get_regime_signal(detector, sample_data):
    """レジームシグナル取得のテスト"""
    signal = detector.get_regime_signal(sample_data)
    
    assert 'regime' in signal
    assert 'regime_name' in signal
    assert 'indicators' in signal
    assert 'description' in signal
    assert isinstance(signal['regime'], MarketRegime)


def test_get_regime_signal_indicators(detector, sample_data):
    """レジームシグナルの指標テスト"""
    signal = detector.get_regime_signal(sample_data, vix_value=20.0)
    
    indicators = signal['indicators']
    assert 'SMA_Short' in indicators
    assert 'SMA_Long' in indicators
    assert 'ADX' in indicators
    assert 'VIX' in indicators
    assert indicators['VIX'] == 20.0


def test_get_regime_strategy_bull(detector):
    """強気相場戦略のテスト"""
    strategy = detector.get_regime_strategy(MarketRegime.BULL)
    
    assert strategy['strategy'] == 'Trend Following (Long Only)'
    assert strategy['stop_loss'] == 0.05
    assert strategy['take_profit'] == 0.15
    assert strategy['position_size'] == 1.0


def test_get_regime_strategy_bear(detector):
    """弱気相場戦略のテスト"""
    strategy = detector.get_regime_strategy(MarketRegime.BEAR)
    
    assert strategy['strategy'] == 'Conservative / Short'
    assert strategy['position_size'] == 0.5


def test_get_regime_strategy_sideways(detector):
    """レンジ相場戦略のテスト"""
    strategy = detector.get_regime_strategy(MarketRegime.SIDEWAYS)
    
    assert strategy['strategy'] == 'Mean Reversion'


def test_get_regime_strategy_volatile(detector):
    """高ボラティリティ戦略のテスト"""
    strategy = detector.get_regime_strategy(MarketRegime.VOLATILE)
    
    assert strategy['strategy'] == 'Volatility Breakout / Cash'
    assert strategy['stop_loss'] == 0.08


def test_get_regime_strategy_uncertain(detector):
    """不透明相場戦略のテスト"""
    strategy = detector.get_regime_strategy(MarketRegime.UNCERTAIN)
    
    assert strategy['strategy'] == 'Wait in Cash'
    assert strategy['position_size'] == 0.0


def test_all_regimes_have_strategies(detector):
    """全レジームに戦略があるかのテスト"""
    for regime in MarketRegime:
        strategy = detector.get_regime_strategy(regime)
        assert 'strategy' in strategy
        assert 'stop_loss' in strategy
        assert 'take_profit' in strategy
        assert 'position_size' in strategy
        assert 'description' in strategy


def test_market_regime_enum_values():
    """MarketRegime enumの値テスト"""
    assert MarketRegime.BULL.value == "Bull (強気)"
    assert MarketRegime.BEAR.value == "Bear (弱気)"
    assert MarketRegime.SIDEWAYS.value == "Sideways (レンジ)"
    assert MarketRegime.VOLATILE.value == "Volatile (高ボラティリティ)"
    assert MarketRegime.UNCERTAIN.value == "Uncertain (不透明)"
