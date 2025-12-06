import unittest
import pandas as pd
import numpy as np
from datetime import datetime, date
from src.formatters import (
    format_currency,
    format_percentage,
    format_number,
    format_large_number,
    format_date,
    get_risk_level,
    get_sentiment_label,
    truncate_text,
    style_dataframe_currency,
    style_dataframe_percentage,
    format_currency_jp
)


class TestFormatCurrency(unittest.TestCase):
    """Tests for format_currency function"""
    
    def test_format_currency_basic(self):
        """Test basic currency formatting"""
        result = format_currency(1234567)
        self.assertEqual(result, "¥1,234,567")
    
    def test_format_currency_with_decimals(self):
        """Test currency with decimals"""
        result = format_currency(1234.56, decimals=2)
        self.assertEqual(result, "¥1,234.56")
    
    def test_format_currency_with_sign(self):
        """Test currency with sign"""
        result = format_currency(1000, show_sign=True)
        self.assertEqual(result, "+¥1,000")
    
    def test_format_currency_none(self):
        """Test currency with None value"""
        result = format_currency(None)
        self.assertEqual(result, "N/A")
    
    def test_format_currency_custom_symbol(self):
        """Test currency with custom symbol"""
        result = format_currency(1000, symbol="$")
        self.assertEqual(result, "$1,000")


class TestFormatPercentage(unittest.TestCase):
    """Tests for format_percentage function"""
    
    def test_format_percentage_basic(self):
        """Test basic percentage formatting"""
        result = format_percentage(0.1534)
        self.assertEqual(result, "15.34%")
    
    def test_format_percentage_with_sign(self):
        """Test percentage with sign"""
        result = format_percentage(0.05, show_sign=True)
        self.assertEqual(result, "+5.00%")
    
    def test_format_percentage_negative(self):
        """Test negative percentage"""
        result = format_percentage(-0.03, decimals=1)
        self.assertEqual(result, "-3.0%")
    
    def test_format_percentage_none(self):
        """Test percentage with None"""
        result = format_percentage(None)
        self.assertEqual(result, "N/A")


class TestFormatNumber(unittest.TestCase):
    """Tests for format_number function"""
    
    def test_format_number_basic(self):
        """Test basic number formatting"""
        result = format_number(12345.67)
        self.assertEqual(result, "12,345.67")
    
    def test_format_number_with_suffix(self):
        """Test number with suffix"""
        result = format_number(1.5, decimals=1, suffix="倍")
        self.assertEqual(result, "1.5倍")
    
    def test_format_number_none(self):
        """Test number with None"""
        result = format_number(None)
        self.assertEqual(result, "N/A")


class TestFormatLargeNumber(unittest.TestCase):
    """Tests for format_large_number function"""
    
    def test_format_large_number_billions(self):
        """Test billions formatting"""
        result = format_large_number(1500000000)
        self.assertEqual(result, "1.5B")
    
    def test_format_large_number_millions(self):
        """Test millions formatting"""
        result = format_large_number(2300000)
        self.assertEqual(result, "2.3M")
    
    def test_format_large_number_thousands(self):
        """Test thousands formatting"""
        result = format_large_number(5600)
        self.assertEqual(result, "5.6K")
    
    def test_format_large_number_small(self):
        """Test small numbers"""
        result = format_large_number(123.45)
        self.assertEqual(result, "123.4")
    
    def test_format_large_number_negative(self):
        """Test negative large number"""
        result = format_large_number(-1500000)
        self.assertEqual(result, "-1.5M")


class TestFormatDate(unittest.TestCase):
    """Tests for format_date function"""
    
    def test_format_date_default(self):
        """Test date with default format"""
        test_date = datetime(2023, 12, 25)
        result = format_date(test_date)
        self.assertEqual(result, "2023-12-25")
    
    def test_format_date_custom_format(self):
        """Test date with custom format"""
        test_date = datetime(2023, 12, 25)
        result = format_date(test_date, "%d/%m/%Y")
        self.assertEqual(result, "25/12/2023")
    
    def test_format_date_none(self):
        """Test date with None"""
        result = format_date(None)
        self.assertEqual(result, "N/A")


class TestGetRiskLevel(unittest.TestCase):
    """Tests for get_risk_level function"""
    
    def test_get_risk_level_low(self):
        """Test low risk level"""
        result = get_risk_level(-0.05)
        self.assertEqual(result, "low")
    
    def test_get_risk_level_medium(self):
        """Test medium risk level"""
        result = get_risk_level(-0.15)
        self.assertEqual(result, "medium")
    
    def test_get_risk_level_high(self):
        """Test high risk level"""
        result = get_risk_level(-0.25)
        self.assertEqual(result, "high")


class TestGetSentimentLabel(unittest.TestCase):
    """Tests for get_sentiment_label function"""
    
    def test_get_sentiment_positive(self):
        """Test positive sentiment"""
        result = get_sentiment_label(0.5)
        self.assertEqual(result, "Positive")
    
    def test_get_sentiment_negative(self):
        """Test negative sentiment"""
        result = get_sentiment_label(-0.5)
        self.assertEqual(result, "Negative")
    
    def test_get_sentiment_neutral(self):
        """Test neutral sentiment"""
        result = get_sentiment_label(0.05)
        self.assertEqual(result, "Neutral")


class TestTruncateText(unittest.TestCase):
    """Tests for truncate_text function"""
    
    def test_truncate_text_short(self):
        """Test text shorter than max length"""
        result = truncate_text("Short text", max_length=50)
        self.assertEqual(result, "Short text")
    
    def test_truncate_text_long(self):
        """Test text longer than max length"""
        long_text = "This is a very long text that should be truncated"
        result = truncate_text(long_text, max_length=20)
        self.assertEqual(result, "This is a very lo...")
    
    def test_truncate_text_custom_suffix(self):
        """Test truncation with custom suffix"""
        result = truncate_text("Long text here", max_length=10, suffix="…")
        self.assertEqual(result, "Long text…")
    
    def test_truncate_text_none(self):
        """Test truncate with None"""
        result = truncate_text(None)
        self.assertEqual(result, "")


class TestDataFrameStylers(unittest.TestCase):
    """Tests for DataFrame styling functions"""
    
    def test_style_dataframe_currency(self):
        """Test DataFrame currency styling"""
        df = pd.DataFrame({
            'Amount': [1000, 2000, 3000],
            'Other': [1, 2, 3]
        })
        
        result = style_dataframe_currency(df, ['Amount'])
        
        self.assertIn('Amount', result.columns)
        self.assertEqual(result['Amount'].iloc[0], "¥1,000")
    
    def test_style_dataframe_percentage(self):
        """Test DataFrame percentage styling"""
        df = pd.DataFrame({
            'Rate': [0.05, 0.10, 0.15],
            'Other': [1, 2, 3]
        })
        
        result = style_dataframe_percentage(df, ['Rate'])
        
        self.assertIn('Rate', result.columns)
        self.assertEqual(result['Rate'].iloc[0], "5.00%")


class TestFormatCurrencyJP(unittest.TestCase):
    """Tests for format_currency_jp function"""
    
    def test_format_currency_jp_billions(self):
        """Test JP currency in billions"""
        result = format_currency_jp(150000000)
        self.assertEqual(result, "¥1.50億")
    
    def test_format_currency_jp_millions(self):
        """Test JP currency in ten thousands"""
        result = format_currency_jp(25000)
        self.assertEqual(result, "¥2.5万")
    
    def test_format_currency_jp_small(self):
        """Test JP currency for small amounts"""
        result = format_currency_jp(5000)
        self.assertEqual(result, "¥5,000")
    
    def test_format_currency_jp_none(self):
        """Test JP currency with None"""
        result = format_currency_jp(None)
        self.assertEqual(result, "N/A")


if __name__ == '__main__':
    unittest.main()
