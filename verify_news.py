"""
Verify AI News Analysis
1. Fetch news via NewsCollector
2. Analyze via LLMReasoner
"""
import logging
from src.news_collector import get_news_collector
from src.llm_reasoner import get_llm_reasoner

# Setup simplified logging
logging.basicConfig(level=logging.INFO)

def verify_news_analysis():
    print("--- 1. Testing NewsCollector ---")
    collector = get_news_collector()
    news = collector.fetch_market_news(limit=3)
    
    if not news:
        print("⚠️ No news fetched. Check network or RSS URL.")
        # Proceed with mock news for LLM test if fetch fails
        news = [
            {'title': 'Toyota posts record profit', 'published': '2025-12-09', 'summary': 'Strong sales in US.'},
            {'title': 'Nikkei 225 drops 2%', 'published': '2025-12-09', 'summary': 'Tech sell-off.'}
        ]
    else:
        print(f"✅ Fetched {len(news)} items.")
        print(f"Sample: {news[0]['title']}")
        
    print("\n--- 2. Testing LLM Reasoner (News Analysis) ---")
    reasoner = get_llm_reasoner()
    
    # Check if API Key is present (Gemini) or Ollama is running
    print(f"Provider: {reasoner.provider}")
    
    try:
        result = reasoner.analyze_news_sentiment(news)
        print("✅ Analysis Result:")
        print(result)
        
        if "sentiment_score" in result:
            print("✅ JSON Structure Valid.")
            return True
        else:
            print("❌ JSON Key missing.")
            return False
            
    except Exception as e:
        print(f"❌ Analysis Failed: {e}")
        return False

if __name__ == "__main__":
    verify_news_analysis()
