import pandas as pd
import ta
from .base import Strategy

class SMACrossoverStrategy(Strategy):
    def __init__(self, short_window: int = 5, long_window: int = 25, trend_period: int = 200) -> None:
        super().__init__(f"SMA Crossover ({short_window}/{long_window})", trend_period)
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        signals = pd.Series(0, index=df.index)
        
        short_sma = df['Close'].rolling(window=self.short_window).mean()
        long_sma = df['Close'].rolling(window=self.long_window).mean()
        
        # Golden Cross
        signals.loc[(short_sma > long_sma) & (short_sma.shift(1) <= long_sma.shift(1))] = 1
        # Dead Cross
        signals.loc[(short_sma < long_sma) & (short_sma.shift(1) >= long_sma.shift(1))] = -1
        
        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "短期移動平均線が長期移動平均線を上抜けました（ゴールデンクロス）。上昇トレンドの始まりを示唆しています。"
        elif signal == -1:
            return "短期移動平均線が長期移動平均線を下抜けました（デッドクロス）。下落トレンドの始まりを示唆しています。"
        return "明確なトレンド転換シグナルは出ていません。"

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, lower: float = 30, upper: float = 70, trend_period: int = 200) -> None:
        super().__init__(f"RSI ({period}) Reversal", trend_period)
        self.period = period
        self.lower = lower
        self.upper = upper

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        rsi_indicator = ta.momentum.RSIIndicator(close=df['Close'], window=self.period)
        rsi = rsi_indicator.rsi()
        signals = pd.Series(0, index=df.index)
        
        if rsi is None or rsi.isna().all():
            return signals

        prev_rsi = rsi.shift(1)
        
        # Buy: Cross above lower
        signals.loc[(prev_rsi < self.lower) & (rsi >= self.lower)] = 1
        # Sell: Cross below upper
        signals.loc[(prev_rsi > self.upper) & (rsi <= self.upper)] = -1
        
        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return f"RSIが{self.lower}を下回った後、回復しました。売られすぎからの反発を示唆しています。"
        elif signal == -1:
            return f"RSIが{self.upper}を上回った後、下落しました。買われすぎからの反落を示唆しています。"
        return "RSIは中立圏内で推移しています。"

class BollingerBandsStrategy(Strategy):
    def __init__(self, length: int = 20, std: float = 2, trend_period: int = 200) -> None:
        super().__init__(f"Bollinger Bands ({length}, {std})", trend_period)
        self.length = length
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
        
        bollinger = ta.volatility.BollingerBands(close=df['Close'], window=self.length, window_dev=self.std)
        lower_band = bollinger.bollinger_lband()
        upper_band = bollinger.bollinger_hband()
        
        signals = pd.Series(0, index=df.index)
        
        # Buy: Touch Lower
        signals.loc[df['Close'] < lower_band] = 1
        # Sell: Touch Upper
        signals.loc[df['Close'] > upper_band] = -1
        
        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "株価がボリンジャーバンドの下限にタッチしました。売られすぎからの反発が期待できます。"
        elif signal == -1:
            return "株価がボリンジャーバンドの上限にタッチしました。過熱感があり、反落の可能性があります。"
        return "バンド内での推移が続いています。"

class CombinedStrategy(Strategy):
    def __init__(self, rsi_period: int = 14, bb_length: int = 20, bb_std: float = 2, trend_period: int = 200) -> None:
        super().__init__("Combined (RSI + BB)", trend_period)
        self.rsi_period = rsi_period
        self.bb_length = bb_length
        self.bb_std = bb_std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Close' not in df.columns:
            return pd.Series(dtype=int)
            
        # RSI
        rsi = ta.momentum.RSIIndicator(close=df['Close'], window=self.rsi_period).rsi()
        
        # BB
        bb = ta.volatility.BollingerBands(close=df['Close'], window=self.bb_length, window_dev=self.bb_std)
        lower_band = bb.bollinger_lband()
        upper_band = bb.bollinger_hband()
        
        signals = pd.Series(0, index=df.index)
        
        # Buy: RSI < 30 AND Close < Lower Band
        signals.loc[(rsi < 30) & (df['Close'] < lower_band)] = 1
        
        # Sell: RSI > 70 AND Close > Upper Band
        signals.loc[(rsi > 70) & (df['Close'] > upper_band)] = -1
        
        return self.apply_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "RSIとボリンジャーバンドの両方が「売られすぎ」を示しています。強い反発のチャンスです。"
        elif signal == -1:
            return "RSIとボリンジャーバンドの両方が「買われすぎ」を示しています。強い反落の警戒が必要です。"
        return "複数の指標による強いシグナルは出ていません。"
