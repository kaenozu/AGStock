"""
Verification Test for Advanced Features (Phases 29, 30, 22)
Mocked for environments without API keys.
"""

import logging
import sys
import os
import json
from unittest.mock import MagicMock, patch

# Mock external services before imports
# We don't mock chromadb here because it's a package with submodules
# but we will mock the rag engine later
sys.modules['google.generativeai'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_phase29_integration():
    """AI委員会と決算データの統合テスト"""
    from src.schemas import TradingDecision
    
    logger.info("Testing Phase 29: Committee Integration")
    
    # 1. 擬似決算データの保存 (DBパスを分ける)
    with patch('src.data.earnings_history.EarningsHistory') as mock_hist:
        mock_hist_inst = mock_hist.return_value
        mock_hist_inst.get_latest_for_ticker.return_value = {
            "recommendation": "BUY",
            "confidence": 0.85,
            "sentiment": "POSITIVE",
            "reasoning": "Mock reasoning."
        }
        
        # 2. 委員会の実行 (Reasonerをモック)
        with patch('src.agents.market_analyst.get_llm_reasoner') as mock_get_reasoner:
            from src.agents.committee import InvestmentCommittee
            
            mock_reasoner = MagicMock()
            mock_reasoner.analyze_market_impact.return_value = {
                "sentiment": "BULLISH",
                "key_drivers": ["Mock Driver"]
            }
            mock_get_reasoner.return_value = mock_reasoner
            
            committee = InvestmentCommittee()
            signal_data = {
                "action": "BUY",
                "strategy": "Ensemble",
                "reason": "Technical breakout",
                "price": 150.0,
                "sentiment_score": 0.5
            }
            
            decision = committee.review_candidate("AAPL", signal_data)
            logger.info(f"Committee Decision for AAPL: {decision.value}")
            
    return decision in [TradingDecision.BUY, TradingDecision.HOLD, TradingDecision.SELL]

def test_phase30_watcher():
    """適時開示ウォッチのテスト (Mocked)"""
    # ここでも依存関係をしっかりモック
    with patch('src.rag.filing_watcher.EarningsAnalyzer') as mock_analyzer, \
         patch('src.rag.filing_watcher.EarningsRAG') as mock_rag, \
         patch('src.rag.filing_watcher.PDFLoader') as mock_loader, \
         patch('src.rag.filing_watcher.EarningsHistory') as mock_hist:
        
        from src.rag.filing_watcher import FilingWatcher
        
        logger.info("Testing Phase 30: Filing Watcher")
        
        watcher = FilingWatcher(watch_dir="./data/test_filings")
        
        # モックの設定
        mock_loader_inst = mock_loader.return_value
        mock_loader_inst.load_pdf.return_value = {
            "text": "Sample PDF text",
            "metadata": {"ticker": "MSFT", "company": "Microsoft"}
        }
        
        mock_analyzer_inst = mock_analyzer.return_value
        mock_analyzer_inst.analyze.return_value = {
            "recommendation": "BUY",
            "sentiment": "POSITIVE",
            "reasoning": "Growth is solid."
        }
        
        # 擬似ファイルの作成
        os.makedirs("./data/test_filings", exist_ok=True)
        with open("./data/test_filings/test.pdf", "w") as f:
            f.write("mock pdf")
            
        watcher.scan_and_process()
        logger.info("Watcher scan completed")
        
    return True

def test_phase22_options():
    """オプション戦略のテスト"""
    from src.strategies.options_strategy import OptionsEngine
    
    logger.info("Testing Phase 22: Options Strategy")
    engine = OptionsEngine()
    
    # 1. Black-Scholes
    res = engine.black_scholes(100, 95, 0.1, 0.2, "put")
    logger.info(f"Put Price: {res['price']:.2f}")
    
    # 2. Hedge Advice
    advice = engine.get_hedge_advice({"equity": 1000000}, 28.0)
    logger.info(f"Hedge Status: {advice['status']}")
    
    return advice["status"] in ["CAUTION", "NORMAL"]

if __name__ == "__main__":
    logger.info("Starting Advanced Features Verification (Mocked)")
    
    results = []
    try:
        results.append(("Phase 29 (Integration)", test_phase29_integration()))
    except Exception as e:
        logger.error(f"Phase 29 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 29 (Integration)", False))
        
    try:
        results.append(("Phase 30 (Watcher)", test_phase30_watcher()))
    except Exception as e:
        logger.error(f"Phase 30 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 30 (Watcher)", False))
        
    try:
        results.append(("Phase 22 (Options)", test_phase22_options()))
    except Exception as e:
        logger.error(f"Phase 22 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase 22 (Options)", False))
    
    logger.info("=" * 30)
    logger.info("TEST SUMMARY")
    logger.info("=" * 30)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    if all(r[1] for r in results):
        logger.info("🎉 ALL TESTS PASSED")
        sys.exit(0)
    else:
        logger.error("❌ SOME TESTS FAILED")
        sys.exit(1)
