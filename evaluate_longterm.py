"""
Long-term Data Evaluation
Evaluates prediction models using 26 years of historical data.
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


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio."""
    excess_returns = returns - risk_free_rate
    if np.std(excess_returns) == 0:
        return 0
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)


def main():
    logger.info("="*70)
    logger.info("26年分データによる予測精度評価")
    logger.info("="*70)
    
    # 1. 最大期間のデータ取得
    logger.info("\n📊 データ取得中（最大期間）...")
    ticker = '7203.T'
    data = fetch_stock_data([ticker], period='max', interval='1d')
    df = data.get(ticker)
    
    if df is None or df.empty:
        logger.error(f"データ取得失敗: {ticker}")
        return
    
    logger.info(f"✅ データ取得完了: {ticker}")
    logger.info(f"   期間: {df.index[0]} ～ {df.index[-1]}")
    logger.info(f"   データ量: {len(df):,} レコード")
    logger.info(f"   約 {(df.index[-1] - df.index[0]).days / 365:.1f} 年分")
    
    # 2. 外部データ取得
    external_data = fetch_external_data(period='max')
    
    # 3. 包括的特徴量生成
    logger.info("\n🔧 包括的特徴量生成中...")
    feature_gen = ComprehensiveFeatureGenerator()
    df_features = feature_gen.generate_all_features(df, external_data)
    
    # Target
    df_features['target'] = df_features['Close'].pct_change().shift(-1)
    df_features = df_features.dropna()
    
    # Feature columns
    exclude_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'target']
    feature_cols = [col for col in df_features.columns if col not in exclude_cols]
    
    logger.info(f"✅ 特徴量生成完了: {len(feature_cols)} features")
    logger.info(f"   有効サンプル数: {len(df_features):,}")
    
    # 4. Train/Test split (80/20)
    X = df_features[feature_cols]
    y = df_features['target']
    
    # Time-series split (最後の20%をテスト)
    split_idx = int(len(X) * 0.8)
    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]
    
    logger.info(f"\n📊 データ分割:")
    logger.info(f"   Train: {len(X_train):,} samples ({X_train.index[0]} ～ {X_train.index[-1]})")
    logger.info(f"   Test:  {len(X_test):,} samples ({X_test.index[0]} ～ {X_test.index[-1]})")
    
    # 5. 基本モデル（全特徴量）
    logger.info("\n🎯 基本モデル評価（全特徴量）...")
    model_full = LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=8,
        num_leaves=64,
        reg_alpha=0.5,
        reg_lambda=0.5,
        random_state=42
    )
    
    model_full.fit(X_train, y_train)
    y_pred_full = model_full.predict(X_test)
    
    acc_full = calculate_directional_accuracy(y_test.values, y_pred_full)
    sharpe_full = calculate_sharpe_ratio(y_pred_full)
    
    logger.info(f"方向性精度: {acc_full:.2%}")
    logger.info(f"シャープレシオ: {sharpe_full:.2f}")
    
    # 6. SHAP特徴量選択
    logger.info("\n🎯 SHAP特徴量選択...")
    selector = SHAPFeatureSelector(n_features=20)
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_test_selected = selector.transform(X_test)
    
    logger.info(f"選択された特徴量: {selector.selected_features[:10]}...")
    
    # 7. 選択特徴量モデル
    logger.info("\n🚀 選択特徴量モデル評価...")
    model_selected = LGBMRegressor(
        n_estimators=300,
        learning_rate=0.03,
        max_depth=8,
        num_leaves=64,
        reg_alpha=1.0,
        reg_lambda=1.0,
        random_state=42
    )
    
    model_selected.fit(X_train_selected, y_train)
    y_pred_selected = model_selected.predict(X_test_selected)
    
    acc_selected = calculate_directional_accuracy(y_test.values, y_pred_selected)
    sharpe_selected = calculate_sharpe_ratio(y_pred_selected)
    
    logger.info(f"方向性精度: {acc_selected:.2%}")
    logger.info(f"シャープレシオ: {sharpe_selected:.2f}")
    
    # 8. スタッキングアンサンブル
    logger.info("\n🎯 スタッキングアンサンブル評価...")
    stacking = create_default_stacking_ensemble()
    stacking.fit(X_train_selected, y_train)
    
    y_pred_stacking = stacking.predict(X_test_selected)
    acc_stacking = calculate_directional_accuracy(y_test.values, y_pred_stacking)
    sharpe_stacking = calculate_sharpe_ratio(y_pred_stacking)
    
    logger.info(f"方向性精度: {acc_stacking:.2%}")
    logger.info(f"シャープレシオ: {sharpe_stacking:.2f}")
    
    # 9. 結果比較
    logger.info("\n" + "="*70)
    logger.info("📊 最終結果比較")
    logger.info("="*70)
    
    results = pd.DataFrame({
        'モデル': [
            'ベースライン（2年、4特徴量）',
            '全特徴量（26年、63特徴量）',
            '選択特徴量（26年、20特徴量）',
            'スタッキング（26年、20特徴量）'
        ],
        'データ量': ['487', f'{len(X_train):,}', f'{len(X_train):,}', f'{len(X_train):,}'],
        '方向性精度': ['56.38%', f'{acc_full:.2%}', f'{acc_selected:.2%}', f'{acc_stacking:.2%}'],
        'シャープレシオ': ['-', f'{sharpe_full:.2f}', f'{sharpe_selected:.2f}', f'{sharpe_stacking:.2f}']
    })
    
    print("\n", results.to_string(index=False))
    
    # 10. 改善率
    baseline_acc = 0.5638
    improvement_full = (acc_full - baseline_acc) * 100
    improvement_selected = (acc_selected - baseline_acc) * 100
    improvement_stacking = (acc_stacking - baseline_acc) * 100
    
    logger.info("\n" + "="*70)
    logger.info("📈 ベースラインからの改善")
    logger.info("="*70)
    logger.info(f"全特徴量:       {improvement_full:+.1f}%pt")
    logger.info(f"選択特徴量:     {improvement_selected:+.1f}%pt")
    logger.info(f"スタッキング:   {improvement_stacking:+.1f}%pt")
    
    # 11. 特徴量重要度
    logger.info("\n" + "="*70)
    logger.info("🏆 重要特徴量 Top 10")
    logger.info("="*70)
    
    importance_df = selector.get_feature_importance()
    print("\n", importance_df.head(10).to_string(index=False))
    
    logger.info("\n" + "="*70)
    logger.info("✅ 評価完了")
    logger.info("="*70)


if __name__ == "__main__":
    main()
