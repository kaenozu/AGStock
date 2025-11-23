import sys
import os
import json
import pandas as pd
import yfinance as yf
import datetime
from src.constants import NIKKEI_225_TICKERS, TICKER_NAMES
from src.strategies import SMACrossoverStrategy, RSIStrategy, BollingerBandsStrategy, CombinedStrategy, MLStrategy
from src.cache_config import install_cache

# Install cache
install_cache()

def load_best_params():
    if os.path.exists("best_params.json"):
        with open("best_params.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_strategy(strategy_name, params):
    # Filter out risk management params that are not part of strategy __init__
    strat_params = {k: v for k, v in params.items() if k not in ['stop_loss', 'take_profit']}
    
    if strategy_name == "RSI Reversal":
        return RSIStrategy(**strat_params)
    elif strategy_name == "Combined":
        return CombinedStrategy(**strat_params)
    elif strategy_name == "Bollinger Bands":
        return BollingerBandsStrategy(**strat_params)
    elif strategy_name == "SMA Crossover":
        return SMACrossoverStrategy(**strat_params)
    elif strategy_name == "AI Random Forest":
        return MLStrategy(**strat_params)
    return None

def main():
    print(f"--- Daily Signal Scan ({datetime.date.today()}) ---")
    
    best_params = load_best_params()
    tickers = NIKKEI_225_TICKERS
    
    print(f"Fetching data for {len(tickers)} tickers...")
    # Fetch slightly more data than needed for indicators (e.g. 1 year)
    try:
        df_all = yf.download(tickers, period="2y", group_by='ticker', auto_adjust=True, threads=True, progress=False)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    signals = []
    
    # Check Market Sentiment
    from src.sentiment import SentimentAnalyzer
    
    print("Analyzing Market Sentiment...")
    try:
        sa = SentimentAnalyzer()
        sentiment = sa.get_market_sentiment()
        print(f"Market Sentiment: {sentiment['label']} (Score: {sentiment['score']:.2f})")
        
        # Filter logic: If sentiment is Very Negative (< -0.2), suppress BUYs
        allow_buy = True
        if sentiment['score'] < -0.2:
            print("⚠️ Market Sentiment is Negative. Suppressing BUY signals.")
            allow_buy = False
            
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        allow_buy = True # Default to allow if error
    
    for ticker in tickers:
        if len(tickers) > 1:
            # yfinance returns MultiIndex if multiple tickers
            # Check if ticker is in columns level 0
            try:
                df = df_all[ticker].copy()
            except KeyError:
                continue
        else:
            df = df_all.copy()
            
        df.dropna(inplace=True)
        if df.empty:
            continue
            
        # Determine which strategy to use
        strategies_to_check = []
        
        if ticker in best_params and best_params[ticker]:
            # Use the best strategy found
            best_strat_name = max(best_params[ticker], key=lambda x: best_params[ticker][x]['train_return'])
            params = best_params[ticker][best_strat_name]['params']
            strategies_to_check.append((best_strat_name, params))
        else:
            # Use defaults
            strategies_to_check.append(("RSI Reversal", {}))
            strategies_to_check.append(("Combined", {}))
            strategies_to_check.append(("AI Random Forest", {}))
            
        for strat_name, params in strategies_to_check:
            strategy = get_strategy(strat_name, params)
            if not strategy:
                continue
                
            # Generate signals
            try:
                sig_series = strategy.generate_signals(df)
            except Exception as e:
                # print(f"Error generating signals for {ticker} with {strat_name}: {e}")
                continue
            
            # Check the last signal (Today's Close)
            if sig_series.empty:
                continue
                
            last_signal = sig_series.iloc[-1]
            
            if last_signal == 1:
                if not allow_buy:
                    continue
                    
                # Check Fundamentals for BUY signals
                from src.data_loader import fetch_fundamental_data
                from src.fundamentals import FundamentalFilter
                
                fund_filter = FundamentalFilter()
                fundamentals = fetch_fundamental_data(ticker)
                
                # Default thresholds (can be moved to config later)
                is_undervalued = fund_filter.filter_undervalued(fundamentals, max_pe=30, max_pbr=5)
                is_quality = fund_filter.filter_quality(fundamentals, min_roe=0.05)
                
                # Add fundamental info to signal
                pe = fundamentals.get('trailingPE') if fundamentals else None
                roe = fundamentals.get('returnOnEquity') if fundamentals else None
                
                # Only filter if we have data, otherwise warn?
                # For now, let's just add the info and maybe mark it
                
                signals.append({
                    "Ticker": ticker,
                    "Name": TICKER_NAMES.get(ticker, ""),
                    "Action": "BUY",
                    "Strategy": strat_name,
                    "Price": df['Close'].iloc[-1],
                    "PER": round(pe, 2) if pe else "N/A",
                    "ROE": round(roe, 4) if roe else "N/A",
                    "Valid_Fund": is_undervalued and is_quality
                })
            elif last_signal == -1:
                signals.append({
                    "Ticker": ticker,
                    "Name": TICKER_NAMES.get(ticker, ""),
                    "Action": "SELL (SHORT)",
                    "Strategy": strat_name,
                    "Price": df['Close'].iloc[-1]
                })
                
    # Output Report
    if not signals:
        print("No signals found for tomorrow.")
    else:
        print(f"\nFound {len(signals)} signals for Tomorrow Open:\n")
        df_sig = pd.DataFrame(signals)
        print(df_sig.to_markdown(index=False))
        
        # Save to file
        df_sig.to_csv("daily_signals.csv", index=False)
        print("\nSaved to daily_signals.csv")

if __name__ == "__main__":
    main()
