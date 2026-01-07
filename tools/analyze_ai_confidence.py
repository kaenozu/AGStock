import pandas as pd
import numpy as np
from src.data_loader import fetch_stock_data
from src.strategies.ml import MLStrategy
import logging

# 
logging.basicConfig(level=logging.ERROR)

def analyze_confidence_vs_accuracy():
    ticker = "9984.T"  # EEEG
    print(f"--- AIEEE(: {ticker}) ---")
    
    # 1. EEE(yfinanceE
    import yfinance as yf
    df = yf.download(ticker, period="5y")
    if df is None or len(df) < 500: 
        print(f"EEEE {len(df) if df is not None else 0}")
        return
    
    # Flatten columns if multi-index (recent yfinance versions)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 2. MLStrategy EEEEE    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # E    import ta
    df["RSI"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["SMA_Ratio"] = df["SMA_20"] / df["SMA_50"]
    df["Volatility"] = df["Close"].rolling(window=20).std() / df["Close"]
    df["Ret_1"] = df["Close"].pct_change(1)
    df["Ret_5"] = df["Close"].pct_change(5)
    df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    df['next_ret'] = df['Close'].pct_change().shift(-1)
    df.dropna(inplace=True)
    
    features = ["RSI", "SMA_Ratio", "Volatility", "Ret_1", "Ret_5"]
    X = df[features]
    y = df["Target"]
    
    # 
    results = []
    train_size = 500 # EEE    test_step = 50 
    
    for i in range(train_size, len(df) - test_step, test_step):
        X_train = X.iloc[i-train_size:i]
        y_train = y.iloc[i-train_size:i]
        X_test = X.iloc[i:i+test_step]
        
        model.fit(X_train, y_train)
        probs = model.predict_proba(X_test)[:, 1]
        
        test_data = df.iloc[i:i+test_step].copy()
        test_data['prob'] = probs
        results.append(test_data)
    
    if not results:
        print("E)"
        return
        
    full_results = pd.concat(results)
    
    # 3. EEEEE    full_results['conf_bin'] = pd.cut(full_results['prob'], bins=[0, 0.4, 0.45, 0.5, 0.55, 0.6, 1.0])
    
    report = full_results.groupby('conf_bin', observed=True).agg({
        'Target': ['count', 'mean'],
        'next_ret': 'mean'
    })
    report.columns = ['', 'EEEEE, 'E']'
    
    print("\n========================================================")
    print("  E")
    print("========================================================")
    print(report)
    print("========================================================")
    print("\nEEE)"
    print(" EE 0.5 (50%) EEAIE)"
    print(" (prob)E0.6 EEEEEE)"
    print(" E 0.4 EEEE)"

if __name__ == "__main__":
    analyze_confidence_vs_accuracy()