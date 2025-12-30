"""マーケットスキャナー

FullyAutomatedTraderから分離した市場スキャンロジック
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.constants import NIKKEI_225_TICKERS, SP500_TICKERS, STOXX50_TICKERS
from src.data_loader import fetch_stock_data

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """スキャン結果"""
    ticker: str
    market: str
    signal: str  # "BUY", "SELL", "HOLD"
    confidence: float
    price: float
    reason: str
    strategy_name: str
    timestamp: datetime


class MarketScanner:
    """市場スキャナークラス

    複数市場の銘柄をスキャンし、取引シグナルを検出
    """

    def __init__(
        self,
        strategies: List[Any],
        min_confidence: float = 0.6,
        max_results: int = 20,
    ):
        """初期化

        Args:
            strategies: 使用する戦略リスト
            min_confidence: 最小信頼度閾値
            max_results: 最大結果数
        """
        self.strategies = strategies
        self.min_confidence = min_confidence
        self.max_results = max_results
        self._cache: Dict[str, Tuple[datetime, List[ScanResult]]] = {}
        self._cache_ttl = 300  # 5分

    def scan_market(
        self,
        market: str = "japan",
        custom_tickers: Optional[List[str]] = None,
    ) -> List[ScanResult]:
        """市場をスキャン

        Args:
            market: 市場（"japan", "us", "europe", "all"）
            custom_tickers: カスタム銘柄リスト

        Returns:
            スキャン結果リスト
        """
        # キャッシュチェック
        cache_key = f"{market}:{','.join(custom_tickers or [])}"
        if cache_key in self._cache:
            cached_time, cached_results = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return cached_results

        # 銘柄リスト取得
        tickers = self._get_tickers(market, custom_tickers)

        results = []
        for ticker in tickers:
            try:
                result = self._scan_ticker(ticker, market)
                if result and result.confidence >= self.min_confidence:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Scan failed for {ticker}: {e}")
                continue

        # 信頼度でソート
        results.sort(key=lambda x: x.confidence, reverse=True)
        results = results[:self.max_results]

        # キャッシュ更新
        self._cache[cache_key] = (datetime.now(), results)

        return results

    def _get_tickers(self, market: str, custom_tickers: Optional[List[str]]) -> List[str]:
        """市場に応じた銀柄リストを取得"""
        if custom_tickers:
            return custom_tickers

        if market == "japan":
            return NIKKEI_225_TICKERS[:50]  # 主要50銀柄
        elif market == "us":
            return SP500_TICKERS[:50]
        elif market == "europe":
            return STOXX50_TICKERS[:30]
        elif market == "all":
            return (
                NIKKEI_225_TICKERS[:30] +
                SP500_TICKERS[:30] +
                STOXX50_TICKERS[:20]
            )
        else:
            return NIKKEI_225_TICKERS[:50]

    def _scan_ticker(self, ticker: str, market: str) -> Optional[ScanResult]:
        """単一銀柄をスキャン"""
        # データ取得
        try:
            df = fetch_stock_data(ticker, period="3mo")
            if df is None or df.empty or len(df) < 20:
                return None
        except Exception:
            return None

        # 各戦略でシグナル検出
        signals = []
        for strategy in self.strategies:
            try:
                signal = self._get_strategy_signal(strategy, df)
                if signal:
                    signals.append(signal)
            except Exception:
                continue

        if not signals:
            return None

        # シグナル集約
        buy_count = sum(1 for s in signals if s["signal"] == "BUY")
        sell_count = sum(1 for s in signals if s["signal"] == "SELL")

        if buy_count > sell_count and buy_count >= 2:
            signal = "BUY"
            confidence = buy_count / len(signals)
        elif sell_count > buy_count and sell_count >= 2:
            signal = "SELL"
            confidence = sell_count / len(signals)
        else:
            return None

        # 現在価格
        current_price = float(df["Close"].iloc[-1])

        # 理由生成
        strategy_names = [s["strategy"] for s in signals if s["signal"] == signal]
        reason = f"{len(strategy_names)}戦略が{signal}シグナル: {', '.join(strategy_names[:3])}"

        return ScanResult(
            ticker=ticker,
            market=market,
            signal=signal,
            confidence=confidence,
            price=current_price,
            reason=reason,
            strategy_name=",".join(strategy_names[:3]),
            timestamp=datetime.now(),
        )

    def _get_strategy_signal(
        self, strategy: Any, df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """戦略からシグナルを取得"""
        try:
            # 戦略のgenerate_signalsメソッドを呼び出し
            if hasattr(strategy, "generate_signals"):
                signals_df = strategy.generate_signals(df)
                if signals_df is not None and not signals_df.empty:
                    last_signal = signals_df["signal"].iloc[-1]
                    if last_signal != 0:
                        return {
                            "signal": "BUY" if last_signal > 0 else "SELL",
                            "strategy": getattr(strategy, "name", strategy.__class__.__name__),
                        }

            # analyzeメソッドがある場合
            elif hasattr(strategy, "analyze"):
                result = strategy.analyze(df)
                if result and result.get("action") in ["BUY", "SELL"]:
                    return {
                        "signal": result["action"],
                        "strategy": getattr(strategy, "name", strategy.__class__.__name__),
                    }
        except Exception:
            pass

        return None

    def get_top_opportunities(
        self,
        signal_type: str = "BUY",
        limit: int = 5,
    ) -> List[ScanResult]:
        """トップ機会を取得

        Args:
            signal_type: シグナルタイプ（"BUY"または"SELL"）
            limit: 取得数

        Returns:
            スキャン結果リスト
        """
        all_results = self.scan_market(market="all")
        filtered = [r for r in all_results if r.signal == signal_type]
        return filtered[:limit]

    def to_dataframe(self, results: List[ScanResult]) -> pd.DataFrame:
        """結果をDataFrameに変換"""
        if not results:
            return pd.DataFrame()

        return pd.DataFrame([
            {
                "Ticker": r.ticker,
                "Market": r.market,
                "Signal": r.signal,
                "Confidence": f"{r.confidence:.1%}",
                "Price": f"{r.price:,.2f}",
                "Reason": r.reason,
                "Strategy": r.strategy_name,
            }
            for r in results
        ])

    def clear_cache(self):
        """キャッシュをクリア"""
        self._cache.clear()
