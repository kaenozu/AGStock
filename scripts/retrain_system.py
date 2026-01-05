"""
AI自動再学習システム
最新データを使用してモデルを更新し、予測精度を維持します。
"""

import logging
import os
from datetime import datetime, timedelta
import pandas as pd
from src.data_loader import fetch_stock_data
from src.lgbm_predictor import LightGBMPredictor
from src.notification_system import send_system_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrain_models():
    """主要銘柄のモデルを再学習"""
    logger.info("🚀 AIモデルの自動再学習を開始します...")
    
    # 再学習対象（主要銘柄）
    tickers = ["7203.T", "9984.T", "8035.T", "6758.T", "^N225"]
    
    success_count = 0
    for ticker in tickers:
        try:
            logger.info(f"📈 {ticker} のデータを取得中...")
            # 過去2年分のデータで再学習
            data = fetch_stock_data([ticker], period="2y")
            df = data.get(ticker)
            
            if df is None or len(df) < 100:
                logger.warning(f"⚠️ {ticker} のデータが不足しています。スキップします。")
                continue
                
            predictor = LightGBMPredictor()
            logger.info(f"⚙️ {ticker} のモデルを訓練中...")
            metrics = predictor.train(df)
            
            # モデルを保存
            model_path = f"models/production/{ticker}_latest.pkl"
            os.makedirs("models/production", exist_ok=True)
            predictor.save(model_path)
            
            logger.info(f"✅ {ticker} 再学習完了: Accuracy={metrics.get('accuracy', 0):.2%}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ {ticker} の再学習中にエラーが発生しました: {e}")

    # 結果を通知
    if success_count > 0:
        send_system_alert(
            f"AI再学習が完了しました。{success_count} 個のモデルを最新データで更新しました。",
            severity="info"
        )
    else:
        send_system_alert("AI再学習に失敗しました。ログを確認してください。", severity="critical")

if __name__ == "__main__":
    retrain_models()
