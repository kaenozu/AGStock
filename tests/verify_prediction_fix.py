
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.prediction_backtester import PredictionBacktester
from src.logger_config import setup_logging

def test_backtester_execution():
    setup_logging()
    print("\nStarting Programmatic Backtest Verification...")
    
    backtester = PredictionBacktester()
    
    # Use dates that we know have data (recent past)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"Running backtest for 8306.T from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        result = backtester.run_backtest(
            ticker="8306.T",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            prediction_days=5
        )
        
        if "error" in result:
            print(f"❌ Backtest Failed with Error: {result['error']}")
            # Check if it is the "No valid prediction data" error
            if "有効な予測データがありません" in result['error']:
                 print("  -> Logic Issue: Still getting 'No valid prediction data'")
        else:
            print("✅ Backtest Succeeded!")
            metrics = result.get("metrics", {})
            print("Metrics:", metrics)
            print(f"Total Predictions: {metrics.get('total_samples')}")
            
            if metrics.get('total_samples', 0) > 0:
                print("  -> Predictions were generated. Fix verified.")
            else:
                print("  -> Success returned but 0 samples. Warning.")

    except Exception as e:
        print(f"❌ Exception during backtest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backtester_execution()
