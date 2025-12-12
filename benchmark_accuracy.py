"""
予測精度ベンチマーク
基本モデル vs 拡張モデルの精度比較
"""
import sys
import os
sys.path.insert(0, os.getcwd())

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def measure_accuracy(predictions, actuals):
    """方向精度を計算"""
    correct = 0
    total = 0
    
    for pred, actual in zip(predictions, actuals):
        if pred is None or actual is None:
            continue
        
        # 方向一致をチェック
        pred_dir = 1 if pred > 0 else -1 if pred < 0 else 0
        actual_dir = 1 if actual > 0 else -1 if actual < 0 else 0
        
        if pred_dir == actual_dir:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0


def backtest_basic_model(df, test_days=30):
    """基本LightGBMモデルのバックテスト"""
    from src.lgbm_predictor import LGBMPredictor
    from src.features import add_advanced_features
    
    predictor = LGBMPredictor()
    predictions = []
    actuals = []
    
    df_feat = add_advanced_features(df.copy())
    
    for i in range(test_days, 0, -1):
        try:
            # 過去データで予測
            train_df = df_feat.iloc[:-i-5] if i + 5 < len(df_feat) else df_feat.iloc[:-i]
            
            if len(train_df) < 100:
                continue
            
            result = predictor.predict(train_df, days_ahead=5)
            
            if "error" not in result:
                pred_change = result.get('change_pct', 0)
                
                # 実際の変化
                actual_idx = len(df_feat) - i
                if actual_idx + 5 < len(df_feat):
                    actual_change = (df_feat['Close'].iloc[actual_idx + 5] / df_feat['Close'].iloc[actual_idx] - 1) * 100
                    
                    predictions.append(pred_change)
                    actuals.append(actual_change)
        except Exception:
            continue
    
    return measure_accuracy(predictions, actuals), len(predictions)


def backtest_ensemble_model(df, test_days=30):
    """アンサンブルモデルのバックテスト"""
    from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor

    predictor = EnhancedEnsemblePredictor()
    predictions = []
    actuals = []
    
    for i in range(test_days, 0, -1):
        try:
            # 過去データで予測
            train_df = df.iloc[:-i-5] if i + 5 < len(df) else df.iloc[:-i]
            
            if len(train_df) < 100:
                continue
            
            result = predictor.predict_trajectory(train_df, days_ahead=5, ticker="TEST")
            
            if "error" not in result:
                pred_change = result.get('change_pct', 0)
                
                # トレンドから方向を取得
                trend = result.get('trend', 'FLAT')
                if trend == 'UP':
                    pred_change = abs(pred_change) if pred_change else 1
                elif trend == 'DOWN':
                    pred_change = -abs(pred_change) if pred_change else -1
                
                # 実際の変化
                actual_idx = len(df) - i
                if actual_idx + 5 < len(df):
                    actual_change = (df['Close'].iloc[actual_idx + 5] / df['Close'].iloc[actual_idx] - 1) * 100
                    
                    predictions.append(pred_change)
                    actuals.append(actual_change)
        except Exception:
            continue
    
    return measure_accuracy(predictions, actuals), len(predictions)


def backtest_intelligent_selector(df, test_days=20):
    """インテリジェントセレクターのバックテスト"""
    from src.intelligent_auto_selector import get_auto_selector
    
    selector = get_auto_selector()
    predictions = []
    actuals = []
    confidence_scores = []
    
    for i in range(test_days, 0, -1):
        try:
            # 過去データで予測
            train_df = df.iloc[:-i-5] if i + 5 < len(df) else df.iloc[:-i]
            
            if len(train_df) < 100:
                continue
            
            result = selector.get_best_prediction(train_df, "TEST")
            
            if "error" not in result:
                trend = result.get('trend', 'FLAT')
                auto_info = result.get('auto_selector', {})
                confidence = auto_info.get('confidence_score', 0.5)
                
                # 方向を数値化
                if trend == 'UP':
                    pred_change = 1
                elif trend == 'DOWN':
                    pred_change = -1
                else:
                    pred_change = 0
                
                # 実際の変化
                actual_idx = len(df) - i
                if actual_idx + 5 < len(df):
                    actual_change = (df['Close'].iloc[actual_idx + 5] / df['Close'].iloc[actual_idx] - 1) * 100
                    
                    predictions.append(pred_change)
                    actuals.append(actual_change)
                    confidence_scores.append(confidence)
        except Exception:
            continue
    
    # 高信頼度のみの精度も計算
    high_conf_acc = 0
    high_conf_count = 0
    for pred, actual, conf in zip(predictions, actuals, confidence_scores):
        if conf >= 0.6:
            pred_dir = 1 if pred > 0 else -1 if pred < 0 else 0
            actual_dir = 1 if actual > 0 else -1 if actual < 0 else 0
            if pred_dir == actual_dir:
                high_conf_acc += 1
            high_conf_count += 1
    
    overall_acc = measure_accuracy(predictions, actuals)
    high_conf_acc = high_conf_acc / high_conf_count if high_conf_count > 0 else 0
    
    return overall_acc, high_conf_acc, len(predictions), high_conf_count


def main():
    print("\n" + "="*60)
    print("📊 予測精度ベンチマーク")
    print("="*60)
    
    # データ取得
    print("\n📥 データ取得中...")
    from src.data_loader import fetch_stock_data
    
    tickers = ["7203.T", "6758.T", "9984.T"]  # トヨタ、ソニー、ソフトバンク
    data = fetch_stock_data(tickers, period="2y")
    
    results = {
        'basic': [],
        'ensemble': [],
        'intelligent': [],
        'intelligent_high_conf': []
    }
    
    for ticker in tickers:
        df = data.get(ticker)
        if df is None or len(df) < 200:
            continue
        
        print(f"\n🔍 {ticker} をテスト中...")
        
        # 1. 基本モデル
        print("   基本LightGBM...")
        try:
            basic_acc, basic_n = backtest_basic_model(df, test_days=20)
            results['basic'].append(basic_acc)
            print(f"   → 精度: {basic_acc:.1%} ({basic_n}件)")
        except Exception as e:
            print(f"   → エラー: {e}")
        
        # 2. アンサンブル（簡易版で測定時間短縮）
        print("   アンサンブル...")
        try:
            ens_acc, ens_n = backtest_ensemble_model(df, test_days=10)
            results['ensemble'].append(ens_acc)
            print(f"   → 精度: {ens_acc:.1%} ({ens_n}件)")
        except Exception as e:
            print(f"   → エラー: {e}")
        
        # 3. インテリジェントセレクター
        print("   インテリジェントセレクター...")
        try:
            int_acc, high_acc, int_n, high_n = backtest_intelligent_selector(df, test_days=10)
            results['intelligent'].append(int_acc)
            results['intelligent_high_conf'].append(high_acc)
            print(f"   → 全体精度: {int_acc:.1%} ({int_n}件)")
            print(f"   → 高信頼度のみ: {high_acc:.1%} ({high_n}件)")
        except Exception as e:
            print(f"   → エラー: {e}")
    
    # サマリー
    print("\n" + "="*60)
    print("📈 精度比較サマリー")
    print("="*60)
    
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0
    
    basic_avg = avg(results['basic'])
    ensemble_avg = avg(results['ensemble'])
    intelligent_avg = avg(results['intelligent'])
    high_conf_avg = avg(results['intelligent_high_conf'])
    
    print(f"\n{'モデル':<30} {'精度':>10}")
    print("-" * 42)
    print(f"{'1. 基本 LightGBM':<30} {basic_avg:>10.1%}")
    print(f"{'2. アンサンブル (5モデル)':<30} {ensemble_avg:>10.1%}")
    print(f"{'3. インテリジェントセレクター':<30} {intelligent_avg:>10.1%}")
    print(f"{'4. 高信頼度シグナルのみ':<30} {high_conf_avg:>10.1%}")
    
    # 改善率
    print("\n" + "="*60)
    print("📊 改善率")
    print("="*60)
    
    if basic_avg > 0:
        ensemble_improvement = (ensemble_avg - basic_avg) / basic_avg * 100
        intelligent_improvement = (intelligent_avg - basic_avg) / basic_avg * 100
        high_conf_improvement = (high_conf_avg - basic_avg) / basic_avg * 100
        
        print(f"\n基本モデル比:")
        print(f"  アンサンブル: {ensemble_improvement:+.1f}%")
        print(f"  インテリジェント: {intelligent_improvement:+.1f}%")
        print(f"  高信頼度のみ: {high_conf_improvement:+.1f}%")
    
    print("\n" + "="*60)
    print("✅ ベンチマーク完了")
    print("="*60)


if __name__ == "__main__":
    main()
