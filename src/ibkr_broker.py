import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.broker import Broker, Position, Order

logger = logging.getLogger(__name__)

# Try to import ib_insync
try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
    HAS_IBKR = True
except ImportError:
    HAS_IBKR = False
    logger.warning("ib_insync not installed. IBKRBroker will not be available.")

class IBKRBroker(Broker):
    """
    Interactive Brokers integration using ib_insync.
    Supports both Paper Trading and Live modes.
    """
    def __init__(
        self,
        mode: str = "paper",  # "paper" or "live"
        host: str = "127.0.0.1",
        port: int = 7497,  # 7497 for paper, 7496 for live
        client_id: int = 1
    ):
        if not HAS_IBKR:
            raise ImportError("ib_insync library not installed. Install with: pip install ib_insync")
        
        self.mode = mode
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.is_connected = False
        
        self.positions_cache: Dict[str, Position] = {}
        self.trade_history: List[Dict[str, Any]] = []
        
    def connect(self):
        """Connect to TWS/IB Gateway."""
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.is_connected = True
            logger.info(f"✅ Connected to IBKR ({self.mode} mode) at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from TWS/IB Gateway."""
        if self.is_connected:
            self.ib.disconnect()
            self.is_connected = False
            logger.info("Disconnected from IBKR")
    
    def get_cash(self) -> float:
        """Returns available cash."""
        if not self.is_connected:
            return 0.0
        
        account_values = self.ib.accountValues()
        for av in account_values:
            if av.tag == 'CashBalance' and av.currency == 'USD':
                return float(av.value)
        return 0.0
    
    def get_positions(self) -> Dict[str, Position]:
        """Returns current positions from IBKR."""
        if not self.is_connected:
            return {}
        
        positions = {}
        for pos in self.ib.positions():
            ticker = pos.contract.symbol
            positions[ticker] = Position(
                ticker=ticker,
                quantity=pos.position,
                average_entry_price=pos.avgCost,
                current_price=0.0  # Will be updated when we fetch prices
            )
        
        self.positions_cache = positions
        return positions
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Returns total portfolio value."""
        cash = self.get_cash()
        positions = self.get_positions()
        
        positions_value = 0.0
        for ticker, pos in positions.items():
            price = current_prices.get(ticker, 0.0)
            if price > 0:
                positions_value += pos.quantity * price
        
        return cash + positions_value
    
    def execute_order(self, order: Order, current_price: float, timestamp: datetime):
        """Execute an order via IBKR."""
        if not self.is_connected:
            logger.error("Cannot execute order: Not connected to IBKR")
            return
        
        try:
            # Create contract
            contract = Stock(order.ticker, 'SMART', 'USD')
            
            # Create order based on type
            if order.order_type == "MARKET":
                ib_order = MarketOrder(order.action, order.quantity)
            elif order.order_type == "LIMIT":
                ib_order = LimitOrder(order.action, order.quantity, order.price)
            else:
                logger.warning(f"Unsupported order type: {order.order_type}")
                return
            
            # Place order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Wait for fill (with timeout)
            self.ib.sleep(2)  # Wait for order to process
            
            # Log trade
            self._log_trade(order, current_price, timestamp, trade)
            logger.info(f"Order executed: {order.action} {order.quantity} {order.ticker} @ {current_price}")
            
        except Exception as e:
            logger.error(f"Failed to execute order: {e}")
    
    def _log_trade(self, order: Order, price: float, timestamp: datetime, trade: Any):
        """Log trade details."""
        self.trade_history.append({
            "timestamp": timestamp.isoformat(),
            "ticker": order.ticker,
            "action": order.action,
            "quantity": order.quantity,
            "price": price,
            "type": order.order_type,
            "order_id": trade.order.orderId if hasattr(trade, 'order') else None
        })
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Returns trade history."""
        return self.trade_history
    
    def save_state(self):
        """IBKR state is maintained by TWS, no need to save locally."""
        pass
    
    def load_state(self):
        """IBKR state is loaded from TWS on connection."""
        pass
