"""
最強のAIモデル最適化・再学習システム
Optunaを使用して銘柄ごとに最適なパラメータを探索し、精度を極限まで高めます。
"""
import logging
import os
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
from src.data_loader import fetch_stock_data
from src.notification_system import send_system_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_features(df):
    """高度な特徴量生成"""
    df = df.copy()
    df["Returns"] = df["Close"].pct_change()
    df["Vol_5"] = df["Close"].rolling(5).std()
    df["Vol_20"] = df["Close"].rolling(20).std()
    df["SMA_Gap"] = (df["Close"] - df["Close"].rolling(20).mean()) / df["Close"].rolling(20).mean()
    
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + gain/(loss + 1e-9)))
    
    df["Target"] = df["Close"].pct_change().shift(-1)
    return df.dropna()

def objective(trial, X, y):
    """Optuna用目的関数"""
    params = {
        "objective": "regression",
        "metric": "rmse",
        "verbosity": -1,
        "boosting_type": "gbdt",
        "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 2, 256),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.4, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.4, 1.0),
        "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
    }
    
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    model = lgb.LGBMRegressor(**params)
    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    return np.sqrt(np.mean((y_val - preds)**2))

def optimize_and_train():
    tickers = ["7203.T", "9984.T", "8035.T", "^N225"]
    results = []

    for ticker in tickers:
        logger.info(f"🔥 {ticker} の最適化を開始...")
        data = fetch_stock_data([ticker], period="2y")
        df = data.get(ticker)
        if df is None or len(df) < 100: continue
        
        df = create_features(df)
        feature_cols = ["Returns", "Vol_5", "Vol_20", "SMA_Gap", "RSI"]
        X, y = df[feature_cols].values, df["Target"].values
        
        # パラメータ探索
        study = optuna.create_study(direction="minimize")
        study.optimize(lambda t: objective(t, X, y), n_trials=30)
        
        best_params = study.best_params
        logger.info(f"✅ {ticker} 最適パラメータ発見: {best_params}")
        
        # 最強モデルで最終学習
        model = lgb.LGBMRegressor(**best_params, verbosity=-1)
        model.fit(X, y)
        
        # モデル保存
        model_path = f"models/production/{ticker}_optimized.pkl"
        import pickle
        os.makedirs("models/production", exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
            
        results.append(f"{ticker}: RMSE={study.best_value:.5f}")

    send_system_alert("AIモデルの究極最適化が完了しました。\n" + "\n".join(results), "info")

if __name__ == "__main__":
    optimize_and_train()
