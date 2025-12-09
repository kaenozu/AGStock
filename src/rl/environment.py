import numpy as np
import pandas as pd

class TradingEnvironment:
    """
    OpenAI Gym-like Stock Trading Environment.
    State: [O, H, L, C, V, Indicators...] (Normalized)
    Action: 0 (HOLD), 1 (BUY), 2 (SELL)
    Reward: Change in Portfolio Value (Simplified)
    """
    def __init__(self, df: pd.DataFrame, initial_balance: float = 1000000.0):
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.reset()
        
        # Determine state size from dataframe columns (assuming all cols are features)
        # We exclude 'Open', 'High', 'Low', 'Close', 'Volume' if they are raw values unscaled.
        # But for simplicity, we assume 'df' passed here is ALREADY SCALED FEATURES.
        self.state_size = df.shape[1]
        self.action_space_size = 3 # HOLD, BUY, SELL

    def reset(self):
        self.balance = self.initial_balance
        self.position = 0 # 0: No pos, 1: Long (Simplified to binary pos for now)
        self.entry_price = 0.0
        self.current_step = 0
        self.max_steps = len(self.df) - 1
        
        return self._get_observation()

    def _get_observation(self):
        return self.df.iloc[self.current_step].values

    def step(self, action):
        """
        Execute action and return (next_state, reward, done, info)
        Action: 0=HOLD, 1=BUY, 2=SELL
        """
        current_price = self.df.iloc[self.current_step]['Close'] # Assuming 'Close' is present or we track it separately
        reward = 0
        done = False
        
        # Basic logic: 
        # BUY: If no position, enter.
        # SELL: If position, exit and take profit/loss.
        # HOLD: Do nothing.
        
        # Note: If df is scaled, 'Close' might be 0.5 etc. 
        # For realistic reward, we need Raw Close Px. 
        # We assume for this prototype, we use percentage gain as reward directly roughly.
        
        # Let's assume the passed DF has a 'Raw_Close' column for PnL calc if possible, 
        # OR we just simulate using the scaled value trend which is risky.
        # FIX: We will rely on simple trend reward for this prototype:
        # If Action=BUY and Next Price > Current Price -> Reward +1
        # If Action=SELL and Next Price < Current Price -> Reward +1
        
        # Ideally, we need lookahead to calculate reward for 'step'.
        
        next_step = self.current_step + 1
        if next_step >= self.max_steps:
            done = True
            return np.zeros(self.state_size), 0, True, {}
            
        next_price = self.df.iloc[next_step]['Close']
        price_change_pct = (next_price - current_price) / current_price if current_price != 0 else 0
        
        if action == 1: # BUY
            if self.position == 0:
                self.position = 1
                self.entry_price = current_price
            reward = price_change_pct * 100 # Reward is % return
            
        elif action == 2: # SELL
            if self.position == 1:
                self.position = 0
                # Realize trade
                trade_return = (current_price - self.entry_price) / self.entry_price
                reward = trade_return * 100
            else:
                # Short selling logic or just penalty for invalid action?
                # Let's say we Short.
                reward = -price_change_pct * 100
                
        else: # HOLD
            # Small penalty for holding? Or 0.
            reward = 0
            
        self.current_step += 1
        next_state = self._get_observation()
        
        return next_state, reward, done, {}
