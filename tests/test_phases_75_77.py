import pytest
import pandas as pd
from src.execution.position_sizer import PositionSizer
from src.data.feedback_store import FeedbackStore
import os

def test_position_sizer_dynamic():
    sizer = PositionSizer(max_position_pct=0.2)
    equity = 1000000
    
    # High confidence should give more amount than low confidence
    size_high = sizer.calculate_size("7203.T", equity, confidence=0.8)
    size_low = sizer.calculate_size("7203.T", equity, confidence=0.2)
    
    assert size_high["amount"] > size_low["amount"]
    assert size_high["params"]["adjusted_p"] > size_low["params"]["adjusted_p"]
    assert size_high["equity_fraction"] <= 0.2

def test_feedback_store_agents():
    db_path = "test_feedback.db"
    if os.path.exists(db_path): os.remove(db_path)
    
    store = FeedbackStore(db_path)
    
    # Save a decision with agent scores
    store.save_decision(
        ticker="AAPL",
        decision="BUY",
        rationale="Test",
        current_price=150.0,
        raw_data={},
        agent_scores={"visual": 0.8, "social": 0.6, "tech": 0.7, "confidence": 0.75}
    )
    
    # Update outcome manually for leaderboard test
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE decision_feedback SET outcome = 'SUCCESS', price_1w = 160.0, return_1w = 0.066 WHERE ticker = 'AAPL'")
    
    leaderboard = store.get_agent_leaderboard()
    assert "visual_pred" in leaderboard
    assert leaderboard["visual_pred"]["total_signals"] == 1
    assert leaderboard["visual_pred"]["accuracy"] == 1.0

if __name__ == "__main__":
    import sqlite3
    test_position_sizer_dynamic()
    test_feedback_store_agents()
    print("Tests passed!")
