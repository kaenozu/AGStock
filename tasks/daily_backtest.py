import pandas as pd
import numpy as np
from src.paper_trader import PaperTrader

def compute_metrics():
    """
    Compute daily metrics for the trading system.
    Returns a DataFrame with columns: win_rate, sharpe, total_equity
    """
    pt = PaperTrader()
    try:
        history = pt.get_trade_history()
        equity_history = pt.get_equity_history()
        
        if not equity_history:
            return pd.DataFrame()
            
        df_equity = pd.DataFrame(equity_history, columns=["date", "total_equity"])
        df_equity["date"] = pd.to_datetime(df_equity["date"])
        df_equity.set_index("date", inplace=True)
        
        # Calculate returns
        df_equity["returns"] = df_equity["total_equity"].pct_change()
        
        # Win rate from history
        if not history.empty and "realized_pnl" in history.columns:
            wins = (history["realized_pnl"] > 0).sum()
            total = len(history)
            win_rate = wins / total if total > 0 else 0.5
        else:
            win_rate = 0.5
            
        # Sharpe ratio
        returns = df_equity["returns"].dropna()
        if len(returns) > 1:
            sharpe = (returns.mean() / (returns.std() + 1e-6)) * np.sqrt(252)
        else:
            sharpe = 0.0
            
        # Create result row
        result = pd.DataFrame({
            "win_rate": [win_rate],
            "sharpe": [sharpe],
            "total_equity": [df_equity["total_equity"].iloc[-1] if not df_equity.empty else 0]
        }, index=[df_equity.index[-1] if not df_equity.empty else pd.Timestamp.now()])
        
        return result
    except Exception:
        return pd.DataFrame()
    finally:
        pt.close()
