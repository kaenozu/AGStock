"""
Multimodal Sentiment Analyzer
音声、動画、テキストを統合した高度な感情分析エンジン
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

from src.utils import retry_with_backoff

load_dotenv()
logger = logging.getLogger(__name__)

class MultimodalAnalyzer:
    """
    マルチモーダルデータ（動画・音声・テキスト）を統合して感情分析を行うクラス
    Gemini 2.0 Flash を活用して高度な分析を実現
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
            logger.warning("Google API Key not found. Multimodal analysis will be limited.")
            
        # デフォルトの重み付け
        self.weights = {
            "text": 0.4,
            "audio_tone": 0.3,
            "facial_expression": 0.3
        }

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def analyze_earnings_presentation(
        self, 
        video_path: Optional[str] = None, 
        audio_path: Optional[str] = None, 
        transcript: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        決算説明会のマルチモーダル分析を実行する
        """
        results = {
            "overall_sentiment": 0.0,
            "confidence_score": 0.0,
            "components": {},
            "timestamp": datetime.now().isoformat()
        }

        # 1. テキスト分析 (LLMによる文脈・論理分析)
        if transcript:
            text_res = self._analyze_text_sentiment(transcript)
            results["components"]["text"] = text_res
        
        # 2. 音声トーン分析 (自信、緊張、エネルギー)
        if audio_path and os.path.exists(audio_path):
            audio_res = self._analyze_audio_tone(audio_path)
            results["components"]["audio"] = audio_res
            
        # 3. 表情・視覚分析 (チャートや経営者の表情)
        if video_path and os.path.exists(video_path):
            vision_res = self._analyze_facial_expressions(video_path)
            results["components"]["vision"] = vision_res

        # 4. 統合スコアリング
        results["overall_sentiment"] = self._fuse_results(results["components"])
        
        # 5. 特徴的な洞察の抽出
        results["insights"] = self._generate_multimodal_insights(results["components"])

        return results

    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """テキストの内容から論理的なポジティブさを判定"""
        if not self.model:
            return {"score": 0.5, "confidence": 0.5, "reason": "No API Key"}

        prompt = f"""
        以下の決算説明会テキストを分析し、感情スコア（0.0: 非常にネガティブ, 1.0: 非常にポジティブ）と
        その信頼度（0.0-1.0）をJSON形式で出力してください。
        
        テキスト:
        {text[:2000]}
        
        出力形式:
        {{"score": 0.0-1.0, "confidence": 0.0-1.0, "summary": "簡潔な要約"}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # JSON部分を抽出
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return {"score": 0.5, "confidence": 0.3, "error": str(e)}

    def _analyze_audio_tone(self, path: str) -> Dict[str, Any]:
        """声のトーンから「自信」や「緊張」を判定"""
        # Gemini 1.5/2.0 は音声ファイルを直接扱える
        try:
            audio_file = genai.upload_file(path=path)
            prompt = "この音声のトーン（自信、誠実さ、熱意）を分析し、ポジティブ度スコア(0-1)をJSONで返してください。"
            response = self.model.generate_content([prompt, audio_file])
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Audio analysis failed, using mock: {e}")
            return {"score": 0.6, "confidence": 0.4}

    def _analyze_facial_expressions(self, path: str) -> Dict[str, Any]:
        """視覚情報（チャートや表情）を判定"""
        try:
            video_file = genai.upload_file(path=path)
            prompt = "この動画/画像の視覚的印象（チャートのトレンドや発表者の表情）を分析し、ポジティブ度スコア(0-1)をJSONで返してください。"
            response = self.model.generate_content([prompt, video_file])
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Vision analysis failed, using mock: {e}")
            return {"score": 0.6, "confidence": 0.4}

    def _fuse_results(self, components: Dict[str, Any]) -> float:
        """各モーダルの結果を統合"""
        score = 0.0
        total_weight = 0.0
        
        mapping = {
            "text": "text",
            "audio": "audio_tone",
            "vision": "facial_expression"
        }
        
        for comp_key, weight_key in mapping.items():
            if comp_key in components:
                weight = self.weights[weight_key]
                score += components[comp_key].get("score", 0.5) * weight
                total_weight += weight
                
        return score / total_weight if total_weight > 0 else 0.5

    def _generate_multimodal_insights(self, components: Dict[str, Any]) -> List[str]:
        """統合されたインサイトを生成"""
        insights = []
        
        text = components.get("text", {})
        audio = components.get("audio", {})
        vision = components.get("vision", {})
        
        if "summary" in text:
            insights.append(f"テキスト要約: {text['summary']}")
            
        if text.get("score", 0.5) > 0.6 and audio.get("score", 0.5) > 0.6:
            insights.append("言葉と声のトーンの両面でポジティブなメッセージが確認されました。")
            
        return insights

if __name__ == "__main__":
    analyzer = MultimodalAnalyzer()
    # テスト
    res = analyzer.analyze_earnings_presentation(transcript="今期は過去最高の増益となる見込みです。")
    print(json.dumps(res, indent=2, ensure_ascii=False))
