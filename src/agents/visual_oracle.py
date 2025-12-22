
import logging
import os
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import io

from src.llm_reasoner import get_llm_reasoner

logger = logging.getLogger(__name__)

class VisualOracle:
    """
    Visual Chart Oracle (Phase 74)
    Generates chart images and uses Gemini Vision to identify technical patterns.
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.reasoner = get_llm_reasoner()
        self.output_dir = "data/charts"
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_chart(self, ticker: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Produce a chart, send to Gemini, and return analysis.
        """
        if df is None or df.empty:
            return {"error": "No data available"}

        # 1. Generate Chart Image
        image_path = self._generate_candlestick_chart(ticker, df)
        if not image_path:
            return {"error": "Failed to generate chart"}

        # 2. Prepare Prompt
        prompt = self._get_analysis_prompt(ticker)

        # 3. Call Gemini Vision
        logger.info(f"👁️ Sending {ticker} chart to Gemini Vision...")
        try:
            analysis = self.reasoner.analyze_image(image_path, prompt)
            analysis["image_path"] = image_path
            return analysis
        except Exception as e:
            logger.error(f"Visual analysis failed for {ticker}: {e}")
            return {"error": str(e)}

    def _generate_candlestick_chart(self, ticker: str, df: pd.DataFrame) -> Optional[str]:
        """
        Generate a simple candlestick-like chart using matplotlib.
        (We use colored bars for simplicity if mplfinance is unavailable)
        """
        try:
            # Use last 60 days for a clear view
            plot_df = df.tail(60).copy()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Simple manual candlestick implementation
            width = 0.6
            width2 = 0.05
            
            prices_up = plot_df[plot_df.Close >= plot_df.Open]
            prices_down = plot_df[plot_df.Close < plot_df.Open]
            
            # Up
            ax.bar(prices_up.index, prices_up.Close - prices_up.Open, width, bottom=prices_up.Open, color='g')
            ax.bar(prices_up.index, prices_up.High - prices_up.Close, width2, bottom=prices_up.Close, color='g')
            ax.bar(prices_up.index, prices_up.Low - prices_up.Open, width2, bottom=prices_up.Open, color='g')
            
            # Down
            ax.bar(prices_down.index, prices_down.Open - prices_down.Close, width, bottom=prices_down.Close, color='r')
            ax.bar(prices_down.index, prices_down.High - prices_down.Open, width2, bottom=prices_down.Open, color='r')
            ax.bar(prices_down.index, prices_down.Low - prices_down.Close, width2, bottom=prices_down.Close, color='r')
            
            # Moving Averages
            if len(plot_df) > 20:
                ma20 = plot_df['Close'].rolling(window=20).mean()
                ax.plot(plot_df.index, ma20, color='blue', label='MA20', alpha=0.7)
            
            ax.set_title(f"{ticker} - Visual Analysis Chart")
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
            # Save
            filename = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            full_path = os.path.abspath(os.path.join(self.output_dir, filename))
            plt.savefig(full_path, bbox_inches='tight')
            plt.close(fig)
            
            return full_path
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return None

    def _get_analysis_prompt(self, ticker: str) -> str:
        return f"""
        あなたはプロのテクニカルアナリストです。
        添付された {ticker} のチャート画像を分析し、以下の項目を特定してください。
        
        1. 顕著なチャートパターン (三尊、逆三尊、ダブルボトム、三角保ち合い、フラッグ等)
        2. トレンドの方向性 (強い上昇、弱い上昇、レンジ、弱い下落、強い下落)
        3. 主要なサポート・レジスタンスラインの有無
        4. 今回の視覚的な買い/売りの推奨度 (0.0 - 1.0)
        
        ## 出力フォーマット (JSONのみ)
        {{
            "patterns": ["パターン1", "パターン2"],
            "trend": "DIRECTION",
            "support_resistance": "説明",
            "visual_confidence": 0.0,
            "reasoning": "画像から読み取れる具体的な理由（150文字以内）",
            "action": "BUY/SELL/HOLD"
        }}
        """
