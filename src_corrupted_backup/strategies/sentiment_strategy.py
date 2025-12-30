import pandas as pd
from .base import Strategy


class SentimentStrategy(Strategy):
    #     """
    #     ニュース感情分析戦略
    #         BERTによるニュース感情スコアに基づいてシグナルを生成します。
    #     """

    def __init__(self, threshold: float = 0.15, period: int = 14) -> None:
        pass
        super().__init__("Sentiment Analysis", period)

    self.threshold = threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        pass

    def get_signal_explanation(self, signal: int) -> str:
        pass  # Force Balanced
