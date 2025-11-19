import pandas as pd
import pandas_ta as ta

class Strategy:
    def __init__(self, name, trend_period=None):
        self.name = name
        self.trend_period = trend_period

    def apply_trend_filter(self, df, signals):
        """
        Filters out Buy signals (1) if Close is below SMA(trend_period).
        """
        if self.trend_period is None:
            return signals
            
        trend_sma = ta.sma(df['Close'], length=self.trend_period)
        if trend_sma is None:
            return signals
            
        # If Close < Trend SMA, set Buy signals (1) to 0
        # We align the mask with signals index
        bearish_mask = df['Close'] < trend_sma
        
        # Only filter positive signals (Entries)
        # We don't want to filter Sell signals (Exits)
        signals.loc[(signals == 1) & bearish_mask] = 0
        
        return signals

    def generate_signals(self, df):
        raise NotImplementedError

class SMACrossoverStrategy(Strategy):
    def __init__(self, short_window=5, long_window=25, trend_period=200):
        super().__init__(f"SMA Crossover ({short_window}/{long_window})", trend_period)
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df):
        signals = pd.DataFrame(index=df.index)
        signals['Signal'] = 0
        
        short_sma = ta.sma(df['Close'], length=self.short_window)
        long_sma = ta.sma(df['Close'], length=self.long_window)
        
        signals.loc[short_sma > long_sma, 'Signal'] = 1 
        signals.loc[short_sma < long_sma, 'Signal'] = -1
        
        signals['Position'] = signals['Signal'].diff()
        
        final_signals = pd.Series(0, index=df.index)
        final_signals.loc[signals['Position'] == 2] = 1
        final_signals.loc[signals['Position'] == -2] = -1
        
        return self.apply_trend_filter(df, final_signals)

class RSIStrategy(Strategy):
    def __init__(self, period=14, lower=30, upper=70, trend_period=200):
        super().__init__(f"RSI ({period}) Reversal", trend_period)
        self.period = period
        self.lower = lower
        self.upper = upper

    def generate_signals(self, df):
        rsi = ta.rsi(df['Close'], length=self.period)
        signals = pd.Series(0, index=df.index)
        
        if rsi is None:
             return signals

        prev_rsi = rsi.shift(1)
        
        signals.loc[(prev_rsi < self.lower) & (rsi >= self.lower)] = 1
        signals.loc[(prev_rsi > self.upper) & (rsi <= self.upper)] = -1
        
        return self.apply_trend_filter(df, signals)

class BollingerBandsStrategy(Strategy):
    def __init__(self, length=20, std=2, trend_period=200):
        super().__init__(f"Bollinger Bands ({length}, {std})", trend_period)
        self.length = length
        self.std = std

    def generate_signals(self, df):
        bb = ta.bbands(df['Close'], length=self.length, std=self.std)
        
        if bb is None:
            return pd.Series(0, index=df.index)
            
        lower_col = f"BBL_{self.length}_{self.std}.0"
        upper_col = f"BBU_{self.length}_{self.std}.0"
        
        if lower_col not in bb.columns:
             cols = bb.columns
             lower_col = cols[0]
             upper_col = cols[2]

        signals = pd.Series(0, index=df.index)
        
        signals.loc[df['Close'] < bb[lower_col]] = 1
        signals.loc[df['Close'] > bb[upper_col]] = -1
        
        return self.apply_trend_filter(df, signals)

class CombinedStrategy(Strategy):
    def __init__(self, rsi_period=14, bb_length=20, bb_std=2, trend_period=200):
        super().__init__(f"RSI + BB Combined", trend_period)
        self.rsi_period = rsi_period
        self.bb_length = bb_length
        self.bb_std = bb_std

    def generate_signals(self, df):
        # RSI Signals
        rsi = ta.rsi(df['Close'], length=self.rsi_period)
        
        # BB Signals
        bb = ta.bbands(df['Close'], length=self.bb_length, std=self.bb_std)
        
        if rsi is None or bb is None:
            return pd.Series(0, index=df.index)
            
        lower_col = f"BBL_{self.bb_length}_{self.bb_std}.0"
        upper_col = f"BBU_{self.bb_length}_{self.bb_std}.0"
        
        if lower_col not in bb.columns:
             cols = bb.columns
             lower_col = cols[0]
             upper_col = cols[2]

        signals = pd.Series(0, index=df.index)
        
        # Confluence: RSI < 30 AND Price < Lower Band
        buy_condition = (rsi < 30) & (df['Close'] < bb[lower_col])
        
        # Confluence: RSI > 70 AND Price > Upper Band
        sell_condition = (rsi > 70) & (df['Close'] > bb[upper_col])
        
        signals.loc[buy_condition] = 1
        signals.loc[sell_condition] = -1
        
        return self.apply_trend_filter(df, signals)
