"""
Phase 51 効果検証スクリプト
各モジュールの動作確認と効果測定
"""
import time
import sys
import os
sys.path.insert(0, os.getcwd())

def test_module(name, test_func):
    """モジュールテスト"""
    print(f"\n{'='*50}")
    print(f"🧪 {name}")
    print('='*50)
    try:
        start = time.time()
        result = test_func()
        elapsed = time.time() - start
        print(f"✅ 成功 ({elapsed:.2f}秒)")
        return True, result
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False, None


def test_attention_selector():
    """アテンション特徴選択テスト"""
    from src.attention_selector import get_attention_selector
    from src.data_loader import fetch_stock_data
    
    selector = get_attention_selector()
    data = fetch_stock_data(["7203.T"], period="6mo")
    df = data.get("7203.T")
    
    # アテンション計算
    attention = selector.compute_temporal_attention(df)
    print(f"   アテンション重み: {len(attention)}件")
    print(f"   最大重み位置: {attention.argmax()} (最新={len(attention)-1})")
    
    # 特徴選択
    features = selector.select_important_features(df, n_features=10)
    print(f"   選択特徴量: {len(features)}件")
    
    return {"attention_shape": len(attention), "features": len(features)}


def test_multi_task_learner():
    """マルチタスク学習テスト"""
    from src.multi_task_learner import get_multi_task_predictor
    from src.data_loader import fetch_stock_data
    
    predictor = get_multi_task_predictor()
    data = fetch_stock_data(["7203.T"], period="1y")
    df = data.get("7203.T")
    
    result = predictor.predict_multi_task(df, days_ahead=5)
    
    if "error" not in result:
        print(f"   トレンド: {result['trend']}")
        print(f"   方向確率: {result['direction_probability']:.1%}")
        print(f"   予想変化: {result['expected_change_pct']:+.2f}%")
        print(f"   予想ボラ: {result['expected_volatility']:.4f}")
    else:
        print(f"   エラー: {result['error']}")
    
    return result


def test_external_data():
    """外部データテスト"""
    from src.external_data import get_external_data
    
    provider = get_external_data()
    indicators = provider.get_economic_indicators()
    
    print(f"   取得指標数: {len(indicators)}")
    for key, value in indicators.items():
        if isinstance(value, dict) and 'current' in value:
            print(f"   {key}: {value['current']:.2f}")
    
    sentiment = provider.get_market_sentiment_score()
    print(f"   市場センチメント: {sentiment:+.2f}")
    
    return {"indicators": len(indicators), "sentiment": sentiment}


def test_async_fetcher():
    """非同期データ取得テスト"""
    from src.async_fetcher import get_async_fetcher
    
    fetcher = get_async_fetcher()
    tickers = ["7203.T", "6758.T", "9984.T", "8306.T"]
    
    start = time.time()
    data = fetcher.fetch_multiple_sync(tickers, period="1mo")
    elapsed = time.time() - start
    
    print(f"   取得銘柄: {len(data)}/{len(tickers)}")
    print(f"   並列取得時間: {elapsed:.2f}秒")
    print(f"   平均/銘柄: {elapsed/len(tickers):.2f}秒")
    
    return {"fetched": len(data), "time": elapsed}


def test_persistent_cache():
    """永続キャッシュテスト"""
    from src.persistent_cache import get_persistent_cache
    
    cache = get_persistent_cache()
    
    # テストデータ保存
    test_key = "test_key_12345"
    test_value = {"test": True, "value": 42}
    
    cache.set(test_key, test_value)
    retrieved = cache.get(test_key)
    
    print(f"   保存成功: {retrieved == test_value}")
    
    stats = cache.get_stats()
    print(f"   キャッシュ件数: {stats['total_entries']}")
    
    # クリーンアップ
    cache.delete(test_key)
    
    return stats


def test_lazy_loader():
    """遅延ローダーテスト"""
    from src.lazy_loader import get_lazy_loader
    
    loader = get_lazy_loader()
    status = loader.get_status()
    
    print(f"   登録モデル: {len(status['registered'])}")
    print(f"   ロード済み: {len(status['loaded'])}")
    print(f"   未ロード: {len(status['unloaded'])}")
    
    # 1つロード
    start = time.time()
    lgbm = loader.get('lgbm')
    elapsed = time.time() - start
    
    print(f"   LGBMロード時間: {elapsed:.2f}秒")
    print(f"   LGBMロード成功: {lgbm is not None}")
    
    return {"registered": len(status['registered']), "loaded": len(status['loaded']) + 1}


def test_data_augmenter():
    """データ拡張テスト"""
    from src.data_augmenter import get_augmenter
    from src.data_loader import fetch_stock_data
    
    augmenter = get_augmenter()
    data = fetch_stock_data(["7203.T"], period="3mo")
    df = data.get("7203.T")
    
    original_len = len(df)
    augmented = augmenter.add_noise(df, n_copies=2)
    
    print(f"   元データ: {original_len}行")
    print(f"   拡張後: {len(augmented)}行")
    print(f"   増加倍率: {len(augmented)/original_len:.1f}x")
    
    return {"original": original_len, "augmented": len(augmented)}


def test_ensemble_predictor():
    """アンサンブル予測テスト（統合）"""
    from src.enhanced_ensemble_predictor import EnhancedEnsemblePredictor
    from src.data_loader import fetch_stock_data

    predictor = EnhancedEnsemblePredictor()
    data = fetch_stock_data(["7203.T"], period="1y")
    df = data.get("7203.T")
    
    start = time.time()
    result = predictor.predict_trajectory(df, days_ahead=5, ticker="7203.T")
    elapsed = time.time() - start
    
    if "error" not in result:
        print(f"   トレンド: {result['trend']}")
        print(f"   予想変化: {result.get('change_pct', 0):+.2f}%")
        print(f"   予測時間: {elapsed:.2f}秒")
    
    return {"trend": result.get('trend'), "time": elapsed}


def test_intelligent_selector():
    """インテリジェントセレクターテスト"""
    from src.intelligent_auto_selector import get_auto_selector
    from src.data_loader import fetch_stock_data
    
    selector = get_auto_selector()
    data = fetch_stock_data(["7203.T"], period="1y")
    df = data.get("7203.T")
    
    start = time.time()
    result = selector.get_best_prediction(df, "7203.T")
    elapsed = time.time() - start
    
    if "error" not in result:
        auto_info = result.get('auto_selector', {})
        print(f"   トレンド: {result['trend']}")
        print(f"   信頼度: {auto_info.get('confidence_score', 0):.0%}")
        print(f"   レベル: {auto_info.get('confidence_level', 'N/A')}")
        print(f"   推奨: {auto_info.get('recommendation', 'N/A')[:30]}...")
        print(f"   予測時間: {elapsed:.2f}秒")
    
    return result


def main():
    print("\n" + "="*60)
    print("🔬 Phase 48-51 効果検証レポート")
    print("="*60)
    
    results = {}
    
    # 各モジュールテスト
    tests = [
        ("アテンション特徴選択", test_attention_selector),
        ("マルチタスク学習", test_multi_task_learner),
        ("外部経済データ", test_external_data),
        ("非同期データ取得", test_async_fetcher),
        ("永続キャッシュ (SQLite)", test_persistent_cache),
        ("遅延モデルローダー", test_lazy_loader),
        ("データ拡張", test_data_augmenter),
        ("アンサンブル予測", test_ensemble_predictor),
        ("インテリジェントセレクター", test_intelligent_selector),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        success, result = test_module(name, test_func)
        if success:
            passed += 1
            results[name] = result
        else:
            failed += 1
    
    # サマリー
    print("\n" + "="*60)
    print("📊 検証結果サマリー")
    print("="*60)
    print(f"✅ 成功: {passed}/{len(tests)}")
    print(f"❌ 失敗: {failed}/{len(tests)}")
    print(f"📈 成功率: {passed/len(tests)*100:.0f}%")
    
    if failed == 0:
        print("\n🎉 全モジュールが正常に動作しています！")
    else:
        print(f"\n⚠️ {failed}件のモジュールで問題が発生しました")
    
    return results


if __name__ == "__main__":
    main()
