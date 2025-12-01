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
    
    def test_calculate_commission_sbi(self):
        """SBI証券の手数料計算テスト"""
        optimizer = CostOptimizer(broker="sbi")
        
        # 10万円以下: 99円
        commission = optimizer.calculate_commission(50000)
        assert commission == 99
        
        # 20万円以下: 115円
        commission = optimizer.calculate_commission(150000)
        assert commission == 115
        
        # 100万円以下: 535円
        commission = optimizer.calculate_commission(500000)
        assert commission == 535
    
    def test_calculate_commission_rakuten(self):
        """楽天証券の手数料計算テスト"""
        optimizer = CostOptimizer(broker="rakuten")
        
        # 10万円以下: 99円
        commission = optimizer.calculate_commission(50000)
        assert commission == 99
        
        # 50万円以下: 275円
        commission = optimizer.calculate_commission(300000)
        assert commission == 275
    
    def test_breakeven_price_buy(self, optimizer):
        """買いポジションの損益分岐点計算テスト"""
        entry_price = 1000
        quantity = 100
        
        breakeven = optimizer.calculate_breakeven_price(
            entry_price, quantity, "BUY"
        )
        
        # 損益分岐点 = 購入価格 + 手数料
        assert breakeven > entry_price
    
    def test_breakeven_price_sell(self, optimizer):
        """売りポジションの損益分岐点計算テスト"""
        entry_price = 1000
        quantity = 100
        
        breakeven = optimizer.calculate_breakeven_price(
            entry_price, quantity, "SELL"
        )
        
        # 損益分岐点 = 売却価格 - 手数料
        assert breakeven < entry_price
    
    def test_optimal_order_size(self, optimizer):
        """最適注文サイズ計算テスト"""
        price = 1000
        available_capital = 100000
        
        optimal_size = optimizer.calculate_optimal_order_size(
            price, available_capital
        )
        
        # 手数料を考慮した最適サイズが返される
        assert optimal_size > 0
        assert optimal_size * price <= available_capital
    
    def test_compare_brokers(self):
        """証券会社比較テスト"""
        order_amount = 100000
        
        comparison = CostOptimizer.compare_brokers(order_amount)
        
        assert len(comparison) > 0
        assert all("broker" in c for c in comparison)
        assert all("commission" in c for c in comparison)
        
        # 手数料順にソートされているか確認
        commissions = [c["commission"] for c in comparison]
        assert commissions == sorted(commissions)
    
    def test_recommend_broker(self):
        """推奨証券会社テスト"""
        order_amount = 100000
        
        recommended = CostOptimizer.recommend_broker(order_amount)
        
        assert recommended is not None
        assert "broker" in recommended
        assert "commission" in recommended
    
    def test_calculate_total_cost(self, optimizer):
        """総コスト計算テスト"""
        entry_price = 1000
        quantity = 100
        
        total_cost = optimizer.calculate_total_cost(entry_price, quantity)
        
        # 総コスト = 購入額 + 往復手数料
        expected_cost = entry_price * quantity + optimizer.calculate_commission(entry_price * quantity) * 2
        assert total_cost == expected_cost


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
