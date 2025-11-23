import pytest
import pandas as pd
import numpy as np
from src.regime import RegimeDetector

@pytest.fixture
def sample_macro_data():
    """Create sample macro data for testing."""
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    
    # Create synthetic data
    vix_data = pd.DataFrame({
        'Close': np.random.uniform(15, 30, 200)
    }, index=dates)
    
    sp500_data = pd.DataFrame({
        'Close': np.linspace(4000, 4500, 200) + np.random.normal(0, 50, 200)
    }, index=dates)
    
    us10y_data = pd.DataFrame({
        'Close': np.random.uniform(3.5, 4.5, 200)
    }, index=dates)
    
    us02y_data = pd.DataFrame({
        'Close': np.random.uniform(4.0, 5.0, 200)
    }, index=dates)
    
    gold_data = pd.DataFrame({
        'Close': np.random.uniform(1800, 2000, 200)
    }, index=dates)
    
    return {
        'VIX': vix_data,
        'SP500': sp500_data,
        'US10Y': us10y_data,
        'US02Y': us02y_data,
        'GOLD': gold_data
    }

def test_regime_detector_initialization():
    """Test RegimeDetector can be initialized."""
    detector = RegimeDetector(n_regimes=3)
    assert detector.n_regimes == 3
    assert not detector.is_fitted

def test_regime_detector_fit(sample_macro_data):
    """Test RegimeDetector can fit on macro data."""
    detector = RegimeDetector(n_regimes=3, lookback_window=60)
    detector.fit(sample_macro_data)
    assert detector.is_fitted

def test_regime_detector_predict(sample_macro_data):
    """Test RegimeDetector can predict current regime."""
    detector = RegimeDetector(n_regimes=3, lookback_window=60)
    detector.fit(sample_macro_data)
    
    regime_id, regime_label, features = detector.predict_current_regime(sample_macro_data)
    
    assert isinstance(regime_id, int)
    assert 0 <= regime_id < 3
    assert isinstance(regime_label, str)
    assert isinstance(features, dict)
    assert 'vix_level' in features

def test_regime_detector_history(sample_macro_data):
    """Test RegimeDetector can generate regime history."""
    detector = RegimeDetector(n_regimes=3, lookback_window=60)
    detector.fit(sample_macro_data)
    
    history = detector.get_regime_history(sample_macro_data, days=30)
    
    assert not history.empty
    assert len(history) <= 30
    assert 'regime_id' in history.columns
    assert 'regime_name' in history.columns

def test_calculate_features(sample_macro_data):
    """Test feature calculation."""
    detector = RegimeDetector(n_regimes=3, lookback_window=60)
    features_df = detector.calculate_features(sample_macro_data)
    
    assert not features_df.empty
    assert 'vix_level' in features_df.columns
    assert 'sp500_trend' in features_df.columns
    assert 'yield_curve' in features_df.columns

def test_regime_detector_with_missing_data():
    """Test RegimeDetector handles missing data gracefully."""
    incomplete_data = {
        'VIX': pd.DataFrame({'Close': [20, 25, 30]}, index=pd.date_range('2023-01-01', periods=3)),
        'SP500': pd.DataFrame({'Close': [4000, 4100, 4200]}, index=pd.date_range('2023-01-01', periods=3))
    }
    
    detector = RegimeDetector(n_regimes=3, lookback_window=60)
    detector.fit(incomplete_data)
    
    # Should not raise but might not be fitted
    # This tests graceful degradation
    assert True
