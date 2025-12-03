"""
戦略基底クラスと共通ユーティリティ

全ての戦略クラスが継承する基底クラスと、
共通で使用されるデータクラス・列挙型を定義します。
"""
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """注文タイプ"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


@dataclass
class Order:
    """注文データクラス"""
    ticker: str
    type: OrderType
    action: str  # 'BUY' or 'SELL'
    quantity: float
    price: Optional[float] = None  # Limit or Stop price
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pct: Optional[float] = None  # For trailing stop logic
    expiry: str = "GTC"  # Good Till Cancelled or DAY


class Strategy:
    """
    戦略基底クラス
    
    全ての戦略はこのクラスを継承して実装します。
    """
    
    def __init__(self, name: str, trend_period: int = 200) -> None:
        """
        Args:
            name: 戦略名
            trend_period: トレンドフィルタ用の期間（0で無効化）
        """
        self.name = name
        self.trend_period = trend_period

    def apply_trend_filter(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        トレンドフィルタを適用
        
        Args:
            df: 価格データ
            signals: 生成されたシグナル
            
        Returns:
            フィルタ適用後のシグナル
        """
        if self.trend_period <= 0:
            return signals
        
        trend_sma = df['Close'].rolling(window=self.trend_period).mean()
        
        filtered_signals = signals.copy()
        
        # Filter Longs: Can only Buy if Close > SMA(200)
        long_condition = df['Close'] > trend_sma
        filtered_signals.loc[(signals == 1) & (~long_condition)] = 0
        
        # Filter Shorts: Can only Short if Close < SMA(200)
        short_condition = df['Close'] < trend_sma
        filtered_signals.loc[(signals == -1) & (~short_condition)] = 0
        
        return filtered_signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        シグナルを生成（サブクラスで実装）
        
        Args:
            df: OHLCV データ
            
        Returns:
            シグナルシリーズ (1: BUY, -1: SELL, 0: HOLD)
        """
        raise NotImplementedError

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        データを分析してシグナルと信頼度を返す
        
        Args:
            df: OHLCV データ
            
        Returns:
            {'signal': int, 'confidence': float}
        """
        signals = self.generate_signals(df)
        if signals.empty:
            return {'signal': 0, 'confidence': 0.0}
            
        # Get the latest signal (for the last available date)
        last_signal = signals.iloc[-1]
        
        return {
            'signal': int(last_signal),
            'confidence': 1.0 if last_signal != 0 else 0.0
        }

    def get_signal_explanation(self, signal: int) -> str:
        """
        シグナルの説明を取得
        
        Args:
            signal: シグナル値
            
        Returns:
            説明文
        """
        if signal == 1:
            return "買いシグナル"
        elif signal == -1:
            return "売りシグナル"
        return "様子見"
