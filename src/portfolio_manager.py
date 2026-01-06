"""
Unified Portfolio Manager

Handles portfolio-level risk management, risk parity weighting, correlation analysis,
and sector diversification.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .base import BaseManager
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PortfolioConstraints:
    """ポートフォリオ制約"""
    max_correlation: float = 0.7
    max_sector_exposure: float = 0.4
    max_position_size: float = 0.2
    min_diversification: int = 5
    target_risk: float = 0.02


class PortfolioManager(BaseManager):
    """
    統合ポートフォリオ管理クラス

    責務:
    - リスクパリティに基づいたウェイト計算
    - 相関リスク管理とチェック
    - セクター分散管理
    - リバランス提案
    """

    def __init__(self, constraints: Optional[PortfolioConstraints] = None, **kwargs):
        if constraints is None:
            # マッピング: kwargs -> PortfolioConstraints
            c_args = {}
            for field in PortfolioConstraints.__dataclass_fields__:
                if field in kwargs:
                    c_args[field] = kwargs.pop(field)
            self.constraints = PortfolioConstraints(**c_args)
        else:
            self.constraints = constraints
        
        self.positions: Dict[str, float] = {}
        self.sector_map: Dict[str, str] = {}
        self.cash_balance = 1000000.0 # Add missing attribute
        super().__init__()

    @property
    def max_correlation(self) -> float:
        return self.constraints.max_correlation

    @property
    def max_sector_exposure(self) -> float:
        return self.constraints.max_sector_exposure

    def total_value(self) -> float:
        """ポートフォリオの総価値（簡易計算）"""
        return self.cash_balance + sum(self.positions.values())

    def add_position(self, ticker: str, quantity: int, price: float):
        """ポジションを追加（テスト用）"""
        self.positions[ticker] = quantity * price

    def get_positions(self) -> Dict[str, float]:
        """現在のポジション一覧を取得"""
        return self.positions

    def _initialize(self):
        """初期化"""
        self.logger.info(f"Initialized with constraints: {self.constraints}")

    def set_sector_map(self, sector_map: Dict[str, str]) -> None:
        """セクターマップ設定"""
        if not sector_map:
            raise ValueError("Sector map cannot be empty")
        self.sector_map = sector_map
        self.logger.info(f"Sector map updated: {len(sector_map)} tickers")

    def calculate_risk_parity_weights(
        self, tickers: List[str], price_history: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        リスクパリティ（各資産のリスク寄与度を均等化）に基づいたウェイトを計算
        """
        vols = {}
        for ticker in tickers:
            df = price_history.get(ticker)
            if df is not None and len(df) > 20:
                # 年率ボラティリティ
                returns = df["Close"].pct_change().dropna()
                vol = returns.std() * np.sqrt(252)
                vols[ticker] = max(vol, 0.01)
            else:
                vols[ticker] = 0.3  # デフォルト 30%

        # ボラティリティの逆数でウェイト付け
        inv_vols = {t: 1.0 / v for t, v in vols.items()}
        total_inv_vol = sum(inv_vols.values())

        if total_inv_vol == 0:
            return {t: 1.0 / len(tickers) for t in tickers}

        weights = {t: v / total_inv_vol for t, v in inv_vols.items()}
        return weights

    def analyze_correlations(self, price_history: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """相関行列を計算"""
        returns_dict = {}
        for ticker, df in price_history.items():
            if df is not None and not df.empty:
                returns_dict[ticker] = df["Close"].pct_change()

        if not returns_dict:
            return pd.DataFrame()

        returns_df = pd.DataFrame(returns_dict).dropna()
        return returns_df.corr()

    def check_new_position(
        self,
        ticker: str,
        current_portfolio: List[str],
        correlation_matrix: Optional[pd.DataFrame] = None,
    ) -> bool:
        """新規ポジション追加の可否をチェック"""
        if not current_portfolio:
            return True

        # 1. 相関チェック
        if correlation_matrix is not None and not correlation_matrix.empty:
            if ticker in correlation_matrix.index:
                try:
                    correlations = correlation_matrix.loc[ticker, current_portfolio]
                    high_corr = correlations[correlations > self.constraints.max_correlation]
                    if not high_corr.empty:
                        return False
                except KeyError as e:
                    self.logger.warning(f"Correlation check failed: {e}")

        # 2. セクターチェック
        if self.sector_map and ticker in self.sector_map:
            sector = self.sector_map[ticker]
            sector_count = sum(1 for t in current_portfolio if self.sector_map.get(t) == sector)
            sector_exposure = sector_count / len(current_portfolio)

            if sector_exposure >= self.constraints.max_sector_exposure:
                return False

        return True

    def calculate_portfolio_volatility(self, weights: Dict[str, float], cov_matrix: pd.DataFrame) -> float:
        """ポートフォリオボラティリティを計算"""
        if not weights or cov_matrix is None or cov_matrix.empty:
            return 0.0

        try:
            tickers = list(weights.keys())
            w = np.array([weights[t] for t in tickers])
            valid_tickers = [t for t in tickers if t in cov_matrix.index]
            
            if len(valid_tickers) != len(tickers):
                return 0.0

            sub_cov = cov_matrix.loc[valid_tickers, valid_tickers]
            port_var = np.dot(w.T, np.dot(sub_cov, w))
            
            return np.sqrt(port_var) if port_var > 0 else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating portfolio volatility: {e}")
            return 0.0

    def suggest_rebalancing(
        self, current_weights: Dict[str, float], target_weights: Dict[str, float]
    ) -> List[Dict[str, any]]:
        """リバランス提案を生成"""
        actions = []
        all_tickers = set(current_weights.keys()) | set(target_weights.keys())

        for ticker in all_tickers:
            current = current_weights.get(ticker, 0.0)
            target = target_weights.get(ticker, 0.0)
            diff = target - current

            if abs(diff) > 0.01:
                actions.append({
                    "ticker": ticker,
                    "action": "BUY" if diff > 0 else "SELL",
                    "current_weight": current,
                    "target_weight": target,
                    "adjustment": abs(diff),
                })

        actions.sort(key=lambda x: x["adjustment"], reverse=True)
        return actions