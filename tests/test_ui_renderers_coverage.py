import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import streamlit as st

# Import modules after streamlit mock is active (via tests/__init__.py)


class TestUIRenderers(unittest.TestCase):
    def setUp(self):
        self.mock_st = patch("src.ui_renderers.st").start()
        self.mock_plotly = patch("src.ui_renderers.go").start()
        self.mock_px = patch("src.ui_renderers.px").start()

        # Import here after mocks are set up
        from src.ui_renderers import (render_integrated_signal, render_market_scan_tab,
                                      render_paper_trading_tab, render_performance_tab,
                                      render_realtime_monitoring_tab)
        self.render_integrated_signal = render_integrated_signal
        self.render_market_scan_tab = render_market_scan_tab
        self.render_paper_trading_tab = render_paper_trading_tab
        self.render_performance_tab = render_performance_tab
        self.render_realtime_monitoring_tab = render_realtime_monitoring_tab

        # Setup common mock returns
        # Make st.columns dynamic to handle different lengths
        def columns_side_effect(spec):
            count = spec if isinstance(spec, int) else len(spec)
            return [MagicMock() for _ in range(count)]

        self.mock_st.columns.side_effect = columns_side_effect

        self.mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]
        self.mock_st.expander.return_value.__enter__.return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_render_performance_tab(self):
        """Test render_performance_tab"""
        # Mock PerformanceAnalyzer
        with patch("src.ui_renderers.PerformanceAnalyzer") as MockAnalyzer:
            analyzer = MockAnalyzer.return_value
            analyzer.calculate_metrics.return_value = {
                "total_return": 0.1,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.05,
                "win_rate": 0.6,
            }
            analyzer.calculate_monthly_returns.return_value = pd.Series([0.01, 0.02], index=["2023-01", "2023-02"])

            # Mock fetch_stock_data
            with patch("src.ui_renderers.pd.read_csv") as mock_read_csv:  # Assuming it reads from CSV or DB?
                # Actually render_performance_tab might fetch data.
                # Let's check the code. It takes ticker_group etc.
                # It probably instantiates PerformanceAnalyzer.

                self.render_performance_tab("All", "Japan", [], "JPY")

                # Verify st calls
                self.assertTrue(
                    self.mock_st.markdown.called or self.mock_st.header.called or self.mock_st.subheader.called
                )

    def test_render_paper_trading_tab(self):
        """Test render_paper_trading_tab"""
        # Mock PaperTrader
        with patch("src.paper_trader.PaperTrader") as MockTrader:
            # Prevent form submission which triggers fetch_stock_data with mock args
            self.mock_st.form_submit_button.return_value = False

            trader = MockTrader.return_value
            trader.initial_capital = 1000000.0  # Set initial capital to avoid TypeError
            trader.get_current_balance.return_value = {
                "cash": 1000000.0,
                "total_equity": 1000000.0,
                "invested_amount": 0.0,
                "unrealized_pnl": 0.0,
            }
            trader.get_positions.return_value = pd.DataFrame()
            trader.get_trade_history.return_value = pd.DataFrame()  # Add this line if needed

            self.render_paper_trading_tab()

            self.render_paper_trading_tab()

            # st.metric is called on columns, not st directly. So check header instead.
            self.assertTrue(self.mock_st.header.called)
            self.assertTrue(self.mock_st.columns.called)

    def test_render_market_scan_tab(self):
        """Test render_market_scan_tab"""
        # This function is complex and calls many other things.
        # We'll do a basic smoke test.

        # Patch Backtester because it is imported inside the function
        # Also patch os.path.exists to prevent reading leftover scan_results.json
        # Also patch SentimentAnalyzer as it is used for fresh runs
        with patch("src.backtester.Backtester") as MockBacktester, patch(
            "src.data_loader.fetch_stock_data"
        ) as mock_fetch, patch("os.path.exists", return_value=False), patch(
            "src.sentiment.SentimentAnalyzer"
        ) as MockSA, patch(
            "src.data_loader.fetch_external_data"
        ) as mock_macro, patch(
            "src.ui_components.display_sentiment_gauge"
        ) as mock_gauge:

            trader = MockBacktester.return_value
            trader.run.return_value = {
                "total_return": 0.1,
                "max_drawdown": -0.05,
                "signals": pd.Series([1] * 10, index=pd.date_range("2023-01-01", periods=10)),
            }  # Return dummy result

            mock_fetch.return_value = {"7203.T": pd.DataFrame({"Close": [100] * 10})}  # Dummy data

            # Mock macro data
            mock_macro.return_value = {
                "USD/JPY": pd.DataFrame({"Close": [140, 141]}),
                "VIX": pd.DataFrame({"Close": [20, 21]}),
            }

            # Mock SentimentAnalyzer behavior
            mock_sa_instance = MockSA.return_value
            mock_sa_instance.get_market_sentiment.return_value = {
                "score": 0.5,
                "label": "Neutral",
                "news_count": 5,
                "top_news": [],
            }
            mock_sa_instance.get_sentiment_history.return_value = []

            # Set st.radio return value to integer to avoid TypeError in timedelta
            self.mock_st.radio.return_value = 7

            self.render_market_scan_tab(
                "All", "Japan", [], "1y", [MagicMock(name="Strategy1")], True, 0.1, False, 50, 5, 10, 100
            )

            self.assertTrue(self.mock_st.button.called)

    def test_render_integrated_signal(self):
        """Test render_integrated_signal"""
        df = pd.DataFrame(
            {"Open": [100] * 10, "High": [110] * 10, "Low": [90] * 10, "Close": [105] * 10, "Volume": [1000] * 10},
            index=pd.date_range("2023-01-01", periods=10),
        )

        self.render_integrated_signal(df, "7203.T", ai_prediction=0.5)

        self.assertTrue(self.mock_st.plotly_chart.called)


if __name__ == "__main__":
    unittest.main()
