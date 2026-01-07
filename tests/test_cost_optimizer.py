"""
CostOptimizerのテスト
"""

import pytest

from src.cost_optimizer import CostOptimizer


class TestCostOptimizer:
    """CostOptimizerのテストクラス"""

    @pytest.fixture
    def optimizer(self):
        """テスト用のCostOptimizerインスタンス"""
        return CostOptimizer(broker="sbi")

    def test_initialization(self, optimizer):
        """初期化テスト"""
        assert optimizer is not None
        assert optimizer.broker == "sbi"

    def test_calculate_fee_sbi(self):
        """SBI証券の手数料計算テスト"""
        optimizer = CostOptimizer(broker="sbi")

        # 5万円以下: 55円
        fee = optimizer.calculate_fee(50000)
        assert fee == 55

        # 10万円以下: 99円
        fee = optimizer.calculate_fee(100000)
        assert fee == 99

        # 20万円以下: 115円
        fee = optimizer.calculate_fee(150000)
        assert fee == 115

        # 50万円以下: 275円
        fee = optimizer.calculate_fee(500000)
        assert fee == 275

    def test_calculate_fee_rakuten(self):
        """楽天証券の手数料計算テスト"""
        optimizer = CostOptimizer(broker="rakuten")

        # 5万円以下: 55円
        fee = optimizer.calculate_fee(50000)
        assert fee == 55

        # 50万円以下: 275円
        fee = optimizer.calculate_fee(300000)
        assert fee == 275

    def test_calculate_break_even(self, optimizer):
        """損益分岐点計算テスト"""
        entry_price = 1000
        shares = 100

        result = optimizer.calculate_break_even(entry_price, shares)

        assert "break_even_price" in result
        assert "total_cost" in result

        # 損益分岐点 > 購入価格 (コスト分)
        assert result["break_even_price"] > entry_price

    def test_optimize_order_size(self, optimizer):
        """最適注文サイズ計算テスト"""
        signal = {"price": 1000}
        available_capital = 100000

        optimal = optimizer.optimize_order_size(signal, available_capital)

        assert "recommended_shares" in optimal
        assert "investment" in optimal

        # 投資額 <= 利用可能資金
        assert optimal["investment"] <= available_capital

    def test_compare_brokers(self, optimizer):
        """証券会社比較テスト"""
        amount = 100000

        comparison = optimizer.compare_brokers(amount)

        assert not comparison.empty
        assert "証券会社" in comparison.columns
        assert "手数料（円）" in comparison.columns

    def test_should_take_profit(self, optimizer):
        """利確判断テスト"""
        position = {"entry_price": 1000, "shares": 100, "investment": 100000}

        # 利益が大きい場合 -> 利確推奨
        should_sell, reason = optimizer.should_take_profit(position, 1100)
        assert should_sell is True

        # 利益が小さい場合 -> 継続保有
        should_sell, reason = optimizer.should_take_profit(position, 1001)
        assert should_sell is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
