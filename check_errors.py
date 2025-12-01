"""
エラー確認スクリプト

Streamlitアプリの潜在的なエラーをチェック
"""
import sys
import traceback

print("="*60)
print("AGStock エラーチェック")
print("="*60)

# 1. インポートテスト
print("\n1. インポートテスト...")
try:
    from src.data_loader import fetch_stock_data, get_latest_price
    print("✅ data_loader: OK")
except Exception as e:
    print(f"❌ data_loader: {e}")
    traceback.print_exc()

try:
    from src.strategies import SMACrossoverStrategy
    print("✅ strategies: OK")
except Exception as e:
    print(f"❌ strategies: {e}")
    traceback.print_exc()

try:
    from src.paper_trader import PaperTrader
    print("✅ paper_trader: OK")
except Exception as e:
    print(f"❌ paper_trader: {e}")
    traceback.print_exc()

try:
    from src.sentiment import SentimentAnalyzer
    print("✅ sentiment: OK")
except Exception as e:
    print(f"❌ sentiment: {e}")
    traceback.print_exc()

# 2. アプリインポート
print("\n2. アプリファイルインポート...")
try:
    import app
    print("✅ app.py: OK")
except Exception as e:
    print(f"❌ app.py: {e}")
    traceback.print_exc()

print("\n" + "="*60)
print("チェック完了")
print("="*60)
