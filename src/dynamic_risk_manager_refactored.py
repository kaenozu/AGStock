"""
Refactored Dynamic Risk Manager

Improved version with dependency injection, better separation of concerns, and testability.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseRiskManager, RiskMetrics, TradeSignal
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RiskParameters:
    """リスクパラメータ"""
    base_stop_loss_pct: float = 0.02
    base_take_profit_pct: float = 0.04
    max_position_size_pct: float = 0.10
    volatility_adjustment_factor: float = 1.0
    regime: str = "normal"
    last_updated: datetime = field(default_factory=datetime.now)


class DynamicRiskManager(BaseRiskManager):
    """
    動的リスク管理マネージャー（リファクタリング版）
    
    責務:
    - 市場状況に応じたリスクパラメータの動的調整
    - ポジションサイズの計算
    - 損切り・利確価格の計算
    """
    
    def __init__(
        self, 
        max_risk: float = 0.02,
        regime_detector: Optional[Any] = None
    ):
        super().__init__(max_risk)
        self.regime_detector = regime_detector
        self.parameters = RiskParameters()
        self.parameter_history: List[RiskParameters] = []
    
    def update_parameters(
        self, 
        df: pd.DataFrame, 
        lookback: int = 20
    ) -> RiskParameters:
        """
        市場状況に基づいてパラメータを更新
        
        Args:
            df: 価格データ
            lookback: 分析期間
            
        Returns:
            更新されたパラメータ
        """
        if df is None or df.empty:
            self.logger.warning("Empty dataframe provided")
            return self.parameters
        
        try:
            # ボラティリティ調整
            vol_adj = self._calculate_volatility_adjustment(df, lookback)
            
            # レジーム検出
            regime = self._detect_regime(df) if self.regime_detector else "normal"
            
            # パラメータ更新
            self.parameters = RiskParameters(
                base_stop_loss_pct=self._adjust_stop_loss(vol_adj, regime),
                base_take_profit_pct=self._adjust_take_profit(vol_adj, regime),
                max_position_size_pct=self._adjust_position_size(vol_adj, regime),
                volatility_adjustment_factor=vol_adj,
                regime=regime,
                last_updated=datetime.now()
            )
            
            # 履歴に追加
            self.parameter_history.append(self.parameters)
            if len(self.parameter_history) > 100:
                self.parameter_history = self.parameter_history[-100:]
            
            self.logger.info(f"Parameters updated: regime={regime}, vol_adj={vol_adj:.2f}")
            
            return self.parameters
            
        except Exception as e:
            self.logger.error(f"Error updating parameters: {e}")
            return self.parameters
    
    def _calculate_volatility_adjustment(
        self, 
        df: pd.DataFrame, 
        lookback: int = 20
    ) -> float:
        """
        ボラティリティ調整係数を計算
        
        Returns:
            調整係数（0.5~2.0）
        """
        if 'Close' not in df.columns:
            return 1.0
        
        try:
            # リターンの標準偏差
            returns = df['Close'].pct_change().dropna()
            current_vol = returns.tail(lookback).std()
            historical_vol = returns.std()
            
            if historical_vol == 0:
                return 1.0
            
            # 相対ボラティリティ
            rel_vol = current_vol / historical_vol
            
            # 0.5~2.0の範囲にクリップ
            adjustment = np.clip(rel_vol, 0.5, 2.0)
            
            return adjustment
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility adjustment: {e}")
            return 1.0
    
    def _detect_regime(self, df: pd.DataFrame) -> str:
        """レジーム検出"""
        if self.regime_detector:
            try:
                return self.regime_detector.detect(df)
            except Exception as e:
                self.logger.error(f"Error detecting regime: {e}")
        
        return "normal"
    
    def _adjust_stop_loss(self, vol_adj: float, regime: str) -> float:
        """損切り幅を調整"""
        base = 0.02
        
        # ボラティリティに応じて調整
        adjusted = base * vol_adj
        
        # レジームに応じて調整
        if regime == "high_volatility":
            adjusted *= 1.5
        elif regime == "low_volatility":
            adjusted *= 0.7
        
        return np.clip(adjusted, 0.01, 0.10)
    
    def _adjust_take_profit(self, vol_adj: float, regime: str) -> float:
        """利確幅を調整"""
        base = 0.04
        
        # ボラティリティに応じて調整
        adjusted = base * vol_adj
        
        # レジームに応じて調整
        if regime == "trending":
            adjusted *= 1.5
        elif regime == "ranging":
            adjusted *= 0.8
        
        return np.clip(adjusted, 0.02, 0.20)
    
    def _adjust_position_size(self, vol_adj: float, regime: str) -> float:
        """ポジションサイズを調整"""
        base = 0.10
        
        # ボラティリティが高いほど小さく
        adjusted = base / vol_adj
        
        # レジームに応じて調整
        if regime == "high_volatility":
            adjusted *= 0.5
        elif regime == "crisis":
            adjusted *= 0.3
        
        return np.clip(adjusted, 0.02, 0.20)
    
    def calculate_position_size(
        self, 
        account_balance: float, 
        signal: TradeSignal
    ) -> float:
        """
        ポジションサイズを計算
        
        Args:
            account_balance: 口座残高
            signal: 取引シグナル
            
        Returns:
            ポジションサイズ（金額）
        """
        if not self.validate_signal(signal):
            return 0.0
        
        # 基本ポジションサイズ
        base_size = account_balance * self.parameters.max_position_size_pct
        
        # 信頼度で調整
        confidence_adj = signal.confidence
        
        # 最終サイズ
        position_size = base_size * confidence_adj
        
        self.logger.debug(
            f"Position size: {position_size:.2f} "
            f"(balance={account_balance}, confidence={confidence_adj:.2f})"
        )
        
        return position_size
    
    def calculate_stop_loss(
        self, 
        entry_price: float, 
        direction: str = 'long'
    ) -> float:
        """
        損切り価格を計算
        
        Args:
            entry_price: エントリー価格
            direction: 'long' or 'short'
            
        Returns:
            損切り価格
        """
        stop_pct = self.parameters.base_stop_loss_pct
        
        if direction == 'long':
            return entry_price * (1 - stop_pct)
        else:
            return entry_price * (1 + stop_pct)
    
    def calculate_take_profit(
        self, 
        entry_price: float, 
        direction: str = 'long'
    ) -> float:
        """
        利確価格を計算
        
        Args:
            entry_price: エントリー価格
            direction: 'long' or 'short'
            
        Returns:
            利確価格
        """
        profit_pct = self.parameters.base_take_profit_pct
        
        if direction == 'long':
            return entry_price * (1 + profit_pct)
        else:
            return entry_price * (1 - profit_pct)
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        現在のリスク指標を取得
        
        Returns:
            リスク指標
        """
        return RiskMetrics(
            volatility=self.parameters.volatility_adjustment_factor,
            max_drawdown=0.0,  # TODO: 実装
            sharpe_ratio=0.0,  # TODO: 実装
            var_95=0.0,  # TODO: 実装
            beta=1.0,  # TODO: 実装
            timestamp=datetime.now()
        )
    
    def should_enter_trade(
        self, 
        signal_strength: float = 0.7, 
        min_strength: float = 0.6
    ) -> bool:
        """
        トレードに入るべきか判断
        
        Args:
            signal_strength: シグナルの強さ
            min_strength: 最小必要強度
            
        Returns:
            トレードに入るべき場合True
        """
        # レジームチェック
        if self.parameters.regime == "crisis":
            min_strength = 0.8  # 危機時は高い閾値
        
        return signal_strength >= min_strength


if __name__ == "__main__":
    # テスト
    risk_manager = DynamicRiskManager(max_risk=0.02)
    
    # サンプルデータ
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'Close': np.random.randn(100).cumsum() + 100
    }, index=dates)
    
    # パラメータ更新
    params = risk_manager.update_parameters(df)
    print(f"Parameters: {params}")
    
    # シグナル作成
    signal = TradeSignal(
        ticker="7203.T",
        action="BUY",
        quantity=100,
        price=1500.0,
        confidence=0.8,
        timestamp=datetime.now(),
        reason="Test signal"
    )
    
    # ポジションサイズ計算
    position_size = risk_manager.calculate_position_size(1000000, signal)
    print(f"Position size: ¥{position_size:,.0f}")
    
    # 損切り・利確
    entry_price = 1500.0
    stop_loss = risk_manager.calculate_stop_loss(entry_price)
    take_profit = risk_manager.calculate_take_profit(entry_price)
    print(f"Entry: {entry_price}, Stop: {stop_loss:.2f}, Target: {take_profit:.2f}")
