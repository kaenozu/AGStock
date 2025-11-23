import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass
from enum import Enum
from src.strategies import Strategy, Order, OrderType

class Backtester:
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, slippage: float = 0.001, allow_short: bool = False, position_size: Union[float, Dict[str, float]] = 1.0) -> None:
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.allow_short = allow_short
        self.position_size = position_size # Default allocation per asset (float) or specific weights (dict)
        self.pending_orders: List[Order] = []

    def run(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], strategy: Union[Strategy, Dict[str, Strategy]], stop_loss: float = 0.05, take_profit: float = 0.10, trailing_stop: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Runs a backtest.
        
        Args:
            data: Single DataFrame or Dictionary of DataFrames {ticker: df}
            strategy: Single Strategy (applied to all) or Dictionary {ticker: strategy}
            stop_loss: Fixed stop loss percentage (e.g., 0.05 for 5%)
            take_profit: Fixed take profit percentage
            trailing_stop: Trailing stop percentage (e.g., 0.05). If set, overrides fixed stop_loss for trailing.
        """
        # Normalize input to Dictionary format
        if isinstance(data, pd.DataFrame):
            data_map = {'Asset': data}
        else:
            data_map = data

        if isinstance(strategy, Strategy):
            strategy_map = {ticker: strategy for ticker in data_map.keys()}
        else:
            strategy_map = strategy

        if not data_map:
            return None

        # 1. Generate Signals for all assets
        signals_map = {}
        for ticker, df in data_map.items():
            if df is None or df.empty:
                continue
            strat = strategy_map.get(ticker)
            if strat:
                signals_map[ticker] = strat.generate_signals(df)
            else:
                signals_map[ticker] = pd.Series(0, index=df.index)

        # 2. Create Unified Index
        all_dates = sorted(list(set().union(*[df.index for df in data_map.values() if df is not None])))
        full_index = pd.DatetimeIndex(all_dates)
        
        # 3. Initialize State
        cash = self.initial_capital
        holdings = {ticker: 0.0 for ticker in data_map.keys()} # Shares
        entry_prices = {ticker: 0.0 for ticker in data_map.keys()}
        trailing_stop_levels = {ticker: None for ticker in data_map.keys()}
        
        portfolio_value_history = []
        trades = []
        
        # Pre-align data for speed
        aligned_data = {}
        for ticker, df in data_map.items():
            # Reindex and forward fill prices, fillna(0) for signals (no signal on missing days)
            aligned_df = df.reindex(full_index)
            aligned_df['Signal'] = signals_map.get(ticker, pd.Series(0, index=df.index)).reindex(full_index).fillna(0)
            aligned_df['Open'] = aligned_df['Open'].ffill()
            aligned_df['High'] = aligned_df['High'].ffill()
            aligned_df['Low'] = aligned_df['Low'].ffill()
            aligned_df['Close'] = aligned_df['Close'].ffill()
            aligned_data[ticker] = aligned_df

        # 4. Event Loop
        for i in range(len(full_index) - 1):
            date = full_index[i]
            next_date = full_index[i+1]
            
            # Calculate Portfolio Value at Open of Day i (or Close of Day i? Logic: Decisions made on Day i Close/Day i+1 Open)
            # We execute at Day i+1 Open based on Day i Signal.
            
            current_portfolio_value = cash
            for ticker, df in aligned_data.items():
                price = df['Close'].iloc[i] # Mark to market at Close
                if pd.isna(price): continue
                current_portfolio_value += holdings[ticker] * price
            
            portfolio_value_history.append(current_portfolio_value)
            
            # Process each asset
            for ticker, df in aligned_data.items():
                # Data for today and tomorrow
                today_sig = df['Signal'].iloc[i]
                
                # Execution Price (Next Open)
                exec_price = df['Open'].iloc[i+1]
                next_high = df['High'].iloc[i+1]
                next_low = df['Low'].iloc[i+1]
                if pd.isna(exec_price): continue
                
                # --- Check Pending Orders ---
                active_orders = [o for o in self.pending_orders if o.ticker == ticker]
                remaining_orders = [o for o in self.pending_orders if o.ticker != ticker]
                unexecuted_orders = []
                
                for order in active_orders:
                    executed = False
                    fill_price = None
                    
                    if order.type == OrderType.LIMIT:
                        if order.action == 'BUY':
                            if next_low <= order.price:
                                fill_price = min(exec_price, order.price) if exec_price < order.price else order.price
                                executed = True
                        elif order.action == 'SELL':
                            if next_high >= order.price:
                                fill_price = max(exec_price, order.price) if exec_price > order.price else order.price
                                executed = True
                                
                    elif order.type == OrderType.STOP:
                        if order.action == 'BUY':
                            if next_high >= order.price:
                                fill_price = max(exec_price, order.price)
                                executed = True
                        elif order.action == 'SELL':
                            if next_low <= order.price:
                                fill_price = min(exec_price, order.price)
                                executed = True
                    
                    if executed and fill_price:
                        # Execute Trade
                        cost = fill_price * order.quantity
                        if order.action == 'BUY':
                            if cash >= cost * (1 + self.commission + self.slippage):
                                cash -= cost * (1 + self.commission + self.slippage)
                                holdings[ticker] += order.quantity
                                entry_prices[ticker] = fill_price # Update entry price (average?) - Simplified to latest
                                if trailing_stop is not None:
                                    trailing_stop_levels[ticker] = fill_price * (1 - trailing_stop)
                        elif order.action == 'SELL':
                            # Assuming closing position or shorting
                            # Simplified: Treat as reducing holdings or shorting
                            proceeds = cost * (1 - self.commission - self.slippage)
                            cash += proceeds
                            holdings[ticker] -= order.quantity
                            if holdings[ticker] < 0: # Short
                                entry_prices[ticker] = fill_price
                                if trailing_stop is not None:
                                    trailing_stop_levels[ticker] = fill_price * (1 + trailing_stop)
                    else:
                        # Check expiry
                        if order.expiry == "GTC":
                            unexecuted_orders.append(order)
                
                self.pending_orders = remaining_orders + unexecuted_orders
                
                # --- Signal Execution ---
                # Handle Order Objects
                if isinstance(today_sig, Order):
                    today_sig.ticker = ticker # Ensure ticker matches
                    if today_sig.type == OrderType.MARKET:
                        if today_sig.action == 'BUY':
                            today_sig = 1
                        elif today_sig.action == 'SELL':
                            today_sig = -1
                    else:
                        # Add to pending orders
                        if today_sig.quantity <= 0:
                            price = today_sig.price if today_sig.price else df['Close'].iloc[i]
                            if isinstance(self.position_size, dict):
                                alloc = self.position_size.get(ticker, 0.0)
                            else:
                                alloc = self.position_size
                            target_amount = current_portfolio_value * alloc
                            today_sig.quantity = target_amount / price
                        
                        self.pending_orders.append(today_sig)
                        today_sig = 0 # No immediate action

                # Recalculate position type before signal execution (in case pending orders changed it)
                current_shares = holdings[ticker]
                position_type = 0
                if current_shares > 0: position_type = 1
                elif current_shares < 0: position_type = -1

                if position_type == 0:
                    if today_sig == 1:
                        # Allocation Logic
                        if isinstance(self.position_size, dict):
                            alloc = self.position_size.get(ticker, 0.0)
                        else:
                            alloc = self.position_size
                        
                        target_amount = current_portfolio_value * alloc
                        
                        # Check Cash
                        cost = target_amount * (1 + self.commission + self.slippage)
                        if cash >= cost:
                            shares = target_amount / exec_price
                            cash -= cost
                            holdings[ticker] = shares
                            entry_prices[ticker] = exec_price
                            
                    elif today_sig == -1 and self.allow_short:
                        # Sell Short
                        if isinstance(self.position_size, dict):
                            alloc = self.position_size.get(ticker, 0.0)
                        else:
                            alloc = self.position_size
                        
                        target_amount = current_portfolio_value * alloc
                        # Margin check: need cash >= target_amount
                        if cash >= target_amount:
                            shares = target_amount / exec_price
                            cash -= target_amount # Lock margin
                            holdings[ticker] = -shares
                            entry_prices[ticker] = exec_price

                elif position_type == 1:
                    if today_sig == -1:
                        # Close Long
                        exit_price = exec_price
                        proceeds = (exit_price * holdings[ticker]) * (1 - self.commission - self.slippage)
                        cash += proceeds
                        
                        ret = (proceeds - (entry_prices[ticker] * holdings[ticker])) / (entry_prices[ticker] * holdings[ticker])
                        
                        trades.append({
                            'ticker': ticker,
                            'exit_date': next_date,
                            'entry_price': entry_prices[ticker],
                            'exit_price': exit_price,
                            'return': ret,
                            'reason': 'Signal',
                            'type': 'Long'
                        })
                        holdings[ticker] = 0
                        entry_prices[ticker] = 0
                        
                        # Flip to Short?
                        if self.allow_short:
                            if isinstance(self.position_size, dict):
                                alloc = self.position_size.get(ticker, 0.0)
                            else:
                                alloc = self.position_size
                            
                            target_amount = current_portfolio_value * alloc
                            if cash >= target_amount:
                                shares = target_amount / exec_price
                                cash -= target_amount
                                holdings[ticker] = -shares
                                entry_prices[ticker] = exec_price

                elif position_type == -1:
                    if today_sig == 1:
                        # Close Short
                        exit_price = exec_price
                        cost = (exit_price * abs(holdings[ticker])) * (1 + self.commission + self.slippage)
                        
                        # PnL calculation
                        entry_val = entry_prices[ticker] * abs(holdings[ticker])
                        pnl = entry_val - cost
                        cash += entry_val + pnl # Return margin + PnL
                        
                        ret = pnl / entry_val
                        
                        trades.append({
                            'ticker': ticker,
                            'exit_date': next_date,
                            'entry_price': entry_prices[ticker],
                            'exit_price': exit_price,
                            'return': ret,
                            'reason': 'Signal',
                            'type': 'Short'
                        })
                        holdings[ticker] = 0
                        entry_prices[ticker] = 0
                        
                        # Flip to Long?
                        if isinstance(self.position_size, dict):
                            alloc = self.position_size.get(ticker, 0.0)
                        else:
                            alloc = self.position_size
                        
                        target_amount = current_portfolio_value * alloc
                        cost = target_amount * (1 + self.commission + self.slippage)
                        if cash >= cost:
                            shares = target_amount / exec_price
                            cash -= cost
                            holdings[ticker] = shares
                            entry_prices[ticker] = exec_price

                # --- Risk Management (SL/TP) ---
                # Check intraday price movement on Day i+1
                # Recalculate position type after signal execution
                current_shares = holdings[ticker]
                position_type = 0
                if current_shares > 0: position_type = 1
                elif current_shares < 0: position_type = -1

                if position_type != 0:
                    entry = entry_prices[ticker]
                    high = df['High'].iloc[i+1]
                    low = df['Low'].iloc[i+1]
                    
                    exit_price = None
                    reason = ""
                    
                    # Update Trailing Stop
                    if trailing_stop is not None:
                        if position_type == 1: # Long
                            if trailing_stop_levels[ticker] is None:
                                trailing_stop_levels[ticker] = entry * (1 - trailing_stop)
                            
                            # Always update with current high
                            trailing_stop_levels[ticker] = max(trailing_stop_levels[ticker], high * (1 - trailing_stop))
                        elif position_type == -1: # Short
                            if trailing_stop_levels[ticker] is None:
                                trailing_stop_levels[ticker] = entry * (1 + trailing_stop)
                            
                            # Always update with current low
                            trailing_stop_levels[ticker] = min(trailing_stop_levels[ticker], low * (1 + trailing_stop))

                    if position_type == 1: # Long
                        # Check Trailing Stop
                        if trailing_stop is not None and low <= trailing_stop_levels[ticker]:
                            exit_price = trailing_stop_levels[ticker]
                            reason = "Trailing Stop"
                        elif (exec_price - entry) / entry <= -stop_loss and trailing_stop is None: # Gap Down (Fixed SL)
                            exit_price = exec_price
                            reason = "SL (Gap)"
                        elif (exec_price - entry) / entry >= take_profit: # Gap Up
                            exit_price = exec_price
                            reason = "TP (Gap)"
                        elif (low - entry) / entry <= -stop_loss and trailing_stop is None:
                            exit_price = entry * (1 - stop_loss)
                            reason = "SL"
                        elif (high - entry) / entry >= take_profit:
                            exit_price = entry * (1 + take_profit)
                            reason = "TP"
                            
                    elif position_type == -1: # Short
                        # Check Trailing Stop
                        if trailing_stop is not None and high >= trailing_stop_levels[ticker]:
                            exit_price = trailing_stop_levels[ticker]
                            reason = "Trailing Stop"
                        elif (entry - exec_price) / entry <= -stop_loss and trailing_stop is None: # Gap Up (Fixed SL)
                            exit_price = exec_price
                            reason = "SL (Gap)"
                        elif (entry - exec_price) / entry >= take_profit: # Gap Down
                            exit_price = exec_price
                            reason = "TP (Gap)"
                        elif (entry - high) / entry <= -stop_loss and trailing_stop is None:
                            exit_price = entry * (1 + stop_loss)
                            reason = "SL"
                        elif (entry - low) / entry >= take_profit:
                            exit_price = entry * (1 - take_profit)
                            reason = "TP"

                    if exit_price:
                        # Execute Exit
                        cost = exit_price * abs(current_shares)
                        if position_type == 1:
                            proceeds = cost * (1 - self.commission - self.slippage)
                            cash += proceeds
                            ret = (proceeds - (entry * abs(current_shares))) / (entry * abs(current_shares))
                        else:
                            proceeds = cost * (1 + self.commission + self.slippage) # Cost to buy back
                            cash -= proceeds 
                            pnl = (entry - exit_price) * abs(current_shares)
                            pnl -= cost * (self.commission + self.slippage) # Transaction costs
                            cash += pnl + (entry * abs(current_shares)) # Return margin (entry value)
                            
                            ret = pnl / (entry * abs(current_shares))

                        trades.append({
                            'ticker': ticker,
                            'entry_date': None, # TODO: Track entry date
                            'exit_date': next_date,
                            'entry_price': entry,
                            'exit_price': exit_price,
                            'return': ret,
                            'reason': reason,
                            'type': 'Long' if position_type == 1 else 'Short'
                        })
                        
                        holdings[ticker] = 0
                        entry_prices[ticker] = 0
                        trailing_stop_levels[ticker] = None # Reset

        # Final Value
        final_portfolio_value = cash
        for ticker, df in aligned_data.items():
            price = df['Close'].iloc[-1]
            if pd.isna(price): continue
            final_portfolio_value += holdings[ticker] * price
            
        portfolio_value_history.append(final_portfolio_value)
        
        # Create Equity Curve
        equity_curve = pd.Series(portfolio_value_history, index=full_index)
        
        # Metrics
        total_return = (final_portfolio_value - self.initial_capital) / self.initial_capital
        
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = drawdown.min()
        
        wins = [t['return'] for t in trades if t['return'] > 0]
        win_rate = len(wins) / len(trades) if trades else 0.0
        avg_return = np.mean([t['return'] for t in trades]) if trades else 0.0
        
        # Sharpe Ratio (annualized)
        daily_returns = equity_curve.pct_change().dropna()
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
        else:
            sharpe_ratio = 0.0
        
        # Create positions series for backward compatibility
        # This is a simplified version - tracks whether we have any position
        positions = pd.Series(0, index=full_index)
        for i, date in enumerate(full_index):
            has_position = any(holdings[ticker] != 0 for ticker in data_map.keys())
            positions.iloc[i] = 1 if has_position else 0
        
        return {
            "total_return": total_return,
            "final_value": final_portfolio_value,
            "equity_curve": equity_curve,
            "signals": signals_map,  # Return the signals map
            "positions": positions,  # Simplified position tracking
            "trades": trades,
            "win_rate": win_rate,
            "avg_return": avg_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": len(trades),
            "num_trades": len(trades)  # Alias for compatibility
        }
