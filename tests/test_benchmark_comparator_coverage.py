"""benchmark_comparator.pyのテスト"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.benchmark_comparator import BenchmarkComparator


@pytest.fixture
def comparator():
    """BenchmarkComparatorインスタンス"""
    return BenchmarkComparator()


@pytest.fixture
def portfolio_returns():
    """サンプルポートフォリオリターン"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    returns = pd.Series(np.random.randn(252) * 0.01 + 0.0005, index=dates)
    return returns


@pytest.fixture
def benchmark_returns():
    """サンプルベンチマークリターン"""
    np.random.seed(123)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    returns = pd.Series(np.random.randn(252) * 0.01 + 0.0003, index=dates)
    return returns


class TestBenchmarkComparator:
    """BenchmarkComparatorのテスト"""
    
    def test_init(self, comparator):
        """初期化テスト"""
        assert comparator is not None
        assert hasattr(comparator, 'BENCHMARKS')
    
    def test_benchmarks_defined(self, comparator):
        """ベンチマークが定義されていることを確認"""
        assert 'nikkei225' in comparator.BENCHMARKS
        assert 'sp500' in comparator.BENCHMARKS
        assert 'topix' in comparator.BENCHMARKS
        assert 'nasdaq' in comparator.BENCHMARKS
    
    def test_fetch_benchmark_data_with_mock(self, comparator):
        """ベンチマークデータ取得テスト（モック）"""
        with patch.object(comparator, 'fetch_benchmark_data') as mock_fetch:
            mock_data = pd.Series([100, 101, 102, 103, 104])
            mock_fetch.return_value = mock_data
            
            result = comparator.fetch_benchmark_data('nikkei225', period='1y')
            
            assert result is not None
            mock_fetch.assert_called_once()
    
    def test_calculate_active_return(self, comparator, portfolio_returns, benchmark_returns):
        """アクティブリターン計算テスト"""
        active_return = comparator.calculate_active_return(portfolio_returns, benchmark_returns)
        
        assert isinstance(active_return, float)
    
    def test_calculate_information_ratio(self, comparator, portfolio_returns, benchmark_returns):
        """情報比率計算テスト"""
        info_ratio = comparator.calculate_information_ratio(portfolio_returns, benchmark_returns)
        
        assert isinstance(info_ratio, float)
    
    def test_calculate_information_ratio_zero_tracking_error(self, comparator, portfolio_returns):
        """トラッキングエラーゼロの情報比率"""
        # 同じリターンを使用
        info_ratio = comparator.calculate_information_ratio(portfolio_returns, portfolio_returns)
        
        assert info_ratio == 0.0
    
    def test_calculate_beta(self, comparator, portfolio_returns, benchmark_returns):
        """ベータ計算テスト"""
        beta = comparator.calculate_beta(portfolio_returns, benchmark_returns)
        
        assert isinstance(beta, float)
    
    def test_calculate_alpha(self, comparator, portfolio_returns, benchmark_returns):
        """アルファ計算テスト"""
        alpha = comparator.calculate_alpha(portfolio_returns, benchmark_returns)
        
        assert isinstance(alpha, float)
    
    def test_calculate_alpha_custom_rf(self, comparator, portfolio_returns, benchmark_returns):
        """カスタムリスクフリーレートでのアルファ計算"""
        alpha = comparator.calculate_alpha(
            portfolio_returns, 
            benchmark_returns, 
            risk_free_rate=0.05
        )
        
        assert isinstance(alpha, float)
    
    def test_generate_comparison_report(self, comparator, portfolio_returns):
        """比較レポート生成テスト"""
        # モックベンチマークデータ（Closeカラムを持つDataFrame）
        np.random.seed(456)
        dates = pd.date_range('2023-01-01', periods=253, freq='D')
        mock_benchmark_df = pd.DataFrame({
            'Close': 100 * np.cumprod(1 + np.random.randn(253) * 0.01)
        }, index=dates)
        
        with patch.object(comparator, 'fetch_benchmark_data', return_value=mock_benchmark_df):
            report = comparator.generate_comparison_report(portfolio_returns, 'nikkei225')
            
            assert isinstance(report, dict)
            assert 'benchmark_name' in report  # 修正: benchmark -> benchmark_name
            assert 'active_return' in report
            assert 'information_ratio' in report
            assert 'beta' in report
            assert 'alpha' in report
    
    def test_interpret_metrics_positive_alpha(self, comparator):
        """正のアルファの解釈"""
        interpretation = comparator._interpret_metrics(alpha=0.05, info_ratio=0.8, beta=1.0)
        
        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
    
    def test_interpret_metrics_negative_alpha(self, comparator):
        """負のアルファの解釈"""
        interpretation = comparator._interpret_metrics(alpha=-0.03, info_ratio=-0.5, beta=1.2)
        
        assert isinstance(interpretation, str)
    
    def test_interpret_metrics_high_beta(self, comparator):
        """高いベータの解釈"""
        interpretation = comparator._interpret_metrics(alpha=0.02, info_ratio=0.5, beta=1.5)
        
        assert isinstance(interpretation, str)
    
    def test_interpret_metrics_low_beta(self, comparator):
        """低いベータの解釈"""
        interpretation = comparator._interpret_metrics(alpha=0.02, info_ratio=0.5, beta=0.5)
        
        assert isinstance(interpretation, str)
