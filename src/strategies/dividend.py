import pandas as pd
from .base import Strategy

class DividendStrategy(Strategy):
    """
    高配当戦略
    
    配当利回りが一定以上の銘柄を買い推奨します。
    （簡易実装：配当データは本来yfinanceのinfo等から取得する必要がありますが、
    ここではデータフレームに 'Dividend_Yield' カラムがあると仮定します）
    """
    
    def __init__(self, min_yield: float = 0.04, trend_period: int = 200) -> None:
        super().__init__("Dividend Yield", trend_period)
        self.min_yield = min_yield
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty or 'Dividend_Yield' not in df.columns:
            return pd.Series(dtype=int)
            
        signals = pd.Series(0, index=df.index)
        
        # 配当利回りが基準以上なら買い
        signals[df['Dividend_Yield'] >= self.min_yield] = 1
        
        # 売却条件は特に設定せず（長期保有前提）、利回りが低下したら売るなどのロジックも追加可能
        signals[df['Dividend_Yield'] < (self.min_yield * 0.8)] = 0 # 利回りが大きく下がったら手仕舞い（例）
        
        return self.apply_trend_filter(df, signals)
        
    def get_signal_explanation(self, signal: int) -> str:
        if signal == 1:
            return f"配当利回りが基準({self.min_yield*100}%)を上回っています。"
        return "配当利回りは基準以下です。"
