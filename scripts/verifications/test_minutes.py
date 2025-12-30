import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.agents.committee import InvestmentCommittee
from src.schemas import TradingDecision

def test_committee_minutes():
    print("Testing AI Committee Meeting Minutes Persistence...")
    committee = InvestmentCommittee()
    
    mock_signal = {
        "ticker": "AAPL",
        "action": "BUY",
        "price": 195.0,
        "strategy": "TestStrategy",
        "reason": "Uptrend detected",
        "sentiment_score": 0.5,
        "history_df": None
    }
    
    # Run committee review
    print("Running committee review...")
    decision = committee.review_candidate("AAPL", mock_signal)
    print(f"Committee Decision: {decision.value}")
    
    # Check if minutes are saved
    from src.paths import DATA_DIR
    minutes_dir = DATA_DIR / "meeting_minutes"
    
    files = list(minutes_dir.glob("*_AAPL.json"))
    print(f"Found {len(files)} minutes files for AAPL.")
    assert len(files) > 0, "No meeting minutes file found!"
    
    # Load and verify content
    with open(files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) > 0
        latest = data[-1]
        print(f"Minutes file content verified. Final Decision: {latest['final_decision']}")
        assert "analyses" in latest
        assert "rationale" in latest

if __name__ == "__main__":
    try:
        test_committee_minutes()
        print("\n✅ AI MINUTES PERSISTENCE VERIFIED")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
