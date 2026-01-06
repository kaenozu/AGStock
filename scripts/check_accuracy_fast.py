import pandas as pd
import numpy as np
from src.data_loader import fetch_stock_data
from src.lgbm_predictor import LGBMPredictor
from src.data_preprocessing import preprocess_for_prediction

def check_current_accuracy(ticker="7203.T"):
    # 1. 過去1年分のデータを取得
    data = fetch_stock_data([ticker], period="1y")
    df = data.get(ticker)
    if df is None or len(df) < 100:
        return None

    # 2. 前処理
    X, y = preprocess_for_prediction(df)
    
    # 3. 直近20%をテストデータとして評価
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    # 4. モデル訓練
    predictor = LGBMPredictor()
    predictor.fit(X_train, y_train)
    
    # 5. 予測と評価
    y_pred = predictor.predict(X_test)
    
    # 方向性の的中率 (UP/DOWN)
    accuracy = np.mean((y_pred > 0) == (y_test > 0))
    
    return {
        "ticker": ticker,
        "accuracy": accuracy,
        "test_samples": len(y_test),
        "period": "Last 1 year (out-of-sample)"
    }

if __name__ == "__main__":
    results = check_current_accuracy()
    if results:
        print(f"--- Accuracy Report ---")
        print(f"Target: {results['ticker']}")
        print(f"Directional Accuracy: {results['accuracy']:.2%}")
        print(f"Evaluation Method: {results['period']}")
        print(f"Test Samples: {results['test_samples']} trading days")
    else:
        print("Data insufficient for accuracy check.")
