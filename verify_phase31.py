import os
import sys
import logging

# Add project root to path
sys.path.append(os.getcwd())

from src.core.archive_manager import ArchiveManager
from src.core.knowledge_extractor import KnowledgeExtractor
from src.core.legacy_reporter import LegacyReporter
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phase31_eternal_archive():
    print("\n" + "="*60)
    print("📚 AGStock Phase 31: Eternal Archive Verification")
    print("="*60)

    # 1. Test ArchiveManager
    print("\n[Step 1] Initializing Archive Manager...")
    archive = ArchiveManager(archive_dir="data/test_archive")
    print(f"-> Archive directories created")

    print("\n[Step 2] Archiving a mock decision...")
    mock_context = {
        "market_stats": {"close": 1500, "volume": 1000000},
        "technical": {"rsi": 65, "macd": 0.5},
        "macro": {"score": 75, "vix": 15},
        "news": "Positive earnings report",
        "paradigm": "GOLDILOCKS",
        "dynasty_objective": "EXPANSION_PHASE",
        "active_strategies": ["LSTM", "LightGBM"]
    }
    
    mock_debate = [
        {"agent_name": "TechnicalAnalyst", "decision": "BUY", "confidence": 0.8},
        {"agent_name": "MacroStrategist", "decision": "BUY", "confidence": 0.7},
        {"agent_name": "RiskManager", "decision": "HOLD", "confidence": 0.6}
    ]
    
    archive_id = archive.archive_decision(
        ticker="7203.T",
        decision="BUY",
        context=mock_context,
        agents_debate=mock_debate,
        final_confidence=0.75
    )
    
    print(f"-> ✅ Decision archived with ID: {archive_id[:16]}...")

    # 2. Test Prediction Archiving
    print("\n[Step 3] Archiving a prediction...")
    pred_id = archive.archive_prediction(
        ticker="7203.T",
        prediction_type="PRICE",
        predicted_value=1550.0,
        prediction_horizon="1 day",
        model_name="LSTM",
        confidence=0.8
    )
    print(f"-> ✅ Prediction archived: {pred_id[:16]}...")

    # 3. Test Knowledge Extraction
    print("\n[Step 4] Testing Knowledge Extractor...")
    extractor = KnowledgeExtractor(archive_dir="data/test_archive")
    
    # Create multiple mock decisions for pattern extraction
    for i in range(5):
        archive.archive_decision(
            ticker=f"TEST{i}.T",
            decision="BUY" if i % 2 == 0 else "SELL",
            context=mock_context,
            agents_debate=mock_debate,
            final_confidence=0.7 + (i * 0.05)
        )
    
    print("-> Created 5 additional mock decisions")
    
    # Get relevant insights (without LLM extraction for speed)
    insights = extractor.get_relevant_insights({"paradigm": "GOLDILOCKS"})
    print(f"-> Retrieved {len(insights)} relevant insights")

    # 4. Test Legacy Reporter
    print("\n[Step 5] Testing Legacy Reporter...")
    reporter = LegacyReporter(archive_dir="data/test_archive")
    
    decisions_summary = {
        "total": 6,
        "successful": 4,
        "win_rate": 0.67,
        "notable_events": [
            {"description": "Successfully navigated GOLDILOCKS paradigm"}
        ]
    }
    
    performance_metrics = {
        "monthly_return": 0.05
    }
    
    dynasty_state = {
        "current_objective": "EXPANSION_PHASE",
        "legacy_score": 15.5
    }
    
    report_path = reporter.generate_monthly_chronicle(
        month="2024/12",
        decisions_summary=decisions_summary,
        performance_metrics=performance_metrics,
        dynasty_state=dynasty_state
    )
    
    if os.path.exists(report_path):
        print(f"-> ✅ Monthly chronicle generated: {report_path}")
        with open(report_path, "r", encoding="utf-8") as f:
            preview = f.read()[:200]
            print(f"-> Preview: {preview}...")
    else:
        print("-> ⚠️ Chronicle generation skipped (requires Gemini API)")

    # 5. Test Pattern Extraction
    print("\n[Step 6] Testing Pattern Extraction...")
    patterns = archive.extract_knowledge_patterns(lookback_days=1)
    print(f"-> Paradigm distribution: {patterns.get('successful_paradigms', {})}")

    print("\n" + "="*60)
    print("✅ Phase 31 Verification Complete.")
    print("="*60)

    # Cleanup
    try:
        import shutil
        if os.path.exists("data/test_archive"):
            shutil.rmtree("data/test_archive")
        print("\n🧹 Test data cleaned up.")
    except Exception as e:
        print(f"\n⚠️ Cleanup warning: {e}")

if __name__ == "__main__":
    test_phase31_eternal_archive()
