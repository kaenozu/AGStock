"""
formattersのテスト
"""
import pytest
import pandas as pd
from datetime import datetime
from src.formatters import (
    format_currency, format_percentage, format_number, format_large_number,
    format_date, get_risk_level, get_sentiment_label, truncate_text,
    style_dataframe_currency, style_dataframe_percentage, format_currency_jp
)


def test_format_currency_basic():
    """基本的な通貨フォーマットのテスト"""
    assert format_currency(1234567) == "¥1,234,567"
    assert format_currency(1234567.89, decimals=2) == "¥1,234,567.89"


def test_format_currency_with_symbol():
    """通貨記号のカスタマイズテスト"""
    assert format_currency(1000, symbol="$") == "$1,000"


def test_format_currency_with_sign():
    """符号表示のテスト"""
    assert format_currency(1000, show_sign=True) == "+¥1,000"
    assert format_currency(-1000, show_sign=True) == "¥-1,000"


def test_format_currency_none():
    """None値のテスト"""
    assert format_currency(None) == "N/A"


def test_format_currency_nan():
    """NaN値のテスト"""
    assert format_currency(float('nan')) == "N/A"


def test_format_percentage_basic():
    """基本的なパーセンテージフォーマットのテスト"""
    assert format_percentage(0.1234) == "12.34%"
    assert format_percentage(0.1234, decimals=1) == "12.3%"


def test_format_percentage_with_sign():
    """符号付きパーセンテージのテスト"""
    assert format_percentage(0.05, show_sign=True) == "+5.00%"
    assert format_percentage(-0.03, show_sign=True) == "-3.00%"


def test_format_percentage_none():
    """None値のテスト"""
    assert format_percentage(None) == "N/A"


def test_format_number_basic():
    """基本的な数値フォーマットのテスト"""
    assert format_number(1234.5678) == "1,234.57"
    assert format_number(1234.5678, decimals=1) == "1,234.6"


def test_format_number_with_suffix():
    """接尾辞付き数値のテスト"""
    assert format_number(2.5, decimals=1, suffix="倍") == "2.5倍"


def test_format_number_none():
    """None値のテスト"""
    assert format_number(None) == "N/A"


def test_format_large_number_thousands():
    """千単位のフォーマットテスト"""
    assert format_large_number(1500) == "1.5K"
    assert format_large_number(999) == "999.0"


def test_format_large_number_millions():
    """百万単位のフォーマットテスト"""
    assert format_large_number(1500000) == "1.5M"


def test_format_large_number_billions():
    """十億単位のフォーマットテスト"""
    assert format_large_number(2500000000) == "2.5B"


def test_format_large_number_negative():
    """負の値のテスト"""
    assert format_large_number(-1500000) == "-1.5M"


def test_format_large_number_none():
    """None値のテスト"""
    assert format_large_number(None) == "N/A"


def test_format_date_basic():
    """基本的な日付フォーマットのテスト"""
    date = datetime(2023, 12, 25)
    assert format_date(date) == "2023-12-25"


def test_format_date_custom_format():
    """カスタムフォーマットのテスト"""
    date = datetime(2023, 12, 25)
    assert format_date(date, format_str="%Y/%m/%d") == "2023/12/25"


def test_format_date_string_input():
    """文字列入力のテスト"""
    result = format_date("2023-12-25")
    assert "2023" in result


def test_format_date_none():
    """None値のテスト"""
    assert format_date(None) == "N/A"


def test_get_risk_level_low():
    """低リスクレベルのテスト"""
    assert get_risk_level(-0.05) == "low"


def test_get_risk_level_medium():
    """中リスクレベルのテスト"""
    assert get_risk_level(-0.15) == "medium"


def test_get_risk_level_high():
    """高リスクレベルのテスト"""
    assert get_risk_level(-0.25) == "high"


def test_get_sentiment_label_positive():
    """ポジティブセンチメントのテスト"""
    assert get_sentiment_label(0.5) == "Positive"


def test_get_sentiment_label_negative():
    """ネガティブセンチメントのテスト"""
    assert get_sentiment_label(-0.5) == "Negative"


def test_get_sentiment_label_neutral():
    """ニュートラルセンチメントのテスト"""
    assert get_sentiment_label(0.0) == "Neutral"
    assert get_sentiment_label(0.1) == "Neutral"


def test_truncate_text_short():
    """短いテキストのテスト"""
    text = "Short text"
    assert truncate_text(text, max_length=50) == "Short text"


def test_truncate_text_long():
    """長いテキストのテスト"""
    text = "This is a very long text that needs to be truncated"
    result = truncate_text(text, max_length=20)
    assert len(result) == 20
    assert result.endswith("...")


def test_truncate_text_custom_suffix():
    """カスタム接尾辞のテスト"""
    text = "Long text here"
    result = truncate_text(text, max_length=10, suffix="…")
    assert result.endswith("…")


def test_truncate_text_none():
    """None値のテスト"""
    assert truncate_text(None) == ""


def test_style_dataframe_currency():
    """DataFrameの通貨スタイリングテスト"""
    df = pd.DataFrame({
        'Amount': [1000, 2000, 3000],
        'Value': [500, 1500, 2500]
    })
    
    styled = style_dataframe_currency(df, ['Amount', 'Value'])
    
    assert styled['Amount'].iloc[0] == "¥1,000"
    assert styled['Value'].iloc[1] == "¥1,500"


def test_style_dataframe_currency_missing_column():
    """存在しないカラムのテスト"""
    df = pd.DataFrame({
        'Amount': [1000, 2000]
    })
    
    styled = style_dataframe_currency(df, ['Amount', 'NonExistent'])
    
    assert 'Amount' in styled.columns
    assert 'NonExistent' not in styled.columns


def test_style_dataframe_percentage():
    """DataFrameのパーセンテージスタイリングテスト"""
    df = pd.DataFrame({
        'Return': [0.05, 0.10, -0.03],
        'Ratio': [0.15, 0.20, 0.25]
    })
    
    styled = style_dataframe_percentage(df, ['Return', 'Ratio'])
    
    assert styled['Return'].iloc[0] == "5.00%"
    assert styled['Ratio'].iloc[1] == "20.00%"


def test_format_currency_jp_small():
    """日本円フォーマット：小額のテスト"""
    assert format_currency_jp(5000) == "¥5,000"


def test_format_currency_jp_man():
    """日本円フォーマット：万円単位のテスト"""
    assert format_currency_jp(50000) == "¥5.0万"


def test_format_currency_jp_oku():
    """日本円フォーマット：億円単位のテスト"""
    assert format_currency_jp(150000000) == "¥1.50億"


def test_format_currency_jp_none():
    """日本円フォーマット：None値のテスト"""
    assert format_currency_jp(None) == "N/A"


def test_format_currency_jp_nan():
    """日本円フォーマット：NaN値のテスト"""
    assert format_currency_jp(float('nan')) == "N/A"
