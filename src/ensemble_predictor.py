"""
アンサンブル予測モジュール（拡張版）
複数のモデル（LSTM, LightGBM, Prophet, SMA）+ ファンダメンタルズを組み合わせて、
より堅牢で信頼性の高い予測を提供します。
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from src.future_predictor import FuturePredictor
from src.lgbm_predictor import LGBMPredictor
from src.prophet_predictor import ProphetPredictor
from src.fundamental_analyzer import FundamentalAnalyzer

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    def __init__(self):
        # 各予測モデルを初期化
        self.lstm_predictor = FuturePredictor()
        self.lgbm_predictor = LGBMPredictor()
        self.prophet_predictor = ProphetPredictor()
        self.fundamental_analyzer = FundamentalAnalyzer()
        
        # 基本重み（ファンダメンタルズで調整される）
        self.base_weights = {
            'lstm': 0.35,     # ディープラーニング
            'lgbm': 0.30,     # 決定木
            'prophet': 0.20,  # 時系列専門
            'sma': 0.15       # ベースライン
        }
        
    def predict_trajectory(
        self, 
        df: pd.DataFrame, 
        days_ahead: int = 5,
        ticker: Optional[str] = None,
        fundamentals: Optional[Dict] = None
    ) -> Dict:
        """
        アンサンブル予測を実行
        
        Args:
            df: 価格データ
            days_ahead: 予測日数
            ticker: ティッカーシンボル（ファンダメンタルズ分析用）
            fundamentals: ファンダメンタルズデータ（オプション）
        """
        try:
            # 1. ファンダメンタルズ分析（利用可能な場合）
            fundamental_result = None
            confidence_multiplier = 1.0
            
            if ticker and fundamentals:
                fundamental_result = self.fundamental_analyzer.analyze(ticker, fundamentals)
                confidence_multiplier = fundamental_result['confidence_multiplier']
                logger.info(f"{ticker}: ファンダメンタルズ評価={fundamental_result['valuation']}, "
                          f"スコア={fundamental_result['score']}")
            
            # 2. 各モデルで予測を実行
            predictions = {}
            
            # LSTM予測
            lstm_result = self.lstm_predictor.predict_trajectory(df, days_ahead)
            if "error" not in lstm_result:
                predictions['lstm'] = lstm_result
                logger.info(f"LSTM予測: {lstm_result['trend']} ({lstm_result['change_pct']:+.1f}%)")
            else:
                logger.warning(f"LSTM prediction failed: {lstm_result['error']}")
            
            # LightGBM予測
            lgbm_result = self.lgbm_predictor.predict_trajectory(df, days_ahead)
            if "error" not in lgbm_result:
                predictions['lgbm'] = lgbm_result
                logger.info(f"LightGBM予測: {lgbm_result['trend']} ({lgbm_result['change_pct']:+.1f}%)")
            else:
                logger.warning(f"LightGBM prediction failed: {lgbm_result['error']}")
            
            # Prophet予測
            prophet_result = self.prophet_predictor.predict_trajectory(df, days_ahead)
            if "error" not in prophet_result:
                predictions['prophet'] = prophet_result
                logger.info(f"Prophet予測: {prophet_result['trend']} ({prophet_result['change_pct']:+.1f}%)")
            else:
                logger.warning(f"Prophet prediction failed: {prophet_result['error']}")
            
            # SMA予測（ベースライン）
            sma_result = self._predict_sma(df, days_ahead)
            predictions['sma'] = sma_result
            logger.info(f"SMA予測: {sma_result['trend']} ({sma_result['change_pct']:+.1f}%)")
            
            # 3. 予測が1つもない場合はエラー
            if not predictions:
                return {"error": "全てのモデルが予測に失敗しました"}
            
            # 4. アンサンブル（加重平均）
            # 利用可能なモデルの重みを正規化
            available_models = list(predictions.keys())
            total_weight = sum(self.base_weights[m] for m in available_models)
            normalized_weights = {m: self.base_weights[m] / total_weight for m in available_models}
            
            # 予測値の配列を取得
            pred_arrays = {}
            for model_name in available_models:
                pred_arrays[model_name] = np.array(predictions[model_name]['predictions'])
            
            # 加重平均を計算
            final_preds = np.zeros(days_ahead)
            for model_name, weight in normalized_weights.items():
                final_preds += pred_arrays[model_name] * weight
            
            # ファンダメンタルズで調整
            # 割安なら上昇予測を強め、割高なら弱める
            current_price = df['Close'].iloc[-1]
            adjustment_factor = (final_preds - current_price) / current_price
            adjusted_preds = current_price + (adjustment_factor * current_price * confidence_multiplier)
            
            # 5. 結果の整形
            peak_price = max(adjusted_preds)
            peak_day_idx = list(adjusted_preds).index(peak_price)
            
            trend = "FLAT"
            if adjusted_preds[-1] > current_price * 1.01:
                trend = "UP"
            elif adjusted_preds[-1] < current_price * 0.99:
                trend = "DOWN"
                
            # 各モデルのトレンド集計
            trend_votes = {'UP': 0, 'DOWN': 0, 'FLAT': 0}
            for model_result in predictions.values():
                trend_votes[model_result['trend']] += 1
                
            return {
                "current_price": current_price,
                "predictions": adjusted_preds.tolist(),
                "peak_price": peak_price,
                "peak_day": peak_day_idx + 1,
                "trend": trend,
                "change_pct": (adjusted_preds[-1] - current_price) / current_price * 100,
                "details": {
                    "models_used": available_models,
                    "trend_votes": trend_votes,
                    "lstm_trend": predictions.get('lstm', {}).get('trend', 'N/A'),
                    "lgbm_trend": predictions.get('lgbm', {}).get('trend', 'N/A'),
                    "prophet_trend": predictions.get('prophet', {}).get('trend', 'N/A'),
                    "sma_trend": predictions.get('sma', {}).get('trend', 'N/A'),
                    "fundamental": fundamental_result
                }
            }
            
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def _predict_sma(self, df: pd.DataFrame, days_ahead: int) -> Dict:
        """
        単純移動平均に基づく予測（ベースライン）
        直近のモメンタムを単純に延長する
        """
        current_price = df['Close'].iloc[-1]
        
        # 直近5日間の平均変化率
        recent_returns = df['Close'].pct_change().tail(5).mean()
        
        # 変化率が極端にならないようにクリップ (-3% ~ +3%)
        recent_returns = np.clip(recent_returns, -0.03, 0.03)
        
        predictions = []
        price = current_price
        
        for _ in range(days_ahead):
            price = price * (1 + recent_returns)
            predictions.append(price)
            
        trend = "FLAT"
        if predictions[-1] > current_price * 1.01:
            trend = "UP"
        elif predictions[-1] < current_price * 0.99:
            trend = "DOWN"
            
        return {
            "current_price": current_price,
            "predictions": predictions,
            "peak_price": max(predictions),
            "trend": trend,
            "change_pct": (predictions[-1] - current_price) / current_price * 100
        }
