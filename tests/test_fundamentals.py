"""
FundamentalFilterのテスト
"""
import pytest
from src.fundamentals import FundamentalFilter


@pytest.fixture
def filter():
    """FundamentalFilterインスタンスを提供"""
    return FundamentalFilter()


def test_init():
    """初期化のテスト"""
    f = FundamentalFilter()
    assert f is not None


def test_filter_undervalued_pass(filter):
    """割安株フィルター：合格"""
    fundamentals = {
        "trailingPE": 15.0,
        "priceToBook": 2.0
    }
    assert filter.filter_undervalued(fundamentals) is True


def test_filter_undervalued_high_pe(filter):
    """割安株フィルター：PERが高い"""
    fundamentals = {
        "trailingPE": 30.0,
        "priceToBook": 2.0
    }
    assert filter.filter_undervalued(fundamentals) is False


def test_filter_undervalued_high_pbr(filter):
    """割安株フィルター：PBRが高い"""
    fundamentals = {
        "trailingPE": 15.0,
        "priceToBook": 5.0
    }
    assert filter.filter_undervalued(fundamentals) is False


def test_filter_undervalued_missing_pe(filter):
    """割安株フィルター：PERが欠損"""
    fundamentals = {
        "priceToBook": 2.0
    }
    assert filter.filter_undervalued(fundamentals) is False


def test_filter_undervalued_missing_pbr(filter):
    """割安株フィルター：PBRが欠損"""
    fundamentals = {
        "trailingPE": 15.0
    }
    assert filter.filter_undervalued(fundamentals) is False


def test_filter_undervalued_empty(filter):
    """割安株フィルター：空の辞書"""
    assert filter.filter_undervalued({}) is False


def test_filter_undervalued_none(filter):
    """割安株フィルター：None"""
    assert filter.filter_undervalued(None) is False


def test_filter_undervalued_custom_thresholds(filter):
    """割安株フィルター：カスタム閾値"""
    fundamentals = {
        "trailingPE": 20.0,
        "priceToBook": 2.5
    }
    assert filter.filter_undervalued(fundamentals, max_pe=30.0, max_pbr=3.0) is True
    assert filter.filter_undervalued(fundamentals, max_pe=15.0, max_pbr=2.0) is False


def test_filter_quality_pass(filter):
    """品質フィルター：合格"""
    fundamentals = {
        "returnOnEquity": 0.15
    }
    assert filter.filter_quality(fundamentals) is True


def test_filter_quality_fail(filter):
    """品質フィルター：不合格"""
    fundamentals = {
        "returnOnEquity": 0.05
    }
    assert filter.filter_quality(fundamentals) is False


def test_filter_quality_missing_roe(filter):
    """品質フィルター：ROEが欠損"""
    fundamentals = {}
    assert filter.filter_quality(fundamentals) is False


def test_filter_quality_none(filter):
    """品質フィルター：None"""
    assert filter.filter_quality(None) is False


def test_filter_quality_custom_threshold(filter):
    """品質フィルター：カスタム閾値"""
    fundamentals = {
        "returnOnEquity": 0.10
    }
    assert filter.filter_quality(fundamentals, min_roe=0.08) is True
    assert filter.filter_quality(fundamentals, min_roe=0.12) is False


def test_filter_large_cap_pass(filter):
    """大型株フィルター：合格"""
    fundamentals = {
        "marketCap": 200_000_000_000
    }
    assert filter.filter_large_cap(fundamentals) is True


def test_filter_large_cap_fail(filter):
    """大型株フィルター：不合格"""
    fundamentals = {
        "marketCap": 50_000_000_000
    }
    assert filter.filter_large_cap(fundamentals) is False


def test_filter_large_cap_missing(filter):
    """大型株フィルター：時価総額が欠損"""
    fundamentals = {}
    assert filter.filter_large_cap(fundamentals) is False


def test_filter_large_cap_none(filter):
    """大型株フィルター：None"""
    assert filter.filter_large_cap(None) is False


def test_filter_large_cap_custom_threshold(filter):
    """大型株フィルター：カスタム閾値"""
    fundamentals = {
        "marketCap": 150_000_000_000
    }
    assert filter.filter_large_cap(fundamentals, min_cap=100_000_000_000) is True
    assert filter.filter_large_cap(fundamentals, min_cap=200_000_000_000) is False


def test_combined_filters(filter):
    """複数フィルターの組み合わせ"""
    fundamentals = {
        "trailingPE": 18.0,
        "priceToBook": 2.5,
        "returnOnEquity": 0.12,
        "marketCap": 150_000_000_000
    }
    
    assert filter.filter_undervalued(fundamentals) is True
    assert filter.filter_quality(fundamentals) is True
    assert filter.filter_large_cap(fundamentals) is True
