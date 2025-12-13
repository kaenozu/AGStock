import json

from src.agents.committee import InvestmentCommittee


def verify_committee_backend():
    print("Initializing Investment Committee...")
    committee = InvestmentCommittee()

    ticker = "7203.T"  # Toyota
    market_stats = {"price": 2500, "vix": 18.0, "market_trend": "Neutral"}

    print(f"Conducting debate for {ticker}...")
    debate_log = committee.conduct_debate(ticker, market_stats)

    print("-" * 30)
    for entry in debate_log:
        print(f"[{entry['agent']}]: {entry['message'][:50]}... (Decision: {entry['decision']})")
    print("-" * 30)

    if len(debate_log) == 3:
        print("SUCCESS: Debate generated 3 entries (Analyst, Risk, Chair).")
    else:
        print(f"FAILURE: Expected 3 entries, got {len(debate_log)}.")


if __name__ == "__main__":
    verify_committee_backend()
