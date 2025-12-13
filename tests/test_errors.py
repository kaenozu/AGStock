"""errors.pyのユニットテスト"""

import pytest

from src.errors import (AGStockException, BacktestError, CacheError,
                        ConfigurationError, DataLoadError, ExecutionError,
                        RiskManagementError, StrategyError)


class TestAGStockException:
    """AGStockExceptionのテスト"""

    def test_agstock_exception_initialization(self):
        """AGStockExceptionの初期化テスト"""
        error = AGStockException("Test error message")
        assert str(error) == "Test error message"
        assert error.error_code == "UNKNOWN_ERROR"
        assert error.details == {}

    def test_agstock_exception_with_error_code_and_details(self):
        """エラーコードと詳細情報を含むAGStockExceptionのテスト"""
        details = {"key": "value"}
        error = AGStockException(message="Test error with code", error_code="TEST_ERROR", details=details)
        assert str(error) == "Test error with code"
        assert error.error_code == "TEST_ERROR"
        assert error.details == details


class TestDataLoadError:
    """DataLoadErrorのテスト"""

    def test_dataload_error_initialization(self):
        """DataLoadErrorの初期化テスト"""
        error = DataLoadError("Data load failed", ticker="7203.T")
        assert str(error) == "Data load failed"
        assert error.error_code == "DATA_LOAD_ERROR"
        assert error.details == {"ticker": "7203.T"}

        error_with_details = DataLoadError(message="Data load failed", ticker="7203.T", details={"period": "1y"})
        assert error_with_details.details == {"ticker": "7203.T", "period": "1y"}


class TestRiskManagementError:
    """RiskManagementErrorのテスト"""

    def test_riskmanagement_error_initialization(self):
        """RiskManagementErrorの初期化テスト"""
        error = RiskManagementError("Risk limit exceeded", risk_type="DRAWDOWN")
        assert str(error) == "Risk limit exceeded"
        assert error.error_code == "RISK_MANAGEMENT_ERROR"
        assert error.details == {"risk_type": "DRAWDOWN"}


class TestStrategyError:
    """StrategyErrorのテスト"""

    def test_strategy_error_initialization(self):
        """StrategyErrorの初期化テスト"""
        error = StrategyError("Strategy calculation failed", strategy_name="RSI")
        assert str(error) == "Strategy calculation failed"
        assert error.error_code == "STRATEGY_ERROR"
        assert error.details == {"strategy_name": "RSI"}


class TestExecutionError:
    """ExecutionErrorのテスト"""

    def test_execution_error_initialization(self):
        """ExecutionErrorの初期化テスト"""
        error = ExecutionError("Execution failed", ticker="7203.T", action="BUY")
        assert str(error) == "Execution failed"
        assert error.error_code == "EXECUTION_ERROR"
        assert error.details == {"ticker": "7203.T", "action": "BUY"}


class TestConfigurationError:
    """ConfigurationErrorのテスト"""

    def test_configuration_error_initialization(self):
        """ConfigurationErrorの初期化テスト"""
        error = ConfigurationError("Config validation failed", config_key="initial_capital")
        assert str(error) == "Config validation failed"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details == {"config_key": "initial_capital"}


class TestBacktestError:
    """BacktestErrorのテスト"""

    def test_backtest_error_initialization(self):
        """BacktestErrorの初期化テスト"""
        error = BacktestError("Backtest failed", strategy_name="Moving Average")
        assert str(error) == "Backtest failed"
        assert error.error_code == "BACKTEST_ERROR"
        assert error.details == {"strategy_name": "Moving Average"}


class TestCacheError:
    """CacheErrorのテスト"""

    def test_cache_error_initialization(self):
        """CacheErrorの初期化テスト"""
        error = CacheError("Cache operation failed", cache_key="test_key")
        assert str(error) == "Cache operation failed"
        assert error.error_code == "CACHE_ERROR"
        assert error.details == {"cache_key": "test_key"}
