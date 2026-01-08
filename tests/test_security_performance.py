"""
セキュリティとパフォーマンスの包括的テストスイート
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import tempfile
import os
import json
import logging

logger = logging.getLogger(__name__)

# テスト対象モジュール
from src.security.secure_config import SecureConfigManager, validate_input_data
from src.security.secure_data_manager import SecureDataManager
from src.security.risk_manager import RiskManager, TradingState, RiskLevel
from src.security.input_validator import InputValidator, RateLimiter
from src.security.error_handling import ErrorHandler, MemoryManager, BaseTradingError, ErrorCategory, ErrorSeverity
from src.performance.async_processor import AsyncAPIClient, CacheManager, DataProcessor, APIResponse, APIRequest


class TestSecureConfigManager:
    """セキュア設定マネージャーのテスト"""

    @pytest.fixture
    def temp_config(self):
        """一時設定ファイル"""
        config_data = {
            "risk": {"max_position_size": 0.1},
            "auto_trading": {"max_daily_trades": 3},
            "gemini_api_key": "",  # 空で安全
            "openai_api_key": "",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    def test_load_config_success(self, temp_config):
        """設定読み込み成功テスト"""
        manager = SecureConfigManager(temp_config)
        config = manager.load_config()

        assert "risk" in config
        assert "auto_trading" in config
        assert config["risk"]["max_position_size"] == 0.1

    def test_load_config_file_not_found(self):
        """設定ファイル不在テスト"""
        manager = SecureConfigManager("nonexistent.json")

        with pytest.raises(FileNotFoundError):
            manager.load_config()

    def test_load_config_invalid_json(self):
        """無効JSONテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            manager = SecureConfigManager(temp_path)
            with pytest.raises(ValueError, match="無効なJSON形式"):
                manager.load_config()
        finally:
            os.unlink(temp_path)

    def test_get_api_key_from_env(self, temp_config):
        """環境変数からAPIキー取得テスト"""
        manager = SecureConfigManager(temp_config)

        # 環境変数を設定
        os.environ["AGSTOCK_GEMINI_API_KEY"] = "test_key_123"

        try:
            api_key = manager.get_api_key("gemini")
            assert api_key == "test_key_123"
        finally:
            os.environ.pop("AGSTOCK_GEMINI_API_KEY", None)

    def test_get_api_key_not_set(self, temp_config):
        """APIキー未設定テスト"""
        manager = SecureConfigManager(temp_config)

        with pytest.raises(ValueError, match="APIキーが設定されていません"):
            manager.get_api_key("gemini")

    def test_hardcoded_api_key_detection(self, temp_config):
        """ハードコードAPIキー検出テスト"""
        # 環境変数が設定されている場合はスキップされる可能性があるため、一時的にクリア
        import os
        old_allow = os.getenv("AGSTOCK_ALLOW_HARDCODED_KEYS")
        if old_allow:
            del os.environ["AGSTOCK_ALLOW_HARDCODED_KEYS"]
            
        try:
            # ハードコードされたAPIキーを含む設定
            config_data = {
                "risk": {"max_position_size": 0.1},
                "gemini_api_key": "hardcoded_key_123",  # ハードコード
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                temp_path = f.name

            manager = SecureConfigManager(temp_path)
            with pytest.raises(ValueError, match="APIキーは環境変数で管理してください"):
                manager.load_config()
        finally:
            if old_allow:
                os.environ["AGSTOCK_ALLOW_HARDCODED_KEYS"] = old_allow
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestInputValidator:
    """入力検証テスト"""

    def test_validate_ticker_success(self):
        """ティッカー検証成功テスト"""
        validator = InputValidator()
        result = validator.validate_ticker("AAPL")

        assert result.is_valid
        assert result.sanitized_data == "AAPL"
        assert len(result.errors) == 0

    def test_validate_ticker_invalid_format(self):
        """ティッカー無効形式テスト"""
        validator = InputValidator()
        result = validator.validate_ticker("INVALID@TICKER")

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_ticker_too_long(self):
        """ティッカー長すぎテスト"""
        validator = InputValidator()
        result = validator.validate_ticker("TOOLONGTICKER")

        assert not result.is_valid
        assert any("長すぎます" in error for error in result.errors)

    def test_validate_price_success(self):
        """価格検証成功テスト"""
        validator = InputValidator()
        result = validator.validate_price("123.45")

        assert result.is_valid
        assert result.sanitized_data == 123.45

    def test_validate_price_invalid_format(self):
        """価格無効形式テスト"""
        validator = InputValidator()
        result = validator.validate_price("invalid_price")

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_price_out_of_range(self):
        """価格範囲外テスト"""
        validator = InputValidator()
        result = validator.validate_price(-10.0)

        assert not result.is_valid
        assert any("低すぎます" in error for error in result.errors)

    def test_validate_quantity_success(self):
        """数量検証成功テスト"""
        validator = InputValidator()
        result = validator.validate_quantity("100")

        assert result.is_valid
        assert result.sanitized_data == 100

    def test_validate_quantity_not_integer(self):
        """数量整数以外テスト"""
        validator = InputValidator()
        result = validator.validate_quantity("100.5")

        assert not result.is_valid
        assert any("整数である必要があります" in error for error in result.errors)

    def test_validate_json_data_success(self):
        """JSONデータ検証成功テスト"""
        validator = InputValidator()
        test_data = {"ticker": "AAPL", "price": 123.45}

        result = validator.validate_json_data(test_data)

        assert result.is_valid
        assert result.sanitized_data == test_data

    def test_validate_json_data_invalid_json(self):
        """JSON無効形式テスト"""
        validator = InputValidator()
        result = validator.validate_json_data('{"invalid": json}')

        assert not result.is_valid
        assert any("無効なJSON形式" in error for error in result.errors)


class TestRateLimiter:
    """レートリミッターテスト"""

    def test_rate_limiter_basic(self):
        """レートリミッター基本機能テスト"""
        limiter = RateLimiter(max_requests_per_second=2, max_requests_per_minute=10)

        # 2リクエストは許可
        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client1")

        # 3リクエスト目は拒否
        assert not limiter.is_allowed("client1")

    def test_rate_limiter_different_clients(self):
        """異なるクライアントテスト"""
        limiter = RateLimiter(max_requests_per_second=1)

        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client2")  # 異なるクライアントは許可

    def test_get_remaining_requests(self):
        """残りリクエスト数取得テスト"""
        limiter = RateLimiter(max_requests_per_second=3)

        remaining = limiter.get_remaining_requests("client1")
        assert remaining == 3

        limiter.is_allowed("client1")
        remaining = limiter.get_remaining_requests("client1")
        assert remaining == 2


class TestRiskManager:
    """リスクマネージャーテスト"""

    def test_evaluate_trade_risk_success(self):
        """取引リスク評価成功テスト"""
        manager = RiskManager()

        can_trade, reason, risk_level = manager.evaluate_trade_risk(
            "AAPL", "buy", 100, 150.0
        )

        assert can_trade
        assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_evaluate_trade_risk_invalid_params(self):
        """無効パラメータテスト"""
        manager = RiskManager()

        can_trade, reason, risk_level = manager.evaluate_trade_risk(
            "",
            "buy",
            100,
            150.0,  # 空のティッカー
        )

        assert not can_trade
        assert risk_level == RiskLevel.CRITICAL

    def test_circuit_breaker_trigger(self):
        """サーキットブレーカー作動テスト"""
        manager = RiskManager()

        # 緊急停止をトリガー
        manager.emergency_stop("テスト緊急停止")

        summary = manager.get_risk_summary()
        assert summary["trading_state"] == TradingState.EMERGENCY_STOP.value
        assert not summary["can_trade"]

    def test_update_metrics(self):
        """メトリクス更新テスト"""
        manager = RiskManager()

        trade_result = {"timestamp": datetime.now().isoformat(), "pnl": 1000.0}

        manager.update_metrics(trade_result)

        summary = manager.get_risk_summary()
        assert summary["daily_pnl"] == 1000.0


class TestErrorHandler:
    """エラーハンドラーテスト"""

    def test_handle_base_trading_error(self):
        """基本取引エラーハンドリングテスト"""
        handler = ErrorHandler()

        error = BaseTradingError(
            "テストエラー", ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM
        )

        error_info = handler.handle_error(error)

        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.exception == error

    def test_handle_regular_exception(self):
        """通常例外ハンドリングテスト"""
        handler = ErrorHandler()

        exception = ValueError("テスト値エラー")
        error_info = handler.handle_error(exception)

        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.exception == exception

    def test_error_stats(self):
        """エラー統計テスト"""
        handler = ErrorHandler()

        # 複数のエラーを処理
        for i in range(5):
            handler.handle_error(ValueError(f"テストエラー{i}"))

        stats = handler.get_error_stats(hours=24)
        assert stats["total_errors"] == 5
        assert "by_category" in stats
        assert "by_severity" in stats


class TestMemoryManager:
    """メモリマネージャーテスト"""

    def test_get_memory_info(self):
        """メモリ情報取得テスト"""
        manager = MemoryManager()

        info = manager.get_memory_info()

        assert "rss_mb" in info
        assert "vms_mb" in info
        assert "percent" in info
        assert info["rss_mb"] > 0

    def test_cache_operations(self):
        """キャッシュ操作テスト"""
        manager = MemoryManager()

        test_obj = {"data": "test"}
        manager.cache_object("test_key", test_obj)

        retrieved = manager.get_cached_object("test_key")
        assert retrieved == test_obj

    def test_cleanup_callback(self):
        """クリーンアップコールバックテスト"""
        manager = MemoryManager()
        callback_called = False

        def test_callback():
            nonlocal callback_called
            callback_called = True

        manager.register_cleanup_callback(test_callback)
        manager.cleanup_memory()

        assert callback_called


class TestCacheManager:
    """キャッシュマネージャーテスト"""

    def test_cache_set_get(self):
        """キャッシュ設定・取得テスト"""
        cache = CacheManager(max_size=10, default_ttl=1)

        cache.set("test_key", "test_value")
        value = cache.get("test_key")

        assert value == "test_value"

    def test_cache_expiry(self):
        """キャッシュ期限切れテスト"""
        cache = CacheManager(default_ttl=1)

        cache.set("test_key", "test_value", ttl=0.1)  # 0.1秒
        time.sleep(0.2)

        value = cache.get("test_key")
        assert value is None

    def test_cache_eviction(self):
        """キャッシュ追い出しテスト"""
        cache = CacheManager(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # 追い出し発生

        # 最も古いキーが追い出される
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_stats(self):
        """キャッシュ統計テスト"""
        cache = CacheManager()

        cache.set("key1", "value1")
        cache.get("key1")  # ヒット
        cache.get("key2")  # ミス

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1


@pytest.mark.asyncio
class TestAsyncAPIClient:
    """非同期APIクライアントテスト"""

    async def test_api_request_success(self):
        """APIリクエスト成功テスト"""
        client = AsyncAPIClient()

        # モックレスポンス
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.text = AsyncMock(return_value='{"data": "test"}')
        mock_response.read = AsyncMock(return_value=b'{"data": "test"}')

        with patch("aiohttp.ClientSession.request") as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response

            from src.performance.async_processor import APIRequest

            request = APIRequest(url="https://api.example.com/test")

            response = await client.request(request)

            assert response.status_code == 200
            assert response.data == {"data": "test"}
            assert not response.cached

        await client.close()

    async def test_api_request_with_cache(self):
        """APIリクエストキャッシュテスト"""
        client = AsyncAPIClient()

        # モックレスポンス
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.text = AsyncMock(return_value='{"data": "test"}')
        mock_response.read = AsyncMock(return_value=b'{"data": "test"}')

        with patch("aiohttp.ClientSession.request") as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response

            from src.performance.async_processor import APIRequest

            request = APIRequest(url="https://api.example.com/test", cache_ttl=300)

            # 1回目のリクエスト
            response1 = await client.request(request)
            assert not response1.cached

            # 2回目のリクエスト（キャッシュヒット）
            response2 = await client.request(request)
            assert response2.cached
            assert response2.data == response1.data

        await client.close()

    async def test_batch_requests(self):
        """バッチリクエストテスト"""
        client = AsyncAPIClient()

        # モックレスポンス
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.text = AsyncMock(return_value='{"data": "test"}')
        mock_response.read = AsyncMock(return_value=b'{"data": "test"}')

        with patch("aiohttp.ClientSession.request") as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response

            from src.performance.async_processor import APIRequest

            requests = [
                APIRequest(url="https://api.example.com/test1"),
                APIRequest(url="https://api.example.com/test2"),
            ]

            responses = await client.batch_requests(requests)

            assert len(responses) == 2
            assert all(isinstance(r, APIResponse) for r in responses)

        await client.close()


@pytest.mark.asyncio
class TestDataProcessor:
    """データプロセッサーテスト"""

    async def test_start_stop_processing(self):
        """処理開始・停止テスト"""
        processor = DataProcessor(max_workers=2)

        await processor.start_processing()
        assert processor._processing

        await processor.stop_processing()
        assert not processor._processing

    async def test_submit_task(self):
        """タスク送信テスト"""
        processor = DataProcessor(max_workers=2)
        await processor.start_processing()

        async def test_task(x):
            return x * 2

        result = await processor.submit_task(test_task, 5)
        assert result == 10

        await processor.stop_processing()


class TestIntegration:
    """統合テスト"""

    def test_security_integration(self):
        """セキュリティ統合テスト"""
        # 設定マネージャー
        config_manager = SecureConfigManager()

        # 入力検証
        validator = InputValidator()
        result = validator.validate_ticker("AAPL")
        assert result.is_valid

        # リスク管理
        risk_manager = RiskManager()
        can_trade, _, _ = risk_manager.evaluate_trade_risk("AAPL", "buy", 100, 150.0)
        assert can_trade

    @pytest.mark.asyncio
    async def test_performance_integration(self):
        """パフォーマンス統合テスト"""
        # APIクライアント
        client = AsyncAPIClient()

        # キャッシュマネージャー
        cache = CacheManager()
        cache.set("test", "value")
        assert cache.get("test") == "value"

        # データプロセッサー
        processor = DataProcessor()
        await processor.start_processing()

        # クリーンアップ
        await processor.stop_processing()
        await client.close()


# パフォーマンステスト
class TestPerformance:
    """パフォーマンステスト"""

    def test_input_validation_performance(self):
        """入力検証パフォーマンステスト"""
        validator = InputValidator()

        start_time = time.time()

        for i in range(1000):
            validator.validate_ticker(f"AAPL{i % 100}")

        elapsed = time.time() - start_time
        assert elapsed < 1.0  # 1秒以内

        logger.info(f"入力検証パフォーマンス: {elapsed:.3f}秒 (1000回)")

    def test_cache_performance(self):
        """キャッシュパフォーマンステスト"""
        cache = CacheManager(max_size=10000)

        # キャッシュ設定
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key{i}", f"value{i}")
        set_time = time.time() - start_time

        # キャッシュ取得
        start_time = time.time()
        for i in range(1000):
            cache.get(f"key{i}")
        get_time = time.time() - start_time

        assert set_time < 0.5
        assert get_time < 0.1

        logger.info(
            f"キャッシュパフォーマンス - 設定: {set_time:.3f}秒, 取得: {get_time:.3f}秒"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
