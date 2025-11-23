import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Union, List
from src.strategies import Strategy

class Backtester:
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, slippage: float = 0.001, allow_short: bool = False, position_size: Union[float, Dict[str, float]] = 1.0) -> None:
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.allow_short = allow_short
        self.position_size = position_size # Default allocation per asset (float) or specific weights (dict)

    def run(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], strategy: Union[Strategy, Dict[str, Strategy]], stop_loss: float = 0.05, take_profit: float = 0.10) -> Optional[Dict[str, Any]]:
        """
        Runs a backtest.
        
        Args:
            data: Single DataFrame or Dictionary of DataFrames {ticker: df}
            strategy: Single Strategy (applied to all) or Dictionary {ticker: strategy}
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
                if pd.isna(exec_price): continue
                
                # Current Position
                current_shares = holdings[ticker]
                position_type = 0
                if current_shares > 0: position_type = 1
                elif current_shares < 0: position_type = -1
                
                # --- Risk Management (SL/TP) ---
                # Check intraday price movement on Day i+1
                # Note: This implies we are peeking into Day i+1 High/Low to exit.
                # If we exit at SL/TP, we update cash and holdings immediately.
                
                # Simplified Risk Management for Portfolio Mode:
                # We only check SL/TP if we have a position.
                # Logic matches original backtester: check Gap, then High/Low.
                
                exit_executed = False
                if position_type != 0:
                    entry = entry_prices[ticker]
                    high = df['High'].iloc[i+1]
                    low = df['Low'].iloc[i+1]
                    
                    exit_price = None
                    reason = ""
                    
                    if position_type == 1: # Long
                        if (exec_price - entry) / entry <= -stop_loss: # Gap Down
                            exit_price = exec_price
                            reason = "SL (Gap)"
                        elif (exec_price - entry) / entry >= take_profit: # Gap Up
                            exit_price = exec_price
                            reason = "TP (Gap)"
                        elif (low - entry) / entry <= -stop_loss:
                            exit_price = entry * (1 - stop_loss)
                            reason = "SL"
                        elif (high - entry) / entry >= take_profit:
                            exit_price = entry * (1 + take_profit)
                            reason = "TP"
                            
                    elif position_type == -1: # Short
                        if (entry - exec_price) / entry <= -stop_loss: # Gap Up
                            exit_price = exec_price
                            reason = "SL (Gap)"
                        elif (entry - exec_price) / entry >= take_profit: # Gap Down
                            exit_price = exec_price
                            reason = "TP (Gap)"
                        elif (entry - high) / entry <= -stop_loss:
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
                            cash -= proceeds # Short covering uses cash
                            # Short logic: Initial sale added to cash. Now we subtract buyback cost.
                            # Wait, standard backtester logic:
                            # Entry Short: Cash += EntryPrice * Shares (minus costs)
                            # Exit Short: Cash -= ExitPrice * Shares (plus costs)
                            # Let's stick to simple PnL adjustment or full cash tracking?
                            # Full cash tracking is better.
                            
                            # Re-verify Short Entry logic below.
                            # If we are simplifying, let's assume Short Entry adds cash?
                            # Usually margin account. Let's assume cash is collateral.
                            # PnL = (Entry - Exit) * Shares.
                            # Cash += PnL.
                            
                            # Let's stick to the PnL method for simplicity in this iteration
                            # to match the previous logic which didn't track margin explicitly.
                            # BUT, for portfolio, we need Cash to buy other things.
                            
                            # Let's assume:
                            # Long Buy: Cash -= Cost
                            # Long Sell: Cash += Proceeds
                            # Short Sell: Cash += Proceeds (Short Proceeds available? No, usually held as margin)
                            # Let's assume Short Sell: Cash -= Margin Requirement?
                            # For simplicity: Short Sell -> Cash stays same (or adds proceeds if we ignore margin rules), 
                            # Short Cover -> Cash adjustment.
                            
                            # To be safe and robust:
                            # Treat Shorting as:
                            # Open: Cash -= 0 (Margin used)
                            # Close: Cash += PnL
                            # This prevents using short proceeds to buy other stocks (conservative).
                            
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
                        exit_executed = True

                # --- Signal Execution ---
                if not exit_executed:
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
