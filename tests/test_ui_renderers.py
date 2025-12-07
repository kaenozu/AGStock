import pytest
import pandas as pd
from unittest.mock import patch
from src.ui_renderers import render_performance_tab

class TestUIRenderers:
    """UIレンダラーのテストクラス"""
    
    @pytest.fixture
    def mock_analyzer(self):
        """Mock PerformanceAnalyzer"""
        with patch('src.ui_renderers.PerformanceAnalyzer') as MockAnalyzer:
            analyzer = MockAnalyzer.return_value
            
            # Default: Empty data
            analyzer.get_cumulative_pnl.return_value = pd.DataFrame()
            analyzer.get_strategy_performance.return_value = pd.DataFrame()
            analyzer.get_ticker_performance.return_value = pd.DataFrame()
            analyzer.get_monthly_returns.return_value = pd.DataFrame()
            
            yield analyzer

    def test_render_performance_tab_empty(self, mock_analyzer):
        """データがない場合のレンダリングテスト"""
        with patch('streamlit.info') as mock_info:
            render_performance_tab("日経225", "Japan", [])
            
            # "取引履歴がありません" などのメッセージが表示されることを確認
            assert mock_info.call_count >= 1

    def test_render_performance_tab_with_data(self, mock_analyzer):
        """データがある場合のレンダリングテスト"""
        # Setup mock data
        mock_analyzer.get_cumulative_pnl.return_value = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=10),
            'cumulative_pnl': range(10)
        })
        mock_analyzer.compare_with_benchmark.return_value = {
            'portfolio': [{'date': '2025-01-01', 'portfolio_return': 0.1}],
            'benchmark': [{'date': '2025-01-01', 'benchmark_return': 0.05}]
        }
        mock_analyzer.get_strategy_performance.return_value = pd.DataFrame({
            'strategy': ['StratA'],
            'trades': [10],
            'win_rate': [0.6],
            'avg_profit': [0.02],
            'total_pnl': [0.1]
        })
        mock_analyzer.get_ticker_performance.return_value = pd.DataFrame({
            'ticker': ['7203'],
            'trades': [5],
            'avg_profit': [0.01],
            'total_pnl': [0.05]
        })
        mock_analyzer.get_monthly_returns.return_value = pd.DataFrame({
            'year': [2025],
            'month': [1],
            'monthly_return': [1000]
        })

        with patch('streamlit.plotly_chart') as mock_chart:
            with patch('streamlit.dataframe') as mock_df:
                render_performance_tab("日経225", "Japan", [])
                
                # チャートとデータフレームが表示されることを確認
                assert mock_chart.call_count >= 1
                assert mock_df.call_count >= 1

    def test_render_performance_tab_error_handling(self, mock_analyzer):
        """エラー発生時のハンドリングテスト"""
        mock_analyzer.get_cumulative_pnl.side_effect = Exception("Test Error")
        
        with patch('streamlit.error') as mock_error:
            render_performance_tab("日経225", "Japan", [])
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_with("パフォーマンス分析エラー: Test Error")

    def test_render_paper_trading_tab(self):
        """ペーパートレーディングタブのレンダリングテスト（スモークテスト）"""
        from src.ui_renderers import render_paper_trading_tab
        
        # Just verify the function exists and is callable
        assert callable(render_paper_trading_tab)

    def test_render_market_scan_tab(self):
        """市場スキャンタブのレンダリングテスト（スモークテスト）"""
        from src.ui_renderers import render_market_scan_tab
        
        # Just verify the function exists and is callable
        assert callable(render_market_scan_tab)
