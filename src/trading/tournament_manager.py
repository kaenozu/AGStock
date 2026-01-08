import logging
import datetime
from typing import Dict, List, Any
import pandas as pd
from src.paper_trader import PaperTrader
from src.constants import NIKKEI_225_TICKERS, SP500_TICKERS

logger = logging.getLogger(__name__)

PERSONALITIES = {
    "shadow_aggressive": {
        "name": "狂犬 (Aggressive)",
        "risk_per_trade": 0.10,
        "stop_loss": 0.15,
        "take_profit": 0.50,
        "description": "高いリスクを取り、大きな利益を狙う。",
    },
    "shadow_conservative": {
        "name": "堅実 (Conservative)",
        "risk_per_trade": 0.02,
        "stop_loss": 0.03,
        "take_profit": 0.07,
        "description": "資産の保全を最優先し、手堅く稼ぐ。",
    },
    "shadow_mean_reversion": {
        "name": "逆張り王 (Mean Reversion)",
        "risk_per_trade": 0.05,
        "stop_loss": 0.05,
        "take_profit": 0.10,
        "description": "売られすぎを狙い、反発を取る。",
    },
    "shadow_trend_follower": {
        "name": "波乗り (Trend Follower)",
        "risk_per_trade": 0.05,
        "stop_loss": 0.07,
        "take_profit": 0.20,
        "description": "強いトレンドに乗り、利益を伸ばす。",
    },
}


class TournamentManager:
    """
    Multiversal Shadow Tournament Manager.
    Runs multiple paper trading accounts with different personalities.
    """

    def __init__(self):
        self.traders = {}
        for acc_id, profile in PERSONALITIES.items():
            self.traders[acc_id] = PaperTrader(account_id=acc_id)

    def run_daily_simulation(self, signals: List[Dict[str, Any]]):
        """Run simulation for each personality based on the same signals."""
        logger.info(f"🏆 Shadow Tournament: Running simulation for {len(signals)} signals...")

        for acc_id, trader in self.traders.items():
            profile = PERSONALITIES[acc_id]
            for sig in signals:
                ticker = sig["ticker"]
                action = sig["action"]
                price = sig["price"]

                if action == "BUY":
                    # Adjust quantity based on personality risk
                    balance = trader.get_current_balance()
                    cash = balance["cash"]

                    # Target investment amount based on personality
                    target_investment = cash * profile["risk_per_trade"]
                    quantity = int(target_investment / price)

                    if quantity > 0:
                        stop_price = price * (1.0 - profile["stop_loss"])
                        trader.execute_trade(
                            ticker=ticker,
                            action="BUY",
                            quantity=quantity,
                            price=price,
                            strategy="Tournament",
                            reason=f"Tournament: {profile['name']} (Stop: {stop_price:,.0f})",
                        )

                elif action == "SELL":
                    # Personalities might have different sell signals, but for now we follow main signals
                    # Or we check if they actually hold it
                    pos = trader.get_positions()
                    if not pos.empty and ticker in pos["ticker"].values:
                        qty = pos[pos["ticker"] == ticker]["quantity"].values[0]
                        trader.execute_trade(
                            ticker=ticker,
                            action="SELL",
                            quantity=qty,
                            price=price,
                            reason=f"Tournament: {profile['name']}",
                        )

            # Daily Equity Update
            trader.update_daily_equity()

    def get_leaderboard(self) -> pd.DataFrame:
        """Get the current ranking of personalities."""
        data = []
        for acc_id, trader in self.traders.items():
            balance = trader.get_current_balance()
            profile = PERSONALITIES[acc_id]
            data.append(
                {
                    "Account ID": acc_id,
                    "Name": profile["name"],
                    "Total Equity": balance["total_equity"],
                    "Daily PnL": balance["daily_pnl"],
                    "Unrealized PnL": balance["unrealized_pnl"],
                    "Description": profile["description"],
                }
            )

        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values("Total Equity", ascending=False)
        return df

    def get_winner_advise(self) -> str:
        """Get investment advice based on the top performing personality."""
        df = self.get_leaderboard()
        if df.empty:
            return "トーナメントデータがありません。"

        winner = df.iloc[0]
        return f"現在、**{winner['Name']}**（{winner['Description']}）がトップです。この相場環境では、{winner['Name']}の戦略を重視することをお勧めします。"

    def get_winner_params(self) -> Dict[str, Any]:
        """Returns the parameters of the winning personality for mirroring."""
        df = self.get_leaderboard()
        if df.empty:
            return PERSONALITIES["shadow_trend_follower"]  # Default

        winner_id = df.iloc[0]["Account ID"]
        return PERSONALITIES[winner_id]
