import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.strategies import Strategy, Order, OrderType
from src.cloud_storage import CloudStorageManager
from src.broker import Broker, Position as BrokerPosition

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Alias for backward compatibility
Position = BrokerPosition

class PaperBroker(Broker):
    """
    Simulates a brokerage account for paper trading.
    Manages cash, positions, and order execution.
    Persists state to a JSON file.
    """
    def __init__(self, initial_capital: float = 100_000.0, state_file: str = "paper_trading_state.json"):
        self.initial_capital = initial_capital
        self.state_file = state_file
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = [] # Active orders (limit/stop) - for now simplified to immediate execution or tracking
        self.storage = CloudStorageManager()
        
        self.load_state()

    def load_state(self):
        data = self.storage.load_json(self.state_file)
        if data:
            try:
                self.cash = data.get("cash", self.initial_capital)
                self.trade_history = data.get("trade_history", [])
                positions_data = data.get("positions", {})
                self.positions = {
                    ticker: Position(**pos_data) for ticker, pos_data in positions_data.items()
                }
                logger.info(f"Loaded paper trading state. Cash: {self.cash}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        else:
            logger.info("No existing state found. Starting fresh.")

    def save_state(self):
        try:
            data = {
                "cash": self.cash,
                "positions": {t: p.to_dict() for t, p in self.positions.items()},
                "trade_history": self.trade_history,
                "last_updated": datetime.now().isoformat()
            }
            self.storage.save_json(data, self.state_file)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_cash(self) -> float:
        """Returns available cash (Broker interface method)."""
        return self.cash
    
    def get_positions(self) -> Dict[str, Position]:
        """Returns current positions (Broker interface method)."""
        return self.positions
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Returns trade history (Broker interface method)."""
        return self.trade_history

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        positions_value = 0.0
        for ticker, pos in self.positions.items():
            price = current_prices.get(ticker, pos.current_price) # Use last known if current not available
            if price > 0:
                positions_value += pos.quantity * price
                # Update position current price for display
                pos.current_price = price
                pos.unrealized_pnl = (price - pos.average_entry_price) * pos.quantity
        return self.cash + positions_value

    def execute_order(self, order: Order, current_price: float, timestamp: datetime):
        """
        Executes an order immediately at the current price (Market Order simulation).
        For Limit/Stop orders, the Engine should only call this when conditions are met.
        """
        cost = 0.0
        if order.action.upper() == "BUY":
            cost = order.quantity * current_price
            if self.cash >= cost:
                self.cash -= cost
                
                # Update position
                if order.ticker in self.positions:
                    pos = self.positions[order.ticker]
                    total_cost = (pos.quantity * pos.average_entry_price) + cost
                    pos.quantity += order.quantity
                    pos.average_entry_price = total_cost / pos.quantity
                else:
                    self.positions[order.ticker] = Position(
                        ticker=order.ticker,
                        quantity=order.quantity,
                        average_entry_price=current_price,
                        current_price=current_price
                    )
                
                self._log_trade(order, current_price, timestamp)
                logger.info(f"BUY EXECUTED: {order.ticker} x {order.quantity} @ {current_price}")
            else:
                logger.warning(f"Insufficient funds for BUY {order.ticker}")

        elif order.action.upper() == "SELL":
            if order.ticker in self.positions:
                pos = self.positions[order.ticker]
                if pos.quantity >= order.quantity:
                    proceeds = order.quantity * current_price
                    self.cash += proceeds
                    
                    pos.quantity -= order.quantity
                    if pos.quantity <= 0:
                        del self.positions[order.ticker]
                    
                    self._log_trade(order, current_price, timestamp)
                    logger.info(f"SELL EXECUTED: {order.ticker} x {order.quantity} @ {current_price}")
                else:
                    logger.warning(f"Insufficient position for SELL {order.ticker}")
            else:
                logger.warning(f"No position found for SELL {order.ticker}")
        
        self.save_state()

    def _log_trade(self, order: Order, price: float, timestamp: datetime):
        self.trade_history.append({
            "timestamp": timestamp.isoformat(),
            "ticker": order.ticker,
            "action": order.action,
            "quantity": order.quantity,
            "price": price,
            "type": order.type.name if hasattr(order.type, 'name') else str(order.type)
        })

class LiveTradingEngine:
    """
    Orchestrates the live trading process.
    Fetches data, runs strategies, and sends orders to the broker.
    """
    def __init__(
        self, 
        broker: Broker, 
        strategies: Dict[str, Strategy], 
        tickers: List[str],
        enable_risk_guard: bool = True,
        initial_portfolio_value: float = 100_000.0
    ):
        self.broker = broker
        self.strategies = strategies
        self.tickers = tickers
        self.is_running = False
        self.interval_seconds = 60 # Run every minute
        self.emergency_stop = False
        
        # Initialize RiskGuard
        if enable_risk_guard:
            from src.risk_guard import RiskGuard
            self.risk_guard = RiskGuard(
                initial_portfolio_value=initial_portfolio_value,
                daily_loss_limit_pct=-5.0,
                max_position_size_pct=10.0,
                max_vix=40.0
            )
        else:
            self.risk_guard = None

    def fetch_realtime_data(self, ticker: str) -> Optional[pd.DataFrame]:
        # This will be replaced by the actual data_loader function
        # For now, we import it inside the method to avoid circular imports if any
        from src.data_loader import fetch_realtime_data
        return fetch_realtime_data(ticker)

    def run_cycle(self):
        """Execute one trading cycle with risk checks."""
        if self.emergency_stop:
            logger.warning("⛔ Emergency stop active - cycle skipped")
            return
            
        logger.info("Starting trading cycle...")
        current_prices = {}
        
        # Risk Guard: Check if trading should be halted
        if self.risk_guard:
            portfolio_value = self.broker.get_portfolio_value({})
            should_halt, reason = self.risk_guard.should_halt_trading(portfolio_value)
            if should_halt:
                logger.critical(f"🚨 Trading halted: {reason}")
                self.emergency_stop = True
                return
        
        for ticker in self.tickers:
            try:
                df = self.fetch_realtime_data(ticker)
                if df is None or df.empty:
                    logger.warning(f"No data for {ticker}")
                    continue
                
                current_price = df['Close'].iloc[-1]
                current_prices[ticker] = current_price
                
                # Run strategy
                strategy = self.strategies.get(ticker)
                if strategy:
                    # Generate signal for the latest data point
                    # Note: Strategies usually expect a history. fetch_realtime_data should return enough history.
                    signals = strategy.generate_signals(df)
                    latest_signal = signals.iloc[-1] if not signals.empty else 0
                    
                    # Process signal
                    # This is a simplified logic. In a real system, we'd handle Order objects more robustly.
                    # Here we assume the strategy might return an int or an Order object.
                    
                    if isinstance(latest_signal, Order):
                        # If it's an Order object, we need to check if it matches current conditions
                        # For Market orders, execute immediately.
                        # For Limit/Stop, we'd need an Order Book in the Broker. 
                        # For simplicity in Phase 1, we execute Market orders immediately.
                        if latest_signal.type == OrderType.MARKET:
                             self.broker.execute_order(latest_signal, current_price, datetime.now())
                    
                    elif isinstance(latest_signal, (int, np.integer)):
                        # Legacy integer signal support
                        qty = 10 # Default quantity for int signals
                        if latest_signal == 1: # BUY
                             order = Order(ticker=ticker, action="BUY", quantity=qty, type=OrderType.MARKET, price=0)
                             self.broker.execute_order(order, current_price, datetime.now())
                        elif latest_signal == -1: # SELL
                             order = Order(ticker=ticker, action="SELL", quantity=qty, type=OrderType.MARKET, price=0)
                             self.broker.execute_order(order, current_price, datetime.now())

            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")

        # Update portfolio value
        total_value = self.broker.get_portfolio_value(current_prices)
        logger.info(f"Cycle complete. Portfolio Value: {total_value:,.2f}")
        self.broker.save_state()

    def start(self):
        self.is_running = True
        logger.info("Live Trading Engine Started")
        while self.is_running:
            self.run_cycle()
            time.sleep(self.interval_seconds)

    def stop(self):
        self.is_running = False
        logger.info("Live Trading Engine Stopped")
