"""metrics.pyのユニットテスト"""

import time
from unittest.mock import patch

from src.metrics import (MetricsCollector, MetricType,
                         get_global_metrics_collector, get_metric_value,
                         increment_counter, observe_histogram,
                         record_business_metric, set_gauge, time_execution)


class TestMetricsCollector:
    """MetricsCollectorのテスト"""

    def test_metrics_collector_initialization(self):
        """MetricsCollectorの初期化テスト"""
        collector = MetricsCollector()
        assert len(collector.get_all_metrics()) == 0
        assert len(collector.get_all_business_metrics()) == 0

    def test_increment_counter(self):
        """カウンターの増加テスト"""
        collector = MetricsCollector()

        # カウンターを増加
        collector.increment_counter("test_counter", description="Test counter")
        assert collector.get_metric("test_counter").value == 1

        # カウンターをさらに増加
        collector.increment_counter("test_counter", value=2)
        assert collector.get_metric("test_counter").value == 3

        # ラベル付きカウンター
        labels = {"type": "buy"}
        collector.increment_counter("trade_counter", labels=labels, value=5)
        metric = collector.get_metric("trade_counter", labels)
        assert metric.value == 5
        assert metric.labels == labels

    def test_set_gauge(self):
        """ゲージの設定テスト"""
        collector = MetricsCollector()

        # ゲージを設定
        collector.set_gauge("cpu_usage", 75.5, description="CPU usage percentage")
        assert collector.get_metric("cpu_usage").value == 75.5

        # ラベル付きゲージ
        labels = {"host": "server1"}
        collector.set_gauge("memory_usage", 80.0, labels=labels)
        metric = collector.get_metric("memory_usage", labels)
        assert metric.value == 80.0
        assert metric.labels == labels

    def test_observe_histogram(self):
        """ヒストグラムの観測テスト"""
        collector = MetricsCollector()

        # 単一の値を観測
        collector.observe_histogram("request_duration", 0.5, description="Request duration in seconds")
        metric = collector.get_metric("request_duration")
        assert metric.type == MetricType.HISTOGRAM
        assert metric.value == [0.5]

        # 複数の値を観測
        collector.observe_histogram("request_duration", 0.8)
        metric = collector.get_metric("request_duration")
        assert metric.value == [0.5, 0.8]

        # ラベル付きヒストグラム
        labels = {"endpoint": "/api/test"}
        collector.observe_histogram("api_duration", 1.2, labels=labels)
        metric = collector.get_metric("api_duration", labels)
        assert metric.value == [1.2]
        assert metric.labels == labels

    def test_record_business_metric(self):
        """ビジネス指標の記録テスト"""
        collector = MetricsCollector()

        # ビジネス指標を記録
        record_data = {"total_return": 0.12, "sharpe_ratio": 1.5}
        collector.record_business_metric(
            "strategy_performance", record_data, description="Strategy performance metrics"
        )

        business_metric = collector.get_business_metric("strategy_performance")
        assert business_metric["value"] == record_data
        assert business_metric["description"] == "Strategy performance metrics"
        assert "timestamp" in business_metric

    def test_get_metric_not_found(self):
        """存在しないメトリクスの取得テスト"""
        collector = MetricsCollector()
        metric = collector.get_metric("nonexistent_metric")
        assert metric is None

    def test_get_business_metric_not_found(self):
        """存在しないビジネス指標の取得テスト"""
        collector = MetricsCollector()
        business_metric = collector.get_business_metric("nonexistent_metric")
        assert business_metric is None

    def test_reset_metrics(self):
        """メトリクスのリセットテスト"""
        collector = MetricsCollector()

        # メトリクスを追加
        collector.increment_counter("test_counter")
        collector.record_business_metric("test_business_metric", "test_value")

        # リセット前
        assert len(collector.get_all_metrics()) > 0
        assert len(collector.get_all_business_metrics()) > 0

        # リセット
        collector.reset_metrics()

        # リセット後
        assert len(collector.get_all_metrics()) == 0
        assert len(collector.get_all_business_metrics()) == 0


class TestGlobalMetricsFunctions:
    """グローバルメトリクス関数のテスト"""

    def test_global_metrics_functions(self):
        """グローバルメトリクス関数の基本テスト"""
        # 既存のグローバルコレクターをリセット
        global_collector = get_global_metrics_collector()
        global_collector.reset_metrics()

        # グローバル関数を使用
        increment_counter("global_counter", value=10)
        set_gauge("global_gauge", 95.0)
        observe_histogram("global_histogram", 2.5)
        record_business_metric("global_business", {"profit": 1000})

        # 値を取得して確認
        assert get_metric_value("global_counter") == 10
        assert get_metric_value("global_gauge") == 95.0
        assert get_metric_value("global_histogram") == [2.5]


class TestTimeExecutionDecorator:
    """time_executionデコレーターのテスト"""

    def test_time_execution_decorator(self):
        """time_executionデコレーターのテスト"""
        # 既存のグローバルコレクターをリセット
        global_collector = get_global_metrics_collector()
        global_collector.reset_metrics()

        @time_execution("test_function_duration", description="Duration of test function")
        def test_function():
            time.sleep(0.01)  # 10msのスリープ
            return "result"

        # 関数を実行
        result = test_function()
        assert result == "result"

        # ヒ果を確認
        duration = get_metric_value("test_function_duration")
        assert isinstance(duration, list)
        assert len(duration) == 1
        assert duration[0] >= 0.01  # 10ms以上か確認（若干のオーバーヘッドあり）

    def test_time_execution_decorator_with_error(self):
        """time_executionデコレーターのエラーテスト"""
        # 既存のグローバルコレクターをリセット
        global_collector = get_global_metrics_collector()
        global_collector.reset_metrics()

        @time_execution("test_function_error_duration", description="Duration of test function with error")
        def error_function():
            time.sleep(0.01)  # 10msのスリープ
            raise ValueError("Test error")

        # エラーを発生させる関数を実行
        with pytest.raises(ValueError):
            error_function()

        # エラー時のヒストグラムを確認
        error_duration = get_metric_value("test_function_error_duration_error")
        assert isinstance(error_duration, list)
        assert len(error_duration) == 1
        assert error_duration[0] >= 0.01
