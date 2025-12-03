from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES


class TestNikkei225Tickers:
    """NIKKEI_225_TICKERSのテスト"""
    
    def test_tickers_not_empty(self):
        """ティッカーリストが空でないことを確認"""
        assert len(NIKKEI_225_TICKERS) > 0
    
    def test_tickers_are_strings(self):
        """すべてのティッカーが文字列であることを確認"""
        assert all(isinstance(ticker, str) for ticker in NIKKEI_225_TICKERS)
    
    def test_tickers_have_tokyo_suffix(self):
        """すべてのティッカーが.T接尾辞を持つことを確認"""
        assert all(ticker.endswith('.T') for ticker in NIKKEI_225_TICKERS)
    
    def test_tickers_are_unique(self):
        """ティッカーに重複がないことを確認"""
        assert len(NIKKEI_225_TICKERS) == len(set(NIKKEI_225_TICKERS))
    
    def test_ticker_format(self):
        """ティッカーが正しい形式（数字.T）であることを確認"""
        for ticker in NIKKEI_225_TICKERS:
            # .Tを除いた部分が数字であることを確認
            code = ticker.replace('.T', '')
            assert code.isdigit(), f"Ticker {ticker} has invalid format"
    
    def test_contains_major_stocks(self):
        """主要な銘柄が含まれていることを確認"""
        major_stocks = ['7203.T', '9984.T', '6758.T']  # Toyota, SoftBank, Sony
        for stock in major_stocks:
            assert stock in NIKKEI_225_TICKERS


class TestTickerNames:
    """TICKER_NAMESのテスト"""
    
    def test_ticker_names_not_empty(self):
        """ティッカー名マッピングが空でないことを確認"""
        assert len(TICKER_NAMES) > 0
    
    def test_all_keys_are_valid_tickers(self):
        """すべてのキーが有効なティッカー形式であることを確認"""
        for ticker in TICKER_NAMES.keys():
            assert ticker.endswith('.T')
            code = ticker.replace('.T', '')
            assert code.isdigit()
    
    def test_all_values_are_strings(self):
        """すべての値が文字列であることを確認"""
        assert all(isinstance(name, str) for name in TICKER_NAMES.values())
    
    def test_all_values_not_empty(self):
        """すべての名前が空でないことを確認"""
        assert all(len(name) > 0 for name in TICKER_NAMES.values())
    
    def test_all_tickers_have_names(self):
        """NIKKEI_225_TICKERSのすべてのティッカーに名前があることを確認"""
        for ticker in NIKKEI_225_TICKERS:
            assert ticker in TICKER_NAMES, f"Ticker {ticker} has no name mapping"
    
    def test_major_company_names(self):
        """主要企業の名前が正しくマッピングされていることを確認"""
        expected_mappings = {
            '7203.T': 'Toyota Motor',
            '9984.T': 'SoftBank Group',
            '6758.T': 'Sony Group'
        }
        
        for ticker, expected_name in expected_mappings.items():
            assert ticker in TICKER_NAMES
            assert TICKER_NAMES[ticker] == expected_name
    
    def test_no_duplicate_names(self):
        """名前に重複がないことを確認（異なる企業は異なる名前を持つべき）"""
        names = list(TICKER_NAMES.values())
        # 一部の企業は似た名前を持つ可能性があるため、完全な一意性は要求しない
        # ただし、大部分は一意であるべき
        unique_names = set(names)
        # 少なくとも90%は一意であることを確認
        assert len(unique_names) >= len(names) * 0.9


class TestConstantsConsistency:
    """定数間の整合性テスト"""
    
    def test_tickers_and_names_same_length(self):
        """ティッカーリストと名前マッピングの長さが一致することを確認"""
        assert len(NIKKEI_225_TICKERS) == len(TICKER_NAMES)
    
    def test_all_tickers_mapped(self):
        """すべてのティッカーが名前にマッピングされていることを確認"""
        for ticker in NIKKEI_225_TICKERS:
            assert ticker in TICKER_NAMES, f"Ticker {ticker} is not mapped to a name"
    
    def test_no_extra_mappings(self):
        """TICKER_NAMESにNIKKEI_225_TICKERSにない余分なマッピングがないことを確認"""
        for ticker in TICKER_NAMES.keys():
            assert ticker in NIKKEI_225_TICKERS, f"Ticker {ticker} in TICKER_NAMES but not in NIKKEI_225_TICKERS"
