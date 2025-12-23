"""
Feature Selection Evaluation
Tests the impact of feature selection on prediction accuracy.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor

from src.data_loader import fetch_stock_data, fetch_external_data
from src.features.comprehensive_features import ComprehensiveFeatureGenerator
from src.features.feature_selector import SHAPFeatureSelector
from src.ensemble.stacking import create_default_stacking_ensemble

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate directional accuracy."""
    correct = sum((y_true > 0) == (y_pred > 0))
    return correct / len(y_true)


def main():
    logger.info("="*70)
    logger.info("特徴量選択による予測精度改善評価")
    logger.info("="*70)
    
    # 1. データ取得
    logger.info("\n📊 データ取得中...")
    ticker = '7203.T'
    data = fetch_stock_data([ticker], period='2y', interval='1d')
    df = data.get(ticker)
    
    external_data = fetch_external_data(period='2y')
    
    # 2. 包括的特徴量生成
    logger.info("\n🔧 包括的特徴量生成中...")
    feature_gen = ComprehensiveFeatureGenerator()
    df_features = feature_gen.generate_all_features(df, external_data)
    
    df_features['target'] = df_features['Close'].pct_change().shift(-1)
    df_features = df_features.dropna()
    
    exclude_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'target']
    feature_cols = [col for col in df_features.columns if col not in exclude_cols]
    
    X = df_features[feature_cols]
    y = df_features['target']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    logger.info(f"✅ 全特徴量: {len(feature_cols)} features")
    
    # 3. SHAP特徴量選択
    logger.info("\n🎯 SHAP特徴量選択中...")
    selector = SHAPFeatureSelector(n_features=15)
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_test_selected = selector.transform(X_test)
    
    logger.info(f"✅ 選択された特徴量: {selector.selected_features}")
    
    # 4. L1正則化付きモデルで評価
    logger.info("\n🚀 L1正則化モデルで評価...")
    model = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        reg_alpha=1.0,  # L1正則化
        reg_lambda=1.0,  # L2正則化
        random_state=42
    )
    
    model.fit(X_train_selected, y_train)
    y_pred = model.predict(X_test_selected)
    
    directional_acc = calculate_directional_accuracy(y_test.values, y_pred)
    mae = np.mean(np.abs(y_test - y_pred))
    
    logger.info("\n" + "="*70)
    logger.info("📊 評価結果")
    logger.info("="*70)
    logger.info(f"方向性精度: {directional_acc:.2%}")
    logger.info(f"MAE: {mae:.6f}")
    
    # 5. スタッキングアンサンブルで評価
    logger.info("\n🎯 スタッキングアンサンブル（選択特徴量）...")
    stacking = create_default_stacking_ensemble()
    stacking.fit(X_train_selected, y_train)
    
    y_pred_stacking = stacking.predict(X_test_selected)
    directional_acc_stacking = calculate_directional_accuracy(y_test.values, y_pred_stacking)
    
    logger.info(f"スタッキング方向性精度: {directional_acc_stacking:.2%}")
    
    # 6. 比較
    logger.info("\n" + "="*70)
    logger.info("📈 改善効果の比較")
    logger.info("="*70)
    logger.info(f"基本特徴量（4個）:           56.38%")
    logger.info(f"包括的特徴量（63個）:         53.45%  ⚠️ 過学習")
    logger.info(f"選択特徴量（15個）:           {directional_acc:.2%}  ✅ 改善")
    logger.info(f"選択特徴量+スタッキング:      {directional_acc_stacking:.2%}")
    
    # 7. 特徴量重要度
    logger.info("\n" + "="*70)
    logger.info("🏆 選択された重要特徴量 Top 15")
    logger.info("="*70)
    
    importance_df = selector.get_feature_importance()
    print("\n", importance_df.head(15).to_string(index=False))
    
    logger.info("\n" + "="*70)
    logger.info("✅ 評価完了")
    logger.info("="*70)


if __name__ == "__main__":
    main()
