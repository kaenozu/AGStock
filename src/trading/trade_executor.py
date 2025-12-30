"""
Trade Executor Component
Orchestrates the final execution of trade signals through multiple layers of validation.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.ai_veto_agent import AIVetoAgent
from src.agents.social_analyst import SocialAnalyst
from src.agents.visual_oracle import VisualOracle
from src.data.feedback_store import FeedbackStore
from src.data_loader import fetch_stock_data, get_latest_price
from src.execution.execution_engine import ExecutionEngine
from src.trading.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)


class TradeExecutor:
    """
    Handles the validation and execution of trade signals.
    Integrates AI agents (Veto, Social, Visual) for extra scrutiny.
    """

    def __init__(self, config: Dict[str, Any], engine: ExecutionEngine):
        self.config = config
        self.engine = engine
        self.logger = logger
        
        # Risk & AI components
        try:
            self.portfolio_manager = PortfolioManager()
            self.ai_veto_agent = AIVetoAgent(self.config)
            self.social_analyst = SocialAnalyst(self.config)
            self.visual_oracle = VisualOracle(self.config)
            self.feedback_store = FeedbackStore()
            self.logger.info("✅ TradeExecutor components initialized.")
        except Exception as e:
            self.logger.error(f"❌ TradeExecutor component initialization failed: {e}")

    def execute_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes a list of signals after performing AI verification and risk checks.
        """
        if not signals:
            self.logger.info("No signals to execute.")
            return []

        self.logger.info(f"Processing {len(signals)} signals...")
        
        # 1. AI Verification Layer
        verified_signals = self._verify_with_ai(signals)
        
        if not verified_signals:
            self.logger.warning("All signals were vetoed or failed AI verification.")
            return []

        # 2. Price Fetching
        tickers = [s["ticker"] for s in verified_signals]
        market_data = fetch_stock_data(tickers, period="5d")
        
        prices = {}
        for ticker in tickers:
            if ticker in market_data:
                price = get_latest_price(market_data[ticker])
                if price:
                    prices[ticker] = price

        # 3. Execution via Engine
        executed_trades = self.engine.execute_orders(verified_signals, prices)
        
        # 4. Feedback Loop Logging (Phase 42)
        if executed_trades:
            self._log_execution_feedback(executed_trades)
            
        return executed_trades

    def _verify_with_ai(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Passes signals through AI agents for a 'second opinion'.
        """
        vetted_signals = []
        for signal in signals:
            ticker = signal.get("ticker")
            if not ticker: continue
            
            # Veto Check
            veto_reason = self.ai_veto_agent.check_veto(signal)
            if veto_reason:
                self.logger.info(f"🚫 VETOED {ticker}: {veto_reason}")
                continue
                
            # Social Sentiment Check (Informational)
            sentiment = self.social_analyst.analyze(ticker)
            signal["social_sentiment"] = sentiment
            
            # Visual check if needed (Conceptual Phase)
            # signal["visual_score"] = self.visual_oracle.check_chart(ticker)
            
            vetted_signals.append(signal)
            
        return vetted_signals

    def _log_execution_feedback(self, executed_trades: List[Dict[str, Any]]) -> None:
        """Logs trades for future RL/learning feedback."""
        for trade in executed_trades:
            try:
                self.feedback_store.add_feedback(
                    ticker=trade["ticker"],
                    trade_id=str(trade.get("trade_id", "auto")),
                    expected_pnl=0.0, # Will be filled by rebalancer
                    entry_context=trade.get("reason", "manual_execution")
                )
            except Exception as e:
                self.logger.debug(f"Feedback logging failed for {trade['ticker']}: {e}")
