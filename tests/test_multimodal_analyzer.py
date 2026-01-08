import pytest
from unittest.mock import MagicMock, patch
from src.analysis.multimodal_analyzer import MultimodalAnalyzer

@pytest.fixture
def mock_gemini():
    # Patch where it is used
    with patch("src.analysis.multimodal_analyzer.genai.GenerativeModel") as mock_model:
        instance = mock_model.return_value
        # Mock JSON response
        mock_response = MagicMock()
        mock_response.text = '{"score": 0.8, "confidence": 0.9, "summary": "Test Summary"}'
        instance.generate_content.return_value = mock_response
        yield instance

def test_multimodal_text_analysis(mock_gemini):
    """テキスト分析の単体テスト"""
    # Create analyzer with a dummy key to ensure self.model is initialized
    analyzer = MultimodalAnalyzer(api_key="test_key")
    # Manually ensure the model is our mock instance if it wasn't already
    analyzer.model = mock_gemini
    
    result = analyzer._analyze_text_sentiment("テストテキスト")
    
    assert result["score"] == 0.8
    assert result["confidence"] == 0.9
    assert result["summary"] == "Test Summary"

def test_multimodal_fusion():
    """複数モーダルの統合ロジックテスト"""
    analyzer = MultimodalAnalyzer(api_key="test_key")
    components = {
        "text": {"score": 0.8},
        "audio": {"score": 0.6},
        "vision": {"score": 0.7}
    }
    
    overall = analyzer._fuse_results(components)
    
    # weights: text=0.4, audio=0.3, vision=0.3
    # 0.8*0.4 + 0.6*0.3 + 0.7*0.3 = 0.32 + 0.18 + 0.21 = 0.71
    assert abs(overall - 0.71) < 1e-5

def test_multimodal_insights():
    """インサイト生成のテスト"""
    analyzer = MultimodalAnalyzer(api_key="test_key")
    components = {
        "text": {"score": 0.8, "summary": "Good earnings"},
        "audio": {"score": 0.7},
    }
    
    insights = analyzer._generate_multimodal_insights(components)
    
    assert any("Good earnings" in i for i in insights)
    assert any("ポジティブなメッセージ" in i for i in insights)