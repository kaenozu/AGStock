"""
Refactored Portfolio Manager

Improved version with better error handling, dependency injection, and testability.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

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


class PortfolioManager(BaseManager):
    """
    ポートフォリオ管理クラス（リファクタリング版）
    
    責務:
    - 相関リスク管理
    - セクター分散管理
    - ポジションサイズ管理
    """
    
    def __init__(self, constraints: Optional[PortfolioConstraints] = None):
        self.constraints = constraints or PortfolioConstraints()
        self.positions: Dict[str, float] = {}
        self.sector_map: Dict[str, str] = {}
        super().__init__()
    
    def _initialize(self):
        """初期化"""
        self.logger.info(f"Initialized with constraints: {self.constraints}")
    
    def set_sector_map(self, sector_map: Dict[str, str]) -> None:
        """セクターマップ設定"""
        if not sector_map:
            raise ValueError("Sector map cannot be empty")
        
        self.sector_map = sector_map
        self.logger.info(f"Sector map updated: {len(sector_map)} tickers")
    
    def check_new_position(
        self, 
        ticker: str, 
        current_portfolio: List[str], 
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> tuple[bool, str]:
        """
        新規ポジション追加の可否をチェック
        
        Args:
            ticker: 追加する銘柄
            current_portfolio: 現在のポートフォリオ
            correlation_matrix: 相関行列
            
        Returns:
            (可否, 理由)
        """
        # 空のポートフォリオは常にOK
        if not current_portfolio:
            return True, "Empty portfolio"
        
        # 相関チェック
        if correlation_matrix is not None and not correlation_matrix.empty:
            if ticker in correlation_matrix.index:
                try:
                    correlations = correlation_matrix.loc[ticker, current_portfolio]
                    high_corr = correlations[correlations > self.constraints.max_correlation]
                    
                    if not high_corr.empty:
                        reason = f"High correlation with {high_corr.index.tolist()}"
                        self.logger.warning(f"Rejecting {ticker}: {reason}")
                        return False, reason
                        
                except KeyError as e:
                    self.logger.warning(f"Correlation check failed: {e}")
        
        # セクターチェック
        if self.sector_map and ticker in self.sector_map:
            sector = self.sector_map[ticker]
            sector_exposure = self._calculate_sector_exposure(
                sector, 
                current_portfolio
            )
            
            if sector_exposure >= self.constraints.max_sector_exposure:
                reason = f"Sector limit reached for {sector} ({sector_exposure:.1%})"
                self.logger.warning(f"Rejecting {ticker}: {reason}")
                return False, reason
        
        return True, "All checks passed"
    
    def _calculate_sector_exposure(
        self, 
        sector: str, 
        portfolio: List[str]
    ) -> float:
        """セクター露出度を計算"""
        if not portfolio:
            return 0.0
        
        sector_count = sum(
            1 for t in portfolio 
            if self.sector_map.get(t) == sector
        )
        
        return sector_count / len(portfolio)
    
    def calculate_portfolio_volatility(
        self, 
        weights: Dict[str, float], 
        cov_matrix: pd.DataFrame
    ) -> float:
        """
        ポートフォリオボラティリティを計算
        
        Args:
            weights: 銘柄ウェイト
            cov_matrix: 共分散行列
            
        Returns:
            ポートフォリオボラティリティ
        """
        if not weights or cov_matrix is None or cov_matrix.empty:
            return 0.0
        
        try:
            tickers = list(weights.keys())
            w = np.array([weights[t] for t in tickers])
            
            # 共分散行列に全銘柄が含まれているか確認
            valid_tickers = [t for t in tickers if t in cov_matrix.index]
            if len(valid_tickers) != len(tickers):
                missing = set(tickers) - set(valid_tickers)
                self.logger.warning(f"Missing tickers in cov_matrix: {missing}")
                return 0.0
            
            sub_cov = cov_matrix.loc[valid_tickers, valid_tickers]
            
            # ポートフォリオ分散
            port_var = np.dot(w.T, np.dot(sub_cov, w))
            
            # 負の分散チェック（数値誤差対策）
            if port_var < 0:
                self.logger.warning(f"Negative variance detected: {port_var}")
                return 0.0
            
            return np.sqrt(port_var)
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio volatility: {e}")
            return 0.0
    
    def get_diversification_score(self, portfolio: List[str]) -> float:
        """
        分散度スコアを計算（0-1）
        
        Args:
            portfolio: ポートフォリオ銘柄リスト
            
        Returns:
            分散度スコア
        """
        if not portfolio:
            return 0.0
        
        # 銘柄数による分散
        size_score = min(len(portfolio) / 20, 1.0)
        
        # セクター分散
        if self.sector_map:
            sectors = [self.sector_map.get(t) for t in portfolio if t in self.sector_map]
            unique_sectors = len(set(sectors))
            sector_score = min(unique_sectors / 10, 1.0)
        else:
            sector_score = 0.5
        
        # 総合スコア
        return (size_score + sector_score) / 2
    
    def suggest_rebalancing(
        self, 
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> List[Dict[str, any]]:
        """
        リバランス提案を生成
        
        Args:
            current_weights: 現在のウェイト
            target_weights: 目標ウェイト
            
        Returns:
            リバランスアクションのリスト
        """
        actions = []
        
        all_tickers = set(current_weights.keys()) | set(target_weights.keys())
        
        for ticker in all_tickers:
            current = current_weights.get(ticker, 0.0)
            target = target_weights.get(ticker, 0.0)
            diff = target - current
            
            if abs(diff) > 0.01:  # 1%以上の差がある場合
                action = {
                    'ticker': ticker,
                    'action': 'BUY' if diff > 0 else 'SELL',
                    'current_weight': current,
                    'target_weight': target,
                    'adjustment': abs(diff)
                }
                actions.append(action)
        
        # 調整量の大きい順にソート
        actions.sort(key=lambda x: x['adjustment'], reverse=True)
        
        return actions


if __name__ == "__main__":
    # テスト
    constraints = PortfolioConstraints(
        max_correlation=0.7,
        max_sector_exposure=0.3
    )
    
    manager = PortfolioManager(constraints)
    
    # セクターマップ設定
    sector_map = {
        "7203.T": "Auto",
        "6758.T": "Electronics",
        "9984.T": "Telecom",
        "8306.T": "Finance"
    }
    manager.set_sector_map(sector_map)
    
    # 分散度スコア
    portfolio = ["7203.T", "6758.T", "9984.T"]
    score = manager.get_diversification_score(portfolio)
    print(f"Diversification score: {score:.2f}")
    
    # リバランス提案
    current = {"7203.T": 0.4, "6758.T": 0.3, "9984.T": 0.3}
    target = {"7203.T": 0.33, "6758.T": 0.33, "9984.T": 0.34}
    actions = manager.suggest_rebalancing(current, target)
    
    print("\nRebalancing suggestions:")
    for action in actions:
        print(f"  {action['ticker']}: {action['action']} {action['adjustment']:.2%}")
