import pandas as pd
import pandas_ta as ta
from typing import Optional

class Strategy:
    def __init__(self, name: str) -> None:
        self.name = name

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Takes a DataFrame with 'Close' column and adds 'Signal' column.
        1: Buy
        -1: Sell
        0: Hold
        """
        raise NotImplementedError

class SMACrossoverStrategy(Strategy):
    def __init__(self, short_window: int = 5, long_window: int = 25) -> None:
        super().__init__(f"SMA Crossover ({short_window}/{long_window})")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 空データフレームチェック
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        signals = pd.DataFrame(index=df.index)
        signals['Signal'] = 0
        
        # Calculate SMAs
        short_sma = ta.sma(df['Close'], length=self.short_window)
        long_sma = ta.sma(df['Close'], length=self.long_window)
        
        # Generate signals
        # Golden Cross: Short crosses above Long
        signals.loc[short_sma > long_sma, 'Signal'] = 1 
        # Dead Cross: Short crosses below Long
        signals.loc[short_sma < long_sma, 'Signal'] = -1
        
        # We want the *change* in signal to be the entry point
        # But for this simple version, let's stick to state: 1 = Bullish Zone, -1 = Bearish Zone
        # To make it a trade signal, we take the difference
        signals['Position'] = signals['Signal'].diff()
        
        # Position = 2 (was -1, now 1) -> Buy
        # Position = -2 (was 1, now -1) -> Sell
        
        final_signals = pd.Series(0, index=df.index)
        final_signals.loc[signals['Position'] == 2] = 1
        final_signals.loc[signals['Position'] == -2] = -1
        
        return final_signals

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, lower: float = 30, upper: float = 70) -> None:
        super().__init__(f"RSI ({period}) Reversal")
        self.period = period
        self.lower = lower
        self.upper = upper

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 空データフレームチェック
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        rsi = ta.rsi(df['Close'], length=self.period)
        signals = pd.Series(0, index=df.index)
        
        # Buy when RSI crosses above lower threshold (recovering from oversold)
        # Or simply Buy when RSI < lower? 
        # Let's do: Buy when RSI < lower, Sell when RSI > upper
        
        # To avoid constant signaling, we look for crossovers
        # Buy: RSI was < lower yesterday, and > lower today (Crossing up)
        # Sell: RSI was > upper yesterday, and < upper today (Crossing down)
        
        if rsi is None:
            return signals

        prev_rsi = rsi.shift(1)
        
        signals.loc[(prev_rsi < self.lower) & (rsi >= self.lower)] = 1
        signals.loc[(prev_rsi > self.upper) & (rsi <= self.upper)] = -1
        
        return signals

class BollingerBandsStrategy(Strategy):
    def __init__(self, length: int = 20, std: float = 2) -> None:
        super().__init__(f"Bollinger Bands ({length}, {std})")
        self.length = length
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 空データフレームチェック
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        # Calculate Bollinger Bands
        bb = ta.bbands(df['Close'], length=self.length, std=self.std)
        
        if bb is None:
            return pd.Series(0, index=df.index)
            
        lower_col = f"BBL_{self.length}_{self.std}.0"
        upper_col = f"BBU_{self.length}_{self.std}.0"
        
        # Check if columns exist (pandas_ta naming can vary)
        if lower_col not in bb.columns:
            # Fallback to guessing column names if needed, but usually standard
            cols = bb.columns
            lower_col = cols[0]
            upper_col = cols[2]

        signals = pd.Series(0, index=df.index)
        
        # Mean Reversion Strategy
        # Buy when price touches lower band
        # Sell when price touches upper band
        
        signals.loc[df['Close'] < bb[lower_col]] = 1
        signals.loc[df['Close'] > bb[upper_col]] = -1
        
        return signals
