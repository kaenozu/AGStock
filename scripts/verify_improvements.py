#!/usr/bin/env python
"""改善実装の検証スクリプト
"""

import sys
import time
from datetime import datetime

def check_import(module_path: str, items: list) -> bool:
    """モジュールインポートをチェック"""
    try:
        module = __import__(module_path, fromlist=items)
        for item in items:
            getattr(module, item)
        return True
    except Exception as e:
        print(f"  ❌ {module_path}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 AGStock 改善実装検証")
    print(f"検証日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    results = {"passed": 0, "failed": 0}
    
    # 1. 機能改善
    print("🚀 1. 機能改善")
    print("-" * 40)
    
    features = [
        ("src.features.earnings_calendar", ["EarningsCalendar", "get_earnings_calendar"]),
        ("src.features.sentiment_indicators", ["SentimentIndicators", "get_sentiment_indicators"]),
        ("src.features.drip", ["DRIPManager", "get_drip_manager"]),
        ("src.features.tax_optimizer", ["TaxOptimizer", "get_tax_optimizer"]),
        ("src.features.sector_rotation", ["SectorRotation", "get_sector_rotation"]),
    ]
    
    for module, items in features:
        name = module.split(".")[-1]
        if check_import(module, items):
            print(f"  ✅ {name}")
            results["passed"] += 1
        else:
            results["failed"] += 1
    print()
    
    # 2. 性能改善
    print("⚡ 2. 性能改善")
    print("-" * 40)
    
    improvements = [
        ("src.improvements.memory_cache", ["MemoryCache", "cached", "get_memory_cache"]),
        ("src.improvements.settings", ["AGStockSettings", "get_settings"]),
        ("src.improvements.numba_utils", ["fast_sma", "fast_rsi", "fast_macd"]),
    ]
    
    for module, items in improvements:
        name = module.split(".")[-1]
        if check_import(module, items):
            print(f"  ✅ {name}")
            results["passed"] += 1
        else:
            results["failed"] += 1
    print()
    
    # 3. UI/UX改善
    print("🎨 3. UI/UX改善")
    print("-" * 40)
    
    ui_modules = [
        ("src.ui.components.quick_overview", ["render_quick_overview"]),
        ("src.ui.components.trade_heatmap", ["render_trade_heatmap", "render_monthly_performance"]),
        ("src.ui.shortcuts", ["KeyboardShortcuts"]),
        ("src.ui.features_hub", ["render_features_hub"]),
    ]
    
    for module, items in ui_modules:
        name = module.split(".")[-1]
        if check_import(module, items):
            print(f"  ✅ {name}")
            results["passed"] += 1
        else:
            results["failed"] += 1
    print()
    
    # 4. 保守性改善
    print("🛠️ 4. 保守性改善")
    print("-" * 40)
    
    maintenance = [
        ("src.trading.market_scanner", ["MarketScanner", "ScanResult"]),
    ]
    
    for module, items in maintenance:
        name = module.split(".")[-1]
        if check_import(module, items):
            print(f"  ✅ {name}")
            results["passed"] += 1
        else:
            results["failed"] += 1
    print()
    
    # 5. メモリキャッシュテスト
    print("💾 5. メモリキャッシュテスト")
    print("-" * 40)
    
    try:
        from src.improvements.memory_cache import get_memory_cache
        cache = get_memory_cache()
        
        # ベンチマーク
        start = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
            cache.get(f"key_{i}")
        elapsed = time.time() - start
        
        print(f"  ✅ 1000回のset/get: {elapsed*1000:.2f}ms")
        print(f"  ✅ キャッシュヒット率: {cache.info()['hit_rate']:.1%}")
        results["passed"] += 1
        cache.flushall()
    except Exception as e:
        print(f"  ❌ キャッシュテスト失敗: {e}")
        results["failed"] += 1
    print()
    
    # サマリー
    print("=" * 60)
    print("📊 検証結果")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    print(f"✅ 成功: {results['passed']}/{total}")
    print(f"❌ 失敗: {results['failed']}/{total}")
    
    if results["failed"] == 0:
        print()
        print("🎉 全ての改善が正常に実装されています！")
        return 0
    else:
        print()
        print("⚠️ 一部の改善に問題があります")
        return 1

if __name__ == "__main__":
    sys.exit(main())
