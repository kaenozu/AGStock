"""
パフォーマンス最適化モジュール
Performance Optimization Module
Streamlitアプリの高速化と応答性改善
"""

import time
import functools
import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import pandas as pd


class PerformanceOptimizer:
    """Streamlitアプリのパフォーマンスを最適化するクラス"""

    def __init__(self):
        self.cache = {}
        self.execution_times = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

    def timed_execution(self, func_name: str = None):
        """実行時間を計測するデコレータ"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    name = func_name or func.__name__
                    self.execution_times[name] = execution_time

                    # 実行時間が遅い場合に警告
                    if execution_time > 3.0:
                        st.warning(f"⚠️ {name} の実行に {execution_time:.2f}秒 かかりました")

                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    name = func_name or func.__name__
                    st.error(f"❌ {name} 実行エラー ({execution_time:.2f}秒): {str(e)}")
                    raise

            return wrapper

        return decorator

    def cache_result(self, cache_key: str, ttl: int = 300):
        """結果をキャッシュするデコレータ"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # キャッシュキーの生成
                full_key = f"{cache_key}_{hash(str(args) + str(kwargs))}"
                current_time = time.time()

                # キャッシュチェック
                if full_key in self.cache:
                    cached_data, cached_time = self.cache[full_key]
                    if current_time - cached_time < ttl:
                        return cached_data

                # 実行とキャッシュ保存
                result = func(*args, **kwargs)
                self.cache[full_key] = (result, current_time)
                return result

            return wrapper

        return decorator

    def async_execution(self, func_name: str = None):
        """非同期実行をサポートするデコレータ"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    # 同期コンテキストで非同期関数を実行
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(func(*args, **kwargs))
                    finally:
                        loop.close()
                else:
                    # 通常の関数はスレッドプールで実行
                    future = self.thread_pool.submit(func, *args, **kwargs)
                    return future.result(timeout=30)

            return wrapper

        return decorator

    def lazy_load(self, placeholder_text: str = "読み込み中..."):
        """遅延読み込みを行うコンテキストマネージャー"""

        class LazyLoadContext:
            def __init__(self, text: str):
                self.text = text
                self.placeholder = None

            def __enter__(self):
                self.placeholder = st.empty()
                with self.placeholder.container():
                    st.info(f"⏳ {self.text}")
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.placeholder.error(f"❌ 読み込みエラー: {str(exc_val)}")
                else:
                    self.placeholder.empty()

        return LazyLoadContext(placeholder_text)

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        if not self.execution_times:
            return {"message": "実行データがありません"}

        times = list(self.execution_times.values())
        return {
            "total_functions": len(times),
            "average_time": sum(times) / len(times),
            "max_time": max(times),
            "min_time": min(times),
            "slow_functions": [
                (name, time_taken) for name, time_taken in self.execution_times.items() if time_taken > 2.0
            ],
            "cache_size": len(self.cache),
        }


# パフォーマンス最適化のインスタンス
optimizer = PerformanceOptimizer()


def optimized_data_loading(data_loader_func: Callable, cache_key: str, ttl: int = 300):
    """データ読み込みを最適化するヘルパー関数"""

    @optimizer.cache_result(cache_key, ttl)
    @optimizer.timed_execution(f"data_load_{cache_key}")
    def load_data():
        return data_loader_func()

    return load_data()


def render_performance_monitor():
    """パフォーマンス監視パネルを表示"""

    with st.expander("⚡ パフォーマンス監視", expanded=False):
        stats = optimizer.get_performance_stats()

        if "message" in stats:
            st.info(stats["message"])
            return

        # 基本統計
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("実行関数数", stats["total_functions"])

        with col2:
            st.metric("平均実行時間", f"{stats['average_time']:.2f}秒")

        with col3:
            st.metric("キャッシュサイズ", stats["cache_size"])

        # 遅い関数の警告
        if stats["slow_functions"]:
            st.warning("🐌 遅い関数が検出されました:")
            for func_name, exec_time in stats["slow_functions"]:
                st.write(f"- {func_name}: {exec_time:.2f}秒")

        # キャッシュクリアボタン
        if st.button("🗑️ キャッシュをクリア", key="clear_cache"):
            optimizer.cache.clear()
            st.success("キャッシュをクリアしました")
            st.rerun()


def optimized_dataframe_display(
    df: pd.DataFrame,
    max_rows: int = 1000,
    use_pagination: bool = True,
    search_columns: List[str] = None,
):
    """データフレームの最適化表示"""

    if df.empty:
        st.info("データがありません")
        return

    # 大きなデータフレームの分割表示
    if len(df) > max_rows:
        if use_pagination:
            st.info(f"データ量が多いため、最初の{max_rows}行を表示しています")
            df = df.head(max_rows)
        else:
            st.warning(f"全{len(df)}行を表示します。パフォーマンスに影響する可能性があります。")

    # 検索機能
    if search_columns:
        search_term = st.text_input("🔍 データ検索", key=f"search_{id(df)}")

        if search_term:
            mask = (
                df[search_columns]
                .apply(lambda x: x.astype(str).str.contains(search_term, case=False, na=False))
                .any(axis=1)
            )
            filtered_df = df[mask]
            st.caption(f"検索結果: {len(filtered_df)} / {len(df)}件")
            df = filtered_df

    # 最適化されたデータフレーム表示
    with st.container():
        st.dataframe(df, use_container_width=True, height=400)


class LazyComponent:
    """遅延読み込みコンポーネント"""

    def __init__(self, component_func: Callable, loading_text: str = "読み込み中..."):
        self.component_func = component_func
        self.loading_text = loading_text
        self._loaded = False
        self._result = None

    def render(self, *args, **kwargs):
        """コンポーネントをレンダリング"""

        if not self._loaded:
            with st.spinner(self.loading_text):
                self._result = self.component_func(*args, **kwargs)
                self._loaded = True

        return self._result

    def reset(self):
        """キャッシュをリセット"""
        self._loaded = False
        self._result = None


def responsive_layout(components: List[Dict[str, Any]]):
    """レスポンシブレイアウトを生成"""

    # 画面サイズに応じてカラム数を調整
    screen_width = st.session_state.get("screen_width", 1200)

    if screen_width < 768:
        cols = 1
    elif screen_width < 1024:
        cols = 2
    else:
        cols = len(components) if len(components) <= 4 else 4

    # カラムの生成
    columns = st.columns(cols)

    # コンポーネントの配置
    for i, component in enumerate(components):
        col_idx = i % cols
        with columns[col_idx]:
            # コンポーネントタイプに応じた処理
            comp_type = component.get("type", "simple")

            if comp_type == "metric":
                st.metric(
                    component["label"],
                    component["value"],
                    component.get("delta"),
                    component.get("help"),
                )

            elif comp_type == "chart":
                component["chart_func"]()

            elif comp_type == "dataframe":
                optimized_dataframe_display(
                    component["data"],
                    component.get("max_rows", 100),
                    component.get("use_pagination", True),
                    component.get("search_columns"),
                )

            elif comp_type == "custom":
                component["render_func"]()

            else:
                st.write(component.get("content", ""))


def batch_processing(items: List[Any], process_func: Callable, batch_size: int = 50):
    """バッチ処理を実行"""

    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        batch_num = i // batch_size + 1

        status_text.text(f"バッチ {batch_num}/{total_batches} を処理中...")

        # バッチ処理の実行
        try:
            batch_results = process_func(batch)
            results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
        except Exception as e:
            st.error(f"バッチ {batch_num} でエラー: {str(e)}")
            results.extend([None] * len(batch))

        # 進捗更新
        progress = (i + len(batch)) / len(items)
        progress_bar.progress(progress)

    status_text.text("処理完了!")
    time.sleep(1)  # 完了表示
    status_text.empty()

    return results


def smart_caching_strategy(data_size: int, complexity: str = "medium") -> Dict[str, Any]:
    """データサイズと複雑さに応じたキャッシュ戦略"""

    if data_size < 1000 and complexity == "low":
        return {
            "use_cache": True,
            "ttl": 600,  # 10分
            "compress": False,
        }
    elif data_size < 10000 or complexity == "medium":
        return {
            "use_cache": True,
            "ttl": 1800,  # 30分
            "compress": True,
        }
    else:
        return {"use_cache": False, "ttl": 0, "compress": False}


# パフォーマンス改善のためのデコレータ
def performance_monitor(func_name: str = None):
    """関数のパフォーマンスを監視するデコレータ"""
    return optimizer.timed_execution(func_name)


def cache_result(cache_key: str, ttl: int = 300):
    """結果をキャッシュするデコレータ"""
    return optimizer.cache_result(cache_key, ttl)


def async_execution(func_name: str = None):
    """非同期実行をサポートするデコレータ"""
    return optimizer.async_execution(func_name)


# 使用例
if __name__ == "__main__":
    # パフォーマンスモニターの表示
    render_performance_monitor()
