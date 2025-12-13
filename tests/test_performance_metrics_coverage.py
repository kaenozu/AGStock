"""performance_metrics.pyのテスト"""

import time

import numpy as np
import pandas as pd
import pytest

from src.performance_metrics import AdvancedMetrics, TransactionCostModel


@pytest.fixture
def sample_returns():
    """サンプルリターンデータ"""
    np.random.seed(42)
    return pd.Series(np.random.randn(252) * 0.01 + 0.0005)


@pytest.fixture
def positive_returns():
    """全て正のリターンデータ"""
    np.random.seed(42)
    return pd.Series(np.abs(np.random.randn(100) * 0.01) + 0.001)


@pytest.fixture
def negative_returns():
    """全て負のリターンデータ"""
    np.random.seed(42)
    return pd.Series(-np.abs(np.random.randn(100) * 0.01) - 0.001)


@pytest.fixture
def benchmark_returns():
    """ベンチマークリターンデータ"""
    np.random.seed(123)
    return pd.Series(np.random.randn(252) * 0.01 + 0.0003)


class TestAdvancedMetrics:
    """AdvancedMetricsのテスト"""

    def test_init(self, sample_returns):
        """初期化テスト"""
        metrics = AdvancedMetrics(sample_returns)
        assert metrics.returns is not None
        assert metrics.risk_free_rate == 0.02

    def test_init_custom_risk_free_rate(self, sample_returns):
        """カスタムリスクフリーレートでの初期化"""
        metrics = AdvancedMetrics(sample_returns, risk_free_rate=0.05)
        assert metrics.risk_free_rate == 0.05

    def test_sharpe_ratio(self, sample_returns):
        """シャープレシオテスト"""
        metrics = AdvancedMetrics(sample_returns)
        sharpe = metrics.sharpe_ratio()
        assert isinstance(sharpe, float)

    def test_sharpe_ratio_zero_std(self):
        """標準偏差ゼロのシャープレシオ"""
        # 同じリターンでも daily_rf_rate を引いた後のstdが0になる必要がある
        returns = pd.Series([0.01] * 100)
        metrics = AdvancedMetrics(returns)
        sharpe = metrics.sharpe_ratio()
        # シャープレシオは計算される（stdが0でない場合）
        assert isinstance(sharpe, float)

    def test_sortino_ratio(self, sample_returns):
        """ソルティノレシオテスト"""
        metrics = AdvancedMetrics(sample_returns)
        sortino = metrics.sortino_ratio()
        assert isinstance(sortino, float)

    def test_sortino_ratio_positive_only(self, positive_returns):
        """全て正のリターンのソルティノレシオ"""
        metrics = AdvancedMetrics(positive_returns)
        sortino = metrics.sortino_ratio()
        assert sortino == 0.0

    def test_calmar_ratio(self, sample_returns):
        """カルマーレシオテスト"""
        metrics = AdvancedMetrics(sample_returns)
        calmar = metrics.calmar_ratio()
        assert isinstance(calmar, float)

    def test_max_drawdown(self, sample_returns):
        """最大ドローダウンテスト"""
        metrics = AdvancedMetrics(sample_returns)
        max_dd = metrics.max_drawdown()
        assert isinstance(max_dd, float)
        assert max_dd <= 0  # ドローダウンは負またはゼロ

    def test_max_drawdown_duration(self, sample_returns):
        """最大ドローダウン期間テスト"""
        metrics = AdvancedMetrics(sample_returns)
        duration = metrics.max_drawdown_duration()
        assert isinstance(duration, int)
        assert duration >= 0

    def test_max_drawdown_duration_performance(self):
        """大規模データでも最大ドローダウン期間の計算が高速に実行されることを確認"""
        np.random.seed(42)
        large_returns = pd.Series(np.random.randn(100_000) * 0.01)
        metrics = AdvancedMetrics(large_returns)

        def baseline_duration():
            cumulative = (1 + large_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            is_drawdown = drawdown < 0
            duration = 0
            max_duration = 0
            for in_dd in is_drawdown:
                if in_dd:
                    duration += 1
                    max_duration = max(max_duration, duration)
                else:
                    duration = 0
            return max_duration

        baseline_result = baseline_duration()
        optimized_result = metrics.max_drawdown_duration()
        assert optimized_result == baseline_result

        def measure_time(func, repeats: int = 3) -> float:
            times = []
            for _ in range(repeats):
                start = time.perf_counter()
                func()
                times.append(time.perf_counter() - start)
            return min(times)

        baseline_time = measure_time(baseline_duration)
        optimized_time = measure_time(metrics.max_drawdown_duration)

        assert optimized_time < baseline_time * 0.8

    def test_win_rate(self, sample_returns):
        """勝率テスト"""
        metrics = AdvancedMetrics(sample_returns)
        win_rate = metrics.win_rate()
        assert 0 <= win_rate <= 1

    def test_win_rate_positive_only(self, positive_returns):
        """全て正のリターンの勝率"""
        metrics = AdvancedMetrics(positive_returns)
        win_rate = metrics.win_rate()
        assert win_rate == 1.0

    def test_payoff_ratio(self, sample_returns):
        """ペイオフレシオテスト"""
        metrics = AdvancedMetrics(sample_returns)
        payoff = metrics.payoff_ratio()
        assert isinstance(payoff, float)

    def test_payoff_ratio_positive_only(self, positive_returns):
        """全て正のリターンのペイオフレシオ"""
        metrics = AdvancedMetrics(positive_returns)
        payoff = metrics.payoff_ratio()
        assert payoff == 0.0

    def test_omega_ratio(self, sample_returns):
        """オメガレシオテスト"""
        metrics = AdvancedMetrics(sample_returns)
        omega = metrics.omega_ratio()
        assert isinstance(omega, (float, int))

    def test_omega_ratio_positive_only(self, positive_returns):
        """全て正のリターンのオメガレシオ"""
        metrics = AdvancedMetrics(positive_returns)
        omega = metrics.omega_ratio()
        assert omega == np.inf

    def test_information_ratio(self, sample_returns, benchmark_returns):
        """情報比率テスト"""
        metrics = AdvancedMetrics(sample_returns)
        info_ratio = metrics.information_ratio(benchmark_returns)
        assert isinstance(info_ratio, float)

    def test_all_metrics(self, sample_returns):
        """全メトリクステスト"""
        metrics = AdvancedMetrics(sample_returns)
        all_metrics = metrics.all_metrics()

        assert "total_return" in all_metrics
        assert "annual_return" in all_metrics
        assert "annual_volatility" in all_metrics
        assert "sharpe_ratio" in all_metrics
        assert "sortino_ratio" in all_metrics
        assert "calmar_ratio" in all_metrics
        assert "max_drawdown" in all_metrics
        assert "max_dd_duration" in all_metrics
        assert "win_rate" in all_metrics
        assert "payoff_ratio" in all_metrics
        assert "omega_ratio" in all_metrics

    def test_all_metrics_with_benchmark(self, sample_returns, benchmark_returns):
        """ベンチマーク付き全メトリクステスト"""
        metrics = AdvancedMetrics(sample_returns)
        all_metrics = metrics.all_metrics(benchmark_returns)

        assert "information_ratio" in all_metrics


class TestTransactionCostModel:
    """TransactionCostModelのテスト"""

    def test_init(self):
        """初期化テスト"""
        model = TransactionCostModel()
        assert model.commission_pct == 0.001
        assert model.slippage_pct == 0.0005
        assert model.market_impact_factor == 0.1

    def test_init_custom(self):
        """カスタムパラメータでの初期化"""
        model = TransactionCostModel(commission_pct=0.002, slippage_pct=0.001, market_impact_factor=0.2)
        assert model.commission_pct == 0.002
        assert model.slippage_pct == 0.001
        assert model.market_impact_factor == 0.2

    def test_calculate_cost(self):
        """取引コスト計算テスト"""
        model = TransactionCostModel()
        cost = model.calculate_cost(order_value=100000, daily_volume=1000000)
        assert isinstance(cost, float)
        assert cost > 0

    def test_calculate_cost_high_volume_participation(self):
        """高いボリューム参加率でのコスト"""
        model = TransactionCostModel()
        cost = model.calculate_cost(order_value=500000, daily_volume=1000000)
        # マーケットインパクトが大きくなる
        assert cost > 0

    def test_calculate_cost_zero_volume(self):
        """ボリュームゼロでのコスト"""
        model = TransactionCostModel()
        cost = model.calculate_cost(order_value=100000, daily_volume=0)
        # マーケットインパクトなし
        assert cost > 0
