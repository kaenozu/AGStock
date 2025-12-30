import logging
import os
import io
import base64
import google.generativeai as genai
import pandas as pd
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
logger = logging.getLogger(__name__)
class ChartVisionEngine:
#     """
#     Translates market data into visual representations (images) and uses
#     Gemini Vision to interpret geometric patterns (Head and Shoulders, etc.)
#     """
def __init__(self):
        self._init_gemini()
    def _init_gemini(self):
        pass
#         """
#             Init Gemini.
#                     self.has_vision = False
#         api_key = os.getenv("GEMINI_API_KEY")
#         if api_key:
#             genai.configure(api_key=api_key)
# # Use 1.5 Pro or Flash (both support vision/multimodal)
#             self.model = genai.GenerativeModel('gemini-1.5-flash')
#             self.has_vision = True
#     """
def analyze_chart_vision(self, df: pd.DataFrame, ticker: str) -> Optional[Dict[str, Any]]:
#         """
#         1. Generates a visual plot of the OHLC data.
#         2. Encodes it as an image.
#         3. Sends to Gemini Vision for pattern analysis.
#                 if not self.has_vision or df.empty:
#                     return None
#             try:
#                 # 1. Generate a simple technical chart image using Matplotlib (no external headless reqs like kaleido)
#             plt.figure(figsize=(10, 6))
#             df_tail = df.tail(60)  # Last 60 bars for clarity
#                 plt.plot(df_tail.index, df_tail['Close'], label='Close Price', color='cyan')
# # Simple Moving Averages for visual context
#             plt.plot(df_tail.index, df_tail['Close'].rolling(20).mean(), label='20 SMA', color='orange', alpha=0.6)
#                 plt.title(f"{ticker} - Visual Analysis Context")
#             plt.grid(True, alpha=0.3)
#             plt.legend()
# # Save to buffer
#             buf = io.BytesIO()
#             plt.savefig(buf, format='png', facecolor='#0E1117')  # Match Streamlit dark theme if possible
#             plt.close()  # Free memory
# # 2. Prepare payload for Gemini
#             image_bytes = buf.getvalue()
# # 3. Prompting
#             prompt = f"""
You are a master chartist and technical analyst. 
            Analyze this price chart for {ticker}.
                        TASK:
                            1. Identify any geometric patterns (Head & Shoulders, Double Top/Bottom, Triangles, Flages, etc.).
            2. Identify support and resistance levels.
            3. Provide a visual verdict (BULLISH, BEARISH, or NEUTRAL).
                        Output ONLY a JSON object with keys:
                            - "patterns": list of identified patterns
            - "support": estimated support price
            - "resistance": estimated resistance price
            - "verdict": "BULLISH" | "BEARISH" | "NEUTRAL"
            - "visual_rationale": Short explanation of what you see in the chart.
            # Combine image and text
            response = self.model.generate_content([
                prompt,
                {'mime_type': 'image/png', 'data': image_bytes}
            ])
# Parsing
text = response.text.replace('```json', '').replace('```', '').strip()
            return pd.io.json.loads(text)
            except Exception as e:
                logger.error(f"Chart vision analysis failed for {ticker}: {e}")
            return None
    def get_image_base64(self, df: pd.DataFrame) -> str:
#             """Utility for UI to display the same 'vision' the AI saw."""
plt.figure(figsize=(10, 4))
        df_tail = df.tail(60)
        plt.plot(df_tail.index, df_tail['Close'], color='cyan')
        plt.title("AI Visual Perspective")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#0E1117')
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')
