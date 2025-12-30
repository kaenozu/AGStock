import numpy as np
import pandas as pd


class TradingEnvironment:
    """
    OpenAI Gym-like Stock Trading Environment.
    State: [O, H, L, C, V, Indicators...] (Normalized)
    Action: 0 (HOLD), 1 (BUY), 2 (SELL)
    Reward: Change in Portfolio Value (Simplified)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 1000000.0,
        transaction_cost_pct: float = 0.001,
    ):
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.transaction_cost_pct = transaction_cost_pct
        self.reset()

        # Determine state size
        # Original features + [Position Status (0/1), Unrealized PnL %]
        self.state_size = df.shape[1] + 2
        self.action_space_size = 3  # HOLD, BUY, SELL

    def reset(self):
        self.balance = self.initial_balance
        self.shares_held = 0
        self.entry_price = 0.0
        self.current_step = 0
        self.max_steps = len(self.df) - 1

        # Portfolio value history for Sharpe calculation (simplified)
        self.portfolio_value = self.initial_balance
        self.prev_portfolio_value = self.initial_balance

        return self._get_observation()

    def _get_observation(self):
        # Base features from DataFrame
        frame = self.df.iloc[self.current_step].values

        # Additional Context features
        position_flag = 1.0 if self.shares_held > 0 else 0.0

        current_price = self.df.iloc[self.current_step]["Close"]
        if self.shares_held > 0 and self.entry_price > 0:
            unrealized_pnl = (current_price - self.entry_price) / self.entry_price
        else:
            unrealized_pnl = 0.0

        # Concatenate
        return np.append(frame, [position_flag, unrealized_pnl])

    def step(self, action):
        """
        Execute action and return (next_state, reward, done, info)
        Action: 0=HOLD, 1=BUY, 2=SELL
        """
        current_price = self.df.iloc[self.current_step]["Close"]

        reward = 0
        done = False

        # Current Total Value for Reward Calculation
        # Value = Cash + (Shares * Current Price)
        current_val = self.balance + (self.shares_held * current_price)

        # Logic
        if action == 1:  # BUY
            if self.shares_held == 0:
                # Buy as much as possible with current balance
                # Apply transaction cost: Cost = Amount * Price * (1 + Fee)
                max_shares = int(
                    self.balance / (current_price * (1 + self.transaction_cost_pct))
                )
                if max_shares > 0:
                    cost = max_shares * current_price * (1 + self.transaction_cost_pct)
                    self.balance -= cost
                    self.shares_held = max_shares
                    self.entry_price = current_price
            # Log trade?
            else:
                # Already holding, do nothing (or maybe add more? simplified to single shot for now)
                pass

        elif action == 2:  # SELL
            if self.shares_held > 0:
                # Sell all
                revenue = (
                    self.shares_held * current_price * (1 - self.transaction_cost_pct)
                )
                self.balance += revenue
                self.shares_held = 0
                self.entry_price = 0.0
            else:
                # No shares to sell
                pass

        # 0 = HOLD, do nothing

        # Update Step
        self.current_step += 1
        if self.current_step >= self.max_steps:
            done = True

        # Calculate Reward
        # New Portfolio Value
        if not done:
            next_price = self.df.iloc[self.current_step][
                "Close"
            ]  # This is actually next step's price now
        else:
            next_price = current_price  # End of episode

        new_val = self.balance + (self.shares_held * next_price)

        # Reward = Change in Portfolio Value - Risk Penalty
        # We want to encourage consistent gains, discourage volatility?
        # For now, let's use Simple Profit Change, but Transaction Cost is already baked into 'new_val' vs 'current_val'
        # If we just bought, balance dropped (cost), shares added. Value is roughly same minus fee.
        # So immediate reward for buying is negative (fee). This is good, prevents churning.

        change = new_val - self.prev_portfolio_value

        # Normalize reward to be smallish (e.g., relative to initial balance or just raw?)
        # For RL stability, smaller is often better. Let's use % change of portfolio.
        reward = (change / self.initial_balance) * 100

        # Penalize holding losing position? (Optional)
        # if self.shares_held > 0 and (next_price < self.entry_price):
        #             pass
        #     reward -= 0.01

        self.prev_portfolio_value = new_val
        self.portfolio_value = new_val

        if done:
            # Final state
            next_state = np.zeros(self.state_size)
        else:
            next_state = self._get_observation()

        info = {
            "portfolio_value": self.portfolio_value,
            "balance": self.balance,
            "shares": self.shares_held,
        }

        return next_state, reward, done, info
