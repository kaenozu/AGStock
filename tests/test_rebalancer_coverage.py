"""rebalancer.pyのテスト"""

from datetime import datetime, timedelta

import pytest

from src.rebalancer import DynamicRebalancer


@pytest.fixture
def rebalancer():
    """基本的なリバランサー"""
    return DynamicRebalancer()


@pytest.fixture
def sample_portfolio():
    """サンプルポートフォリオ"""
    return {
        "AAPL": {"quantity": 100, "current_price": 150.0},
        "GOOGL": {"quantity": 50, "current_price": 200.0},
        "MSFT": {"quantity": 75, "current_price": 100.0},
    }


@pytest.fixture
def target_weights():
    """目標ウェイト"""
    return {
        "AAPL": 0.40,
        "GOOGL": 0.35,
        "MSFT": 0.25,
    }


class TestDynamicRebalancer:
    """DynamicRebalancerのテスト"""

    def test_init_default(self):
        """デフォルト初期化テスト"""
        rebalancer = DynamicRebalancer()
        assert rebalancer.rebalance_threshold == 0.05
        assert rebalancer.rebalance_frequency == "monthly"
        assert rebalancer.transaction_cost_pct == 0.001

    def test_init_custom(self):
        """カスタムパラメータ初期化テスト"""
        rebalancer = DynamicRebalancer(
            rebalance_threshold=0.10, rebalance_frequency="weekly", transaction_cost_pct=0.002
        )
        assert rebalancer.rebalance_threshold == 0.10
        assert rebalancer.rebalance_frequency == "weekly"
        assert rebalancer.transaction_cost_pct == 0.002

    def test_calculate_current_weights(self, rebalancer, sample_portfolio):
        """現在ウェイト計算テスト"""
        weights = rebalancer.calculate_current_weights(sample_portfolio)

        # ウェイトの合計が1になることを確認
        assert abs(sum(weights.values()) - 1.0) < 0.01

        # 各銘柄のウェイトが存在することを確認
        assert "AAPL" in weights
        assert "GOOGL" in weights
        assert "MSFT" in weights

    def test_calculate_current_weights_empty(self, rebalancer):
        """空ポートフォリオのウェイト計算"""
        weights = rebalancer.calculate_current_weights({})
        assert weights == {}

    def test_needs_rebalancing_yes(self, rebalancer, sample_portfolio):
        """リバランス必要の判定"""
        # 大きくずれた目標ウェイト
        target_weights = {
            "AAPL": 0.10,
            "GOOGL": 0.80,
            "MSFT": 0.10,
        }

        result = rebalancer.needs_rebalancing(sample_portfolio, target_weights)
        assert result is True

    def test_needs_rebalancing_no(self, rebalancer, sample_portfolio):
        """リバランス不要の判定"""
        current_weights = rebalancer.calculate_current_weights(sample_portfolio)

        # 現在のウェイトに近い目標
        result = rebalancer.needs_rebalancing(sample_portfolio, current_weights)
        assert result is False

    def test_generate_rebalance_orders(self, rebalancer, sample_portfolio, target_weights):
        """リバランス注文生成テスト"""
        orders = rebalancer.generate_rebalance_orders(sample_portfolio, target_weights)

        assert isinstance(orders, list)
        for order in orders:
            assert "ticker" in order
            assert "action" in order  # 'buy' or 'sell'
            assert "quantity" in order

    def test_calculate_transaction_costs(self, rebalancer, sample_portfolio, target_weights):
        """取引コスト計算テスト"""
        orders = rebalancer.generate_rebalance_orders(sample_portfolio, target_weights)
        cost = rebalancer.calculate_transaction_costs(orders)

        assert isinstance(cost, float)
        assert cost >= 0

    def test_calculate_transaction_costs_empty(self, rebalancer):
        """空の注文リストのコスト計算"""
        cost = rebalancer.calculate_transaction_costs([])
        assert cost == 0.0

    def test_should_rebalance_by_time_daily(self):
        """日次リバランスタイミング判定"""
        rebalancer = DynamicRebalancer(rebalance_frequency="daily")

        # 初回は常にTrue
        result = rebalancer.should_rebalance_by_time(datetime.now())
        assert result is True

    def test_should_rebalance_by_time_weekly(self):
        """週次リバランスタイミング判定"""
        rebalancer = DynamicRebalancer(rebalance_frequency="weekly")

        result = rebalancer.should_rebalance_by_time(datetime.now())
        assert isinstance(result, bool)

    def test_should_rebalance_by_time_monthly(self):
        """月次リバランスタイミング判定"""
        rebalancer = DynamicRebalancer(rebalance_frequency="monthly")

        result = rebalancer.should_rebalance_by_time(datetime.now())
        assert isinstance(result, bool)

    def test_should_rebalance_by_time_quarterly(self):
        """四半期リバランスタイミング判定"""
        rebalancer = DynamicRebalancer(rebalance_frequency="quarterly")

        result = rebalancer.should_rebalance_by_time(datetime.now())
        assert isinstance(result, bool)
