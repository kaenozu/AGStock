import sys
import os
import pandas as pd
import yfinance as yf
import warnings
from src.cache_config import install_cache

# Install cache
install_cache()

# Add current directory to path to import src
sys.path.append(os.getcwd())

from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy
from src.backtester import Backtester

# Suppress warnings
warnings.filterwarnings("ignore")

def fetch_data_local(tickers, period="2y"):
    print(f"Fetching data for {len(tickers)} tickers...")
    try:
        df = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True, progress=False)
        data_dict = {}
        for ticker in tickers:
            if len(tickers) > 1:
                stock_df = df[ticker].copy()
            else:
                stock_df = df.copy()
            stock_df.dropna(inplace=True)
            if not stock_df.empty:
                data_dict[ticker] = stock_df
        return data_dict
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

def main():
    print("Starting Accuracy Verification...")
    
    # 1. Fetch Data
    tickers = NIKKEI_225_TICKERS
    data_map = fetch_data_local(tickers, period="2y")
    
    if not data_map:
        print("No data fetched.")
        return

    # 2. Initialize Strategies
    strategies = [
        SMACrossoverStrategy(5, 25),
        RSIStrategy(14, 30, 70),
        BollingerBandsStrategy(20, 2),
        CombinedStrategy()
    ]
    
    backtester = Backtester()
    
    results = []
    
    print(f"Running backtests on {len(data_map)} tickers...")
    
    for ticker, df in data_map.items():
        for strategy in strategies:
            # Run with default risk management (SL 5%, TP 10%)
            res = backtester.run(df, strategy, stop_loss=0.05, take_profit=0.10)
            if res:
                results.append({
                    "Ticker": ticker,
                    "Strategy": strategy.name,
                    "Total Return": res['total_return'],
                    "Win Rate": res['win_rate'],
                    "Total Trades": res['total_trades'],
                    "Avg Return": res['avg_return'],
                    "Max Drawdown": res['max_drawdown']
                })
    
    # 3. Aggregate Results
    results_df = pd.DataFrame(results)
    
    if results_df.empty:
        print("No results generated.")
        return
        
    with open("report.md", "w", encoding="utf-8") as f:
        f.write("# Verification Results (Realistic Simulation)\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> These results include **0.1% transaction costs** and **slippage**, and trades are executed at the **Next Day Open**.\n")
        f.write("> **Stop Loss**: 5%, **Take Profit**: 10%\n\n")
        
        # Overall Stats
        f.write(f"**Total Backtests**: {len(results_df)}\n")
        f.write(f"**Average Win Rate**: {results_df['Win Rate'].mean()*100:.2f}%\n")
        f.write(f"**Average Return per Trade**: {results_df['Avg Return'].mean()*100:.2f}%\n")
        f.write(f"**Average Max Drawdown**: {results_df['Max Drawdown'].mean()*100:.2f}%\n\n")
        
        # By Strategy
        f.write("## Performance by Strategy\n\n")
        strat_stats = results_df.groupby("Strategy").agg({
            "Win Rate": "mean",
            "Total Return": "mean",
            "Total Trades": "mean",
            "Avg Return": "mean",
            "Max Drawdown": "mean"
        })
        
        # Format for display
        strat_stats['Win Rate'] = strat_stats['Win Rate'].apply(lambda x: f"{x*100:.2f}%")
        strat_stats['Total Return'] = strat_stats['Total Return'].apply(lambda x: f"{x*100:.2f}%")
        strat_stats['Avg Return'] = strat_stats['Avg Return'].apply(lambda x: f"{x*100:.2f}%")
        strat_stats['Max Drawdown'] = strat_stats['Max Drawdown'].apply(lambda x: f"{x*100:.2f}%")
        strat_stats['Total Trades'] = strat_stats['Total Trades'].apply(lambda x: f"{x:.1f}")
        
        f.write(strat_stats.to_markdown())
        f.write("\n\n")
        
        # Top Performers
        f.write("## Top 5 Performing Combinations (by Total Return)\n\n")
        top_5 = results_df.sort_values(by="Total Return", ascending=False).head(5)
        for _, row in top_5.iterrows():
            f.write(f"- **{row['Ticker']}** ({TICKER_NAMES.get(row['Ticker'], '')}) - {row['Strategy']}: Return {row['Total Return']*100:.1f}%, Win Rate {row['Win Rate']*100:.1f}%, Max DD {row['Max Drawdown']*100:.1f}% ({row['Total Trades']} trades)\n")

    print("Report generated: report.md")

if __name__ == "__main__":
    main()
