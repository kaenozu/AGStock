"""
AGStock 次世代型フルオート・トレーダー
AI投資委員会、リスクガード、オンライン学習を統合した完全自律型システム
"""
import logging
import time
from datetime import datetime
from src.data_loader import fetch_stock_data
from src.lgbm_predictor import LGBMPredictor
from src.agents.committee import InvestmentCommittee
from src.risk_guard import RiskGuard
from src.online_learner import OnlineLearner
from src.notification_system import notification_manager, send_trade_notification
from src.smart_notifier import SmartNotifier
from src.paper_trader import PaperTrader
from src.execution import ExecutionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomousTrader:
    def __init__(self):
        self.committee = InvestmentCommittee()
        self.risk_guard = RiskGuard()
        self.learner = OnlineLearner()
        self.predictor = LGBMPredictor()

    def run_daily_cycle(self):
        """1日の運用サイクルを実行"""
        logger.info("⚡ 自律運用サイクル開始")
        
        tickers = ["7203.T", "9984.T", "8035.T", "^N225"]
        
        for ticker in tickers:
            # 1. データの取得とリスクチェック
            data = fetch_stock_data([ticker], period="1mo")
            df = data.get(ticker)
            if df is None: continue
            
            if self.risk_guard.detect_black_swan(df):
                logger.warning(f"🚨 {ticker} ブラックスワン検知！避難行動をとります。")
                continue

            # 2. AIスコアリング
            prediction = self.predictor.predict_trajectory(df, days_ahead=1)
            ai_score = prediction.get("predicted_change_pct", 0) / 100 + 0.5 # 0-1へスケール

            # 3. AI投資委員会での議論
            decision_data = self.committee.debate(ticker, ai_score, {
                "volatility": df["Close"].pct_change().std(),
                "rsi": 50 # 簡易化
            })
            
            decision = decision_data["decision"]
            logger.info(f"🤖 {ticker} 最終結論: {decision} (信頼度: {decision_data['consensus_score']:.2f})")

            # 4. 取引実行（シミュレーション）と通知
            if decision != "HOLD":
                send_trade_notification(ticker, decision, 100, df["Close"].iloc[-1])
                
            # 5. オンライン学習
            # 実際には翌日に前日の結果を元に行うが、ここでは基盤のみ呼び出し
            self.learner.incremental_update(ticker, df.iloc[-1:], 0.01)

        logger.info("✨ 本日の自律運用サイクル完了")

from src.trading.fully_automated_trader import FullyAutomatedTrader

if __name__ == "__main__":
    trader = FullyAutomatedTrader()
    # main execution logic...