"""
リスク管理システムの包括的テスト
リスク計算、ポジション管理、アラート機能をテスト
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# テスト対象モジュール
from src.advanced_risk import AdvancedRiskManager
from src.dynamic_risk_manager import DynamicRiskManager
from src.risk_guard import RiskGuard
from src.advanced_risk import DrawdownProtection


class TestRiskManagement:
    """リスク管理システムのテストスイート"""

    @pytest.fixture
    def mock_config(self):
        """モック設定"""
        return {
            "risk_management": {
                "max_daily_loss_pct": 0.02,
                "max_position_size": 0.1,
                "stop_loss_pct": 0.05,
                "var_confidence": 0.95,
                "max_correlation": 0.7,
            },
            "portfolio": {"initial_balance": 1000000, "max_drawdown": 0.15},
        }

    @pytest.fixture
    def risk_manager(self, mock_config):
        """リスク管理インスタンス"""
        return AdvancedRiskManager(mock_config)

    @pytest.fixture
    def sample_portfolio(self):
        """サンプルポートフォリオ"""
        return {
            "AAPL": {
                "quantity": 100,
                "entry_price": 150.0,
                "current_price": 155.0,
                "market_value": 15500,
                "weight": 0.0155,
            },
            "GOOGL": {
                "quantity": 10,
                "entry_price": 2500.0,
                "current_price": 2600.0,
                "market_value": 26000,
                "weight": 0.0260,
            },
            "MSFT": {
                "quantity": 50,
                "entry_price": 300.0,
                "current_price": 290.0,
                "market_value": 14500,
                "weight": 0.0145,
            },
        }

    @pytest.fixture
    def price_history(self):
        """価格履歴データ"""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        np.random.seed(42)

        return pd.DataFrame(
            {
                "AAPL": 150 * (1 + np.random.randn(100) * 0.02),
                "GOOGL": 2500 * (1 + np.random.randn(100) * 0.02),
                "MSFT": 300 * (1 + np.random.randn(100) * 0.02),
            },
            index=dates,
        )

    def test_risk_manager_initialization(self, risk_manager, mock_config):
        """リスク管理の初期化テスト"""
        assert risk_manager.max_daily_loss_pct == 0.02
        assert risk_manager.max_position_size == 0.1
        assert risk_manager.stop_loss_pct == 0.05
        assert risk_manager.var_confidence == 0.95

    def test_position_risk_calculation(self, risk_manager, sample_portfolio):
        """ポジションリスク計算のテスト"""
        for ticker, position in sample_portfolio.items():
            position_risk = risk_manager.calculate_position_risk(position)

            assert isinstance(position_risk, dict)
            assert "unrealized_pnl" in position_risk
            assert "pnl_pct" in position_risk
            assert "risk_amount" in position_risk
            assert "stop_loss_price" in position_risk

    def test_portfolio_risk_metrics(self, risk_manager, sample_portfolio):
        """ポートフォリオリスク指標の計算テスト"""
        portfolio_risk = risk_manager.calculate_portfolio_risk(sample_portfolio)

        assert isinstance(portfolio_risk, dict)
        assert "total_value" in portfolio_risk
        assert "total_pnl" in portfolio_risk
        assert "portfolio_beta" in portfolio_risk
        assert "var_95" in portfolio_risk
        assert "risk_score" in portfolio_risk

    def test_value_at_risk_calculation(self, risk_manager, price_history):
        """VaR計算のテスト"""
        returns = price_history.pct_change().dropna()

        # VaR計算
        var_95 = risk_manager.calculate_var(returns, confidence=0.95)
        var_99 = risk_manager.calculate_var(returns, confidence=0.99)

        assert isinstance(var_95, float)
        assert isinstance(var_99, float)
        assert var_99 < var_95  # 99% VaRは95% VaRより小さい（より悪い）
        assert var_95 < 0  # VaRは負の値

    def test_maximum_drawdown_calculation(self, risk_manager, price_history):
        """最大ドローダウン計算のテスト"""
        for ticker in price_history.columns:
            prices = price_history[ticker]
            mdd = risk_manager.calculate_max_drawdown(prices)

            assert isinstance(mdd, float)
            assert 0 >= mdd >= -1  # ドローダウンは0から-100%の範囲

    def test_correlation_analysis(self, risk_manager, price_history):
        """相関分析のテスト"""
        returns = price_history.pct_change().dropna()
        correlation_matrix = risk_manager.calculate_correlation(returns)

        assert isinstance(correlation_matrix, pd.DataFrame)
        assert correlation_matrix.shape == (3, 3)

        # 対角要素は1
        for i in range(3):
            assert abs(correlation_matrix.iloc[i, i] - 1.0) < 1e-6

    def test_stop_loss_trigger(self, risk_manager, sample_portfolio):
        """損切りトリガーのテスト"""
        # 損失ポジション
        losing_position = {
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 140.0,  # 6.67%損失
            "stop_loss_pct": 0.05,
        }

        should_stop = risk_manager.should_trigger_stop_loss(losing_position)
        assert should_stop is True

        # 利益ポジション
        winning_position = {
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 155.0,  # 3.33%利益
            "stop_loss_pct": 0.05,
        }

        should_stop = risk_manager.should_trigger_stop_loss(winning_position)
        assert should_stop is False

    def test_position_sizing_limits(self, risk_manager):
        """ポジションサイジング制限のテスト"""
        portfolio_value = 1000000
        risk_per_trade = 20000  # 2%

        # 最大ポジションサイズのチェック
        max_position = risk_manager.calculate_max_position_size(portfolio_value)
        assert max_position == portfolio_value * risk_manager.max_position_size
        assert max_position == 100000

    def test_risk_alert_generation(self, risk_manager, sample_portfolio):
        """リスクアラート生成のテスト"""
        # 高リスク状態のシミュレーション
        risk_metrics = risk_manager.calculate_portfolio_risk(sample_portfolio)
        risk_metrics["risk_score"] = 0.8  # 高リスク

        alerts = risk_manager.generate_risk_alerts(risk_metrics)

        assert isinstance(alerts, list)
        if alerts:  # アラートがある場合
            assert all(isinstance(alert, dict) for alert in alerts)
            assert all("type" in alert for alert in alerts)
            assert all("message" in alert for alert in alerts)

    def test_dynamic_risk_adjustment(self, mock_config):
        """動的リスク調整のテスト"""
        dynamic_risk = DynamicRiskManager(mock_config)

        # 市場ボラティリティに応じたリスク調整
        low_vol = 0.1
        high_vol = 0.3

        low_vol_risk = dynamic_risk.adjust_risk_for_volatility(low_vol)
        high_vol_risk = dynamic_risk.adjust_risk_for_volatility(high_vol)

        assert high_vol_risk < low_vol_risk  # 高ボラティリティではリスクを減らす

    def test_risk_guard_validation(self, mock_config):
        """リスクガードによる検証テスト"""
        risk_guard = RiskGuard(mock_config)

        # 取引前のリスクチェック
        trade_request = {
            "ticker": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "portfolio_value": 1000000,
        }

        is_valid, reason = risk_guard.validate_trade(trade_request)

        assert isinstance(is_valid, bool)
        assert isinstance(reason, str)

    def test_drawdown_protection(self, mock_config):
        """ドローダウン保護のテスト"""
        protection = DrawdownProtection(mock_config)

        # ドローダウン計算
        peak_value = 1000000
        current_value = 900000  # 10%ドローダウン

        is_critical, dd_pct = protection.check_drawdown(peak_value, current_value)

        assert isinstance(is_critical, bool)
        assert isinstance(dd_pct, float)
        assert dd_pct == -0.1

    def test_portfolio_rebalancing_signal(self, risk_manager, sample_portfolio):
        """ポートフォリオリバランスシグナルのテスト"""
        # 重みが不均衡なポートフォリオ
        unbalanced_portfolio = sample_portfolio.copy()
        unbalanced_portfolio["AAPL"]["weight"] = 0.5  # 50%集中

        rebalance_signal = risk_manager.should_rebalance(unbalanced_portfolio)

        assert isinstance(rebalance_signal, bool)

    def test_stress_testing(self, risk_manager, price_history, sample_portfolio):
        """ストレステストのテスト"""
        # 市場ショックのシミュレーション
        stress_scenarios = {
            "market_crash": -0.2,
            "sector_crisis": -0.15,
            "volatility_spike": 0.05,
        }

        stress_results = risk_manager.run_stress_test(
            sample_portfolio, price_history, stress_scenarios
        )

        assert isinstance(stress_results, dict)
        for scenario in stress_scenarios:
            assert scenario in stress_results
            assert "portfolio_impact" in stress_results[scenario]

    def test_risk_metrics_history(self, risk_manager):
        """リスク指標履歴のテスト"""
        # リスク指標の記録
        risk_metrics = {
            "date": datetime.now(),
            "portfolio_value": 1000000,
            "var_95": -20000,
            "max_drawdown": -0.05,
            "sharpe_ratio": 1.2,
        }

        risk_manager.record_risk_metrics(risk_metrics)

        # 履歴データの確認
        history = risk_manager.get_risk_history(days=7)
        assert isinstance(history, list)
        assert len(history) >= 1

    def test_model_risk_assessment(self, risk_manager):
        """モデルリスク評価のテスト"""
        model_predictions = {
            "AAPL": {"prediction": 160, "confidence": 0.8},
            "GOOGL": {"prediction": 2700, "confidence": 0.7},
            "MSFT": {"prediction": 320, "confidence": 0.9},
        }

        model_risk = risk_manager.assess_model_risk(model_predictions)

        assert isinstance(model_risk, dict)
        assert "avg_confidence" in model_risk
        assert "prediction_consistency" in model_risk
        assert "model_risk_score" in model_risk

    @pytest.mark.asyncio
    async def test_real_time_risk_monitoring(self, risk_manager, sample_portfolio):
        """リアルタイムリスク監視のテスト"""
        # リスク監視のモック
        monitoring_data = {
            "timestamp": datetime.now(),
            "portfolio": sample_portfolio,
            "market_data": {"VIX": 20.5, "market_sentiment": "neutral"},
        }

        # リスク評価
        risk_status = await risk_manager.monitor_real_time_risk(monitoring_data)

        assert isinstance(risk_status, dict)
        assert "overall_risk" in risk_status
        assert "alerts" in risk_status
        assert "recommendations" in risk_status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
