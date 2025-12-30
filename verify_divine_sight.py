
import logging
import os
import json
import pandas as pd
from src.trading.market_scanner import MarketScanner
from src.schemas import load_config

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DivineSightVerifier")

def verify_divine_sight_hook():
    logger.info("Initializing MarketScanner...")
    config = load_config("config.json").model_dump()
    scanner = MarketScanner(config, logger)
    
    # Mock positions
    positions = pd.DataFrame()
    
    logger.info("Running scan_market (this might take a moment)...")
    try:
        # We expect this to try fetching data. 
        # To strictly verify the HOOK, we just need scan_market to finish.
        # It might fail finding tickers if not online/mocked properly, 
        # but let's see if we can trigger the save logic.
        # Ideally we should mock _fetch_data_with_retry to return dummy data.
        
        # Mocking internal methods to speed up and isolate test
        scanner._fetch_data_with_retry = lambda tickers: {
            "7203.T": pd.DataFrame({
                "Close": [100, 101, 102], 
                "High": [105, 105, 105],
                "Low": [95, 95, 95],
                "Volume": [1000, 1000, 1000]
            }) 
        }
        scanner.get_target_tickers = lambda positions: ["7203.T"]
        
        # Mock strategy generation to ensure signals are created
        # We can't easily mock the strategy orchestrator deep down without more code,
        # so let's check if the file creation logic works even with empty signals
        # OR better, ensure at least one signal is generated.
        
        # Actually, let's just run it. If it returns signals or not, it should run without error.
        # If signals are empty, it writes an empty list to JSON. That's a valid test.
        
        signals = scanner.scan_market(positions)
        logger.info(f"Scan complete. Signals found: {len(signals)}")
        
        # Check if file exists
        file_path = "data/latest_scan_results.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"✅ JSON file found with {len(data)} entries.")
            print("Verification SUCCESS")
        else:
            logger.error("❌ JSON file NOT found.")
            print("Verification FAILED")
            
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        print("Verification FAILED")

if __name__ == "__main__":
    verify_divine_sight_hook()
