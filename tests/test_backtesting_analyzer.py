"""BacktestingAnalyzerのテストモジュール。"""

import numpy as np
import pandas as pd
import pytest

from src.backtesting.analyzer import (calculate_performance_metrics,
                                      calculate_risk_metrics,
                                      generate_backtest_report)


def test_calculate_performance_metrics():
    """パフォーマンス指標計算のテスト"""
    # サンプルデータ作成
    dates = pd.date_range(start="2023-01-01", end="2023-02-01", freq="D")
    equity_curve = pd.Series(np.linspace(1_000_000, 1_200_000, len(dates)), index=dates)
    trades = [{"return": 0.05}, {"return": -0.02}, {"return": 0.03}, {"return": -0.01}, {"return": 0.08}]
    initial_capital = 1_000_000

    metrics = calculate_performance_metrics(equity_curve, trades, initial_capital)

    assert "total_return" in metrics
    assert "final_value" in metrics
    assert "win_rate" in metrics
    assert "avg_return" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe_ratio" in metrics
    assert "total_trades" in metrics

    # 具体的な値の検証
    expected_total_return = (equity_curve.iloc[-1] - initial_capital) / initial_capital
    assert abs(metrics["total_return"] - expected_total_return) < 0.001

    expected_win_rate = 3 / 5  # 5取引中3勝
    assert abs(metrics["win_rate"] - expected_win_rate) < 0.001

    expected_avg_return = sum(t["return"] for t in trades) / len(trades)
    assert abs(metrics["avg_return"] - expected_avg_return) < 0.001


def test_calculate_performance_metrics_empty_data():
    """空のデータに対するパフォーマンス指標計算のテスト"""
    empty_equity_curve = pd.Series([], dtype=float)
    empty_trades = []
    initial_capital = 1_000_000

    metrics = calculate_performance_metrics(empty_equity_curve, empty_trades, initial_capital)

    # 空のデータの場合はデフォルト値が返ること
    assert metrics == {}


def test_calculate_risk_metrics():
    """リスク指標計算のテスト"""
    # サンプルデータ作成
    dates = pd.date_range(start="2023-01-01", end="2023-02-01", freq="D")
    equity_curve = pd.Series(np.random.randn(len(dates)).cumsum() + 1_000_000, index=dates)
    trades = [{"return": 0.02}, {"return": -0.03}, {"return": -0.01}, {"return": 0.01}, {"return": -0.05}]

    metrics = calculate_risk_metrics(equity_curve, trades)

    assert "var_5" in metrics
    assert "cvar_5" in metrics
    assert "avg_trade_pnl" in metrics
    assert "avg_loss_per_trade" in metrics
    assert "max_loss_per_trade" in metrics

    # 具体的な値の検証（概算）
    daily_returns = equity_curve.pct_change().dropna()
    expected_var_5 = daily_returns.quantile(0.05)
    assert abs(metrics["var_5"] - expected_var_5) < 0.001

    expected_avg_pnl = sum(t["return"] for t in trades) / len(trades)
    assert abs(metrics["avg_trade_pnl"] - expected_avg_pnl) < 0.001

    losing_trades = [t for t in trades if t["return"] < 0]
    if losing_trades:
        expected_avg_loss = sum(t["return"] for t in losing_trades) / len(losing_trades)
        assert abs(metrics["avg_loss_per_trade"] - expected_avg_loss) < 0.001

        expected_max_loss = min(t["return"] for t in losing_trades)
        assert abs(metrics["max_loss_per_trade"] - expected_max_loss) < 0.001


def test_generate_backtest_report():
    """バックテストレポート生成のテスト"""
    perf_metrics = {
        "total_return": 0.2,
        "final_value": 1_200_000,
        "win_rate": 0.6,
        "avg_return": 0.02,
        "max_drawdown": 0.1,
        "sharpe_ratio": 1.5,
        "total_trades": 10,
    }

    risk_metrics = {
        "var_5": -0.03,
        "cvar_5": -0.05,
        "avg_trade_pnl": 0.01,
        "avg_loss_per_trade": -0.02,
        "max_loss_per_trade": -0.05,
    }

    report = generate_backtest_report(perf_metrics, risk_metrics)

    # レポートが文字列であり、必要な要素が含まれていることを確認
    assert isinstance(report, str)
    assert "# バックテストレポート" in report
    assert "## パフォーマンス指標" in report
    assert "## リスク指標" in report
    assert "総リターン: 20.00%" in report
    assert "勝率: 60.00%" in report
    assert "5% VaR: -3.00%" in report
