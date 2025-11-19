import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=1000000, commission=0.001, slippage=0.001):
        """
        Args:
            initial_capital (float): Starting cash.
            commission (float): Trading fee per trade (e.g., 0.001 for 0.1%).
            slippage (float): Estimated slippage per trade (e.g., 0.001 for 0.1%).
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self, df, strategy, stop_loss=0.05, take_profit=0.10):
        """
        Runs a strategy on a dataframe with realistic constraints.
        
        Args:
            df (pd.DataFrame): OHLCV data.
            strategy (Strategy): Strategy instance.
            stop_loss (float): Stop loss percentage (e.g., 0.05 for 5%).
            take_profit (float): Take profit percentage (e.g., 0.10 for 10%).
        """
        if df is None or df.empty:
            return None

        # Generate signals based on *today's* close (available at end of day)
        raw_signals = strategy.generate_signals(df)
        
        # Align signals
        df = df.copy()
        df['Signal'] = raw_signals
        
        # Execution Logic:
        # If Signal is generated at index `i` (End of Day),
        # We enter at index `i+1` (Next Day Open).
        
        trades = []
        current_position = 0 # 0: Flat, 1: Long, -1: Short
        entry_price = 0.0
        entry_date = None
        
        # Equity tracking
        cash = self.initial_capital
        holdings = 0.0
        equity_curve = []
        
        # Iterate through days
        # We need to access next day's Open, so we iterate up to len-1
        dates = df.index
        
        for i in range(len(df) - 1):
            date = dates[i]
            next_date = dates[i+1]
            
            # Data available for decision making (Today's Close)
            signal = df['Signal'].iloc[i]
            
            # Execution Price (Next Day Open)
            # We assume we can execute at the Open price of the next bar
            exec_price = df['Open'].iloc[i+1]
            
            # Current Portfolio Value (Mark to Market at Close)
            current_close = df['Close'].iloc[i]
            current_equity = cash + (holdings * current_close)
            equity_curve.append(current_equity)

            # Risk Management Check (Intraday High/Low could trigger SL/TP)
            # For simplicity in this version, we check against Next Day's Open first,
            # then we could check High/Low if we were in a position.
            # Here, we'll check SL/TP based on the *execution price* vs entry price for simplicity,
            # or check if the *previous* day's move triggered it.
            # A robust way: Check if Open triggered SL/TP. If not, check High/Low.
            
            if current_position != 0:
                # Check for Stop Loss / Take Profit
                # We use the Next Day's Open as the potential exit price if we hold overnight
                # But wait, if we are holding, we experience the overnight gap.
                
                price_change_pct = (exec_price - entry_price) / entry_price
                
                exit_triggered = False
                exit_reason = ""
                
                if current_position == 1: # Long
                    if price_change_pct <= -stop_loss:
                        exit_triggered = True
                        exit_reason = "Stop Loss"
                    elif price_change_pct >= take_profit:
                        exit_triggered = True
                        exit_reason = "Take Profit"
                
                if exit_triggered:
                    # Execute Exit at Open
                    # Apply costs
                    cost = exec_price * (self.commission + self.slippage)
                    effective_price = exec_price - cost if current_position == 1 else exec_price + cost
                    
                    cash += holdings * effective_price
                    holdings = 0
                    
                    trade_return = (effective_price - entry_price) / entry_price if current_position == 1 else (entry_price - effective_price) / entry_price
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': next_date,
                        'entry_price': entry_price,
                        'exit_price': effective_price,
                        'return': trade_return,
                        'reason': exit_reason
                    })
                    current_position = 0
                    continue # Trade closed, move to next logic

            # Signal Processing (Entry/Exit)
            # If we are flat, look for entry
            if current_position == 0:
                if signal == 1: # Buy Signal
                    # Enter Long at Next Open
                    cost = exec_price * (self.commission + self.slippage)
                    effective_entry_price = exec_price + cost
                    
                    # Calculate position size (e.g., 100% of equity)
                    # For simplicity, use all cash
                    if cash > 0:
                        holdings = cash / effective_entry_price
                        cash = 0
                        entry_price = effective_entry_price
                        entry_date = next_date
                        current_position = 1
            
            # If we are Long, look for exit signal
            elif current_position == 1:
                if signal == -1: # Sell Signal
                    # Exit Long at Next Open
                    cost = exec_price * (self.commission + self.slippage)
                    effective_exit_price = exec_price - cost
                    
                    cash += holdings * effective_exit_price
                    holdings = 0
                    
                    trade_return = (effective_exit_price - entry_price) / entry_price
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': next_date,
                        'entry_price': entry_price,
                        'exit_price': effective_exit_price,
                        'return': trade_return,
                        'reason': "Signal"
                    })
                    current_position = 0

        # Final Day Accounting
        final_close = df['Close'].iloc[-1]
        final_equity = cash + (holdings * final_close)
        equity_curve.append(final_equity)
        
        # Convert equity curve to Series
        equity_series = pd.Series(equity_curve, index=df.index[:len(equity_curve)])
        
        # Calculate Metrics
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        if not trades:
            return {
                "total_return": 0.0,
                "final_value": self.initial_capital,
                "equity_curve": equity_series,
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_return": 0.0,
                "max_drawdown": 0.0,
                "trades": []
            }

        trade_returns = [t['return'] for t in trades]
        wins = [r for r in trade_returns if r > 0]
        win_rate = len(wins) / len(trades)
        avg_return = sum(trade_returns) / len(trades)
        
        # Max Drawdown
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        return {
            "total_return": total_return,
            "final_value": final_equity,
            "equity_curve": equity_series,
            "total_trades": len(trades),
            "win_rate": win_rate,
            "avg_return": avg_return,
            "max_drawdown": max_drawdown,
            "trades": trades
        }
