import pandas as pd
import ta
from .base import TechnicalStrategy

class BollingerBandsStrategy(TechnicalStrategy):
    def __init__(self, length: int = 20, std: float = 1.5, trend_period: int = 200) -> None:
        super().__init__(f"Bollinger Bands ({length}, {std})", trend_period)
        self.length = length
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if not self._validate_dataframe(df):
            return pd.Series(dtype=int)

        bollinger = ta.volatility.BollingerBands(close=df["Close"], window=self.length, window_dev=self.std)
        lower_band = bollinger.bollinger_lband()
        upper_band = bollinger.bollinger_hband()

        signals = self._create_signals_series(df)

        # Buy: Touch Lower
        signals.loc[df["Close"] < lower_band] = 1
        # Sell: Touch Upper
        signals.loc[df["Close"] > upper_band] = -1

        return self._apply_standard_trend_filter(df, signals)

    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return "株価がボリンジャーバンドの下限にタッチしました。売られすぎからの反発が期待できます。"
        elif signal == -1:
            return "株価がボリンジャーバンドの上限にタッチしました。過熱感があり、反落の可能性があります。"
        return "バンド内での推移が続いています。"
