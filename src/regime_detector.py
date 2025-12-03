"""
市場レジーム検出モジュール

市場環境を自動分類し、レジーム別の最適な戦略を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketRegimeDetector:
    """
    市場レジーム検出器
    
    トレンドとボラティリティを分析し、現在の市場環境を分類します。
    """
    
    def __init__(self):
        self.regimes = {
            'trending_up': 'トレンド上昇',
            'trending_down': 'トレンド下降',
            'ranging': 'レンジ相場',
            'high_volatility': '高ボラティリティ',
            'low_volatility': '低ボラティリティ'
        }
        
        self.current_regime = None
        self.regime_history = []
        
        logger.info("MarketRegimeDetector initialized")
    
    def detect_regime(self, df: pd.DataFrame, lookback: int = 20) -> str:
        """
        現在の市場レジームを検出
        
        Args:
            df: 価格データ (OHLCV)
            lookback: 分析期間（日数）
            
        Returns:
            検出されたレジーム名
        """
        # トレンド検出
        trend = self._detect_trend(df, lookback)
        
        # ボラティリティ検出
        volatility = self._detect_volatility(df, lookback)
        
        # レジーム判定
        regime = self._classify_regime(trend, volatility)
        
        # 履歴に追加
        self.current_regime = regime
        self.regime_history.append({
            'timestamp': pd.Timestamp.now(),
            'regime': regime,
            'trend': trend,
            'volatility': volatility
        })
        
        logger.info(f"Detected regime: {regime} (trend={trend}, volatility={volatility})")
        
        return regime
    
    def _detect_trend(self, df: pd.DataFrame, lookback: int) -> str:
        """
        トレンド検出
        
        ADX指標を使用してトレンドの強さと方向を判定します。
        
        Args:
            df: 価格データ
            lookback: 分析期間
            
        Returns:
            'up', 'down', 'ranging'
        """
        try:
            from ta.trend import ADXIndicator
            
            # ADX計算
            adx_indicator = ADXIndicator(
                high=df['High'], 
                low=df['Low'], 
                close=df['Close'], 
                window=lookback
            )
            
            adx_value = adx_indicator.adx().iloc[-1]
            adx_pos = adx_indicator.adx_pos().iloc[-1]
            adx_neg = adx_indicator.adx_neg().iloc[-1]
            
            # トレンド判定
            if adx_value > 25:  # 強いトレンド
                if adx_pos > adx_neg:
                    return 'up'
                else:
                    return 'down'
            else:  # 弱いトレンド = レンジ
                return 'ranging'
                
        except Exception as e:
            logger.warning(f"Error in trend detection: {e}. Using fallback method.")
            return self._detect_trend_fallback(df, lookback)
    
    def _detect_trend_fallback(self, df: pd.DataFrame, lookback: int) -> str:
        """
        トレンド検出のフォールバック（移動平均ベース）
        
        Args:
            df: 価格データ
            lookback: 分析期間
            
        Returns:
            'up', 'down', 'ranging'
        """
        # 短期・長期移動平均
        short_ma = df['Close'].rolling(window=lookback//2).mean().iloc[-1]
        long_ma = df['Close'].rolling(window=lookback).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        # トレンド判定
        if short_ma > long_ma and current_price > short_ma:
            return 'up'
        elif short_ma < long_ma and current_price < short_ma:
            return 'down'
        else:
            return 'ranging'
    
    def _detect_volatility(self, df: pd.DataFrame, lookback: int) -> str:
        """
        ボラティリティ検出
        
        ATR指標を使用してボラティリティレベルを判定します。
        
        Args:
            df: 価格データ
            lookback: 分析期間
            
        Returns:
            'high', 'normal', 'low'
        """
        try:
            from ta.volatility import AverageTrueRange
            
            # ATR計算
            atr_indicator = AverageTrueRange(
                high=df['High'], 
                low=df['Low'], 
                close=df['Close'], 
                window=lookback
            )
            
            atr_value = atr_indicator.average_true_range().iloc[-1]
            
            # 過去のATRと比較
            atr_history = atr_indicator.average_true_range().iloc[-lookback*2:-lookback]
            atr_mean = atr_history.mean()
            atr_std = atr_history.std()
            
            # ボラティリティ判定
            if atr_value > atr_mean + atr_std:
                return 'high'
            elif atr_value < atr_mean - atr_std:
                return 'low'
            else:
                return 'normal'
                
        except Exception as e:
            logger.warning(f"Error in volatility detection: {e}. Using fallback method.")
            return self._detect_volatility_fallback(df, lookback)
    
    def _detect_volatility_fallback(self, df: pd.DataFrame, lookback: int) -> str:
        """
        ボラティリティ検出のフォールバック（標準偏差ベース）
        
        Args:
            df: 価格データ
            lookback: 分析期間
            
        Returns:
            'high', 'normal', 'low'
        """
        # リターンの標準偏差
        returns = df['Close'].pct_change()
        current_vol = returns.iloc[-lookback:].std()
        historical_vol = returns.iloc[-lookback*2:-lookback].std()
        
        # ボラティリティ判定
        if current_vol > historical_vol * 1.5:
            return 'high'
        elif current_vol < historical_vol * 0.7:
            return 'low'
        else:
            return 'normal'
    
    def _classify_regime(self, trend: str, volatility: str) -> str:
        """
        トレンドとボラティリティからレジームを分類
        
        Args:
            trend: トレンド ('up', 'down', 'ranging')
            volatility: ボラティリティ ('high', 'normal', 'low')
            
        Returns:
            レジーム名
        """
        # ボラティリティが極端な場合は優先
        if volatility == 'high':
            return 'high_volatility'
        elif volatility == 'low':
            return 'low_volatility'
        
        # トレンドベースの分類
        if trend == 'up':
            return 'trending_up'
        elif trend == 'down':
            return 'trending_down'
        else:
            return 'ranging'
    
    def get_regime_strategy(self, regime: str = None) -> Dict[str, Any]:
        """
        レジームに応じた戦略パラメータを返す
        
        Args:
            regime: レジーム名（Noneの場合は現在のレジーム）
            
        Returns:
            戦略パラメータの辞書
        """
        if regime is None:
            regime = self.current_regime
        
        if regime is None:
            logger.warning("No regime detected yet. Using default parameters.")
            regime = 'ranging'
        
        strategies = {
            'trending_up': {
                'stop_loss': 0.03,  # 緩めの損切り
                'take_profit': 0.15,  # 大きな利確
                'position_size': 1.2,  # 大きめのポジション
                'strategy': 'trend_following',
                'description': 'トレンドフォロー戦略（上昇）'
            },
            'trending_down': {
                'stop_loss': 0.02,  # 厳しめの損切り
                'take_profit': 0.08,
                'position_size': 0.5,  # 小さめのポジション
                'strategy': 'counter_trend',
                'description': 'カウンタートレンド戦略（下降）'
            },
            'ranging': {
                'stop_loss': 0.02,
                'take_profit': 0.05,  # 小さめの利確
                'position_size': 0.8,
                'strategy': 'mean_reversion',
                'description': '平均回帰戦略（レンジ）'
            },
            'high_volatility': {
                'stop_loss': 0.05,  # 広めの損切り
                'take_profit': 0.20,
                'position_size': 0.6,  # リスク抑制
                'strategy': 'volatility_breakout',
                'description': 'ボラティリティブレイクアウト戦略'
            },
            'low_volatility': {
                'stop_loss': 0.015,
                'take_profit': 0.04,
                'position_size': 1.0,
                'strategy': 'range_trading',
                'description': 'レンジトレーディング戦略'
            }
        }
        
        return strategies.get(regime, strategies['ranging'])
    
    def get_regime_history(self, n: int = 10) -> list:
        """
        レジーム履歴を取得
        
        Args:
            n: 取得する履歴数
            
        Returns:
            レジーム履歴のリスト
        """
        return self.regime_history[-n:]
    
    def get_regime_statistics(self) -> Dict[str, Any]:
        """
        レジーム統計を取得
        
        Returns:
            レジーム統計の辞書
        """
        if not self.regime_history:
            return {'message': 'No regime history available'}
        
        # レジームの出現頻度
        regime_counts = {}
        for record in self.regime_history:
            regime = record['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        total = len(self.regime_history)
        regime_percentages = {
            regime: (count / total) * 100 
            for regime, count in regime_counts.items()
        }
        
        return {
            'current_regime': self.current_regime,
            'total_observations': total,
            'regime_counts': regime_counts,
            'regime_percentages': regime_percentages,
            'most_common_regime': max(regime_counts, key=regime_counts.get)
        }


# 使用例
if __name__ == "__main__":
    # サンプルデータ
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # レジーム検出
    detector = MarketRegimeDetector()
    regime = detector.detect_regime(df)
    
    print(f"Detected regime: {regime}")
    print(f"Regime description: {detector.regimes[regime]}")
    
    # 戦略パラメータ
    strategy = detector.get_regime_strategy()
    print(f"Strategy parameters: {strategy}")
    
    # 統計
    stats = detector.get_regime_statistics()
    print(f"Regime statistics: {stats}")
