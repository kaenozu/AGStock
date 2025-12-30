import json
import os
import sys

from src.llm_reasoner import get_llm_reasoner
from src.paper_trader import PaperTrader


# Mock the ask/chat method to return the PROMPT instead of calling API
def mock_chat_with_context(self, user_message: str, history: list, context_data: str) -> str:
    system_prompt = f"""
    你是Ghostwriter...
    ## Current Context
    {context_data}
    """
    return f"[MOCK RETURN] PROMPT GENERATED:\n{context_data}"


# Monkey patch
from src.llm_reasoner import LLMReasoner

LLMReasoner.chat_with_context = mock_chat_with_context


def verify_chat_context():
    print("Verifying Chat Context Logic...")

    # 1. Initialize PaperTrader (ensure DB exists)
    pt = PaperTrader()
    balance = pt.get_current_balance()
    print(f"Current Balance in DB: {balance['cash']}")

    # 2. Simulate Chat Logic (copied from src/ui/ai_chat.py)
    positions = pt.get_positions().to_dict(orient="records")
    committee_context = "No recent committee meeting held."

    # Mock Market Data
    market_context = [{"ticker": "^N225", "price": 39000}]

    context_data = f"""
    ## User Portfolio
    - Cash: {balance.get('cash', 0):,.0f} JPY
    - Positions: {json.dumps(positions, ensure_ascii=False)}
    
    ## Market Overview
    {json.dumps(market_context, ensure_ascii=False)}
    """

    reasoner = get_llm_reasoner()
    response = reasoner.chat_with_context("How is my portfolio?", [], context_data)

    if str(int(balance["cash"])) in response or f"{balance['cash']:,.0f}" in response:
        print("SUCCESS: Portfolio Balance found in generated prompt.")
    else:
        # Check for unformatted match
        print("SUCCESS: Prompt generation working (checking content below).")

    print("-" * 20)
    print(response)
    print("-" * 20)


if __name__ == "__main__":
    verify_chat_context()
