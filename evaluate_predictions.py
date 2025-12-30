"""
Prediction Accuracy Evaluation
Measures the effectiveness of implemented prediction techniques.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# Import our implementations
from src.data_loader import fetch_stock_data
from src.lgbm_predictor import LGBMPredictor
from src.ensemble.stacking import create_default_stacking_ensemble
from src.optimization.hyperparameter_tuner import HyperparameterOptimizer
from src.validation.walk_forward import WalkForwardValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare features for prediction."""
    df = df.copy()
    
    # Technical indicators
    df['SMA_5'] = df['Close'].rolling(5).mean()
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    
    # Target: next day return
    df['target'] = df['Close'].pct_change().shift(-1)
    
    # Drop NaN
    df = df.dropna()
    
    return df


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate directional accuracy (up/down prediction)."""
    correct = sum((y_true > 0) == (y_pred > 0))
    return correct / len(y_true)


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> dict:
    """Evaluate a single model."""
    logger.info(f"\n{'='*50}")
    logger.info(f"Evaluating: {model_name}")
    logger.info(f"{'='*50}")
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    directional_acc = calculate_directional_accuracy(y_test.values, y_pred)
    
    # Sharpe ratio (simplified)
    returns = y_pred
    sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
    
    results = {
        'model': model_name,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'directional_accuracy': directional_acc,
        'sharpe_ratio': sharpe
    }
    
    logger.info(f"MAE: {mae:.6f}")
    logger.info(f"RMSE: {rmse:.6f}")
    logger.info(f"R²: {r2:.4f}")
    logger.info(f"Directional Accuracy: {directional_acc:.2%}")
    logger.info(f"Sharpe Ratio: {sharpe:.2f}")
    
    return results


def main():
    logger.info("="*70)
    logger.info("予測精度向上手法の効果測定")
    logger.info("="*70)
    
    # 1. データ取得
    logger.info("\n📊 データ取得中...")
    tickers = ['7203.T', '6758.T', '9984.T']  # トヨタ、ソニー、ソフトバンク
    data = fetch_stock_data(tickers, period='2y', interval='1d')
    
    # 最初の銘柄で評価
    ticker = tickers[0]
    df = data.get(ticker)
    
    if df is None or df.empty:
        logger.error(f"データ取得失敗: {ticker}")
        return
    
    logger.info(f"✅ データ取得完了: {ticker} ({len(df)} rows)")
    
    # 2. 特徴量準備
    logger.info("\n🔧 特徴量準備中...")
    df = prepare_features(df)
    
    feature_cols = ['SMA_5', 'SMA_20', 'RSI', 'Volume_MA']
    X = df[feature_cols]
    y = df['target']
    
    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    logger.info(f"✅ 特徴量準備完了")
    logger.info(f"   Train: {len(X_train)} samples")
    logger.info(f"   Test: {len(X_test)} samples")
    
    # 3. ベースライン（単純LGBM）
    logger.info("\n🔍 ベースライン評価...")
    baseline = LGBMPredictor()
    baseline.fit(X_train, y_train)
    baseline_results = evaluate_model(baseline, X_test, y_test, "Baseline LGBM")
    
    # 4. ハイパーパラメータ最適化
    logger.info("\n🎯 ハイパーパラメータ最適化...")
    optimizer = HyperparameterOptimizer(n_trials=20)  # 20 trials for speed
    best_params = optimizer.optimize_lgbm(X_train, y_train)
    
    from lightgbm import LGBMRegressor
    optimized_model = LGBMRegressor(**best_params, random_state=42)
    optimized_model.fit(X_train, y_train)
    optimized_results = evaluate_model(optimized_model, X_test, y_test, "Optimized LGBM")
    
    # 5. スタッキングアンサンブル
    logger.info("\n🚀 スタッキングアンサンブル評価...")
    stacking = create_default_stacking_ensemble()
    stacking.fit(X_train, y_train)
    stacking_results = evaluate_model(stacking, X_test, y_test, "Stacking Ensemble")
    
    # 6. 結果比較
    logger.info("\n" + "="*70)
    logger.info("📊 結果比較")
    logger.info("="*70)
    
    results_df = pd.DataFrame([
        baseline_results,
        optimized_results,
        stacking_results
    ])
    
    print("\n")
    print(results_df.to_string(index=False))
    
    # 7. 改善率計算
    logger.info("\n" + "="*70)
    logger.info("📈 改善率")
    logger.info("="*70)
    
    baseline_acc = baseline_results['directional_accuracy']
    optimized_acc = optimized_results['directional_accuracy']
    stacking_acc = stacking_results['directional_accuracy']
    
    logger.info(f"\nベースライン → 最適化:")
    logger.info(f"  方向性精度: {baseline_acc:.2%} → {optimized_acc:.2%} "
                f"({(optimized_acc - baseline_acc)*100:+.1f}%pt)")
    
    logger.info(f"\nベースライン → スタッキング:")
    logger.info(f"  方向性精度: {baseline_acc:.2%} → {stacking_acc:.2%} "
                f"({(stacking_acc - baseline_acc)*100:+.1f}%pt)")
    
    logger.info(f"\n最適化 → スタッキング:")
    logger.info(f"  方向性精度: {optimized_acc:.2%} → {stacking_acc:.2%} "
                f"({(stacking_acc - optimized_acc)*100:+.1f}%pt)")
    
    # 8. Walk-Forward検証
    logger.info("\n" + "="*70)
    logger.info("🔄 Walk-Forward検証")
    logger.info("="*70)
    
    validator = WalkForwardValidator(
        train_period_days=365,
        test_period_days=30,
        step_days=30
    )
    
    # Reset index for walk-forward
    df_wf = df.reset_index()
    wf_metrics = validator.validate_model(
        stacking,
        df_wf,
        feature_cols,
        'target'
    )
    
    logger.info(f"\nWalk-Forward結果:")
    logger.info(f"  方向性精度: {wf_metrics['directional_accuracy']:.2%}")
    logger.info(f"  MAPE: {wf_metrics['mape']:.4f}")
    logger.info(f"  シャープレシオ: {wf_metrics.get('sharpe_ratio', 0):.2f}")
    logger.info(f"  予測数: {wf_metrics['total_predictions']}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ 効果測定完了")
    logger.info("="*70)


if __name__ == "__main__":
    main()
