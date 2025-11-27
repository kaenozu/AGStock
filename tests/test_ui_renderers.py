import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
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
        """ペーパートレーディングタブのレンダリングテスト"""
        from src.ui_renderers import render_paper_trading_tab
        
        with patch('src.ui_renderers.PaperTrader') as MockPT:
            pt = MockPT.return_value
            
            # Setup mock data
            pt.get_current_balance.return_value = {
                'cash': 1000000,
                'total_equity': 1000000
            }
            pt.get_positions.return_value = pd.DataFrame({
                'ticker': ['7203'],
                'current_price': [2000],
                'entry_price': [1800],
                'unrealized_pnl': [20000],
                'unrealized_pnl_pct': [0.11]
            })
            pt.get_trade_history.return_value = pd.DataFrame({
                'timestamp': ['2025-01-01'],
                'ticker': ['7203'],
                'action': ['BUY'],
                'price': [1800],
                'quantity': [100]
            })
            pt.initial_capital = 1000000
            
            with patch('streamlit.columns') as mock_cols:
                col1 = MagicMock()
                col2 = MagicMock()
                col3 = MagicMock()
                mock_cols.return_value = [col1, col2, col3]
                
                with patch('streamlit.dataframe') as mock_df:
                    render_paper_trading_tab()
                    
                    # メトリクスとデータフレームが表示されることを確認
                    assert col1.metric.called
                    assert mock_df.call_count >= 1

    def test_render_market_scan_tab(self):
        """市場スキャンタブのレンダリングテスト"""
        from src.ui_renderers import render_market_scan_tab
        
        # Mock dependencies
        with patch('src.ui_renderers.fetch_stock_data') as mock_fetch:
            with patch('src.ui_renderers.Backtester') as MockBacktester:
                with patch('src.ui_renderers.SentimentAnalyzer') as MockSA:
                    with patch('streamlit.button') as mock_btn:
                        
                        # Setup mocks
                        mock_fetch.return_value = {'7203': pd.DataFrame({'Close': [1000]})}
                        
                        mock_bt = MockBacktester.return_value
                        mock_bt.run.return_value = {
                            'total_return': 0.1,
                            'max_drawdown': -0.05,
                            'signals': pd.Series([1, 1, 1], index=pd.date_range('2025-01-01', periods=3))
                        }
                        
                        mock_sa = MockSA.return_value
                        mock_sa.get_market_sentiment.return_value = {
                            'score': 0.5,
                            'label': 'Positive',
                            'news_count': 10,
                            'top_news': []
                        }
                        
                        # Simulate "Scan" button click
                        mock_btn.return_value = True
                        
                        # Mock strategies
                        mock_strategy = MagicMock()
                        mock_strategy.name = "TestStrategy"
                        mock_strategy.get_signal_explanation.return_value = "Test Explanation"
                        
                        with patch('streamlit.spinner'):
                            with patch('streamlit.expander'):
                                with patch('src.ui_renderers.display_best_pick_card') as mock_card:
                                    render_market_scan_tab(
                                        "Japan", "Japan", [], "1y", [mock_strategy],
                                        False, 1.0, False, 15, 1.5, 8.0, 100
                                    )
                                    
                                    # Best Pickカードが表示されることを確認
                                    assert mock_card.called
