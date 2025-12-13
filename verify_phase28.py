import os
import sys
from io import BytesIO
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), ""))


def test_embeddings_hunter():
    print("\n[VERIFY] Phase 28: Earnings Hunter")

    # 1. Dependency Check
    try:
        import pypdf

        print("  Dependency (pypdf): OK")
    except ImportError:
        print("  FAILURE: pypdf not installed")
        return

    # 2. Backend Import Check
    try:
        from src.analysis.pdf_reader import EarningsAnalyzer, PDFExtractor

        print("  Backend Imports: OK")
    except ImportError as e:
        print(f"  FAILURE: Import error: {e}")
        return

    # 3. Analyze Logic Check (Mocking LLM)
    try:
        analyzer = EarningsAnalyzer()
        # Mock LLMReasoner
        analyzer.llm = MagicMock()
        analyzer.llm.analyze_earnings_report.return_value = {
            "summary": "Mock Summary",
            "raw_analysis": "Mock Analysis Result: Positive",
        }

        result = analyzer.analyze_report("This is a dummy earnings report text.")

        if "raw_analysis" in result:
            print("  Analyzer Logic: OK")
        else:
            print(f"  FAILURE: Analyzer output mismatch: {result}")

    except Exception as e:
        print(f"  FAILURE: Logic check failed: {e}")

    # 4. UI Import Check
    try:
        from src.ui.earnings_analyst import render_earnings_analyst

        print("  UI Imports: OK")
        print("  SUCCESS")
    except ImportError as e:
        print(f"  FAILURE: UI Import error: {e}")


if __name__ == "__main__":
    test_embeddings_hunter()
