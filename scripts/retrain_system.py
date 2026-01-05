"""
AI自動再学習システム
最新データを使用してモデルを更新し、予測精度を維持します。
"""
import logging
import os
import pandas as pd
from src.data_loader import fetch_stock_data
from src.lgbm_predictor import LGBMPredictor
from src.notification_system import send_system_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrain_models():
    logger.info("🚀 AIモデルの自動再学習を開始します...")
    tickers = ["7203.T", "9984.T", "^N225"]
    
    success_count = 0
    for ticker in tickers:
        try:
            logger.info(f"📈 {ticker} データを取得中...")
            data = fetch_stock_data([ticker], period="1y")
            df = data.get(ticker)
            
            if df is None or len(df) < 50:
                continue
                
            predictor = LGBMPredictor()
            predictor.fit(df)
            
            model_path = f"models/production/{ticker}_latest.pkl"
            os.makedirs("models/production", exist_ok=True)
            predictor.save(model_path)
            
            logger.info(f"✅ {ticker} 再学習完了")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ {ticker} エラー: {e}")

    if success_count > 0:
        send_system_alert(f"AI再学習が完了しました（{success_count}銘柄）。", "info")

if __name__ == "__main__":
    retrain_models()
