"""
未来予測UIの動作確認スクリプト
"""
import sys
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

# Streamlitをモック
sys.modules["streamlit"] = MagicMock()
import streamlit as st

# 必要なモジュールをインポート
from src.future_predictor import FuturePredictor

def verify_prediction_ui():
    print("🔍 未来予測UIロジックの動作確認を開始します...")
    
    # 1. データ不足のケース（21件）
    print("\n🧪 テストケース1: データ不足（21件）")
    df_short = pd.DataFrame({
        'Close': np.random.rand(21) * 100,
        'Volume': np.random.rand(21) * 1000,
        'High': np.random.rand(21) * 100,
        'Low': np.random.rand(21) * 100,
        'Open': np.random.rand(21) * 100
    })
    
    predictor = FuturePredictor()
    result = predictor.predict_trajectory(df_short, days_ahead=5)
    
    if "error" in result:
        print(f"❌ エラー: {result['error']}")
    else:
        print(f"✅ 成功: トレンド={result['trend']}, 変動={result['change_pct']:.2f}%")
        print(f"   予測価格: {result['predictions']}")
    
    # 2. データ十分なケース（100件）
    print("\n🧪 テストケース2: データ十分（100件）")
    df_long = pd.DataFrame({
        'Close': np.random.rand(100) * 100,
        'Volume': np.random.rand(100) * 1000,
        'High': np.random.rand(100) * 100,
        'Low': np.random.rand(100) * 100,
        'Open': np.random.rand(100) * 100
    })
    
    result_long = predictor.predict_trajectory(df_long, days_ahead=5)
    
    if "error" in result_long:
        print(f"❌ エラー: {result_long['error']}")
    else:
        print(f"✅ 成功: トレンド={result_long['trend']}, 変動={result_long['change_pct']:.2f}%")
    
    print("\n✅ 動作確認完了")

if __name__ == "__main__":
    verify_prediction_ui()
