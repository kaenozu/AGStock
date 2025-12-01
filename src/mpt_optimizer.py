"""
Modern Portfolio Theory (MPT) Optimizer - モダンポートフォリオ理論による最適化

効率的フロンティアを計算し、最適なポートフォリオ配分を提案
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import List, Dict, Tuple, Optional
import logging


class MPTOptimizer:
    """Modern Portfolio Theoryに基づくポートフォリオ最適化"""
    
    def __init__(self, risk_free_rate: float = 0.001):
        """
        Args:
            risk_free_rate: リスクフリーレート（年率）
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
    
    def calculate_portfolio_stats(self, weights: np.ndarray, 
                                  returns: pd.DataFrame) -> Tuple[float, float, float]:
        """
        ポートフォリオの統計値を計算
        
        Args:
            weights: 資産配分ウェイト
            returns: 各資産のリターン（DataFrame）
            
        Returns:
            (期待リターン, ボラティリティ, シャープレシオ)
        """
        # 期待リターン（年率）
        portfolio_return = np.sum(returns.mean() * weights) * 252
        
        # ポートフォリオの分散・標準偏差（年率）
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        
        # シャープレシオ
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std if portfolio_std > 0 else 0
        
        return portfolio_return, portfolio_std, sharpe_ratio
    
    def optimize_sharpe_ratio(self, returns: pd.DataFrame) -> Dict:
        """
        シャープレシオを最大化するポートフォリオを計算
        
        Args:
            returns: 各資産のリターン（DataFrame）
            
        Returns:
            最適ポートフォリオの情報
        """
        num_assets = len(returns.columns)
        
        # 目的関数（シャープレシオの負数を最小化）
        def neg_sharpe(weights):
            ret, std, sharpe = self.calculate_portfolio_stats(weights, returns)
            return -sharpe
        
        # 制約条件
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # ウェイトの合計=1
        )
        
        # 境界条件（各ウェイト0〜1）
        bounds = tuple((0, 1) for _ in range(num_assets))
        
        # 初期値（均等配分）
        init_weights = np.array([1/num_assets] * num_assets)
        
        # 最適化
        result = minimize(
            neg_sharpe,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if not result.success:
            self.logger.warning(f"Optimization failed: {result.message}")
        
        optimal_weights = result.x
        ret, std, sharpe = self.calculate_portfolio_stats(optimal_weights, returns)
        
        return {
            'weights': dict(zip(returns.columns, optimal_weights)),
            'expected_return': ret,
            'volatility': std,
            'sharpe_ratio': sharpe,
            'optimization_success': result.success
        }
    
    def optimize_min_volatility(self, returns: pd.DataFrame) -> Dict:
        """
        ボラティリティを最小化するポートフォリオを計算
        
        Args:
            returns: 各資産のリターン（DataFrame）
            
        Returns:
            最小分散ポートフォリオの情報
        """
        num_assets = len(returns.columns)
        
        # 目的関数（ボラティリティを最小化）
        def portfolio_volatility(weights):
            _, std, _ = self.calculate_portfolio_stats(weights, returns)
            return std
        
        # 制約条件
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        )
        
        # 境界条件
        bounds = tuple((0, 1) for _ in range(num_assets))
        
        # 初期値
        init_weights = np.array([1/num_assets] * num_assets)
        
        # 最適化
        result = minimize(
            portfolio_volatility,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        ret, std, sharpe = self.calculate_portfolio_stats(optimal_weights, returns)
        
        return {
            'weights': dict(zip(returns.columns, optimal_weights)),
            'expected_return': ret,
            'volatility': std,
            'sharpe_ratio': sharpe,
            'optimization_success': result.success
        }
    
    def generate_efficient_frontier(self, returns: pd.DataFrame, 
                                   num_portfolios: int = 100) -> pd.DataFrame:
        """
        効率的フロンティアを生成
        
        Args:
            returns: 各資産のリターン（DataFrame）
            num_portfolios: 生成するポートフォリオ数
            
        Returns:
            効率的フロンティアのデータフレーム
        """
        num_assets = len(returns.columns)
        
        # 最小・最大リターンを計算
        min_vol_portfolio = self.optimize_min_volatility(returns)
        max_sharpe_portfolio = self.optimize_sharpe_ratio(returns)
        
        min_return = min_vol_portfolio['expected_return']
        max_return = max_sharpe_portfolio['expected_return'] * 1.2  # 少し余裕を持たせる
        
        # リターンの範囲を設定
        target_returns = np.linspace(min_return, max_return, num_portfolios)
        
        efficient_portfolios = []
        
        for target_return in target_returns:
            # 目的関数（ボラティリティを最小化）
            def portfolio_volatility(weights):
                _, std, _ = self.calculate_portfolio_stats(weights, returns)
                return std
            
            # 制約条件（ウェイト合計=1、目標リターン達成）
            constraints = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x, tr=target_return: 
                 np.sum(returns.mean() * x) * 252 - tr}
            )
            
            # 境界条件
            bounds = tuple((0, 1) for _ in range(num_assets))
            
            # 初期値
            init_weights = np.array([1/num_assets] * num_assets)
            
            # 最適化
            result = minimize(
                portfolio_volatility,
                init_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                weights = result.x
                ret, std, sharpe = self.calculate_portfolio_stats(weights, returns)
                
                efficient_portfolios.append({
                    'return': ret,
                    'volatility': std,
                    'sharpe_ratio': sharpe
                })
        
        return pd.DataFrame(efficient_portfolios)
    
    def recommend_portfolio(self, returns: pd.DataFrame, 
                          risk_tolerance: str = "medium") -> Dict:
        """
        リスク許容度に基づいてポートフォリオを推奨
        
        Args:
            returns: 各資産のリターン（DataFrame）
            risk_tolerance: リスク許容度（"low", "medium", "high"）
            
        Returns:
            推奨ポートフォリオの情報
        """
        if risk_tolerance == "low":
            # 低リスク: 最小分散ポートフォリオ
            return self.optimize_min_volatility(returns)
        
        elif risk_tolerance == "high":
            # 高リスク: 最大シャープレシオポートフォリオ
            return self.optimize_sharpe_ratio(returns)
        
        else:  # medium
            # 中リスク: 中間的なポートフォリオ
            min_vol = self.optimize_min_volatility(returns)
            max_sharpe = self.optimize_sharpe_ratio(returns)
            
            # ウェイトの平均を取る
            weights = {}
            for ticker in returns.columns:
                weights[ticker] = (min_vol['weights'][ticker] + max_sharpe['weights'][ticker]) / 2
            
            # 正規化
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            
            # 統計値を再計算
            weights_array = np.array([weights[col] for col in returns.columns])
            ret, std, sharpe = self.calculate_portfolio_stats(weights_array, returns)
            
            return {
                'weights': weights,
                'expected_return': ret,
                'volatility': std,
                'sharpe_ratio': sharpe,
                'optimization_success': True
            }


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # ダミーデータ作成
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=252)
    
    returns_data = {
        '7203.T': np.random.randn(252) * 0.02,  # トヨタ
        '9984.T': np.random.randn(252) * 0.025,  # ソフトバンクG
        '6758.T': np.random.randn(252) * 0.03    # ソニー
    }
    
    returns = pd.DataFrame(returns_data, index=dates)
    
    # MPT最適化
    optimizer = MPTOptimizer()
    
    print("=== Modern Portfolio Theory 最適化 ===\n")
    
    # 最小分散ポートフォリオ
    min_vol = optimizer.optimize_min_volatility(returns)
    print("【最小分散ポートフォリオ】")
    print(f"期待リターン: {min_vol['expected_return']*100:.2f}%")
    print(f"ボラティリティ: {min_vol['volatility']*100:.2f}%")
    print(f"シャープレシオ: {min_vol['sharpe_ratio']:.2f}")
    print(f"ウェイト: {min_vol['weights']}\n")
    
    # 最大シャープレシオポートフォリオ
    max_sharpe = optimizer.optimize_sharpe_ratio(returns)
    print("【最大シャープレシオポートフォリオ】")
    print(f"期待リターン: {max_sharpe['expected_return']*100:.2f}%")
    print(f"ボラティリティ: {max_sharpe['volatility']*100:.2f}%")
    print(f"シャープレシオ: {max_sharpe['sharpe_ratio']:.2f}")
    print(f"ウェイト: {max_sharpe['weights']}\n")
    
    # リスク許容度別推奨
    for risk in ["low", "medium", "high"]:
        portfolio = optimizer.recommend_portfolio(returns, risk)
        print(f"【推奨ポートフォリオ: {risk}リスク】")
        print(f"期待リターン: {portfolio['expected_return']*100:.2f}%")
        print(f"シャープレシオ: {portfolio['sharpe_ratio']:.2f}")
        print()
