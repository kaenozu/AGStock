from unittest.mock import patch, MagicMock
from src.sentiment import SentimentAnalyzer

def test_analyze_sentiment():
    sa = SentimentAnalyzer()
    
    assert sa.analyze_sentiment("I love this stock! It is amazing.") > 0
    assert sa.analyze_sentiment("This is terrible. I hate it.") < 0
    assert sa.analyze_sentiment("The stock price is 100 dollars.") == 0

@patch('src.sentiment.feedparser.parse')
def test_fetch_news(mock_parse):
    # Mock feed response
    mock_entry = MagicMock()
    mock_entry.title = "Test News"
    mock_entry.link = "http://example.com"
    mock_entry.summary = "Summary"
    
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed
    
    sa = SentimentAnalyzer()
    news = sa.fetch_news()
    
    assert len(news) > 0
    assert news[0]['title'] == "Test News"

@patch('src.sentiment.SentimentAnalyzer.fetch_news')
def test_get_market_sentiment(mock_fetch):
    sa = SentimentAnalyzer()
    
    # Case 1: Positive
    mock_fetch.return_value = [
        {'title': 'Great earnings', 'summary': 'Stock is up'},
        {'title': 'Excellent growth', 'summary': 'Revenue increased'}
    ]
    sentiment = sa.get_market_sentiment()
    assert sentiment['score'] > 0
    assert sentiment['label'] == 'Positive'
    
    # Case 2: Negative
    mock_fetch.return_value = [
        {'title': 'Crash coming', 'summary': 'Market is down'},
        {'title': 'Terrible loss', 'summary': 'Revenue decreased'}
    ]
    sentiment = sa.get_market_sentiment()
    assert sentiment['score'] < 0
    assert sentiment['label'] == 'Negative'
