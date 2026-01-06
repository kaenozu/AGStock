import pandas as pd
import numpy as np
import lightgbm as lgb
from src.data_loader import fetch_stock_data

def evaluate_current_performance(ticker="7203.T"):
    # データを取得（過去1年）
    data = fetch_stock_data([ticker], period="1y")
    df = data.get(ticker)
    if df is None or len(df) < 60:
        return "データ不足"

    # 特徴量生成
    df = df.copy()
    df["Returns"] = df["Close"].pct_change()
    df["SMA_5"] = df["Close"].rolling(5).mean()
    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["Volatility"] = df["Close"].rolling(20).std()
    
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + gain/loss))
    
    df["Target"] = df["Close"].pct_change().shift(-1)
    df.dropna(inplace=True)

    # 分割
    feature_cols = ["Returns", "SMA_5", "SMA_20", "Volatility", "RSI"]
    X = df[feature_cols].values
    y = df["Target"].values
    
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # 学習
    model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, verbose=-1)
    model.fit(X_train, y_train)

    # 評価
    y_pred = model.predict(X_test)
    
    # 指標
    # 1. 的中率 (正負の一致)
    hit_rate = np.mean((y_pred > 0) == (y_test > 0))
    
    # 2. 利益（予測がプラスなら買い、マイナスなら何もしない/売る場合の仮想リターン）
    strategy_returns = np.where(y_pred > 0, y_test, 0)
    cumulative_return = (1 + strategy_returns).prod() - 1
    market_return = (1 + y_test).prod() - 1

    return {
        "ticker": ticker,
        "hit_rate": hit_rate,
        "strategy_return": cumulative_return,
        "market_return": market_return,
        "test_days": len(y_test)
    }

if __name__ == "__main__":
    for t in ["7203.T", "9984.T", "^N225"]:
        res = evaluate_current_performance(t)
        if isinstance(res, dict):
            print(f"[{res['ticker']}]")
            print(f"  的中率 (Directional Accuracy): {res['hit_rate']:.2%}")
            print(f"  戦略リターン (期間内): {res['strategy_return']:+.2%}")
            print(f"  市場リターン (同期間): {res['market_return']:+.2%}")
            print(f"  検証日数: {res['test_days']} days")
        else:
            print(f"[{t}] {res}")
