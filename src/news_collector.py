"""
News Collector Module
Fetches latest financial news from RSS feeds.
"""

import datetime
import logging
from typing import Dict, List

import feedparser

logger = logging.getLogger(__name__)

# RSS Feed URLs (Japanese)
RSS_FEEDS = {
    "YAHOO_JP_BIZ": "https://news.yahoo.co.jp/rss/topics/business.xml",
    "REUTERS_JP_BIZ": "http://feeds.reuters.com/reuters/JPBusinessNews",
    "NIKKEI_HK": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",  # Third party aggregator or official if available
}


try:
    from src.cache_manager import CacheManager

    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False


class NewsCollector:
    def __init__(self):
        self.cache = CacheManager() if HAS_CACHE else None

    def fetch_market_news(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetches general market news from Yahoo Finance/Reuters.

        Returns:
            List of dicts: [{'title': str, 'link': str, 'published': str, 'summary': str}]
        """
        cache_key = f"market_news_limit_{limit}"

        # 1. Check Cache
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug("Hit cache for market_news")
                return cached_data

        all_news = []

        # Yahoo Business
        try:
            feed = feedparser.parse(RSS_FEEDS["YAHOO_JP_BIZ"])
            for entry in feed.entries[:limit]:
                all_news.append(
                    {
                        "source": "Yahoo Finance",
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                        "summary": entry.get("summary", ""),  # specific to ticker if scraping, but RSS usually generic
                    }
                )
        except Exception as e:
            logger.error(f"Error fetching Yahoo RSS: {e}")

        # 2. Save to Cache (TTL 30 mins = 1800s)
        if self.cache and all_news:
            self.cache.set(cache_key, all_news, ttl_seconds=1800)

        # Sort by date if possible (though RSS format varies)
        return all_news[:limit]

    def fetch_news_for_ticker(self, ticker: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetches news specific to a ticker.
        Note: Specific ticker RSS is hard to find without paid API.
        We will use a search-based RSS or fallback to general market news for now,
        OR scrape Yahoo Finance specific page (Simulated for safety).

        For this implementation, we will fetch generic business news and
        filter if the ticker name (or company name) appears in tile.
        """
        # In a real PRO app, we would use an API like NewsAPI or Google Search API.
        # Here we fetch general news and maybe find matches, or just return general news
        # as context for "Market Sentiment".

        # Let's fetch general news for now as "Market Context".
        return self.fetch_market_news(limit)


_collector = None


def get_news_collector():
    global _collector
    if _collector is None:
        _collector = NewsCollector()
    return _collector
