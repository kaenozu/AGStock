import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.trading.tournament_manager import TournamentManager, PERSONALITIES
from src.paper_trader import PaperTrader
from src.paths import PAPER_TRADING_DB

def test_shadow_tournament_cycle():
    print("=== 🏆 Shadow Tournament Full Cycle Test ===")
    
    # 1. Initialize
    print("\n[1/4] Initializing TournamentManager...")
    tm = TournamentManager()
    
    # Verify initial state
    lb_initial = tm.get_leaderboard()
    print(f"Personalities loaded: {len(lb_initial)}")
    assert len(lb_initial) == len(PERSONALITIES)
    
    # 2. Simulate Trades
    print("\n[2/4] Simulating Daily Cycle with Dummy Signals...")
    # Generate some mock signals
    mock_signals = [
        {"ticker": "7203.T", "action": "BUY", "price": 2500.0},  # Toyota
        {"ticker": "9984.T", "action": "BUY", "price": 8000.0},  # Softbank
        {"ticker": "AAPL", "action": "BUY", "price": 190.0},    # Apple
    ]
    
    # Run simulation
    tm.run_daily_simulation(mock_signals)
    print("Simulation execution completed.")
    
    # 3. Verify Database Updates
    print("\n[3/4] Verifying Database Records...")
    conn = sqlite3.connect(PAPER_TRADING_DB)
    cursor = conn.cursor()
    
    for acc_id in PERSONALITIES.keys():
        # Check if orders were placed
        cursor.execute("SELECT COUNT(*) FROM orders WHERE account_id = ?", (acc_id,))
        order_count = cursor.fetchone()[0]
        print(f"Account {acc_id}: {order_count} orders placed.")
        # Some might have failed if cost > cash, but given 1M initial and mock price, they should pass.
        assert order_count > 0, f"No orders found for {acc_id}"
        
        # Check positions
        cursor.execute("SELECT COUNT(*) FROM positions WHERE account_id = ?", (acc_id,))
        pos_count = cursor.fetchone()[0]
        print(f"Account {acc_id}: {pos_count} active positions.")
        assert pos_count > 0, f"No positions found for {acc_id}"
    
    conn.close()
    
    # 4. Check Leaderboard & Advice
    print("\n[4/4] Checking Leaderboard and Advice...")
    lb_after = tm.get_leaderboard()
    print("\nUpdated Leaderboard:")
    print(lb_after[["Name", "Total Equity", "Unrealized PnL"]])
    
    advice = tm.get_winner_advise()
    print(f"\nAI Advice:\n{advice}")
    assert "現在、" in advice
    
    print("\n✨ TOURNAMENT CYCLE TEST PASSED ✨")

if __name__ == "__main__":
    try:
        test_shadow_tournament_cycle()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
