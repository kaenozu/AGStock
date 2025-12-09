"""
Final Benchmark - 最終精度検証
Before (Legacy) vs After (Phase 52 Ultimate) の精度比較
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import accuracy_score
import logging
from src.data_loader import fetch_stock_data
from src.advanced_features_v2 import get_advanced_features_v2

# ログ抑制
logging.getLogger("src.data_loader").setLevel(logging.ERROR)

def prepare_data_legacy(ticker="7203.T", period="1y"):
    """従来のデータと特徴量"""
    data = fetch_stock_data([ticker], period=period)
    df = data[ticker].copy()
    
    # シンプルな特徴量
    df['Returns'] = df['Close'].pct_change()
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['RSI'] = 50 + (df['Returns'] * 100) # 簡易RSI
    
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    return df.dropna()

def prepare_data_ultimate(ticker="7203.T", period="max"):
    """Phase 52 Ultimate データと特徴量"""
    # 1. データ拡張 (10y)
    data = fetch_stock_data([ticker], period=period)
    df = data[ticker].copy()
    
    # 2. 高度特徴量 V2 (Wavelet, FFT)
    v2 = get_advanced_features_v2()
    df = v2.add_wavelet_features(df)
    df = v2.add_fft_features(df)
    
    # 基本特徴量も追加
    df['Returns'] = df['Close'].pct_change()
    df['MA5'] = df['Close'].rolling(5).mean()
    df['Vol'] = df['Volume'].pct_change()
    
    # ターゲット: 翌日の騰落
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    return df.dropna()

def train_and_eval(df, name):
    """モデル学習と評価"""
    # 時系列分割
    train_size = int(len(df) * 0.8)
    train = df.iloc[:train_size]
    test = df.iloc[train_size:]
    
    features = [c for c in df.columns if c not in ['Target', 'Close', 'Open', 'High', 'Low', 'Volume', 'Adj Close']]
    
    X_train = train[features]
    y_train = train['Target']
    X_test = test[features]
    y_test = test['Target']
    
    model = lgb.LGBMClassifier(random_state=42, verbose=-1)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    
    print(f"📊 {name}")
    print(f"   データ数: {len(df)} (Train: {len(train)}, Test: {len(test)})")
    print(f"   特徴量数: {len(features)}")
    print(f"   ✅ 正解率: {acc:.2%}")
    return acc

def main():
    print("\n" + "="*50)
    print("🏆 最終精度比較ベンチマーク")
    print("="*50)
    
    ticker = "7203.T" # トヨタ自動車
    
    # 1. Legacy Performance
    print("\n[1] Legacy System (1年分データ + 基本特徴量)")
    df_old = prepare_data_legacy(ticker, period="1y")
    acc_old = train_and_eval(df_old, "Legacy")
    
    # 2. Ultimate Performance
    print("\n[2] Ultimate System (10年分データ + Wavelet/FFT)")
    df_new = prepare_data_ultimate(ticker, period="max")
    acc_new = train_and_eval(df_new, "Phase 52 Ultimate")
    
    # サマリー
    print("\n" + "="*50)
    print("📈 改善結果")
    print("="*50)
    diff = acc_new - acc_old
    print(f"改善幅: {diff:+.2%}")
    
    if acc_new > 0.55:
        print("🎉 目標達成 (>55%)")
    else:
        print("⚠️ さらなる改善の余地あり")

if __name__ == "__main__":
    main()
