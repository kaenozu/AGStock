"""
MultiTimeframeAnalyzerのテスト
"""
import pytest
import pandas as pd
import numpy as np
from src.multi_timeframe import MultiTimeframeAnalyzer


@pytest.fixture
def analyzer():
    """MultiTimeframeAnalyzerインスタンスを提供"""
    return MultiTimeframeAnalyzer()


@pytest.fixture
def daily_data():
    """日次データを提供"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    base_price = 100
    trend = np.linspace(0, 20, 100)
    noise = np.random.randn(100) * 2
    prices = base_price + trend + noise
    
    data = {
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': [1000000] * 100
    }
    df = pd.DataFrame(data, index=dates)
    return df


def test_init():
    """初期化のテスト"""
    analyzer = MultiTimeframeAnalyzer()
    assert analyzer is not None


def test_resample_data_weekly(analyzer, daily_data):
    """週次リサンプリングのテスト"""
    weekly = analyzer.resample_data(daily_data, 'W')
    
    assert not weekly.empty
    assert len(weekly) < len(daily_data)
    assert 'Open' in weekly.columns
    assert 'Close' in weekly.columns


def test_resample_data_monthly(analyzer, daily_data):
    """月次リサンプリングのテスト"""
    monthly = analyzer.resample_data(daily_data, 'M')
    
    assert not monthly.empty
    assert len(monthly) < len(daily_data)


def test_resample_data_empty(analyzer):
    """空のDataFrameのリサンプリング"""
    empty_df = pd.DataFrame()
    result = analyzer.resample_data(empty_df, 'W')
    
    assert result.empty


def test_resample_data_none(analyzer):
    """NoneのDataFrameのリサンプリング"""
    result = analyzer.resample_data(None, 'W')
    
    assert result.empty


def test_resample_data_with_adj_close(analyzer):
    """Adj Closeカラムがある場合のリサンプリング"""
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'Open': [100] * 50,
        'High': [105] * 50,
        'Low': [95] * 50,
        'Close': [102] * 50,
        'Volume': [1000000] * 50,
        'Adj Close': [101] * 50
    }, index=dates)
    
    weekly = analyzer.resample_data(df, 'W')
    
    assert 'Adj Close' in weekly.columns


def test_resample_data_non_datetime_index(analyzer):
    """DatetimeIndexでない場合の変換"""
    df = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [95, 96, 97],
        'Close': [102, 103, 104],
        'Volume': [1000000, 1000000, 1000000]
    }, index=['2023-01-01', '2023-01-02', '2023-01-03'])
    
    weekly = analyzer.resample_data(df, 'W')
    
    assert isinstance(weekly.index, pd.DatetimeIndex)


def test_calculate_mtf_indicators(analyzer, daily_data):
    """MTFインジケーター計算のテスト"""
    weekly = analyzer.resample_data(daily_data, 'W')
    weekly_with_indicators = analyzer.calculate_mtf_indicators(weekly, 'W_')
    
    # 追加されたカラムを確認
    assert 'W_SMA_20' in weekly_with_indicators.columns
    assert 'W_SMA_50' in weekly_with_indicators.columns
    assert 'W_Trend' in weekly_with_indicators.columns
    assert 'W_RSI' in weekly_with_indicators.columns
    assert 'W_MACD' in weekly_with_indicators.columns
    assert 'W_MACD_Signal' in weekly_with_indicators.columns
    assert 'W_MACD_Hist' in weekly_with_indicators.columns


def test_calculate_mtf_indicators_trend_values(analyzer, daily_data):
    """トレンド値が正しく計算されることを確認"""
    weekly = analyzer.resample_data(daily_data, 'W')
    weekly_with_indicators = analyzer.calculate_mtf_indicators(weekly, 'W_')
    
    # Trendは1または-1
    assert weekly_with_indicators['W_Trend'].isin([1, -1]).all()


def test_merge_mtf_features(analyzer, daily_data):
    """MTF特徴量のマージテスト"""
    weekly = analyzer.resample_data(daily_data, 'W')
    weekly_with_indicators = analyzer.calculate_mtf_indicators(weekly, 'W_')
    
    merged = analyzer.merge_mtf_features(daily_data, weekly_with_indicators, 'W_')
    
    # 元のデータと同じ長さ
    assert len(merged) == len(daily_data)
    
    # MTF特徴量が追加されている
    assert 'W_SMA_20' in merged.columns
    assert 'W_Trend' in merged.columns


def test_merge_mtf_features_empty_daily(analyzer):
    """空の日次データのマージ"""
    empty_daily = pd.DataFrame()
    weekly = pd.DataFrame({'W_SMA_20': [100, 101]})
    
    result = analyzer.merge_mtf_features(empty_daily, weekly, 'W_')
    
    assert result.empty


def test_merge_mtf_features_empty_mtf(analyzer, daily_data):
    """空のMTFデータのマージ"""
    empty_weekly = pd.DataFrame()
    
    result = analyzer.merge_mtf_features(daily_data, empty_weekly, 'W_')
    
    # 元のデータがそのまま返る
    assert len(result) == len(daily_data)


def test_merge_mtf_features_none(analyzer, daily_data):
    """NoneのMTFデータのマージ"""
    result = analyzer.merge_mtf_features(daily_data, None, 'W_')
    
    # 元のデータがそのまま返る
    assert len(result) == len(daily_data)


def test_merge_mtf_features_no_prefix_columns(analyzer, daily_data):
    """プレフィックス付きカラムがない場合"""
    weekly = pd.DataFrame({
        'Open': [100, 101],
        'Close': [102, 103]
    }, index=pd.date_range('2023-01-01', periods=2, freq='W'))
    
    result = analyzer.merge_mtf_features(daily_data, weekly, 'W_')
    
    # 元のデータがそのまま返る
    assert len(result) == len(daily_data)


def test_add_mtf_features(analyzer, daily_data):
    """MTF特徴量追加のメインメソッドテスト"""
    result = analyzer.add_mtf_features(daily_data)
    
    # 週次と月次の特徴量が追加されている
    assert 'W_SMA_20' in result.columns
    assert 'W_Trend' in result.columns
    assert 'M_SMA_20' in result.columns
    assert 'M_Trend' in result.columns
    
    # 元のデータと同じ長さ
    assert len(result) == len(daily_data)


def test_add_mtf_features_integration(analyzer):
    """統合テスト：実際のワークフロー"""
    # 十分なデータ量で実行
    dates = pd.date_range(start='2022-01-01', periods=365, freq='D')
    np.random.seed(42)
    
    prices = 100 + np.cumsum(np.random.randn(365) * 0.5)
    
    df = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': [1000000] * 365
    }, index=dates)
    
    result = analyzer.add_mtf_features(df)
    
    # すべての特徴量が追加されている
    weekly_features = [col for col in result.columns if col.startswith('W_')]
    monthly_features = [col for col in result.columns if col.startswith('M_')]
    
    assert len(weekly_features) > 0
    assert len(monthly_features) > 0
    
    # NaNが少ない（forward fillされている）
    assert result['W_Trend'].notna().sum() > len(result) * 0.8
