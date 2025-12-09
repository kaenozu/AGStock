import pandas as pd
from .base import Strategy
from .technical import CombinedStrategy

# Try to import MultiTimeframeAnalyzer, handle if missing
try:
    from src.multi_timeframe import MultiTimeframeAnalyzer
except ImportError:
    MultiTimeframeAnalyzer = None

class MultiTimeframeStrategy(Strategy):
    """
    マルチタイムフレーム戦略
    
    週足トレンドをフィルターとして使用し、
    日足シグナルが長期トレンドと一致する場合のみエントリーします。
    """
    def __init__(self, base_strategy: Strategy = None, trend_period: int = 200) -> None:
        super().__init__("Multi-Timeframe", trend_period)
        self.base_strategy = base_strategy if base_strategy else CombinedStrategy()
        self.mtf_analyzer = MultiTimeframeAnalyzer() if MultiTimeframeAnalyzer else None
        
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if df is None or df.empty:
            return pd.Series(dtype=int)
            
        # ベース戦略のシグナル生成
        base_signals = self.base_strategy.generate_signals(df)
        
        if not self.mtf_analyzer:
            return base_signals
        
        try:
            # リサンプリング
            weekly_df = self.mtf_analyzer.resample_data(df, 'W-FRI')
            
            # 週足トレンド計算 (SMA20 > SMA50)
            weekly_df['SMA_20'] = weekly_df['Close'].rolling(window=20).mean()
            weekly_df['SMA_50'] = weekly_df['Close'].rolling(window=50).mean()
            
            weekly_df['Weekly_Trend'] = 0
            weekly_df.loc[(weekly_df['Close'] > weekly_df['SMA_20']) & (weekly_df['SMA_20'] > weekly_df['SMA_50']), 'Weekly_Trend'] = 1 # Uptrend
            weekly_df.loc[(weekly_df['Close'] < weekly_df['SMA_20']) & (weekly_df['SMA_20'] < weekly_df['SMA_50']), 'Weekly_Trend'] = -1 # Downtrend
            
            # 日足にマージ
            # reindex + ffill で直近の週足トレンドを適用
            weekly_trend_series = weekly_df['Weekly_Trend'].reindex(df.index, method='ffill').fillna(0)
            
            # フィルター適用
            final_signals = base_signals.copy()
            
            # 買いシグナル: 週足が上昇トレンド(1)の時のみ許可
            final_signals[(final_signals == 1) & (weekly_trend_series != 1)] = 0
            
            # 売りシグナル: 週足が下降トレンド(-1)の時のみ許可
            final_signals[(final_signals == -1) & (weekly_trend_series != -1)] = 0
            
            return final_signals
            
        except Exception as e:
            # エラー時はベース戦略のシグナルをそのまま返す（安全策）
            print(f"MTF Error: {e}")
            return base_signals
            
    def get_signal_explanation(self, signal: int) -> str:
        base_expl = self.base_strategy.get_signal_explanation(signal)
        if signal == 1:
            return f"{base_expl} さらに、週足が上昇トレンドを示しており、長期的な上昇が見込まれます。"
        elif signal == -1:
            return f"{base_expl} さらに、週足が下降トレンドを示しており、長期的な下落が見込まれます。"
        return base_expl
