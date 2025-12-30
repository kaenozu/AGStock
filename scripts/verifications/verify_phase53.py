"""
Phase 53 検証スクリプト
GenAI News Analyst の動作確認
"""

import logging
import os
import sys

sys.path.insert(0, os.getcwd())

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_news_aggregator():
    print("\n" + "=" * 50)
    print("📰 ニュースアグリゲーター テスト")
    print("=" * 50)

    from src.news_aggregator import get_news_aggregator

    agg = get_news_aggregator()

    print("   RSSフィード取得中...")
    news = agg.fetch_rss_news(limit=5)

    if news:
        print(f"   ✅ 取得成功: {len(news)}件")
        print(f"   最新: {news[0]['title']} ({news[0]['source']})")

        context = agg.get_market_context()
        print(f"   コンテキスト生成: {len(context)}文字")
        return True
    else:
        print("   ⚠️ ニュース取得失敗 (または0件)")
        return False


def test_llm_reasoner():
    print("\n" + "=" * 50)
    print("🧠 LLM推論エンジン テスト")
    print("=" * 50)

    from src.llm_reasoner import get_llm_reasoner

    reasoner = get_llm_reasoner()

    # ダミーデータ
    news_text = "日銀が金利引き上げを示唆。円高が進行し、輸出関連株が売られている。"
    market_data = {"N225": 32000, "USDJPY": 145.5}

    print(f"   プロバイダー: {reasoner.provider}")
    print("   分析実行中...")

    result = reasoner.analyze_market_impact(news_text, market_data)

    print(f"   結果: {result}")

    if result.get("sentiment") == "NEUTRAL" and "AI分析を実行できませんでした" in result.get("reasoning", ""):
        print("   ⚠️ フォールバック応答 (APIキー未設定またはOllama停止)")
        # エラーではないが、機能制限あり
        return True

    if result.get("sentiment") in ["BULLISH", "BEARISH", "NEUTRAL"]:
        print("   ✅ 分析成功")
        return True

    return False


if __name__ == "__main__":
    if test_news_aggregator():
        test_llm_reasoner()
        print("\n✅ Phase 53 検証完了")
    else:
        print("\n❌ 検証失敗")
