
import pandas as pd
import numpy as np
import os
from src.agents.visual_oracle import VisualOracle
from src.data_loader import fetch_stock_data

def test_visual_oracle():
    print("Testing VisualOracle (Phase 74)...")
    
    # 1. Fetch some real data
    tickers = ["7203.T", "^GSPC"]
    data = fetch_stock_data(tickers, period="60d")
    
    oracle = VisualOracle()
    
    for ticker in tickers:
        df = data.get(ticker)
        if df is not None:
            print(f"Analyzing {ticker}...")
            result = oracle.analyze_chart(ticker, df)
            
            if "error" in result:
                print(f"❌ Error for {ticker}: {result['error']}")
            else:
                print(f"✅ Analysis for {ticker}:")
                print(f"  Trend: {result.get('trend')}")
                print(f"  Action: {result.get('action')}")
                print(f"  Patterns: {result.get('patterns')}")
                print(f"  Confidence: {result.get('visual_confidence')}")
                print(f"  Reasoning: {result.get('reasoning')}")
                print(f"  Image saved at: {result.get('image_path')}")

if __name__ == "__main__":
    test_visual_oracle()
