import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.benchmark_comparator import BenchmarkComparator

def test_calculate_sharpe_ratio():
    bc = BenchmarkComparator()
    
    # 1. Empty series
    assert bc.calculate_sharpe_ratio(pd.Series(dtype=float)) == 0.0
    
    # 2. Constant positive returns (0 variance) -> should handle division by zero
    returns_const = pd.Series([0.01] * 100)
    assert bc.calculate_sharpe_ratio(returns_const) == 0.0
    
    # 3. Normal case
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.01, 252)) # Mean ~0.001 (daily), Std 0.01
    
    # Approx calc:
    # Excess mean ~ 0.001 - 0.001/252 ~ 0.001
    # Annualized excess ~ 0.001 * 252 ~ 0.252
    # Annualized std ~ 0.01 * sqrt(252) ~ 0.158
    # Sharpe ~ 1.59
    
    sharpe = bc.calculate_sharpe_ratio(returns, risk_free_rate=0.0)
    
    expected_mean = returns.mean() * 252
    expected_std = returns.std() * np.sqrt(252)
    expected_sharpe = expected_mean / expected_std
    
    assert np.isclose(sharpe, expected_sharpe)

def test_calculate_auc_with_sklearn():
    bc = BenchmarkComparator()
    
    # Mock sklearn availability if strictly testing logic, 
    # but here we rely on env. If sklearn missing, it returns 0.5.
    
    y_true = np.array([0, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.2, 0.8])
    # Perfect classification -> AUC = 1.0
    
    try:
        import sklearn.metrics
        auc = bc.calculate_auc(y_true, y_score)
        assert auc == 1.0
    except ImportError:
        # If no sklearn, checking fallback
        auc = bc.calculate_auc(y_true, y_score)
        assert auc == 0.5 

def test_calculate_auc_missing_data():
    bc = BenchmarkComparator()
    # Missing data handling
    y_true = np.array([0, 1, np.nan, 1])
    y_score = np.array([0.1, 0.9, 0.2, np.nan])
    
    # Only the first 2 are valid: 0(0.1), 1(0.9) -> Perfect -> AUC 1.0
    
    try:
        import sklearn.metrics
        auc = bc.calculate_auc(y_true, y_score)
        assert auc == 1.0
    except ImportError:
        pass
