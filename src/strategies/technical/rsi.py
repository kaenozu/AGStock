import pandas as pd
import ta
from .base import TechnicalStrategy

class RSIStrategy(TechnicalStrategy):
    def __init__(
        self,
        period: int = 14,
        lower: float = 10,
        upper: float = 90,
        trend_period: int = 200,
    ) -> None:
        super().__init__(f"RSI ({period}) Reversal", trend_period)
        self.period = period
        self.lower = lower
        self.upper = upper

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if not self._validate_dataframe(df):
            return pd.Series(dtype=int)

        rsi_indicator = ta.momentum.RSIIndicator(close=df["Close"], window=self.period)
        rsi = rsi_indicator.rsi()
        signals = self._create_signals_series(df)

        if rsi is None or rsi.isna().all():
            return signals

        prev_rsi = rsi.shift(1)

        # Buy: Cross above lower
        signals.loc[(prev_rsi < self.lower) & (rsi >= self.lower)] = 1
        # Sell: Cross below upper
        signals.loc[(prev_rsi > self.upper) & (rsi <= self.upper)] = -1

        return self._apply_standard_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return f"RSIが{self.lower}を下回った後、回復しました。売られすぎからの反発を示唆しています。"
        elif signal == -1:
            return f"RSIが{self.upper}を上回った後、下落しました。買われすぎからの反落を示唆しています。"
        return "RSIは中立圏内で推移しています。"
