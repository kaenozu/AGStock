#!/usr/bin/env python3
"""
Global Market Integration System - Simplified
簡易版グローバル市場監視システム
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any


class SimpleGlobalMonitor:
    """簡易グローバル市場監視"""

    def __init__(self):
        self.markets = self.init_markets()
        self.assets = {}
        self.update_data()

    def init_markets(self):
        """市場初期化"""
        return {
            "NYSE": {"timezone": "America/New_York", "open": "09:30", "close": "16:00"},
            "NASDAQ": {
                "timezone": "America/New_York",
                "open": "09:30",
                "close": "16:00",
            },
            "TSE": {"timezone": "Asia/Tokyo", "open": "09:00", "close": "15:00"},
            "LSE": {"timezone": "Europe/London", "open": "08:00", "close": "16:30"},
            "HKEX": {"timezone": "Asia/Hong_Kong", "open": "09:30", "close": "16:00"},
        }

    def update_data(self):
        """データ更新"""
        # 主要株価指数
        indices = {
            "S&P 500": {
                "price": 4500 + np.random.normal(0, 50),
                "change": np.random.normal(0, 2),
            },
            "NASDAQ": {
                "price": 14000 + np.random.normal(0, 200),
                "change": np.random.normal(0, 3),
            },
            "NIKKEI": {
                "price": 33000 + np.random.normal(0, 300),
                "change": np.random.normal(0, 1.5),
            },
            "FTSE": {
                "price": 7500 + np.random.normal(0, 100),
                "change": np.random.normal(0, 1),
            },
            "HSI": {
                "price": 17000 + np.random.normal(0, 200),
                "change": np.random.normal(0, 1.5),
            },
        }

        for name, data in indices.items():
            self.assets[name] = {
                "type": "index",
                "price": data["price"],
                "change": data["change"],
                "change_pct": (data["change"] / data["price"]) * 100,
                "volume": np.random.randint(1000000, 10000000),
            }

        # 為替
        forex = {
            "USD/JPY": {
                "price": 148 + np.random.normal(0, 1),
                "change": np.random.normal(0, 0.5),
            },
            "EUR/USD": {
                "price": 1.08 + np.random.normal(0, 0.01),
                "change": np.random.normal(0, 0.002),
            },
            "GBP/USD": {
                "price": 1.26 + np.random.normal(0, 0.01),
                "change": np.random.normal(0, 0.003),
            },
        }

        for pair, data in forex.items():
            self.assets[pair] = {
                "type": "forex",
                "price": data["price"],
                "change": data["change"],
                "change_pct": (data["change"] / data["price"]) * 100,
                "volume": np.random.randint(100000000, 1000000000),
            }

        # コモディティ
        commodities = {
            "Gold": {
                "price": 2000 + np.random.normal(0, 50),
                "change": np.random.normal(0, 10),
            },
            "Crude Oil": {
                "price": 75 + np.random.normal(0, 3),
                "change": np.random.normal(0, 1),
            },
            "Silver": {
                "price": 23 + np.random.normal(0, 1),
                "change": np.random.normal(0, 0.5),
            },
        }

        for name, data in commodities.items():
            self.assets[name] = {
                "type": "commodity",
                "price": data["price"],
                "change": data["change"],
                "change_pct": (data["change"] / data["price"]) * 100,
                "volume": np.random.randint(10000, 1000000),
            }

    def display_overview(self):
        """概要表示"""
        print("=" * 60)
        print("GLOBAL MARKET OVERVIEW")
        print("=" * 60)

        # 市場ステータス
        print("\nMarket Status:")
        current_time = datetime.now()
        for market, info in self.markets.items():
            # 簡易的な営業時間判定
            print(f"  {market}: Active")  # デモでは常にアクティブ

        # 主要資産パフォーマンス
        print("\nMajor Assets Performance:")
        for name, asset in self.assets.items():
            change_icon = "+" if asset["change"] > 0 else ""
            print(
                f"  {name}: {asset['price']:.2f} ({change_icon}{asset['change']:.2f}, {asset['change_pct']:+.2f}%)"
            )

        # グローバルセンチメント
        total_changes = [asset["change_pct"] for asset in self.assets.values()]
        global_sentiment = np.mean(total_changes)

        print(f"\nGlobal Sentiment: {global_sentiment:+.2f}%")
        if global_sentiment > 1:
            print("  Market Mood: BULLISH")
        elif global_sentiment < -1:
            print("  Market Mood: BEARISH")
        else:
            print("  Market Mood: NEUTRAL")

        # 地域別分析
        print("\nRegional Analysis:")
        us_assets = ["S&P 500", "NASDAQ"]
        asia_assets = ["NIKKEI", "HSI"]
        europe_assets = ["FTSE"]

        us_avg = np.mean(
            [self.assets[a]["change_pct"] for a in us_assets if a in self.assets]
        )
        asia_avg = np.mean(
            [self.assets[a]["change_pct"] for a in asia_assets if a in self.assets]
        )
        europe_avg = np.mean(
            [self.assets[a]["change_pct"] for a in europe_assets if a in self.assets]
        )

        print(f"  US Markets: {us_avg:+.2f}%")
        print(f"  Asian Markets: {asia_avg:+.2f}%")
        print(f"  European Markets: {europe_avg:+.2f}%")

        # 時間差裁定機会
        print("\nTime Zone Arbitrage Opportunities:")
        print("  - US-Asia: Active (6-8 hour time difference)")
        print("  - Europe-US: Active (5-7 hour time difference)")
        print("  - Asia-Europe: Limited overlap")

        # 相関分析
        print("\nCorrelation Analysis:")
        indices = list(self.assets.keys())[:5]  # 上位5資産
        correlations = {}

        for i, asset1 in enumerate(indices):
            for asset2 in indices[i + 1 :]:
                # デモ相関値
                corr = np.random.uniform(-0.3, 0.8)
                if abs(corr) > 0.6:
                    print(f"  {asset1} - {asset2}: {corr:.3f} (High Correlation)")

        # 為替影響分析
        print("\nCurrency Impact Analysis:")
        usd_jpy = self.assets.get("USD/JPY", {}).get("change_pct", 0)
        if abs(usd_jpy) > 0.5:
            print(
                f"  USD/JPY movement: {usd_jpy:+.2f}% - Significant export/import impact"
            )

        # コモディティと株式の関係
        gold_change = self.assets.get("Gold", {}).get("change_pct", 0)
        oil_change = self.assets.get("Crude Oil", {}).get("change_pct", 0)

        print(f"\nCommodity-Equity Relationship:")
        print(f"  Gold (Safe Haven): {gold_change:+.2f}%")
        print(f"  Oil (Growth Indicator): {oil_change:+.2f}%")

        if gold_change > 1 and global_sentiment < -1:
            print("  -> Flight to safety pattern detected")
        elif oil_change > 2 and global_sentiment > 1:
            print("  -> Growth optimism pattern detected")

        # 24時間監視サマリー
        print("\n24-Hour Monitoring Summary:")
        print(f"  Total Assets Monitored: {len(self.assets)}")
        print(f"  Markets Covered: {len(self.markets)}")
        print(f"  Update Frequency: Real-time (demo: every 60 seconds)")
        print(f"  Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def get_alerts(self):
        """アラート取得"""
        alerts = []

        # 大幅変動アラート
        for name, asset in self.assets.items():
            if abs(asset["change_pct"]) > 2:
                alerts.append(
                    {
                        "type": "price_movement",
                        "asset": name,
                        "severity": "high"
                        if abs(asset["change_pct"]) > 3
                        else "medium",
                        "message": f"{name} moved {asset['change_pct']:+.2f}%",
                    }
                )

        # グローバルセンチメントアラート
        total_changes = [asset["change_pct"] for asset in self.assets.values()]
        global_sentiment = np.mean(total_changes)

        if global_sentiment > 2:
            alerts.append(
                {
                    "type": "sentiment",
                    "severity": "medium",
                    "message": f"Strong bullish sentiment: {global_sentiment:+.2f}%",
                }
            )
        elif global_sentiment < -2:
            alerts.append(
                {
                    "type": "sentiment",
                    "severity": "medium",
                    "message": f"Strong bearish sentiment: {global_sentiment:+.2f}%",
                }
            )

        return alerts


def main():
    """メイン実行"""
    print("Global Market Integration System Starting...")

    monitor = SimpleGlobalMonitor()

    # 複数回更新をシミュレート
    for i in range(3):
        print(f"\n--- Update {i + 1}/3 ---")
        monitor.update_data()
        monitor.display_overview()

        # アラート表示
        alerts = monitor.get_alerts()
        if alerts:
            print("\nALERTS:")
            for alert in alerts:
                severity_icon = "!!!" if alert["severity"] == "high" else "!"
                print(f"  {severity_icon} {alert['message']}")
        else:
            print("\nALERTS: None")

        if i < 2:
            print(f"\nWaiting for next update... ({i + 1}/3)")
            import time

            time.sleep(1)

    print("\nGlobal Market Integration System Complete!")

    # エクスポートデータ
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "assets": monitor.assets,
        "markets": len(monitor.markets),
        "total_assets": len(monitor.assets),
    }

    with open("data/global_market_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print("Data exported to: data/global_market_snapshot.json")


if __name__ == "__main__":
    main()
