import datetime
import sqlite3
from typing import Dict, List

import feedparser

from agstock.src.bert_sentiment import get_bert_analyzer


class SentimentAnalyzer:
    def __init__(self, db_path: str = "sentiment_history.db"):
        # RSS Feeds for Global/US Market Sentiment
        self.feeds = [
            "https://finance.yahoo.com/news/rssindex",
            "http://feeds.marketwatch.com/marketwatch/topstories/",
            "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        ]
        self.db_path = db_path
        self._init_database()
        self.bert_analyzer = get_bert_analyzer()

    def fetch_news(self, limit: int = 20) -> List[Dict]:
        """
        Fetches news headlines from RSS feeds.
        """
        news_items = []
        seen_titles = set()

        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:  # Top 10 from each
                    title = entry.title
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)

                    news_items.append(
                        {
                            "title": title,
                            "link": entry.link,
                            "published": entry.get("published", str(datetime.datetime.now())),
                            "summary": entry.get("summary", ""),
                        }
                    )
            except Exception as e:
                print(f"Error fetching feed {url}: {e}")

        return news_items[:limit]

    def analyze_sentiment(self, text: str) -> float:
        """
        Analyzes sentiment of a text using BERT.
        Returns score between -1.0 (Negative) and 1.0 (Positive).
        """
        result = self.bert_analyzer.analyze(text)
        return result["score"]

    def get_market_sentiment(self) -> Dict:
        """
        Calculates overall market sentiment from recent news.
        """
        news = self.fetch_news(limit=30)
        if not news:
            return {"score": 0.0, "label": "Neutral", "news_count": 0}

        total_score = 0.0
        count = 0

        for item in news:
            # Analyze title and summary
            text = f"{item['title']} {item['summary']}"
            score = self.analyze_sentiment(text)
            total_score += score
            count += 1

        avg_score = total_score / count if count > 0 else 0.0

        # Determine Label
        if avg_score > 0.15:
            label = "Positive"
        elif avg_score < -0.15:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "score": avg_score,
            "label": label,
            "news_count": count,
            "top_news": news[:5],
        }

    def _init_database(self):
        """
        Initializes sentiment history database with index.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sentiment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    score REAL NOT NULL,
                    label TEXT NOT NULL,
                    news_count INTEGER NOT NULL
                )
            """
            )
            # Add index for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON sentiment_history(timestamp)
            """
            )

    def save_sentiment_history(self, sentiment_data: Dict):
        """
        Saves sentiment data to the database with current timestamp.

        Args:
            sentiment_data: Dictionary containing 'score', 'label', 'news_count'

        Raises:
            KeyError: If required keys are missing from sentiment_data
        """
        required_keys = ["score", "label", "news_count"]
        if not all(key in sentiment_data for key in required_keys):
            raise KeyError(f"sentiment_data must contain: {required_keys}")

        timestamp = datetime.datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sentiment_history (timestamp, score, label, news_count)
                VALUES (?, ?, ?, ?)
            """,
                (
                    timestamp,
                    sentiment_data["score"],
                    sentiment_data["label"],
                    sentiment_data["news_count"],
                ),
            )

    def get_sentiment_history(self, days: int = 7) -> List[Dict]:
        """
        Retrieves sentiment history for the specified number of days.

        Args:
            days: Number of days to retrieve (default: 7)

        Returns:
            List of dictionaries containing timestamp, score, label, news_count
        """
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, score, label, news_count
                FROM sentiment_history
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """,
                (cutoff_date,),
            )

            rows = cursor.fetchall()

        return [
            {
                "timestamp": row[0],
                "score": row[1],
                "label": row[2],
                "news_count": row[3],
            }
            for row in rows
        ]


if __name__ == "__main__":
    sa = SentimentAnalyzer()
    sentiment = sa.get_market_sentiment()
    print(f"Market Sentiment: {sentiment['label']} (Score: {sentiment['score']:.2f})")
    print("Top News:")
    for news in sentiment["top_news"]:
        print(f"- {news['title']}")
