
import logging
from src.trading.fully_automated_trader import FullyAutomatedTrader

def test_ai_veto():
    logging.basicConfig(level=logging.INFO)
    trader = FullyAutomatedTrader()
    
    # Mock signals
    signals = [
        {
            "ticker": "7203.T", 
            "action": "BUY", 
            "price": 2500.0, 
            "reason": "Numerical Model prediction (UP 57%)"
        }
    ]
    
    print("\n=== AI Veto Test Start ===")
    trader.execute_signals(signals)
    print("=== AI Veto Test Complete ===\n")

if __name__ == "__main__":
    test_ai_veto()
