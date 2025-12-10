import sys
import os
sys.path.append(os.getcwd())

from src.cache_config import install_cache
from src.auto_selector import AutoSelector

install_cache()

def main():
    print("🚀 Initializing AutoSelector Verification...")
    selector = AutoSelector()
    
    print("running select_daily_config()... (This may take time to fetch data)")
    config = selector.select_daily_config()
    
    print("\n=== Auto Selection Result ===")
    print(f"📊 Regime: {config['regime_info']['regime_name']}")
    print(f"🧠 Strategy: {config['strategy_cls'].__name__}")
    print(f"🔧 Params: {config['strategy_params']}")
    print(f"🎯 Selected Tickers ({len(config['tickers'])}):")
    for ticker in config['tickers']:
        print(f"  - {ticker}")
        
    print("\n✅ Verification Successful if tickers and strategy are populated.")

if __name__ == "__main__":
    main()
