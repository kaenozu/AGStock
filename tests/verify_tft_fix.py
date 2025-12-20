"""
TFT Model Verification Script
TransformerPredictorの動作確認とデバッグ
"""

import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_tft_basic():
    """TFT基本動作テスト"""
    from src.transformer_predictor import TransformerPredictor
    
    logger.info("=" * 60)
    logger.info("Test 1: TFT Basic Functionality")
    logger.info("=" * 60)
    
    # Create predictor
    predictor = TransformerPredictor()
    
    # Create dummy data (2D as EnhancedEnsemblePredictor would pass)
    n_samples = 100
    n_features = 20
    X = np.random.randn(n_samples, n_features)
    y = np.random.randn(n_samples)
    
    logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
    
    # Test fit
    try:
        predictor.fit(X, y)
        logger.info("✅ Fit completed without crash")
    except Exception as e:
        logger.error(f"❌ Fit failed: {e}")
        return False
    
    # Test predict
    try:
        predictions = predictor.predict(X[:10])
        logger.info(f"✅ Predict completed. Output shape: {predictions.shape}")
        logger.info(f"Sample predictions: {predictions[:5]}")
    except Exception as e:
        logger.error(f"❌ Predict failed: {e}")
        return False
    
    return True

def test_tft_with_dataframe():
    """DataFrameを使ったテスト"""
    from src.transformer_predictor import TransformerPredictor
    
    logger.info("=" * 60)
    logger.info("Test 2: TFT with DataFrame Input")
    logger.info("=" * 60)
    
    predictor = TransformerPredictor()
    
    # Create DataFrame (as EnhancedEnsemblePredictor would pass)
    n_samples = 100
    n_features = 20
    feature_names = [f"feature_{i}" for i in range(n_features)]
    X_df = pd.DataFrame(np.random.randn(n_samples, n_features), columns=feature_names)
    y_series = pd.Series(np.random.randn(n_samples))
    
    logger.info(f"Training data: X={X_df.shape}, y={y_series.shape}")
    
    # Test fit
    try:
        predictor.fit(X_df, y_series)
        logger.info("✅ Fit with DataFrame completed")
    except Exception as e:
        logger.error(f"❌ Fit with DataFrame failed: {e}")
        return False
    
    # Test predict
    try:
        predictions = predictor.predict(X_df[:10])
        logger.info(f"✅ Predict with DataFrame completed. Output: {predictions.shape}")
    except Exception as e:
        logger.error(f"❌ Predict with DataFrame failed: {e}")
        return False
    
    return True

def test_tft_integration():
    """EnhancedEnsemblePredictorとの統合テスト"""
    from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor
    
    logger.info("=" * 60)
    logger.info("Test 3: TFT Integration with EnhancedEnsemblePredictor")
    logger.info("=" * 60)
    
    predictor = EnhancedEnsemblePredictor()
    
    # Create dummy features
    n_samples = 100
    feature_names = [
        'Open', 'High', 'Low', 'Close', 'Volume',
        'SMA_20', 'SMA_50', 'RSI', 'MACD', 'BB_upper'
    ]
    X_df = pd.DataFrame(np.random.randn(n_samples, len(feature_names)), columns=feature_names)
    y_series = pd.Series(np.random.randn(n_samples))
    
    logger.info(f"Ensemble training data: X={X_df.shape}, y={y_series.shape}")
    
    # Test fit (should include TFT)
    try:
        predictor.fit(X_df, y_series)
        logger.info("✅ Ensemble fit completed (includes TFT)")
    except Exception as e:
        logger.error(f"❌ Ensemble fit failed: {e}")
        return False
    
    # Test predict
    try:
        result = predictor.predict_point(X_df.iloc[-1:])
        logger.info(f"✅ Ensemble predict completed")
        logger.info(f"Result keys: {result.keys()}")
        if 'ensemble_signals' in result:
            logger.info(f"Model signals: {result['ensemble_signals']}")
    except Exception as e:
        logger.error(f"❌ Ensemble predict failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting TFT Verification Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Basic Functionality", test_tft_basic()))
    results.append(("DataFrame Input", test_tft_with_dataframe()))
    results.append(("Ensemble Integration", test_tft_integration()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("❌ SOME TESTS FAILED")
        logger.error("=" * 60)
        sys.exit(1)
