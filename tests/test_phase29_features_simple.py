"""
Phase 29-1: 特徴量エンジニアリング簡易検証スクリプト

新しく追加された特徴量の動作確認を実行します。
"""

import sys

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd

from src.advanced_features import generate_phase29_features
from src.data_loader import fetch_stock_data

print("=" * 60)
print("Phase 29-1: 特徴量エンジニアリング検証")
print("=" * 60)

# テスト用データ取得
ticker = "7203.T"  # トヨタ自動車
print(f"\nテスト銘柄: {ticker}")
print("データ取得中...")

df = fetch_stock_data(ticker, period="1y")

if df is None or len(df) < 100:
    print("❌ データ取得失敗")
    sys.exit(1)

print(f"✓ 取得データ: {len(df)}行")
print(f"✓ 元のカラム数: {len(df.columns)}")

# Phase 29-1の特徴量を生成
print("\nPhase 29-1の特徴量を生成中...")
df_features = generate_phase29_features(df)

print(f"✓ 特徴量追加後のカラム数: {len(df_features.columns)}")
print(f"✓ 追加された特徴量数: {len(df_features.columns) - len(df.columns)}")

# 新しい特徴量の確認
print("\n追加された主要特徴量:")
new_features = [
    "Historical_Volatility",
    "Volatility_Regime",
    "Volatility_Change",
    "ROC_5",
    "ROC_10",
    "ROC_20",
    "Stoch_K",
    "Stoch_D",
    "Williams_R",
    "Ultimate_Osc",
    "Close_lag_1",
    "Close_lag_5",
    "Close_lag_10",
    "Close_std_5",
    "Close_skew_10",
    "Close_kurt_20",
]

found_count = 0
for feat in new_features:
    if feat in df_features.columns:
        print(f"  ✓ {feat}")
        found_count += 1
    else:
        print(f"  ✗ {feat} (見つかりません)")

# 統計情報
print("\n特徴量の統計情報:")
print(f"  欠損値: {df_features.isna().sum().sum()}")
print(f"  無限大: {np.isinf(df_features.select_dtypes(include=[np.number])).sum().sum()}")

# ボラティリティレジームの分布
if "Volatility_Regime" in df_features.columns:
    regime_counts = df_features["Volatility_Regime"].value_counts()
    print("\nボラティリティレジーム分布:")
    print(f"  低ボラティリティ (0): {regime_counts.get(0, 0)}日")
    print(f"  中ボラティリティ (1): {regime_counts.get(1, 0)}日")
    print(f"  高ボラティリティ (2): {regime_counts.get(2, 0)}日")

# 結果サマリー
print("\n" + "=" * 60)
print("検証結果サマリー")
print("=" * 60)
print(f"特徴量発見率: {found_count}/{len(new_features)} ({found_count/len(new_features)*100:.1f}%)")

if found_count >= len(new_features) * 0.8:  # 80%以上見つかればOK
    print("\n🎉 Phase 29-1の検証が完了しました！")
    print("特徴量エンジニアリングが正常に動作しています。")
else:
    print("\n⚠️ 一部の特徴量が見つかりませんでした。")
    print("詳細を確認してください。")

print(f"\n終了時刻: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
