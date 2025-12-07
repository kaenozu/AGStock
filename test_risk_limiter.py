"""
リスク制限テストスクリプト

risk_limiterの動作確認
"""
from src.risk_limiter import RiskLimiter


def test_all_checks():
    """全チェック機能テスト"""
    print("\n" + "="*70)
    print("🧪 リスク制限テスト")
    print("="*70)
    
    limiter = RiskLimiter("config_test.json")
    
    # リスク設定表示
    print(limiter.get_risk_report())
    
    # テストケース1: 正常ケース
    print("\n" + "="*70)
    print("テスト1: 正常な取引")
    print("="*70)
    
    trade = {
        "position_value": 4000  # 4%
    }
    
    portfolio = {
        "total_equity": 100000,
        "trades_today": 0,
        "daily_pnl_pct": -0.5,
        "invested_amount": 50000,
        "cash": 50000,
        "total_pnl_pct": -1.0,
        "initial_capital": 100000
    }
    
    passed, checks = limiter.validate_trade(trade, portfolio)
    print(f"\n結果: {'✅ 合格' if passed else '❌ 不合格'}")
    for check in checks:
        if check != "OK":
            print(f"  {check}")
    
    # テストケース2: ポジションサイズ超過
    print("\n" + "="*70)
    print("テスト2: ポジションサイズ超過")
    print("="*70)
    
    trade = {
        "position_value": 6000  # 6% - 上限5%超過
    }
    
    passed, checks = limiter.validate_trade(trade, portfolio)
    print(f"\n結果: {'✅ 合格' if passed else '❌ 不合格（想定通り）'}")
    for check in checks:
        if check != "OK":
            print(f"  {check}")
    
    # テストケース3: 日次損失超過
    print("\n" + "="*70)
    print("テスト3: 日次損失超過")
    print("="*70)
    
    trade = {"position_value": 4000}
    portfolio["daily_pnl_pct"] = -2.5  # -2%超過
    
    passed, checks = limiter.validate_trade(trade, portfolio)
    print(f"\n結果: {'✅ 合格' if passed else '❌ 不合格（想定通り）'}")
    for check in checks:
        if check != "OK":
            print(f"  {check}")
    
    # テストケース4: 緊急停止発動
    print("\n" + "="*70)
    print("テスト4: 緊急停止発動")
    print("="*70)
    
    portfolio["daily_pnl_pct"] = -1.0
    portfolio["total_pnl_pct"] = -6.0  # -5%超過
    
    passed, checks = limiter.validate_trade(trade, portfolio)
    print(f"\n結果: {'✅ 合格' if passed else '🚨 緊急停止（想定通り）'}")
    for check in checks:
        if check != "OK":
            print(f"  {check}")
    
    # テストケース5: 現金不足
    print("\n" + "="*70)
    print("テスト5: 現金不足")
    print("="*70)
    
    portfolio["total_pnl_pct"] = -1.0
    portfolio["cash"] = 30000  # 30% - 最低40%不足
    
    passed, checks = limiter.validate_trade(trade, portfolio)
    print(f"\n結果: {'✅ 合格' if passed else '❌ 不合格（想定通り）'}")
    for check in checks:
        if check != "OK":
            print(f"  {check}")
    
    print("\n" + "="*70)
    print("✅ 全テスト完了")
    print("="*70)


def test_error_handler():
    """エラーハンドラーテスト"""
    print("\n" + "="*70)
    print("🧪 エラーハンドラーテスト")
    print("="*70)
    
    from src.error_handler import retry_on_error, safe_execute, CircuitBreaker
    
    # リトライテスト
    print("\nテスト1: リトライ機能")
    
    attempt_count = 0
    
    @retry_on_error(max_retries=2, delay=0.5)
    def sometimes_fails():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  試行{attempt_count}")
        if attempt_count < 2:
            raise Exception("意図的なエラー")
        return "成功"
    
    try:
        result = sometimes_fails()
        print(f"✅ 結果: {result}")
    except:
        print("❌ 失敗（リトライ後）")
    
    # 安全実行テスト
    print("\nテスト2: 安全実行")
    
    def risky_function():
        raise ValueError("危険な操作")
    
    result = safe_execute(lambda: risky_function(), default="デフォルト値")
    print(f"✅ デフォルト値を返却: {result}")
    
    # サーキットブレーカーテスト
    print("\nテスト3: サーキットブレーカー")
    
    cb = CircuitBreaker(failure_threshold=3, timeout=2.0)
    failure_count = 0
    
    def failing_operation():
        nonlocal failure_count
        failure_count += 1
        raise Exception(f"失敗{failure_count}")
    
    for i in range(5):
        try:
            cb.call(failing_operation)
        except Exception as e:
            print(f"  試行{i+1}: {e}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_all_checks()
    test_error_handler()
