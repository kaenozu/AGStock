import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital

    def run(self, df, strategy):
        """
        Runs a strategy on a dataframe and returns performance metrics.
        """
        if df is None or df.empty:
            return None

        signals = strategy.generate_signals(df)
        
        # Align signals with data
        df = df.copy()
        df['Signal'] = signals
        
        # Calculate returns
        # If Signal is 1 (Buy), we hold the stock until Signal is -1 (Sell)
        # This is a simplified backtest.
        
        positions = pd.Series(0, index=df.index)
        current_pos = 0
        
        for i in range(len(df)):
            sig = df['Signal'].iloc[i]
            if sig == 1:
                current_pos = 1
            elif sig == -1:
                current_pos = 0
            positions.iloc[i] = current_pos
            
        # Shift positions by 1 because we enter on the *next* open/close after signal
        # For simplicity, let's assume we trade at Close of the signal day (optimistic)
        # Or more realistically, we trade at Close.
        
        # Daily returns of the stock
        df['Pct_Change'] = df['Close'].pct_change()
        
        # Strategy returns: if we held the stock (position=1), we get the return
        df['Strategy_Return'] = positions.shift(1) * df['Pct_Change']
        
        # Cumulative Return
        df['Cumulative_Return'] = (1 + df['Strategy_Return']).cumprod()
        
        # Metrics
        total_return = df['Cumulative_Return'].iloc[-1] - 1 if not df['Cumulative_Return'].empty else 0
        
        # Win Rate calculation (per trade)
        trades = signals[signals != 0]
        # This is tricky without a full trade log. 
        # Let's approximate: Count days with positive strategy return vs negative?
        # No, better to count completed trades.
        
        # Simple metric: Total Return is the most important for ranking.
        
        return {
            "total_return": total_return,
            "final_value": self.initial_capital * (1 + total_return),
            "signals": signals,
            "positions": positions,
            "equity_curve": df['Cumulative_Return']
        }
