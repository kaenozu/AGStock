"""
ポートフォリオ最適化のテスト（TDD）

現代ポートフォリオ理論に基づく最適化機能をテスト駆動開発で実装します。
"""

import pytest
import pandas as pd
import numpy as np


class TestPortfolioOptimizer:
    """PortfolioOptimizerクラスのテスト"""
    
    @pytest.fixture
    def sample_returns(self):
        """テスト用のリターンデータを生成"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=252, freq='D')  # 1年分
        
        # 3銘柄のリターン（相関あり）
        returns = pd.DataFrame({
            'AAPL': np.random.randn(252) * 0.02 + 0.0005,
            'GOOGL': np.random.randn(252) * 0.025 + 0.0006,
            'MSFT': np.random.randn(252) * 0.018 + 0.0004,
        }, index=dates)
        
        return returns
    
    @pytest.fixture
    def optimizer(self, sample_returns):
        """テスト用のOptimizerインスタンスを作成"""
        from src.portfolio_optimizer import PortfolioOptimizer
        
        return PortfolioOptimizer(sample_returns)
    
    def test_optimizer_initialization(self, optimizer, sample_returns):
        """Optimizerの初期化をテスト"""
        assert optimizer is not None
        assert optimizer.returns is not None
        assert len(optimizer.returns.columns) == 3
        assert list(optimizer.returns.columns) == ['AAPL', 'GOOGL', 'MSFT']
    
    def test_calculate_portfolio_metrics(self, optimizer):
        """ポートフォリオメトリクス計算をテスト"""
        weights = np.array([0.4, 0.3, 0.3])
        
        metrics = optimizer.calculate_portfolio_metrics(weights)
        
        # メトリクスが返ってくるか
        assert 'return' in metrics
        assert 'risk' in metrics
        assert 'sharpe' in metrics
        
        # 値が妥当な範囲か
        assert -1.0 < metrics['return'] < 1.0  # 年率リターン
        assert 0.0 < metrics['risk'] < 1.0      # 年率リスク
        assert -5.0 < metrics['sharpe'] < 10.0  # シャープレシオ
    
    def test_find_efficient_frontier(self, optimizer):
        """効率的フロンティアの計算をテスト"""
        frontier = optimizer.find_efficient_frontier(num_points=10)
        
        # フロンティアが返ってくるか
        assert isinstance(frontier, list)
        assert len(frontier) == 10
        
        # 各点が適切な情報を持つか
        for point in frontier:
            assert 'return' in point
            assert 'risk' in point
            assert 'weights' in point
            assert len(point['weights']) == 3
            assert np.abs(np.sum(point['weights']) - 1.0) < 1e-6  # ウェイト合計=1
    
    def test_maximize_sharpe_ratio(self, optimizer):
        """シャープレシオ最大化をテスト"""
        optimal_weights = optimizer.maximize_sharpe_ratio()
        
        # ウェイトが返ってくるか
        assert optimal_weights is not None
        assert len(optimal_weights) == 3
        
        # ウェイトの制約が守られているか
        assert np.all(optimal_weights >= 0)  # 非負制約
        assert np.abs(np.sum(optimal_weights) - 1.0) < 1e-6  # 合計=1
    
    def test_minimize_variance(self, optimizer):
        """最小分散ポートフォリオをテスト"""
        min_var_weights = optimizer.minimize_variance()
        
        assert min_var_weights is not None
        assert len(min_var_weights) == 3
        assert np.all(min_var_weights >= 0)
        assert np.abs(np.sum(min_var_weights) - 1.0) < 1e-6
    
    def test_risk_parity(self, optimizer):
        """リスクパリティポートフォリオをテスト"""
        rp_weights = optimizer.risk_parity()
        
        assert rp_weights is not None
        assert len(rp_weights) == 3
        assert np.all(rp_weights >= 0)
        assert np.abs(np.sum(rp_weights) - 1.0) < 1e-6
        
        # 各資産のリスク寄与度がほぼ等しいか
        metrics = optimizer.calculate_portfolio_metrics(rp_weights)
        # リスク寄与度の計算とチェック（簡易版）
        assert metrics['risk'] > 0


class TestDynamicRebalancer:
    """DynamicRebalancerクラスのテスト"""
    
    @pytest.fixture
    def sample_portfolio(self):
        """テスト用のポートフォリオデータ"""
        return {
            'AAPL': {'quantity': 100, 'current_price': 150.0},
            'GOOGL': {'quantity': 50, 'current_price': 140.0},
            'MSFT': {'quantity': 75, 'current_price': 350.0},
        }
    
    @pytest.fixture
    def target_weights(self):
        """目標ウェイト"""
        return {
            'AAPL': 0.4,
            'GOOGL': 0.3,
            'MSFT': 0.3
        }
    
    def test_rebalancer_initialization(self):
        """Rebalancerの初期化をテスト"""
        from src.rebalancer import DynamicRebalancer
        
        rebalancer = DynamicRebalancer(
            rebalance_threshold=0.05,  # 5%のズレでリバランス
            rebalance_frequency='monthly'
        )
        
        assert rebalancer is not None
        assert rebalancer.rebalance_threshold == 0.05
        assert rebalancer.rebalance_frequency == 'monthly'
    
    def test_calculate_current_weights(self, sample_portfolio):
        """現在のウェイト計算をテスト"""
        from src.rebalancer import DynamicRebalancer
        
        rebalancer = DynamicRebalancer()
        current_weights = rebalancer.calculate_current_weights(sample_portfolio)
        
        assert isinstance(current_weights, dict)
        assert len(current_weights) == 3
        assert np.abs(sum(current_weights.values()) - 1.0) < 1e-6
    
    def test_needs_rebalancing(self, sample_portfolio, target_weights):
        """リバランスが必要かどうかの判定をテスト"""
        from src.rebalancer import DynamicRebalancer
        
        rebalancer = DynamicRebalancer(rebalance_threshold=0.05)
        
        needs_rebal = rebalancer.needs_rebalancing(
            sample_portfolio,
            target_weights
        )
        
        assert isinstance(needs_rebal, bool)
    
    def test_generate_rebalance_orders(self, sample_portfolio, target_weights):
        """リバランス注文生成をテスト"""
        from src.rebalancer import DynamicRebalancer
        
        rebalancer = DynamicRebalancer()
        
        orders = rebalancer.generate_rebalance_orders(
            sample_portfolio,
            target_weights
        )
        
        assert isinstance(orders, list)
        
        # 各注文が適切な情報を持つか
        for order in orders:
            assert 'ticker' in order
            assert 'action' in order  # BUY or SELL
            assert 'quantity' in order
            assert order['action'] in ['BUY', 'SELL']
            assert order['quantity'] > 0


class TestBlackLitterman:
    """Black-Littermanモデルのテスト"""
    
    def test_black_litterman_basic(self):
        """Black-Littermanの基本機能をテスト"""
        # 実装後にテストを追加
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
