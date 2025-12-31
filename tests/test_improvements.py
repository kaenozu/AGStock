"""改善モジュールのテスト"""

import pytest
import time
from datetime import datetime


class TestMemoryCache:
    """MemoryCacheのテスト"""

    def test_basic_set_get(self):
        from src.improvements.memory_cache import MemoryCache
        
        cache = MemoryCache(max_size=100)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        cache.close()

    def test_ttl(self):
        from src.improvements.memory_cache import MemoryCache
        
        cache = MemoryCache(max_size=100)
        cache.set("key1", "value1", ex=1)
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None
        cache.close()

    def test_lru_eviction(self):
        from src.improvements.memory_cache import MemoryCache
        
        cache = MemoryCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # key1を追い出す
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
        cache.close()

    def test_nx_flag(self):
        from src.improvements.memory_cache import MemoryCache
        
        cache = MemoryCache(max_size=100)
        assert cache.set("key1", "value1", nx=True) is True
        assert cache.set("key1", "value2", nx=True) is False
        assert cache.get("key1") == "value1"
        cache.close()

    def test_incr(self):
        from src.improvements.memory_cache import MemoryCache
        
        cache = MemoryCache(max_size=100)
        assert cache.incr("counter") == 1
        assert cache.incr("counter") == 2
        assert cache.incr("counter", 5) == 7
        cache.close()

    def test_info(self):
        from src.improvements.memory_cache import MemoryCache
        
        cache = MemoryCache(max_size=100)
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2")  # miss
        
        info = cache.info()
        assert info["keys"] == 1
        assert info["hits"] == 1
        assert info["misses"] == 1
        cache.close()


class TestSettings:
    """AGStockSettingsのテスト"""

    def test_default_values(self):
        from src.improvements.settings import AGStockSettings
        
        settings = AGStockSettings()
        assert settings.max_daily_loss_pct == -5.0
        assert settings.max_position_size_pct == 10.0
        assert settings.trading_scenario == "neutral"

    def test_risk_limits_property(self):
        from src.improvements.settings import AGStockSettings
        
        settings = AGStockSettings()
        limits = settings.risk_limits
        assert "max_daily_loss" in limits
        assert "max_position" in limits


class TestEarningsCalendar:
    """EarningsCalendarのテスト"""

    def test_risk_level_calculation(self):
        from src.features.earnings_calendar import EarningsCalendar
        
        cal = EarningsCalendar()
        assert cal._calculate_risk_level(1) == "CRITICAL"
        assert cal._calculate_risk_level(3) == "HIGH"
        assert cal._calculate_risk_level(7) == "MEDIUM"
        assert cal._calculate_risk_level(14) == "LOW"


class TestTaxOptimizer:
    """TaxOptimizerのテスト"""

    def test_tax_calculation(self):
        from src.features.tax_optimizer import TaxOptimizer, JP_TAX_RATE
        
        optimizer = TaxOptimizer()
        result = optimizer.simulate_harvest(
            ticker="AAPL",
            quantity=100,
            current_price=150,
            cost_basis=100,
            realized_gains_ytd=100000,
        )
        
        assert "pnl" in result
        assert "tax_savings" in result
        assert result["pnl"] == 5000  # (150-100) * 100


class TestSectorRotation:
    """SectorRotationのテスト"""

    def test_cycle_description(self):
        from src.features.sector_rotation import SectorRotation, EconomicCycle
        
        sr = SectorRotation()
        desc = sr._get_cycle_description(EconomicCycle.EARLY_EXPANSION)
        assert "景気回復" in desc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
