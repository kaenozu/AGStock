import logging
import sqlite3
import json
import os
import re
from typing import List, Dict, Any
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

class StrategyGenerator:
    """
    Analyzes past failures and evolves new strategy code using LLM.
    """

    def __init__(self, api_key: str = None):
        if api_key:
            genai.configure(api_key=api_key)
        self.output_dir = "src/strategies/evolved"
        os.makedirs(self.output_dir, exist_ok=True)

    def evolve_strategies(self, db_path: str = "committee_feedback.db"):
        """
        1. Extract failures from DB
        2. Ask Gemini to find patterns and write a NEW Python strategy
        3. Save the strategy to disk
        """
        failures = self._get_recent_failures(db_path)
        if not failures:
            logger.info("No failures to learn from. Evolution skipping.")
            return

        lessons_summary = self._summarize_failures(failures)
        new_strategy_code = self._generate_strategy_code(lessons_summary)
        
        if new_strategy_code:
            filename = f"evolved_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_strategy_code)
            logger.info(f"New evolved strategy saved: {file_path}")

    def _get_recent_failures(self, db_path: str) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM decision_feedback WHERE outcome = 'FAILURE' ORDER BY timestamp DESC LIMIT 10")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to fetch failures for evolution: {e}")
            return []

    def _summarize_failures(self, failures: List[Dict[str, Any]]) -> str:
        summary = "【過去の失敗事例の概要】\n"
        for f in failures:
            summary += f"- {f['ticker']}: 判断={f['decision']}, 理由={f['rationale']}, 収益率={f['return_1w']*100:.1f}%\n"
        return summary

    def _generate_strategy_code(self, context: str) -> str:
        """Calls Gemini to write refined Python code."""
        prompt = f"""
あなたは伝説的なクオンツ・エンジニアです。
以下の失敗パターンを分析し、これらを克服するための新しい「自律進化型トレード戦略」をPythonで記述してください。

{context}

【制約事項】
1. `src.strategies.base.Strategy` クラスを継承すること。
2. `generate_signals(self, df: pd.DataFrame) -> pd.Series` メソッドを実装すること。
3. `explain_prediction` などの説明メソッドも含めること。
4. ライブラリは `pandas`, `ta`, `numpy` 等を使用可能。
5. 出力は「Pythonコードのみ」とすること（マニュアルや説明文は不要）。
6. クラス名は `EvolvedStrategy` とすること。

コードを開始してください：
"""
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            code = response.text
            # Clean up markdown if LLM includes it
            if "```python" in code:
                code = re.search(r"```python\n(.*?)```", code, re.DOTALL).group(1)
            elif "```" in code:
                code = re.search(r"```\n(.*?)```", code, re.DOTALL).group(1)
            return code
        except Exception as e:
            logger.error(f"Failing to query Gemini for evolution: {e}")
            return None
