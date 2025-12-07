"""
visualizerのテスト
"""
import pytest
import pandas as pd
import os
import matplotlib
# GUIバックエンドを使わないように設定
matplotlib.use('Agg')
from src.visualizer import ReportVisualizer


@pytest.fixture
def visualizer(tmp_path):
    """一時ディレクトリを使用するVisualizer"""
    return ReportVisualizer(output_dir=str(tmp_path))


def test_init(tmp_path):
    """初期化のテスト"""
    viz = ReportVisualizer(output_dir=str(tmp_path))
    assert os.path.exists(str(tmp_path))


def test_generate_equity_chart(visualizer):
    """資産推移チャート生成のテスト"""
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'total_equity': [10000 + i*100 for i in range(10)]
    })
    
    output_path = visualizer.generate_equity_chart(df, "test_equity.png")
    
    assert output_path is not None
    assert os.path.exists(output_path)


def test_generate_equity_chart_empty(visualizer):
    """空データでのチャート生成テスト"""
    output_path = visualizer.generate_equity_chart(pd.DataFrame())
    assert output_path is None


def test_generate_equity_chart_missing_columns(visualizer):
    """カラム不足でのチャート生成テスト"""
    df = pd.DataFrame({'A': [1, 2, 3]})
    output_path = visualizer.generate_equity_chart(df)
    assert output_path is None


def test_generate_pnl_bar_chart(visualizer):
    """日次損益チャート生成のテスト"""
    output_path = visualizer.generate_pnl_bar_chart(5000.0, "test_pnl.png")
    
    assert output_path is not None
    assert os.path.exists(output_path)


def test_generate_pnl_bar_chart_negative(visualizer):
    """負の損益でのチャート生成テスト"""
    output_path = visualizer.generate_pnl_bar_chart(-2000.0, "test_pnl_neg.png")
    
    assert output_path is not None
    assert os.path.exists(output_path)


def test_generate_equity_chart_timestamp_col(visualizer):
    """timestampカラムでのチャート生成テスト"""
    dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
    df = pd.DataFrame({
        'timestamp': dates,
        'total_equity': [10000 + i*100 for i in range(10)]
    })
    
    output_path = visualizer.generate_equity_chart(df, "test_equity_ts.png")
    
    assert output_path is not None
    assert os.path.exists(output_path)
