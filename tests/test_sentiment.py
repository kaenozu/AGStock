"""
SentimentAnalyzerの包括的なテスト
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from src.sentiment import SentimentAnalyzer


@pytest.fixture
def mock_bert():
    with patch("src.sentiment.get_bert_analyzer") as mock:
        analyzer = MagicMock()
        analyzer.analyze.return_value = {"score": 0.8}
        mock.return_value = analyzer
        yield mock


@pytest.fixture
def mock_sqlite():
    with patch("sqlite3.connect") as mock:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock.return_value.__enter__.return_value = conn
        yield mock


@pytest.fixture
def analyzer(mock_bert, mock_sqlite):
    return SentimentAnalyzer(db_path=":memory:")


def test_init(analyzer):
    """初期化のテスト"""
    assert analyzer.db_path == ":memory:"
    assert len(analyzer.feeds) > 0


@patch("src.sentiment.feedparser.parse")
def test_fetch_news(mock_parse, analyzer):
    """ニュース取得のテスト"""
    # フィードのモックレスポンス
    feed_mock = MagicMock()
    entry = MagicMock()
    entry.title = "Test News"
    entry.link = "http://example.com"
    entry.get.return_value = "Summary"
    feed_mock.entries = [entry]
    mock_parse.return_value = feed_mock

    news = analyzer.fetch_news(limit=5)

    assert len(news) > 0
    assert news[0]["title"] == "Test News"


def test_analyze_sentiment(analyzer):
    """センチメント分析のテスト"""
    score = analyzer.analyze_sentiment("Good news")
    assert score == 0.8


@patch("src.sentiment.SentimentAnalyzer.fetch_news")
def test_get_market_sentiment(mock_fetch, analyzer):
    """市場センチメント取得のテスト"""
    mock_fetch.return_value = [
        {"title": "Good news", "summary": "Market is up"},
        {"title": "Bad news", "summary": "Market is down"},
    ]

    # BERTアナライザーのモック動作を調整
    analyzer.bert_analyzer.analyze.side_effect = [{"score": 0.5}, {"score": -0.5}]

    sentiment = analyzer.get_market_sentiment()

    assert sentiment["score"] == 0.0
    assert sentiment["label"] == "Neutral"
    assert sentiment["news_count"] == 2


def test_save_sentiment_history(analyzer, mock_sqlite):
    """履歴保存のテスト"""
    data = {"score": 0.5, "label": "Positive", "news_count": 10}

    analyzer.save_sentiment_history(data)

    conn = mock_sqlite.return_value.__enter__.return_value
    cursor = conn.cursor.return_value
    cursor.execute.assert_called()


def test_save_sentiment_history_missing_keys(analyzer):
    """履歴保存時のキー不足エラーテスト"""
    data = {"score": 0.5}
    with pytest.raises(KeyError):
        analyzer.save_sentiment_history(data)


def test_get_sentiment_history(analyzer, mock_sqlite):
    """履歴取得のテスト"""
    conn = mock_sqlite.return_value.__enter__.return_value
    cursor = conn.cursor.return_value

    # モックデータ
    cursor.fetchall.return_value = [("2023-01-01", 0.5, "Positive", 10)]

    history = analyzer.get_sentiment_history(days=7)

    assert len(history) == 1
    assert history[0]["score"] == 0.5
