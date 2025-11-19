import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

class Backtester:
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, slippage: float = 0.001, allow_short: bool = False, position_size: float = 1.0) -> None:
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.allow_short = allow_short
        self.position_size = position_size # 0.0 to 1.0

    def run(self, df: pd.DataFrame, strategy: 'Strategy', stop_loss: float = 0.05, take_profit: float = 0.10) -> Optional[Dict[str, Any]]:
        """
        Runs a strategy on a dataframe and returns performance metrics.
        Executes trades at the Next Day Open.
        """
        if df is None or df.empty:
            return None

        signals = strategy.generate_signals(df)
        
        # Align signals with data
        df = df.copy()
        df['Signal'] = signals
        
        trades = []
        current_position = 0 # 0: Flat, 1: Long, -1: Short
        entry_price = 0.0
        entry_date = None
        
        positions = pd.Series(0, index=df.index)
        
        # Iterate through the dataframe
        for i in range(len(df) - 1):
            date = df.index[i]
            next_date = df.index[i+1]
            
            # Signal from Day i
            sig = df['Signal'].iloc[i]
            
            # Price at Day i+1 Open (Execution Price)
            price = df['Open'].iloc[i+1]
            
            executed_action = None # 'EXIT', 'ENTRY', 'FLIP'
            
            # --- Risk Management Check (Exit Logic) ---
            # Check if the Open price or intraday movement triggers SL/TP for existing position
            if current_position != 0:
                exit_price = None
                reason = ""
                
                if current_position == 1: # Long
                    # Check Open gap
                    pct_change_open = (price - entry_price) / entry_price
                    if pct_change_open <= -stop_loss:
                        exit_price = price
                        reason = "SL (Gap)"
                    elif pct_change_open >= take_profit:
                        exit_price = price
                        reason = "TP (Gap)"
                    else:
                        # Check Low/High of the day
                        low_price = df['Low'].iloc[i+1]
                        high_price = df['High'].iloc[i+1]
                        
                        if (low_price - entry_price) / entry_price <= -stop_loss:
                            exit_price = entry_price * (1 - stop_loss)
                            reason = "SL"
                        elif (high_price - entry_price) / entry_price >= take_profit:
                            exit_price = entry_price * (1 + take_profit)
                            reason = "TP"
                            
                elif current_position == -1: # Short
                    # Check Open gap
                    pct_change_open = (entry_price - price) / entry_price
                    if pct_change_open <= -stop_loss: # Loss if price UP
                        exit_price = price
                        reason = "SL (Gap)"
                    elif pct_change_open >= take_profit: # Profit if price DOWN
                        exit_price = price
                        reason = "TP (Gap)"
                    else:
                        # Check High/Low
                        low_price = df['Low'].iloc[i+1]
                        high_price = df['High'].iloc[i+1]
                        
                        if (entry_price - high_price) / entry_price <= -stop_loss:
                            exit_price = entry_price * (1 + stop_loss)
                            reason = "SL"
                        elif (entry_price - low_price) / entry_price >= take_profit:
                            exit_price = entry_price * (1 - take_profit)
                            reason = "TP"

                if exit_price:
                    # Execute Exit
                    trade_return = 0.0
                    if current_position == 1:
                        # Sell to Close
                        effective_exit = exit_price * (1 - self.slippage - self.commission)
                        trade_return = (effective_exit - entry_price) / entry_price
                    else:
                        # Buy to Cover
                        effective_exit = exit_price * (1 + self.slippage + self.commission)
                        trade_return = (entry_price - effective_exit) / entry_price
                        
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': next_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'return': trade_return,
                        'reason': reason,
                        'type': 'Long' if current_position == 1 else 'Short'
                    })
                    
                    current_position = 0
                    executed_action = 'EXIT'

            # --- Signal Execution Logic ---
            if executed_action != 'EXIT':
                if current_position == 0:
                    if sig == 1:
                        # Open Long
                        current_position = 1
                        entry_price = price * (1 + self.slippage + self.commission)
                        entry_date = next_date
                    elif sig == -1 and self.allow_short:
                        # Open Short
                        current_position = -1
                        entry_price = price * (1 - self.slippage - self.commission)
                        entry_date = next_date
                        
                elif current_position == 1:
                    if sig == -1:
                        # Close Long
                        exit_price = price
                        effective_exit = exit_price * (1 - self.slippage - self.commission)
                        trade_return = (effective_exit - entry_price) / entry_price
                        
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': next_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'return': trade_return,
                            'reason': 'Signal',
                            'type': 'Long'
                        })
                        current_position = 0
                        
                        # Flip to Short
                        if self.allow_short:
                            current_position = -1
                            entry_price = price * (1 - self.slippage - self.commission)
                            entry_date = next_date

                elif current_position == -1:
                    if sig == 1:
                        # Close Short
                        exit_price = price
                        effective_exit = exit_price * (1 + self.slippage + self.commission)
                        trade_return = (entry_price - effective_exit) / entry_price
                        
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': next_date,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'return': trade_return,
                            'reason': 'Signal',
                            'type': 'Short'
                        })
                        current_position = 0
                        
                        # Flip to Long
                        current_position = 1
                        entry_price = price * (1 + self.slippage + self.commission)
                        entry_date = next_date

            positions.loc[next_date] = current_position

        # Calculate Metrics
        
        # Equity Curve (Approximate for visualization)
        df['Pct_Change'] = df['Close'].pct_change().fillna(0)
        df['Strategy_Return'] = positions * df['Pct_Change'] * self.position_size
        df['Cumulative_Return'] = (1 + df['Strategy_Return']).cumprod()
        
        # Total Return (Mark-to-Market)
        final_total_return = df['Cumulative_Return'].iloc[-1] - 1
        
        # Max Drawdown
        cum_ret = df['Cumulative_Return']
        running_max = cum_ret.cummax()
        drawdown = (cum_ret - running_max) / running_max
        max_drawdown = drawdown.min() if not drawdown.empty else 0.0
        
        wins = [t['return'] for t in trades if t['return'] > 0]
        win_rate = len(wins) / len(trades) if trades else 0
        avg_return = sum([t['return'] for t in trades]) / len(trades) if trades else 0
        
        return {
            "total_return": final_total_return,
            "final_value": self.initial_capital * (1 + final_total_return),
            "signals": signals,
            "positions": positions,
            "equity_curve": df['Cumulative_Return'],
            "total_trades": len(trades),
            "win_rate": win_rate,
            "avg_return": avg_return,
            "max_drawdown": max_drawdown,
            "trades": trades
        }
