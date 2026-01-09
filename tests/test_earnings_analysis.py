"""
Test script for Earnings RAG and Analyzer
決算分析機能のテスト
"""

import pytest
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@pytest.mark.skip(reason="chromadb not installed")
def test_rag_basic():
    """RAGエンジンの基本テスト"""
    from src.rag.earnings_rag import EarningsRAG
    
    logger.info("=" * 60)
    logger.info("Test 1: RAG Basic Functionality")
    logger.info("=" * 60)
    
    try:
        rag = EarningsRAG()
        
        # サンプルデータ
        sample_pdf_data = {
            "text": """
            当社の2024年第3四半期決算について報告いたします。
            
            売上高: 1000億円（前年同期比+15%）
            営業利益: 120億円（前年同期比+20%）
            純利益: 80億円（前年同期比+18%）
            
            主要トピック:
            - 新製品Aの販売が好調で、売上の30%を占める
            - 海外市場での売上が前年比+25%と大幅増
            - コスト削減施策により、利益率が改善
            
            リスク要因:
            - 原材料価格の上昇圧力
            - 為替変動による影響
            """,
            "metadata": {
                "company": "テスト株式会社",
                "date": "2024-11-01"
            }
        }
        
        # インデックス化
        logger.info("Indexing document...")
        success = rag.index_document(sample_pdf_data, "TEST_2024Q3")
        
        if success:
            logger.info("✅ Indexing successful")
        else:
            logger.error("❌ Indexing failed")
            return False
        
        # 検索テスト
        logger.info("Testing query...")
        results = rag.query("売上高はいくらですか？", n_results=2)
        
        if results:
            logger.info(f"✅ Query successful. Found {len(results)} results")
            for idx, r in enumerate(results):
                logger.info(f"Result {idx + 1}: {r['text'][:100]}...")
        else:
            logger.warning("⚠️ No results found")
        
        # ドキュメント要約
        summary = rag.get_document_summary("TEST_2024Q3")
        logger.info(f"Document summary: {summary}")
        
        # クリーンアップ
        rag.delete_document("TEST_2024Q3")
        logger.info("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


@pytest.mark.skip(reason="chromadb not installed")
def test_analyzer_basic():
    """LLM分析器の基本テスト"""
    from src.rag.earnings_analyzer import EarningsAnalyzer
    
    logger.info("=" * 60)
    logger.info("Test 2: Analyzer Basic Functionality")
    logger.info("=" * 60)
    
    try:
        analyzer = EarningsAnalyzer()
        
        # サンプルデータ
        sample_pdf_data = {
            "text": """
            当社の2024年第3四半期決算について報告いたします。
            
            売上高: 1000億円（前年同期比+15%）
            営業利益: 120億円（前年同期比+20%）
            純利益: 80億円（前年同期比+18%）
            
            主要トピック:
            - 新製品Aの販売が好調で、売上の30%を占める
            - 海外市場での売上が前年比+25%と大幅増
            - コスト削減施策により、利益率が改善
            
            リスク要因:
            - 原材料価格の上昇圧力
            - 為替変動による影響
            - 競合他社の新製品投入
            """,
            "metadata": {
                "company": "テスト株式会社",
                "date": "2024-11-01"
            }
        }
        
        # 分析実行
        logger.info("Analyzing earnings...")
        result = analyzer.analyze(sample_pdf_data)
        
        if "error" in result:
            logger.error(f"❌ Analysis failed: {result['error']}")
            return False
        
        logger.info("✅ Analysis successful")
        logger.info(f"Recommendation: {result.get('recommendation')}")
        logger.info(f"Confidence: {result.get('confidence')}")
        logger.info(f"Sentiment: {result.get('sentiment')}")
        logger.info(f"Reasoning: {result.get('reasoning')}")
        
        # 簡易サマリーテスト
        logger.info("Testing quick summary...")
        summary = analyzer.quick_summary(sample_pdf_data)
        logger.info(f"Quick summary: {summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


@pytest.mark.skip(reason="chromadb not installed")
def test_integration():
    """RAG + Analyzer統合テスト"""
    from src.rag.earnings_rag import EarningsRAG
    from src.rag.earnings_analyzer import EarningsAnalyzer
    
    logger.info("=" * 60)
    logger.info("Test 3: RAG + Analyzer Integration")
    logger.info("=" * 60)
    
    try:
        rag = EarningsRAG()
        analyzer = EarningsAnalyzer()
        
        # サンプルデータ
        sample_pdf_data = {
            "text": """
            当社の2024年第3四半期決算について報告いたします。
            
            【業績ハイライト】
            売上高: 1000億円（前年同期比+15%）
            営業利益: 120億円（前年同期比+20%）
            純利益: 80億円（前年同期比+18%）
            EPS: 120円（前年同期比+18%）
            
            【事業別売上】
            - デジタルソリューション事業: 600億円（+20%）
            - ハードウェア事業: 300億円（+8%）
            - サービス事業: 100億円（+15%）
            
            【主要トピック】
            1. 新製品Aの販売が好調で、売上の30%を占める
            2. 海外市場での売上が前年比+25%と大幅増
            3. コスト削減施策により、利益率が改善
            4. AI関連事業への投資を拡大
            
            【リスク要因】
            - 原材料価格の上昇圧力
            - 為替変動による影響
            - 競合他社の新製品投入
            - サプライチェーンの不安定性
            
            【今後の見通し】
            通期業績予想は据え置き。ただし、第4四半期は季節要因により増収増益を見込む。
            """,
            "metadata": {
                "company": "統合テスト株式会社",
                "date": "2024-11-01"
            }
        }
        
        # RAGインデックス化
        logger.info("Indexing with RAG...")
        doc_id = "INTEGRATION_TEST_2024Q3"
        success = rag.index_document(sample_pdf_data, doc_id)
        
        if not success:
            logger.error("❌ RAG indexing failed")
            return False
        
        logger.info("✅ RAG indexing successful")
        
        # RAGを使用した分析
        logger.info("Analyzing with RAG...")
        result = analyzer.analyze(sample_pdf_data, rag, doc_id)
        
        if "error" in result:
            logger.error(f"❌ Analysis failed: {result['error']}")
            return False
        
        logger.info("✅ Analysis with RAG successful")
        logger.info(f"Recommendation: {result.get('recommendation')}")
        logger.info(f"Confidence: {result.get('confidence')}")
        logger.info(f"Key Topics: {result.get('key_topics')}")
        logger.info(f"Risk Factors: {result.get('risk_factors')}")
        
        # クリーンアップ
        rag.delete_document(doc_id)
        logger.info("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Starting Earnings Analysis Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("RAG Basic", test_rag_basic()))
    results.append(("Analyzer Basic", test_analyzer_basic()))
    results.append(("Integration", test_integration()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("❌ SOME TESTS FAILED")
        logger.error("=" * 60)
        sys.exit(1)
