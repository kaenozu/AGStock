"""
MorningBriefのテスト
"""
import pytest
from unittest.mock import Mock, patch
from morning_brief import MorningBrief


class TestMorningBrief:
    """MorningBriefのテストクラス"""
    
    @pytest.fixture
    def morning_brief(self):
        """テスト用のMorningBriefインスタンス"""
        with patch('morning_brief.SmartNotifier'):
            mb = MorningBrief()
            return mb
    
    def test_initialization(self, morning_brief):
        """初期化テスト"""
        assert morning_brief is not None
    
    @patch('yfinance.Ticker')
    def test_get_market_overview(self, mock_ticker, morning_brief):
        """市場概況取得テスト"""
        # モックデータ
        mock_nikkei = Mock()
        mock_nikkei.history.return_value = Mock(empty=False)
        mock_nikkei.history.return_value.__getitem__ = Mock(return_value=[30000, 30500])
        
        mock_ticker.return_value = mock_nikkei
        
        overview = morning_brief.get_market_overview()
        
        assert overview is not None
        assert isinstance(overview, dict)
    
    @patch('src.sentiment.SentimentAnalyzer')
    def test_get_market_sentiment(self, mock_sentiment, morning_brief):
        """市場センチメント取得テスト"""
        # モックセンチメント
        mock_sa = Mock()
        mock_sa.get_market_sentiment.return_value = {
            'label': 'ポジティブ',
            'score': 0.75
        }
        mock_sentiment.return_value = mock_sa
        
        sentiment = morning_brief.get_market_sentiment()
        
        assert sentiment is not None
        assert 'label' in sentiment
        assert 'score' in sentiment
    
    def test_get_trading_strategy(self, morning_brief):
        """取引戦略取得テスト"""
        # VIXとセンチメントのモック
        with patch.object(morning_brief, 'get_market_overview', return_value={'vix': 15}):
            with patch.object(morning_brief, 'get_market_sentiment', return_value={'score': 0.5}):
                strategy = morning_brief.get_trading_strategy()
                
                assert strategy is not None
                assert isinstance(strategy, str)
                assert len(strategy) > 0
    
    def test_generate_brief(self, morning_brief):
        """ブリーフ生成テスト"""
        with patch.object(morning_brief, 'get_market_overview', return_value={'nikkei': 30000, 'vix': 15}):
            with patch.object(morning_brief, 'get_market_sentiment', return_value={'label': 'ポジティブ', 'score': 0.5}):
                with patch.object(morning_brief, 'get_trading_strategy', return_value="買い優勢"):
                    brief = morning_brief.generate_brief()
                    
                    assert brief is not None
                    assert isinstance(brief, str)
                    assert "市場概況" in brief or "Good Morning" in brief
    
    @patch('morning_brief.SmartNotifier')
    def test_send_brief(self, mock_notifier, morning_brief):
        """ブリーフ送信テスト"""
        morning_brief.notifier = mock_notifier
        
        with patch.object(morning_brief, 'generate_brief', return_value="Test brief"):
            result = morning_brief.send_brief()
            
            # 通知が呼ばれたか
            assert mock_notifier.send_line_notify.called or result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
