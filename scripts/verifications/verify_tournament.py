import os
import sys
import sqlite3
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.paper_trader import PaperTrader
from src.trading.tournament_manager import TournamentManager, PERSONALITIES
from src.paths import PAPER_TRADING_DB

def test_tournament_init():
    print("Testing Tournament Initialization...")
    main_pt = PaperTrader(account_id="main")
    tm = TournamentManager()
    
    # Check if all accounts are initialized in DB
    conn = sqlite3.connect(PAPER_TRADING_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT account_id FROM balance")
    accounts = [row[0] for row in cursor.fetchall()]
    print(f"Initialized accounts in balance table: {accounts}")
    
    for acc_id in PERSONALITIES.keys():
        assert acc_id in accounts, f"{acc_id} missing from balance table"
        
    # Check if 'main' also exists (backward compatibility)
    assert "main" in accounts, "'main' account should exist"
    
    print("✅ Tournament DB Initialization OK")
    
    # Check leaderboard
    lb = tm.get_leaderboard()
    print("\nInitial Leaderboard:")
    print(lb[["Name", "Total Equity"]])
    assert len(lb) == len(PERSONALITIES)
    print("✅ Leaderboard Generation OK")

if __name__ == "__main__":
    try:
        test_tournament_init()
        print("\n✨ TOURNAMENT INFRASTRUCTURE VERIFIED ✨")
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
