from sqlalchemy.orm import Session
from sqlalchemy import func
from src.db.database import SessionLocal
from src.db.models import MarketScan, TradeLog, CouncilVote, SystemEvent
import logging
from datetime import datetime
logger = logging.getLogger(__name__)
class DatabaseManager:
#     """
#     High-level interface for database operations.
#     """
def __init__(self):
        self.db: Session = SessionLocal()
    def log_scan(self, ticker: str, signal: int, confidence: float, reasoning: str, technicals: dict = None):
        pass
        try:
            rsi = technicals.get("RSI") if technicals else None
            sma_20 = technicals.get("SMA_20") if technicals else None
            sma_50 = technicals.get("SMA_50") if technicals else None
                scan = MarketScan(
                ticker=ticker,
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                rsi=rsi,
                sma_20=sma_20,
                sma_50=sma_50,
            )
            self.db.add(scan)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log scan: {e}")
            self.db.rollback()
            return False
    def log_trade(
        self, ticker: str, action: str, price: float, quantity: float, strategy: str = "Manual", pnl: float = 0.0
#     """
#     ):
#         pass
#         try:
#             trade = TradeLog(
#                 ticker=ticker, action=action, price=price, quantity=quantity, strategy_name=strategy, pnl=pnl
#             )
#             self.db.add(trade)
#             self.db.commit()
#             return True
#         except Exception as e:
#             logger.error(f"Failed to log trade: {e}")
#             self.db.rollback()
#             return False
#     def log_council_vote(self, ticker: str, vote_data: dict):
#         pass
#         try:
#             vote = CouncilVote(
#                 ticker=ticker,
#                 avatar_id=vote_data.get("id"),
#                 avatar_name=vote_data.get("name"),
#                 trait=vote_data.get("trait"),
#                 score=vote_data.get("score"),
#                 stance=vote_data.get("stance"),
#                 quote=vote_data.get("quote"),
#             )
#             self.db.add(vote)
#             self.db.commit()
#             return True
#         except Exception as e:
#             logger.error(f"Failed to log vote: {e}")
#             self.db.rollback()
#             return False
#     def log_event(self, event_type: str, message: str, details: str = None):
#         pass
#         try:
#             event = SystemEvent(event_type=event_type, message=message, details=details)
#             self.db.add(event)
#             self.db.commit()
#         except Exception as e:
#             logger.error(f"Failed to log event: {e}")
#             self.db.rollback()
#     def get_strategy_performance(self) -> dict:
#         """
Calculates cumulative PnL for each strategy.
                try:
                    results = (
                self.db.query(
                    TradeLog.strategy_name,
                    func.sum(TradeLog.pnl).label("total_pnl"),
                    func.count(TradeLog.id).label("trade_count"),
                )
                .group_by(TradeLog.strategy_name)
                .all()
            )
                return {r.strategy_name: {"total_pnl": r.total_pnl, "trade_count": r.trade_count} for r in results}
        except Exception as e:
            logger.error(f"Failed to query strategy performance: {e}")
            return {}
#     """
#     def get_recent_trades(self, strategy_name: str = None, limit: int = 50) -> list:
#         """
Retrieves recent trades, optionally filtered by strategy.
                try:
                    query = self.db.query(TradeLog)
            if strategy_name:
                query = query.filter(TradeLog.strategy_name == strategy_name)
                trades = query.order_by(TradeLog.timestamp.desc()).limit(limit).all()
            return trades
        except Exception as e:
            logger.error(f"Failed to query recent trades: {e}")
            return []
#     """
#     def close(self):
#         """
Close.
                self.db.close()
# """
