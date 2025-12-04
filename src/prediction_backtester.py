"""
予測バックテストエンジン
過去データで予測の精度を検証し、各モデルのパフォーマンスを評価します。
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from src.ensemble_predictor import EnsemblePredictor
from src.data_loader import fetch_stock_data, fetch_fundamental_data

logger = logging.getLogger(__name__)

class PredictionBacktester:
    def __init__(self):
        self.predictor = EnsemblePredictor()
        
    def run_backtest(
        self, 
        ticker: str, 
        start_date: str,
        end_date: str,
        prediction_days: int = 5
    ) -> Dict:
        """
        指定期間で予測のバックテストを実行
        
        Args:
            ticker: ティッカーシンボル
            start_date: バックテスト開始日 (YYYY-MM-DD)
            end_date: バックテスト終了日 (YYYY-MM-DD)
            prediction_days: 予測日数
            
        Returns:
            バックテスト結果の辞書
        """
        try:
            logger.info(f"Starting backtest for {ticker}: {start_date} to {end_date}")
            
            # データ取得
            data_map = fetch_stock_data([ticker], period="2y")
            df = data_map.get(ticker)
            
            if df is None or df.empty:
                return {"error": f"データ取得失敗: {ticker}"}
            
            # ファンダメンタルズ取得（最新のみ）
            fundamentals = fetch_fundamental_data(ticker)
            
            # 日付範囲をフィルタ
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # バックテスト期間内の各日で予測を実行
            predictions = []
            actuals = []
            dates = []
            
            # 予測を行う日付リストを生成（週次でサンプリング）
            test_dates = pd.date_range(start=start_dt, end=end_dt, freq='W')
            
            for test_date in test_dates:
                # その日までのデータで予測
                historical_data = df[df.index < test_date]
                
                if len(historical_data) < 50:
                    continue  # データ不足
                
                # 予測実行
                result = self.predictor.predict_trajectory(
                    historical_data,
                    days_ahead=prediction_days,
                    ticker=ticker,
                    fundamentals=fundamentals
                )
                
                if "error" in result:
                    logger.warning(f"Prediction failed for {test_date}: {result['error']}")
                    continue
                
                # 実際の結果を取得
                future_date = test_date + timedelta(days=prediction_days)
                future_data = df[(df.index >= test_date) & (df.index <= future_date)]
                
                if len(future_data) < prediction_days:
                    continue  # 未来データ不足
                
                # 予測値と実際の値を記録
                predicted_price = result['predictions'][-1]
                actual_price = future_data['Close'].iloc[-1]
                current_price = historical_data['Close'].iloc[-1]
                
                predicted_change_pct = (predicted_price - current_price) / current_price * 100
                actual_change_pct = (actual_price - current_price) / current_price * 100
                
                predictions.append({
                    'date': test_date,
                    'current_price': current_price,
                    'predicted_price': predicted_price,
                    'actual_price': actual_price,
                    'predicted_change_pct': predicted_change_pct,
                    'actual_change_pct': actual_change_pct,
                    'predicted_trend': result['trend'],
                    'actual_trend': 'UP' if actual_change_pct > 1 else 'DOWN' if actual_change_pct < -1 else 'FLAT',
                    'models_used': result['details'].get('models_used', []),
                    'trend_votes': result['details'].get('trend_votes', {}),
                    'fundamental_score': result['details'].get('fundamental', {}).get('score', None) if result['details'].get('fundamental') else None
                })
                
                dates.append(test_date)
            
            if not predictions:
                return {"error": "有効な予測データがありません"}
            
            # 精度指標の計算
            metrics = self._calculate_metrics(predictions)
            
            return {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "prediction_days": prediction_days,
                "total_predictions": len(predictions),
                "predictions": predictions,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def _calculate_metrics(self, predictions: List[Dict]) -> Dict:
        """
        予測精度の指標を計算
        """
        # 方向性の正解率（UP/DOWN/FLATが一致したか）
        direction_correct = sum(
            1 for p in predictions 
            if p['predicted_trend'] == p['actual_trend']
        )
        direction_accuracy = direction_correct / len(predictions) * 100
        
        # 平均絶対誤差（MAE）
        mae = np.mean([
            abs(p['predicted_change_pct'] - p['actual_change_pct'])
            for p in predictions
        ])
        
        # 平均二乗誤差の平方根（RMSE）
        rmse = np.sqrt(np.mean([
            (p['predicted_change_pct'] - p['actual_change_pct']) ** 2
            for p in predictions
        ]))
        
        # 予測に従って取引した場合のWin Rate
        # UP予測で実際UP、またはDOWN予測で実際DOWN
        profitable_trades = sum(
            1 for p in predictions
            if (p['predicted_trend'] == 'UP' and p['actual_change_pct'] > 0) or
               (p['predicted_trend'] == 'DOWN' and p['actual_change_pct'] < 0)
        )
        
        # FLAT予測は除外
        tradable_predictions = [p for p in predictions if p['predicted_trend'] != 'FLAT']
        win_rate = (profitable_trades / len(tradable_predictions) * 100) if tradable_predictions else 0
        
        # 信頼区間（95%）
        errors = [p['predicted_change_pct'] - p['actual_change_pct'] for p in predictions]
        confidence_interval = 1.96 * np.std(errors)
        
        return {
            'direction_accuracy': direction_accuracy,
            'mae': mae,
            'rmse': rmse,
            'win_rate': win_rate,
            'confidence_interval_95': confidence_interval,
            'total_samples': len(predictions),
            'tradable_samples': len(tradable_predictions)
        }
    
    def compare_models(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        各モデルのパフォーマンスを比較
        
        注: 現在のEnsemblePredictorは各モデルを個別に実行しているので、
        details から各モデルの予測を取得して評価できます。
        """
        # 実装は複雑になるため、まずは統合アンサンブルのみを評価
        # 将来的には各モデル単体のバックテストも追加可能
        pass
