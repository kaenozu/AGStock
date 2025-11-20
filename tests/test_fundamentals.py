import pytest
from src.fundamentals import FundamentalFilter

def test_filter_undervalued():
    f = FundamentalFilter()
    
    # Good case
    data_good = {"trailingPE": 15.0, "priceToBook": 1.5}
    assert f.filter_undervalued(data_good, max_pe=20, max_pbr=2) == True
    
    # Bad PE
    data_bad_pe = {"trailingPE": 25.0, "priceToBook": 1.5}
    assert f.filter_undervalued(data_bad_pe, max_pe=20, max_pbr=2) == False
    
    # Bad PBR
    data_bad_pbr = {"trailingPE": 15.0, "priceToBook": 2.5}
    assert f.filter_undervalued(data_bad_pbr, max_pe=20, max_pbr=2) == False
    
    # Missing data
    assert f.filter_undervalued({}, max_pe=20, max_pbr=2) == False
    assert f.filter_undervalued({"trailingPE": 15.0}, max_pe=20, max_pbr=2) == False

def test_filter_quality():
    f = FundamentalFilter()
    
    # Good case
    data_good = {"returnOnEquity": 0.15}
    assert f.filter_quality(data_good, min_roe=0.10) == True
    
    # Bad ROE
    data_bad = {"returnOnEquity": 0.05}
    assert f.filter_quality(data_bad, min_roe=0.10) == False
    
    # Missing data
    assert f.filter_quality({}) == False

def test_filter_large_cap():
    f = FundamentalFilter()
    
    # Good case
    data_good = {"marketCap": 200_000_000_000}
    assert f.filter_large_cap(data_good, min_cap=100_000_000_000) == True
    
    # Small cap
    data_small = {"marketCap": 50_000_000_000}
    assert f.filter_large_cap(data_small, min_cap=100_000_000_000) == False
