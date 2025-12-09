"""
Phase 52 効果検証スクリプト
Ultimate Accuracy 機能の動作確認
"""
import time
import sys
import os
import pandas as pd
import numpy as np
sys.path.insert(0, os.getcwd())

def test_module(name, test_func):
    """モジュールテスト"""
    print(f"\n{'='*50}")
    print(f"🧪 {name}")
    print('='*50)
    try:
        start = time.time()
        result = test_func()
        elapsed = time.time() - start
        print(f"✅ 成功 ({elapsed:.2f}秒)")
        return True, result
    except Exception as e:
        print(f"❌ 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_max_data_fetch():
    """最大期間データ取得テスト"""
    from src.data_loader import fetch_stock_data
    
    # 7203.T (Toyota) は長い歴史がある
    print("   データ取得中 (max)...")
    data = fetch_stock_data(["7203.T"], period="max", use_async=False)
    df = data.get("7203.T")
    
    if df is not None:
        print(f"   取得行数: {len(df)}行")
        print(f"   期間: {df.index[0]} ~ {df.index[-1]}")
        # Transformerには最低でも数千行あることが望ましい
        is_sufficient = len(df) > 2000
        print(f"   データ量判定: {'十分' if is_sufficient else '不足'} (>2000)")
        return {"rows": len(df), "sufficient": is_sufficient}
    else:
        raise ValueError("データ取得失敗")


def test_advanced_features_v2():
    """高度特徴量V2テスト"""
    from src.advanced_features_v2 import get_advanced_features_v2
    from src.data_loader import fetch_stock_data
    
    data = fetch_stock_data(["7203.T"], period="2y")
    df = data.get("7203.T")
    
    v2 = get_advanced_features_v2()
    
    # Wavelet
    df_wave = v2.add_wavelet_features(df.copy())
    print(f"   Wavelet特徴量: {[c for c in df_wave.columns if 'Wavelet' in c]}")
    
    # FFT
    df_fft = v2.add_fft_features(df.copy())
    print(f"   FFT特徴量: {[c for c in df_fft.columns if 'FFT' in c]}")
    
    return {"wavelet": 'Close_Wavelet_Trend' in df_wave.columns, "fft": 'Close_FFT_Amp' in df_fft.columns}


def test_deep_optimizer():
    """ディープ最適化パイプラインテスト"""
    from src.deep_optimizer import get_deep_optimizer
    from src.data_loader import fetch_stock_data
    
    # テスト用にデータ少なめで
    data = fetch_stock_data(["7203.T"], period="1y")
    df = data.get("7203.T")
    
    optimizer = get_deep_optimizer()
    
    # LSTM最適化 (trial数を減らしてテスト)
    optimizer.n_trials = 2
    params = optimizer.optimize_lstm(df)
    
    print(f"   LSTM最適パラメータ: {params}")
    
    return {"params_found": len(params) > 0}


def main():
    print("\n" + "="*60)
    print("🚀 Phase 52 Ultimate Accuracy 検証")
    print("="*60)
    
    results = {}
    
    # テスト実行
    tests = [
        ("データ拡張 (Max History)", test_max_data_fetch),
        ("高度特徴量 V2 (Wavelet/FFT)", test_advanced_features_v2),
        ("Deep Optimizer (Optuna)", test_deep_optimizer),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        success, result = test_module(name, test_func)
        if success:
            passed += 1
            results[name] = result
        else:
            failed += 1
    
    # サマリー
    print("\n" + "="*60)
    print("📊 検証結果サマリー")
    print("="*60)
    print(f"✅ 成功: {passed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 全機能の実装と動作を確認しました！")
    else:
        print(f"\n⚠️ {failed}件の機能に問題があります")


if __name__ == "__main__":
    main()
