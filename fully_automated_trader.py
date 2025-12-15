"""
Compatibility shim for tests that import `fully_automated_trader` at repo root.
Delegates to the actual implementation under src/trading and re-exports key symbols
so patching works in unit tests.
"""

import src.trading.fully_automated_trader as fat
import datetime as datetime  # re-export for patching in tests
from src.data_loader import fetch_fundamental_data, fetch_stock_data  # re-export for patching
from src.execution import ExecutionEngine  # re-export for patching
from src.paper_trader import PaperTrader  # re-export for patching
from src.smart_notifier import SmartNotifier  # re-export for patching


class FullyAutomatedTrader(fat.FullyAutomatedTrader):
    """
    Wrapper that injects patchable dependencies from this shim module.
    Tests patch `fully_automated_trader.SmartNotifier` etc., so we forward those
    globals into the underlying implementation before initialization.
    """

    def __init__(self, config_path: str = "config.json") -> None:
        # Forward current globals to the underlying module so patching works
        fat.SmartNotifier = globals().get("SmartNotifier", SmartNotifier)
        fat.PaperTrader = globals().get("PaperTrader", PaperTrader)
        fat.ExecutionEngine = globals().get("ExecutionEngine", ExecutionEngine)
        fat.fetch_fundamental_data = globals().get("fetch_fundamental_data", fetch_fundamental_data)
        fat.fetch_stock_data = globals().get("fetch_stock_data", fetch_stock_data)
        super().__init__(config_path)

    def _fetch_data_with_retry(self, tickers):
        """
        Override to refresh the fetch_stock_data reference at call time so
        unittest.mock.patch on fully_automated_trader.fetch_stock_data is respected.
        """
        fat.fetch_stock_data = globals().get("fetch_stock_data", fetch_stock_data)
        return super()._fetch_data_with_retry(tickers)

    def scan_market(self):
        """
        Keep fundamentals/price fetchers in sync with patched globals before delegating.
        """
        fat.fetch_fundamental_data = globals().get("fetch_fundamental_data", fetch_fundamental_data)
        fat.fetch_stock_data = globals().get("fetch_stock_data", fetch_stock_data)
        return super().scan_market()


if __name__ == "__main__":
    # Simple smoke run: load config and print whether trading is safe
    trader = FullyAutomatedTrader()
    safe, reason = trader.is_safe_to_trade()
    print(f"Safe to trade: {safe}, reason: {reason}")
