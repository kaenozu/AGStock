"""
End-to-End Trading Flow Integration Test
予測エンジン → 投資委員会 → 注文実行の全フローを検証
"""

import logging
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_predictor_to_committee_flow():
    """予測エンジン → 投資委員会のデータフロー検証"""
    from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor
    from src.agents.committee import InvestmentCommittee
    
    logger.info("=" * 60)
    logger.info("Test: Predictor → Committee Data Flow")
    logger.info("=" * 60)
    
    # 1. Create predictor and train
    predictor = EnhancedEnsemblePredictor()
    
    # Mock training data
    n_samples = 100
    feature_names = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'RSI']
    X = pd.DataFrame(np.random.randn(n_samples, len(feature_names)), columns=feature_names)
    y = pd.Series(np.random.randn(n_samples))
    
    logger.info(f"Training predictor with {n_samples} samples...")
    predictor.fit(X, y)
    
    # 2. Generate prediction
    current_features = X.iloc[-1:]
    prediction_result = predictor.predict_point(current_features)
    
    logger.info(f"Prediction result keys: {prediction_result.keys()}")
    logger.info(f"Final prediction: {prediction_result.get('final_prediction')}")
    logger.info(f"Confidence: {prediction_result.get('confidence_score')}")
    
    # 3. Create committee and pass prediction
    committee = InvestmentCommittee()
    
    # Mock signal data (as would come from automated trader)
    signal_data = {
        "price": 100.0,
        "action": "BUY",
        "strategy": "TestStrategy",
        "reason": "Test signal",
        "vix": 15.0,
        "features": current_features,
        # The committee will generate prediction_report from features
    }
    
    logger.info("Sending signal to committee...")
    decision = committee.review_candidate("TEST", signal_data)
    
    logger.info(f"Committee decision: {decision}")
    
    # 4. Verify prediction_report was created
    if committee.last_meeting_result:
        analyses = committee.last_meeting_result.get("analyses", [])
        logger.info(f"Number of agent analyses: {len(analyses)}")
        
        for analysis in analyses:
            logger.info(f"  - {analysis['agent_name']}: {analysis['decision']} (conf: {analysis['confidence']:.2f})")
            if "Quant Models" in analysis.get('reasoning', ''):
                logger.info("    ✅ Quantitative prediction data found in reasoning")
                return True
    
    logger.error("❌ Quantitative prediction data NOT found in committee reasoning")
    return False

def test_committee_to_order_flow():
    """投資委員会 → 注文実行のフロー検証"""
    from src.agents.committee import InvestmentCommittee
    
    logger.info("=" * 60)
    logger.info("Test: Committee → Order Execution Flow")
    logger.info("=" * 60)
    
    committee = InvestmentCommittee()
    
    # Mock strong BUY signal
    signal_data = {
        "price": 100.0,
        "action": "BUY",
        "strategy": "StrongMomentum",
        "reason": "Golden cross + high volume",
        "vix": 12.0,
        "sentiment_score": 0.8,
        "prediction_report": {
            "ensemble_decision": "UP",
            "confidence": 0.92,
            "components": {"LGBM": 0.03, "Prophet": 0.025},
            "market_regime": "Bullish"
        }
    }
    
    logger.info("Testing strong BUY signal...")
    decision = committee.review_candidate("TEST", signal_data)
    
    logger.info(f"Committee decision: {decision}")
    
    if decision.value == "BUY":
        logger.info("✅ Committee approved BUY")
        return True
    else:
        logger.warning(f"⚠️ Committee did not approve BUY (decision: {decision.value})")
        return False

def test_error_handling():
    """エラーハンドリングの検証"""
    from src.agents.committee import InvestmentCommittee
    
    logger.info("=" * 60)
    logger.info("Test: Error Handling")
    logger.info("=" * 60)
    
    committee = InvestmentCommittee()
    
    # Test 1: Missing features (should fallback gracefully)
    signal_data_no_features = {
        "price": 100.0,
        "action": "BUY",
        "strategy": "Test",
        "reason": "Test"
    }
    
    logger.info("Test 1: Missing features...")
    try:
        decision = committee.review_candidate("TEST", signal_data_no_features)
        logger.info(f"  Decision: {decision} (should use fallback UNKNOWN report)")
        
        # Check that fallback was used
        if committee.last_meeting_result:
            # Look for UNKNOWN in analyses
            found_unknown = False
            for analysis in committee.last_meeting_result.get("analyses", []):
                if "UNKNOWN" in analysis.get('reasoning', ''):
                    found_unknown = True
                    break
            
            if found_unknown:
                logger.info("  ✅ Fallback to UNKNOWN prediction report worked")
            else:
                logger.warning("  ⚠️ UNKNOWN not found in reasoning")
    except Exception as e:
        logger.error(f"  ❌ Exception raised: {e}")
        return False
    
    # Test 2: Invalid prediction report
    signal_data_invalid = {
        "price": 100.0,
        "prediction_report": {"invalid": "data"}
    }
    
    logger.info("Test 2: Invalid prediction report...")
    try:
        decision = committee.review_candidate("TEST", signal_data_invalid)
        logger.info(f"  Decision: {decision}")
        logger.info("  ✅ Handled invalid report gracefully")
    except Exception as e:
        logger.error(f"  ❌ Exception raised: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting End-to-End Integration Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Predictor → Committee", test_predictor_to_committee_flow()))
    results.append(("Committee → Order", test_committee_to_order_flow()))
    results.append(("Error Handling", test_error_handling()))
    
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
        logger.info("🎉 ALL INTEGRATION TESTS PASSED")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("❌ SOME TESTS FAILED")
        logger.error("=" * 60)
        sys.exit(1)
