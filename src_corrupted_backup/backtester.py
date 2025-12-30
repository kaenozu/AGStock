from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from src.strategies import Order, OrderSide, OrderType, Strategy


class Backtester:
    #     """
    #         Parameters
    #     ----------
    #     initial_capital: float, default 100_000
    #         Starting cash for the simulation.
    #     position_size: Union[float, Dict[str, float]], default 0.1
    #         Fraction of portfolio to allocate per trade. Can be a dict per ticker.
    #     commission: float, default 0.001
    #         Proportional transaction cost.
    #     slippage: float, default 0.001
    #         Proportional slippage cost.
    #     allow_short: bool, default True
    #         Whether short positions are permitted.
    #     """

    (self,)
    initial_capital: float = (100_000,)
    position_size: Union[float, Dict[str, float]] = (0.1,)
    commission: float = (0.001,)
    slippage: float = (0.001,)
    allow_short: bool = (True,)
    self.initial_capital = initial_capital
    self.position_size = position_size
    self.commission = commission
    self.slippage = slippage
    self.allow_short = allow_short
    #     """Calculate number of shares for a new position.
    #         Uses ``self.position_size`` which may be a float or a dict per ticker.
    #             if isinstance(self.position_size, dict):
        pass
    #                 alloc = self.position_size.get(ticker, 0.0)
    #         else:
        pass
    #             alloc = self.position_size
    #         target_amount = portfolio_value * alloc
    #         return target_amount / exec_price if exec_price != 0 else 0.0
    #     """
    #     """
    #         strategy: Union[Strategy, Dict[str, Strategy]],
    #         stop_loss: float = 0.05,
    #         take_profit: float = 0.1,
    #         trailing_stop: Optional[float] = None,
    #     ) -> Dict[str, Any]:
        pass
    #             Supports integer signals (1 for long entry, -1 for exit/short) and ``Order`` objects.
    #         # Handle None or empty DataFrame
    #         if data is None:
        pass
    #             return None
    #         if isinstance(data, pd.DataFrame) and data.empty:
        pass
    #             return None
    # # Track if single DataFrame input for backward compatibility
    #         single_asset_mode = isinstance(data, pd.DataFrame)
    # # Normalise inputs
    #         if isinstance(data, pd.DataFrame):
        pass
    #             data_map = {"Asset": data}
    #         else:
        pass
    #             data_map = data
    #             if isinstance(strategy, Strategy):
        pass
    #                 strategy_map = {ticker: strategy for ticker in data_map}
    #         else:
        pass
    #             strategy_map = strategy
    #             if not data_map:
        pass
    #                 return {}
    # # Generate signals per ticker (could be int or Order)
    #         signals_map: Dict[str, pd.Series] = {}
    #         for ticker, df in data_map.items():
        pass
    #             if df is None or df.empty:
        pass
    #                 continue
    #             strat = strategy_map.get(ticker)
    #             if strat:
        pass
    #                 signals_map[ticker] = strat.generate_signals(df)
    #             else:
        pass
    #                 signals_map[ticker] = pd.Series(0, index=df.index)
    # # Unified index across all tickers
    #         all_dates = sorted(set().union(*[df.index for df in data_map.values() if df is not None]))
    #         full_index = pd.DatetimeIndex(all_dates)
    # # Initialise state
    #         cash = self.initial_capital
    #         holdings: Dict[str, float] = {t: 0.0 for t in data_map}
    #         entry_prices: Dict[str, float] = {t: 0.0 for t in data_map}
    #         trades: List[Dict[str, Any]] = []
    #         portfolio_value_history: List[float] = []
    #         position_history: List[int] = []  # Track position state at each timestep
    #         trailing_stop_levels: Dict[str, float] = {t: 0.0 for t in data_map}  # Track trailing stop per ticker
    #         highest_prices: Dict[str, float] = {t: 0.0 for t in data_map}  # Track highest price since entry
    # # Align data and attach signals
    #         aligned_data: Dict[str, pd.DataFrame] = {}
    #         for ticker, df in data_map.items():
        pass
    #             aligned = df.reindex(full_index).ffill()
    #             aligned["Signal"] = signals_map.get(ticker, pd.Series(0, index=df.index)).reindex(full_index).fillna(0)
    #             aligned_data[ticker] = aligned
    # # Main simulation loop (skip last day – no next open price)
    #         for i in range(len(full_index) - 1):
        pass
    #             # Portfolio market-to-market value for sizing decisions
    # # For short positions, calculate value as: entry_price - current_price
    #             current_portfolio_value = cash
    #             for t in data_map:
        pass
    #                 if holdings[t] != 0 and not pd.isna(aligned_data[t]["Close"].iloc[i]):
        pass
    #                     if holdings[t] > 0:  # Long position
    #                         current_portfolio_value += holdings[t] * aligned_data[t]["Close"].iloc[i]
    #                     else:  # Short position
    # # Short value = entry_price * abs(shares) - current_price * abs(shares)
    # # Which simplifies to: (entry_price - current_price) * abs(shares)
    #                         entry_price_val = entry_prices[t]
    #                         current_price_val = aligned_data[t]["Close"].iloc[i]
    #                         profit = (entry_price_val - current_price_val) * abs(holdings[t])
    #                         current_portfolio_value += profit
    #                 for ticker, df in aligned_data.items():
        pass
    #                     today_sig = df["Signal"].iloc[i]
    #                 exec_price = df["Open"].iloc[i + 1]
    #                 position = holdings[ticker]
    #                 exit_executed = False
    #                 today_high = df["High"].iloc[i]
    #                 today_low = df["Low"].iloc[i]
    # # ----- CHECK STOP LOSS / TAKE PROFIT / TRAILING STOP -----
    #                 if position != 0:
        pass
    #                     entry = entry_prices[ticker]
    # # Update highest price for trailing stop
    #                     if position > 0:  # Long position
    #                         highest_prices[ticker] = max(highest_prices[ticker], today_high)
    # # Update trailing stop level if set
    #                         if trailing_stop and trailing_stop > 0:
        pass
    #                             new_stop = highest_prices[ticker] * (1 - trailing_stop)
    #                             trailing_stop_levels[ticker] = max(trailing_stop_levels[ticker], new_stop)
    # # Check trailing stop
    #                         if (
    #                             trailing_stop
    #                             and trailing_stop_levels[ticker] > 0
    #                             and today_low <= trailing_stop_levels[ticker]
    #                         ):
        pass
    #                             trades.append(
    #                                 {
    #                                     "ticker": ticker,
    #                                     "entry_date": None,
    #                                     "exit_date": full_index[i],
    #                                     "entry_price": entry,
    #                                     "exit_price": trailing_stop_levels[ticker],
    #                                     "return": (trailing_stop_levels[ticker] - entry) / entry,
    #                                     "type": "Long",
    #                                     "reason": "Trailing Stop",
    #                                 }
    #                             )
    #                             cash += holdings[ticker] * trailing_stop_levels[ticker]
    #                             holdings[ticker] = 0.0
    #                             entry_prices[ticker] = 0.0
    #                             trailing_stop_levels[ticker] = 0.0
    #                             highest_prices[ticker] = 0.0
    #                             exit_executed = True
    #                             continue
    # # Check take profit
    #                         elif take_profit and (today_high - entry) / entry >= take_profit:
        pass
    #                             trades.append(
    #                                 {
    #                                     "ticker": ticker,
    #                                     "entry_date": None,
    #                                     "exit_date": full_index[i],
    #                                     "entry_price": entry,
    #                                     "exit_price": entry * (1 + take_profit),
    #                                     "return": take_profit,
    #                                     "type": "Long",
    #                                     "reason": "Take Profit",
    #                                 }
    #                             )
    #                             cash += holdings[ticker] * (entry * (1 + take_profit))
    #                             holdings[ticker] = 0.0
    #                             entry_prices[ticker] = 0.0
    #                             trailing_stop_levels[ticker] = 0.0
    #                             highest_prices[ticker] = 0.0
    #                             exit_executed = True
    #                             continue
    # # Check stop loss
    #                         elif stop_loss and (entry - today_low) / entry >= stop_loss:
        pass
    #                             trades.append(
    #                                 {
    #                                     "ticker": ticker,
    #                                     "entry_date": None,
    #                                     "exit_date": full_index[i],
    #                                     "entry_price": entry,
    #                                     "exit_price": entry * (1 - stop_loss),
    #                                     "return": -stop_loss,
    #                                     "type": "Long",
    #                                     "reason": "Stop Loss",
    #                                 }
    #                             )
    #                             cash += holdings[ticker] * (entry * (1 - stop_loss))
    #                             holdings[ticker] = 0.0
    #                             entry_prices[ticker] = 0.0
    #                             trailing_stop_levels[ticker] = 0.0
    #                             highest_prices[ticker] = 0.0
    #                             exit_executed = True
    #                             continue
    # # ----- EXIT LOGIC FOR INTEGER SIGNALS -----
    #                 if isinstance(today_sig, (int, np.integer)):
        pass
    #                     if position > 0 and today_sig == -1:
        pass
    #                         entry = entry_prices[ticker]
    #                         ret = (exec_price - entry) / entry
    #                         trades.append(
    #                             {
    #                                 "ticker": ticker,
    #                                 "entry_date": None,
    #                                 "exit_date": full_index[i + 1],
    #                                 "entry_price": entry,
    #                                 "exit_price": exec_price,
    #                                 "return": ret,
    #                                 "type": "Long",
    #                             }
    #                         )
    #                         cash += holdings[ticker] * exec_price
    #                         holdings[ticker] = 0.0
    #                         entry_prices[ticker] = 0.0
    #                         exit_executed = True
    #                     elif position < 0 and today_sig == 1:
        pass
    #                         entry = entry_prices[ticker]
    #                         ret = (entry - exec_price) / entry
    #                         trades.append(
    #                             {
    #                                 "ticker": ticker,
    #                                 "entry_date": None,
    #                                 "exit_date": full_index[i + 1],
    #                                 "entry_price": entry,
    #                                 "exit_price": exec_price,
    #                                 "return": ret,
    #                                 "type": "Short",
    #                             }
    #                         )
    # # For short, cash update is PnL: (entry - exit) * shares
    #                         cash += (entry - exec_price) * abs(holdings[ticker])
    #                         holdings[ticker] = 0.0
    #                         entry_prices[ticker] = 0.0
    #                         exit_executed = True
    # # ----- ORDER OBJECT LOGIC -----
    #                 if isinstance(today_sig, Order):
        pass
    #                     # Ensure ticker attribute is set
    #                     if not today_sig.ticker:
        pass
    #                         today_sig.ticker = ticker
    # # Determine if order should execute based on type
    #                     should_execute = False
    #                     fill_price = exec_price
    #                         if today_sig.type == OrderType.MARKET:
        pass
    #                             should_execute = True
    #                     elif today_sig.type == OrderType.LIMIT:
        pass
    #                         # Limit BUY: execute if price drops to or below limit
    # # Limit SELL: execute if price rises to or above limit
    #                         if today_sig.action.upper() == "BUY":
        pass
    #                             # Check if Low of next day <= limit price
    #                             if df["Low"].iloc[i + 1] <= today_sig.price:
        pass
    #                                 should_execute = True
    #                                 fill_price = min(today_sig.price, exec_price)
    #                         else:  # SELL
    # # Check if High of next day >= limit price
    #                             if df["High"].iloc[i + 1] >= today_sig.price:
        pass
    #                                 should_execute = True
    #                                 fill_price = max(today_sig.price, exec_price)
    #                     elif today_sig.type == OrderType.STOP:
        pass
    #                         # Stop BUY: execute if price rises to or above stop
    # # Stop SELL: execute if price drops to or below stop
    #                         if today_sig.action.upper() == "BUY":
        pass
    #                             # Check if High of next day >= stop price
    #                             if df["High"].iloc[i + 1] >= today_sig.price:
        pass
    #                                 should_execute = True
    #                                 fill_price = max(today_sig.price, exec_price)
    #                         else:  # SELL
    # # Check if Low of next day <= stop price
    #                             if df["Low"].iloc[i + 1] <= today_sig.price:
        pass
    #                                 should_execute = True
    #                                 fill_price = min(today_sig.price, exec_price)
    # # Execute order if conditions met
    #                     if should_execute:
        pass
    #                         # BUY action
    #                         if today_sig.action.upper() == "BUY":
        pass
    #                             if holdings[ticker] == 0:
        pass
    #                                 qty = (
    #                                     today_sig.quantity
    #                                     if today_sig.quantity
    #                                     else self._size_position(ticker, current_portfolio_value, fill_price)
    #                                 )
    #                                 holdings[ticker] = qty
    #                                 entry_prices[ticker] = fill_price
    # # Initialize trailing stop tracking
    #                                 highest_prices[ticker] = fill_price
    #                                 if trailing_stop and trailing_stop > 0:
        pass
    #                                     trailing_stop_levels[ticker] = fill_price * (1 - trailing_stop)
    # # SELL action (close existing position)
    #                         elif today_sig.action.upper() == "SELL":
        pass
    #                             if holdings[ticker] != 0:
        pass
    #                                 entry = entry_prices[ticker]
    #                                 if holdings[ticker] > 0:
        pass
    #                                     ret = (fill_price - entry) / entry
    #                                     trade_type = "Long"
    #                                 else:
        pass
    #                                     ret = (entry - fill_price) / entry
    #                                     trade_type = "Short"
    #                                 trades.append(
    #                                     {
    #                                         "ticker": ticker,
    #                                         "entry_date": None,
    #                                         "exit_date": full_index[i + 1],
    #                                         "entry_price": entry,
    #                                         "exit_price": fill_price,
    #                                         "return": ret,
    #                                         "type": trade_type,
    #                                     }
    #                                 )
    #                                 holdings[ticker] = 0.0
    #                                 entry_prices[ticker] = 0.0
    #                                 exit_executed = True
    #                     if not exit_executed and isinstance(today_sig, (int, np.integer)):
        pass
    #                         if holdings[ticker] == 0 and today_sig == 1:
        pass
    #                             # Open long position
    #                         shares = self._size_position(ticker, current_portfolio_value, exec_price)
    #                         holdings[ticker] = shares
    #                         entry_prices[ticker] = exec_price
    #                         cash -= shares * exec_price
    # # Initialize trailing stop tracking
    #                         highest_prices[ticker] = exec_price
    #                         if trailing_stop and trailing_stop > 0:
        pass
    #                             trailing_stop_levels[ticker] = exec_price * (1 - trailing_stop)
    #                     elif holdings[ticker] == 0 and today_sig == -1 and self.allow_short:
        pass
    #                         # Open short position
    #                         shares = self._size_position(ticker, current_portfolio_value, exec_price)
    #                         holdings[ticker] = -shares
    #                         entry_prices[ticker] = exec_price
    # # Cash unchanged for short entry (margin model)
    # # Record portfolio value and position state at end of day i
    # # For short positions, calculate value correctly
    #             end_of_day_value = cash
    #             for t in data_map:
        pass
    #                 if holdings[t] != 0 and not pd.isna(aligned_data[t]["Close"].iloc[i]):
        pass
    #                     if holdings[t] > 0:  # Long position
    #                         end_of_day_value += holdings[t] * aligned_data[t]["Close"].iloc[i]
    #                     else:  # Short position
    #                         entry_price_val = entry_prices[t]
    #                         current_price_val = aligned_data[t]["Close"].iloc[i]
    #                         profit = (entry_price_val - current_price_val) * abs(holdings[t])
    #                         end_of_day_value += profit
    #             portfolio_value_history.append(end_of_day_value)
    # # Record position state: 1 if long, -1 if short, 0 if flat
    #             position_state = 0
    #             for h in holdings.values():
        pass
    #                 if h > 0:
        pass
    #                     position_state = 1
    #                     break
    #                 elif h < 0:
        pass
    #                     position_state = -1
    #                     break
    #             position_history.append(position_state)
    # # Final valuation after last day
    # # For short positions, calculate value correctly
    #         final_portfolio_value = cash
    #         for t in data_map:
        pass
    #             if holdings[t] != 0 and not pd.isna(aligned_data[t]["Close"].iloc[-1]):
        pass
    #                 if holdings[t] > 0:  # Long position
    #                     final_portfolio_value += holdings[t] * aligned_data[t]["Close"].iloc[-1]
    #                 else:  # Short position
    #                     entry_price_val = entry_prices[t]
    #                     current_price_val = aligned_data[t]["Close"].iloc[-1]
    #                     profit = (entry_price_val - current_price_val) * abs(holdings[t])
    #                     final_portfolio_value += profit
    #         portfolio_value_history.append(final_portfolio_value)
    #         equity_curve_raw = pd.Series(portfolio_value_history, index=full_index)
    # # Normalize equity curve to start at 1.0
    #         equity_curve = equity_curve_raw / self.initial_capital
    #         total_return = (final_portfolio_value - self.initial_capital) / self.initial_capital
    # # Simple performance metrics
    #         win_rate = sum(1 for tr in trades if tr["return"] > 0) / len(trades) if trades else 0.0
    #         avg_return = np.mean([tr["return"] for tr in trades]) if trades else 0.0
    #         running_max = equity_curve.cummax()
    #         drawdown = (running_max - equity_curve) / running_max
    #         max_drawdown = drawdown.max() if not drawdown.empty else 0.0
    #         daily_returns = equity_curve.pct_change().dropna()
    #         sharpe_ratio = (
    #             (np.sqrt(252) * daily_returns.mean() / daily_returns.std())
    #             if len(daily_returns) > 0 and daily_returns.std() > 0
    #             else 0.0
    #         )
    # # Add final position state
    #         final_position_state = 0
    #         for h in holdings.values():
        pass
    #             if h > 0:
        pass
    #                 final_position_state = 1
    #                 break
    #             elif h < 0:
        pass
    #                 final_position_state = -1
    #                 break
    #         position_history.append(final_position_state)
    #             positions = pd.Series(position_history, index=full_index)
    # # Adjust signals format for backward compatibility
    #         if single_asset_mode:
        pass
    #             # Single asset: return Series directly
    #             result_signals = signals_map.get("Asset", pd.Series(0, index=full_index))
    #         else:
        pass
    #             # Multi-asset: return Dict
    #             result_signals = signals_map
    #             return {
    #             "total_return": total_return,
    #             "final_value": final_portfolio_value,
    #             "equity_curve": equity_curve,
    #             "signals": result_signals,
    #             "positions": positions,
    #             "trades": trades,
    #             "win_rate": win_rate,
    #             "avg_return": avg_return,
    #             "max_drawdown": max_drawdown,
    #             "sharpe_ratio": sharpe_ratio,
    #             "total_trades": len(trades),
    #             "num_trades": len(trades),
    #         }
    #     """
    (self,)
    (full_index,)
    (aligned_data,)
    (data_map,)
    (cash,)
    (holdings,)
    (entry_prices,)
    (trades,)
    (portfolio_value_history,)
    (position_history,)
    (trailing_stop_levels,)
    (highest_prices,)
    (stop_loss,)
    (take_profit,)
    trailing_stop
    #     """Simulation loop extracted from run method to reduce complexity."""
    # Main simulation loop (skip last day – no next open price)
    for i in range(len(full_index) - 1):
        # Portfolio market-to-market value for sizing decisions
        # For short positions, calculate value as: entry_price - current_price
        current_portfolio_value = cash
        for t in data_map:
            if holdings[t] != 0 and not pd.isna(aligned_data[t]["Close"].iloc[i]):
                if holdings[t] > 0:  # Long position
                    current_portfolio_value += (
                        holdings[t] * aligned_data[t]["Close"].iloc[i]
                    )
                else:  # Short position
                    # Short value = entry_price * abs(shares) - current_price * abs(shares)
                    # Which simplifies to: (entry_price - current_price) * abs(shares)
                    entry_price_val = entry_prices[t]
                    current_price_val = aligned_data[t]["Close"].iloc[i]
                    profit = (entry_price_val - current_price_val) * abs(holdings[t])
                    current_portfolio_value += profit
            for ticker, df in aligned_data.items():
                pass
            today_sig = df["Signal"].iloc[i]
            exec_price = df["Open"].iloc[i + 1]
            position = holdings[ticker]
            exit_executed = False
            today_high = df["High"].iloc[i]
            today_low = df["Low"].iloc[i]
            # ----- CHECK STOP LOSS / TAKE PROFIT / TRAILING STOP -----
            if position != 0:
                entry = entry_prices[ticker]
                # Update highest price for trailing stop
                if position > 0:  # Long position
                    highest_prices[ticker] = max(highest_prices[ticker], today_high)
                    # Update trailing stop level if set
                    if trailing_stop and trailing_stop > 0:
                        new_stop = highest_prices[ticker] * (1 - trailing_stop)
                        trailing_stop_levels[ticker] = max(
                            trailing_stop_levels[ticker], new_stop
                        )
                    # Check trailing stop
                    if (
                        trailing_stop
                        and trailing_stop > 0
                        and trailing_stop_levels[ticker] > 0
                        and today_low <= trailing_stop_levels[ticker]
                    ):
                        trades.append(
                            {
                                "ticker": ticker,
                                "entry_date": None,
                                "exit_date": full_index[i],
                                "entry_price": entry,
                                "exit_price": trailing_stop_levels[ticker],
                                "return": (trailing_stop_levels[ticker] - entry)
                                / entry,
                                "type": "Long",
                                "reason": "Trailing Stop",
                            }
                        )
                        cash += holdings[ticker] * trailing_stop_levels[ticker]
                        holdings[ticker] = 0.0
                        entry_prices[ticker] = 0.0
                        trailing_stop_levels[ticker] = 0.0
                        highest_prices[ticker] = 0.0
                        exit_executed = True
                        continue
                    # Check take profit
                    elif take_profit and (today_high - entry) / entry >= take_profit:
                        trades.append(
                            {
                                "ticker": ticker,
                                "entry_date": None,
                                "exit_date": full_index[i],
                                "entry_price": entry,
                                "exit_price": entry * (1 + take_profit),
                                "return": take_profit,
                                "type": "Long",
                                "reason": "Take Profit",
                            }
                        )
                        cash += holdings[ticker] * (entry * (1 + take_profit))
                        holdings[ticker] = 0.0
                        entry_prices[ticker] = 0.0
                        trailing_stop_levels[ticker] = 0.0
                        highest_prices[ticker] = 0.0
                        exit_executed = True
                        continue
                    # Check stop loss
                    elif stop_loss and (entry - today_low) / entry >= stop_loss:
                        trades.append(
                            {
                                "ticker": ticker,
                                "entry_date": None,
                                "exit_date": full_index[i],
                                "entry_price": entry,
                                "exit_price": max(today_low, entry * (1 - stop_loss)),
                                "return": (
                                    max(today_low, entry * (1 - stop_loss)) - entry
                                )
                                / entry,
                                "type": "Long",
                                "reason": "Stop Loss",
                            }
                        )
                        cash += holdings[ticker] * max(
                            today_low, entry * (1 - stop_loss)
                        )
                        holdings[ticker] = 0.0
                        entry_prices[ticker] = 0.0
                        trailing_stop_levels[ticker] = 0.0
                        highest_prices[ticker] = 0.0
                        exit_executed = True
                        continue
            # ----- PROCESS ORDERS FROM SIGNALS -----
            if isinstance(today_sig, Order):
                # Order-based strategy
                if today_sig.side == OrderSide.BUY and position == 0:
                    # Enter long
                    # Use fixed fraction of portfolio for now
                    # In the original, it was a fixed amount (e.g., 100 shares)
                    # Let's keep the same logic here.
                    size = today_sig.size
                    cost = exec_price * size
                    if cash >= cost:
                        cash -= cost
                        holdings[ticker] = size
                        entry_prices[ticker] = exec_price
                        highest_prices[ticker] = exec_price
                elif today_sig.side == OrderSide.SELL and position > 0:
                    # Exit long
                    cash += position * exec_price
                    holdings[ticker] = 0.0
                    entry_prices[ticker] = 0.0
                    trailing_stop_levels[ticker] = 0.0
                    highest_prices[ticker] = 0.0
            else:
                # Integer-based strategy
                # 1: Enter/exit long
                # -1: Exit long, enter short (currently unsupported)
                # 0: Hold
                if today_sig == 1 and position == 0:
                    # Enter long
                    # Use fixed fraction of portfolio for now
                    # In the original, it was a fixed amount (e.g., 100 shares)
                    # Let's keep the same logic here.
                    shares = 100  # Fixed lot size for this example
                    cost = exec_price * shares
                    if cash >= cost:
                        cash -= cost
                        holdings[ticker] = shares
                        entry_prices[ticker] = exec_price
                        highest_prices[ticker] = exec_price
                elif (today_sig == -1 or today_sig == 1) and position != 0:
                    # Exit any existing position
                    cash += position * exec_price
                    holdings[ticker] = 0.0
                    entry_prices[ticker] = 0.0
                    trailing_stop_levels[ticker] = 0.0
                    highest_prices[ticker] = 0.0
        # Record values
        portfolio_value_history.append(current_portfolio_value)
        # A simple aggregate position (long/flat) for the whole portfolio
        total_holdings_value = sum(
            holdings[t] * aligned_data[t]["Close"].iloc[i] if holdings[t] != 0 else 0.0
            for t in data_map
        )
        if total_holdings_value > 0:
            position_history.append(1)
        elif total_holdings_value < 0:
            position_history.append(-1)
        else:
            position_history.append(0)


# """
#
# """
