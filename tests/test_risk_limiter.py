"""
リスク制限テストスクリプト

risk_limiterの動作確認
"""

import json
from unittest.mock import mock_open, patch

import pytest

from src.risk_limiter import RiskLimiter


@pytest.fixture
def default_config():
    return {
        "risk_limits": {
            "max_position_size": 0.05,
            "max_daily_trades": 3,
            "max_daily_loss_pct": -3.0,
            "max_total_exposure": 0.80,
            "require_confirmation": True,
            "emergency_stop_loss_pct": -10.0,
            "min_cash_reserve": 0.20,
        }
    }


@pytest.fixture
def risk_limiter(default_config):
    with patch("builtins.open", mock_open(read_data=json.dumps(default_config))):
        return RiskLimiter("dummy_config.json")


def test_init_defaults():
    """設定ファイルがない場合のデフォルト設定テスト"""
    with patch("builtins.open", side_effect=FileNotFoundError):
        limiter = RiskLimiter("non_existent.json")
        assert limiter.risk_limits["max_position_size"] == 0.05


def test_check_position_size(risk_limiter):
    """ポジションサイズチェックテスト"""
    # 正常ケース (5%以下)
    passed, msg = risk_limiter.check_position_size(4000, 100000)
    assert passed
    assert msg == "OK"

    # 異常ケース (5%超過)
    passed, msg = risk_limiter.check_position_size(6000, 100000)
    assert not passed
    assert "ポジションサイズ超過" in msg


def test_check_daily_trades(risk_limiter):
    """日次取引数チェックテスト"""
    # 正常ケース (3回未満)
    passed, msg = risk_limiter.check_daily_trades(2)
    assert passed
    assert msg == "OK"

    # 異常ケース (3回以上)
    passed, msg = risk_limiter.check_daily_trades(3)
    assert not passed
    assert "日次取引数上限" in msg


def test_check_daily_loss(risk_limiter):
    """日次損失チェックテスト"""
    # 正常ケース (-3%より大きい)
    passed, msg = risk_limiter.check_daily_loss(-2.0)
    assert passed
    assert msg == "OK"

    # 異常ケース (-3%以下)
    passed, msg = risk_limiter.check_daily_loss(-3.1)
    assert not passed
    assert "日次損失上限" in msg


def test_check_total_exposure(risk_limiter):
    """総投資比率チェックテスト"""
    # 正常ケース (80%以下)
    passed, msg = risk_limiter.check_total_exposure(70000, 100000)
    assert passed
    assert msg == "OK"

    # 異常ケース (80%超過)
    passed, msg = risk_limiter.check_total_exposure(81000, 100000)
    assert not passed
    assert "総投資比率超過" in msg


def test_check_cash_reserve(risk_limiter):
    """現金準備チェックテスト"""
    # 正常ケース (20%以上)
    passed, msg = risk_limiter.check_cash_reserve(25000, 100000)
    assert passed
    assert msg == "OK"

    # 異常ケース (20%未満)
    passed, msg = risk_limiter.check_cash_reserve(15000, 100000)
    assert not passed
    assert "現金不足" in msg


def test_check_emergency_stop(risk_limiter):
    """緊急停止チェックテスト"""
    # 正常ケース (-10%より大きい)
    passed, msg = risk_limiter.check_emergency_stop(-5.0, 100000)
    assert passed
    assert msg == "OK"

    # 異常ケース (-10%以下)
    passed, msg = risk_limiter.check_emergency_stop(-11.0, 100000)
    assert not passed
    assert "緊急停止発動" in msg


def test_validate_trade_success(risk_limiter):
    """総合バリデーション成功テスト"""
    trade = {"position_value": 4000}
    portfolio = {
        "total_equity": 100000,
        "trades_today": 0,
        "daily_pnl_pct": -1.0,
        "invested_amount": 50000,
        "cash": 50000,
        "total_pnl_pct": -2.0,
        "initial_capital": 100000,
    }

    passed, checks = risk_limiter.validate_trade(trade, portfolio)
    assert passed
    assert all(check == "OK" for check in checks)


def test_validate_trade_failure(risk_limiter):
    """総合バリデーション失敗テスト"""
    trade = {"position_value": 6000}  # 6% (Fail)
    portfolio = {
        "total_equity": 100000,
        "trades_today": 3,  # Fail
        "daily_pnl_pct": -4.0,  # Fail
        "invested_amount": 85000,  # Fail
        "cash": 15000,  # Fail
        "total_pnl_pct": -11.0,  # Fail
        "initial_capital": 100000,
    }

    passed, checks = risk_limiter.validate_trade(trade, portfolio)
    assert not passed
    assert len([c for c in checks if c != "OK"]) == 6


def test_get_risk_report(risk_limiter):
    """リスクレポート生成テスト"""
    # 違反を追加
    risk_limiter.violations.append("Test Violation")

    report = risk_limiter.get_risk_report()
    assert "リスク制限設定" in report
    assert "Test Violation" in report
