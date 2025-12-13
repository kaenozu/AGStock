import threading
import time
from datetime import datetime

import pandas as pd
import yfinance as yf


class marketStreamer:
    """
    Simulates real-time data streaming by polling yfinance.
    In a real scenario, this would connect to a WebSocket.
    """

    def __init__(self, tickers, interval_sec=60):
        self.tickers = tickers
        self.interval_sec = interval_sec
        self.latest_data = {}
        self.running = False
        self.thread = None
        self.callbacks = []

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _poll_loop(self):
        while self.running:
            try:
                self._fetch_latest()
                time.sleep(self.interval_sec)
            except Exception as e:
                print(f"Streamer Error: {e}")
                time.sleep(5)

    def _fetch_latest(self):
        # Batch fetch for efficiency
        tickers_str = " ".join(self.tickers)
        try:
            # period='1d', interval='1m' gets the latest minute data
            data = yf.download(tickers_str, period="1d", interval="1m", progress=False)

            timestamp = datetime.now()

            if len(self.tickers) == 1:
                # Handle single ticker case where columns are not MultiIndex
                row = data.iloc[-1]
                update = {"ticker": self.tickers[0], "price": row["Close"], "volume": row["Volume"], "time": timestamp}
                self._notify(update)
            else:
                # MultiIndex: (PriceType, Ticker)
                for ticker in self.tickers:
                    try:
                        # yfinance structure varies by version, safely accessing
                        # Assuming 'Close' -> Ticker
                        price = data["Close"][ticker].iloc[-1]
                        volume = data["Volume"][ticker].iloc[-1]

                        update = {"ticker": ticker, "price": price, "volume": volume, "time": timestamp}
                        self._notify(update)
                    except KeyError:
                        continue

        except Exception as e:
            print(f"Fetch Error: {e}")

    def _notify(self, data):
        self.latest_data[data["ticker"]] = data
        for cb in self.callbacks:
            cb(data)


# Singleton instance placeholder
_monitor = None


def get_streamer(tickers=None):
    global _monitor
    if _monitor is None and tickers:
        _monitor = marketStreamer(tickers)
    return _monitor
