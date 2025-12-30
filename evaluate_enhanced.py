"""
Enhanced Prediction Evaluation with Comprehensive Features
Tests the impact of 50+ advanced features on prediction accuracy.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.data_loader import fetch_stock_data, fetch_external_data
from src.features.comprehensive_features import ComprehensiveFeatureGenerator
from src.ensemble.stacking import create_default_stacking_ensemble
from src.optimization.hyperparameter_tuner import HyperparameterOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate directional accuracy."""
    correct = sum((y_true > 0) == (y_pred > 0))
    return correct / len(y_true)


def main():
    logger.info("="*70)
    logger.info("包括的特徴量による予測精度評価")
    logger.info("="*70)
    
    # 1. データ取得
    logger.info("\n📊 データ取得中...")
    ticker = '7203.T'  # トヨタ
    data = fetch_stock_data([ticker], period='2y', interval='1d')
    df = data.get(ticker)
    
    if df is None or df.empty:
        logger.error(f"データ取得失敗: {ticker}")
        return
    
    # 外部データ取得
    external_data = fetch_external_data(period='2y')
    
    logger.info(f"✅ データ取得完了: {ticker} ({len(df)} rows)")
    
    # 2. 包括的特徴量生成
    logger.info("\n🔧 包括的特徴量生成中...")
    feature_gen = ComprehensiveFeatureGenerator()
    df_features = feature_gen.generate_all_features(df, external_data)
    
    # Target
    df_features['target'] = df_features['Close'].pct_change().shift(-1)
    df_features = df_features.dropna()
    
    # Feature columns (exclude OHLCV and target)
    exclude_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'target']
    feature_cols = [col for col in df_features.columns if col not in exclude_cols]
    
    logger.info(f"✅ 特徴量生成完了: {len(feature_cols)} features")
    logger.info(f"   特徴量例: {feature_cols[:10]}")
    
    # 3. Train/Test split
    X = df_features[feature_cols]
    y = df_features['target']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    logger.info(f"\n📊 データ分割:")
    logger.info(f"   Train: {len(X_train)} samples")
    logger.info(f"   Test: {len(X_test)} samples")
    
    # 4. ハイパーパラメータ最適化
    logger.info("\n🎯 ハイパーパラメータ最適化中...")
    optimizer = HyperparameterOptimizer(n_trials=30)
    best_params = optimizer.optimize_lgbm(X_train, y_train)
    
    # 5. 最適化モデルで評価
    from lightgbm import LGBMRegressor
    model = LGBMRegressor(**best_params, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    # 6. 評価
    directional_acc = calculate_directional_accuracy(y_test.values, y_pred)
    mae = np.mean(np.abs(y_test - y_pred))
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    
    logger.info("\n" + "="*70)
    logger.info("📊 評価結果（包括的特徴量）")
    logger.info("="*70)
    logger.info(f"方向性精度: {directional_acc:.2%}")
    logger.info(f"MAE: {mae:.6f}")
    logger.info(f"RMSE: {rmse:.6f}")
    
    # 7. 特徴量重要度
    logger.info("\n" + "="*70)
    logger.info("📈 特徴量重要度 Top 20")
    logger.info("="*70)
    
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n", feature_importance.head(20).to_string(index=False))
    
    # 8. スタッキングアンサンブルで評価
    logger.info("\n🚀 スタッキングアンサンブル評価...")
    stacking = create_default_stacking_ensemble()
    stacking.fit(X_train, y_train)
    
    y_pred_stacking = stacking.predict(X_test)
    directional_acc_stacking = calculate_directional_accuracy(y_test.values, y_pred_stacking)
    
    logger.info(f"\nスタッキング方向性精度: {directional_acc_stacking:.2%}")
    
    # 9. 比較
    logger.info("\n" + "="*70)
    logger.info("📊 改善効果")
    logger.info("="*70)
    logger.info(f"基本特徴量（4個）: 56.38%")
    logger.info(f"包括的特徴量（{len(feature_cols)}個）: {directional_acc:.2%}")
    logger.info(f"改善: {(directional_acc - 0.5638)*100:+.1f}%pt")
    
    logger.info("\n" + "="*70)
    logger.info("✅ 評価完了")
    logger.info("="*70)


if __name__ == "__main__":
    main()
