import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, Optional, Tuple
from ta.trend import ADXIndicator

class MarketRegime(Enum):
    BULL = "Bull (強気)"
    BEAR = "Bear (弱気)"
    SIDEWAYS = "Sideways (レンジ)"
    VOLATILE = "Volatile (高ボラティリティ)"
    UNCERTAIN = "Uncertain (不透明)"

class RegimeDetector:
    """
    Detects the current market regime based on technical indicators.
    Used to adjust trading strategies dynamically.
    """
    
    def __init__(self, window_short: int = 50, window_long: int = 200, adx_threshold: int = 20, vix_threshold: float = 25.0):
        self.window_short = window_short
        self.window_long = window_long
        self.adx_threshold = adx_threshold
        self.vix_threshold = vix_threshold

    def detect_regime(self, df: pd.DataFrame, vix_value: Optional[float] = None) -> MarketRegime:
        """
        Analyzes DataFrame to determine market regime.
        df requires: 'Close', 'High', 'Low'
        """
        if df is None or df.empty or len(df) < self.window_long:
            return MarketRegime.UNCERTAIN

        # 1. Check Volatility first (if VIX provided)
        if vix_value is not None and vix_value > self.vix_threshold:
            return MarketRegime.VOLATILE
            
        # 2. Calculate Indicators
        # Dataframe cleaning for yfinance (Series vs Dataframe issue)
        close = df['Close'].squeeze()
        high = df['High'].squeeze()
        low = df['Low'].squeeze()
        
        sma_short = close.rolling(window=self.window_short).mean()
        sma_long = close.rolling(window=self.window_long).mean()
        
        # ADX for Trend Strength
        adx_indicator = ADXIndicator(high, low, close, window=14)
        adx = adx_indicator.adx()
        
        current_price = close.iloc[-1]
        current_sma_short = sma_short.iloc[-1]
        current_sma_long = sma_long.iloc[-1]
        current_adx = adx.iloc[-1]
        
        # 3. Classification Logic
        
        # Sideways / Range: Weak Trend
        if current_adx < self.adx_threshold:
            return MarketRegime.SIDEWAYS
            
        # Bull Market: Golden Cross alignment
        if current_price > current_sma_short > current_sma_long:
            return MarketRegime.BULL
            
        # Bear Market: Death Cross alignment
        if current_price < current_sma_short < current_sma_long:
            return MarketRegime.BEAR
            
        # Pullback in Bull (Price < SMA50 but SMA50 > SMA200) -> Still Bullish but cautious, or Sideways?
        # For simplicity, let's treat mixed signals as Uncertain or Sideways
        if current_sma_short > current_sma_long:
            return MarketRegime.BULL # Broadly Bullish even if pullback
            
        if current_sma_short < current_sma_long:
            return MarketRegime.BEAR # Broadly Bearish
            
        return MarketRegime.UNCERTAIN

    def get_regime_signal(self, df: pd.DataFrame, vix_value: Optional[float] = None) -> Dict:
        """
        Returns rich details about the regime for UI display.
        """
        regime = self.detect_regime(df, vix_value)
        
        # Get indicators for display
        if len(df) >= self.window_long:
             # Squeeze for safety (ensure Series)
             close = df['Close'].squeeze()
             
             sma_short = close.rolling(window=self.window_short).mean().iloc[-1]
             sma_long = close.rolling(window=self.window_long).mean().iloc[-1]
             
             adx = ADXIndicator(
                 df['High'].squeeze(), 
                 df['Low'].squeeze(), 
                 close, 
                 window=14
             ).adx().iloc[-1]
        else:
             sma_short, sma_long, adx = 0, 0, 0
        
        return {
            "regime": regime,
            "regime_name": regime.value,
            "indicators": {
                "SMA_Short": sma_short,
                "SMA_Long": sma_long,
                "ADX": adx,
                "VIX": vix_value
            },
            "description": self._get_description(regime)
        }
        
    def _get_description(self, regime: MarketRegime) -> str:
        if regime == MarketRegime.BULL:
            return "上昇トレンド継続中。順張り戦略（押し目買い）が機能しやすい環境です。"
        elif regime == MarketRegime.BEAR:
            return "下落トレンド。慎重な取引、または空売り・現金化を推奨します。"
        elif regime == MarketRegime.SIDEWAYS:
            return "トレンドが弱く方向感がありません。レンジ取引（RSI逆張り）が有効です。"
        elif regime == MarketRegime.VOLATILE:
            return "市場の変動が激しすぎます。リスク管理を最優先し、ポジションを縮小してください。"
        else:
            return "方向性が定まりません。様子見を推奨します。"

    def get_regime_strategy(self, regime: MarketRegime) -> Dict:
        """
        Returns the base strategy parameters for the given regime.
        """
        if regime == MarketRegime.BULL:
            return {
                "stop_loss": 0.05,
                "take_profit": 0.15,
                "position_size": 1.0,
                "strategy": "Trend Following (Long Only)",
                "description": "強気相場: 積極的な買い、深めのストップロス"
            }
        elif regime == MarketRegime.BEAR:
            return {
                "stop_loss": 0.03,
                "take_profit": 0.08,
                "position_size": 0.5,
                "strategy": "Conservative / Short",
                "description": "弱気相場: 防御的運用、ポジション縮小"
            }
        elif regime == MarketRegime.SIDEWAYS:
            return {
                "stop_loss": 0.03,
                "take_profit": 0.05,
                "position_size": 0.8,
                "strategy": "Mean Reversion",
                "description": "レンジ相場: 短期売買、回転重視"
            }
        elif regime == MarketRegime.VOLATILE:
            return {
                "stop_loss": 0.08,
                "take_profit": 0.20,
                "position_size": 0.3, # Size down significantly
                "strategy": "Volatility Breakout / Cash",
                "description": "高ボラティリティ: リスク回避最優先、現金比率向上"
            }
        else: # UNCERTAIN
            return {
                "stop_loss": 0.02,
                "take_profit": 0.04,
                "position_size": 0.0, # Do not trade
                "strategy": "Wait in Cash",
                "description": "不透明: 取引停止推奨"
            }
