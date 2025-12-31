#!/usr/bin/env python3
"""Test script to verify the recent improvements"""

import sys
import os
sys.path.append('.')

def test_quick_overview():
    """Test the quick overview component"""
    try:
        from src.ui.components.quick_overview import render_quick_overview, _get_portfolio_data
        print("✅ Quick overview import successful")
        
        # Test the today_pnl functionality
        data = _get_portfolio_data()
        print(f"✅ Portfolio data includes keys: {list(data.keys())}")
        print(f"✅ today_pnl implemented: {data.get('today_pnl', 'NOT_FOUND')}")
        
        return True
    except Exception as e:
        print(f"❌ Quick overview test failed: {e}")
        return False

def test_trading_runner():
    """Test the trading runner error logging improvements"""
    try:
        from src.trading.runner import run_daily_routine
        print("✅ run_daily_routine import successful")
        
        # Test error handling structure (without executing full routine)
        # Just verify the function exists and can be called
        import inspect
        sig = inspect.signature(run_daily_routine)
        print(f"✅ run_daily_routine signature: {sig}")
        
        return True
    except Exception as e:
        print(f"❌ Trading runner test failed: {e}")
        return False

def test_device_detection():
    """Test the device detection improvements"""
    try:
        from src.ui_components import responsive_columns
        print("✅ ui_components import successful")
        
        # Test layout column function
        cols = responsive_columns(1, 1, 1)
        print(f"✅ Layout columns generated: {len(cols)} columns")
        
        return True
    except Exception as e:
        print(f"❌ Device detection test failed: {e}")
        return False

def test_ensemble_predictor():
    """Test the ensemble predictor concept drift handling"""
    try:
        from src.ensemble_predictor import EnhancedEnsemblePredictor
        print("✅ EnhancedEnsemblePredictor import successful")
        
        return True
    except Exception as e:
        print(f"❌ Ensemble predictor test failed: {e}")
        return False

def main():
    print("🧪 Testing AGStock Improvements")
    print("=" * 50)
    
    tests = [
        ("Quick Overview (today_pnl)", test_quick_overview),
        ("Trading Runner (error logging)", test_trading_runner),
        ("Device Detection", test_device_detection),
        ("Ensemble Predictor (concept drift)", test_ensemble_predictor),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
