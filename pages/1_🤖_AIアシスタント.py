"""
AI投資アシスタント：自然言語対話インターフェース
ユーザーの質問を自然言語で理解し、回答を生成
"""

import streamlit as st
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass

# 設定
st.set_page_config(page_title="AI投資アシスタント", page_icon="🤖", layout="centered")


@dataclass
class ConversationContext:
    """会話コンテキスト"""

    user_id: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    user_preferences: Dict[str, Any]
    last_intent: Optional[str] = None
    last_entities: Dict[str, Any] = None


class NLUProcessor:
    """自然言語理解処理クラス"""

    def __init__(self):
        self.intents = {
            "portfolio_inquiry": [
                r"ポートフォリオ",
                r"資産",
                r"保有",
                r"現在の状況",
                r"どれくらい",
                r"いくら",
                r"成績",
                r"利益",
                r"損失",
            ],
            "market_analysis": [
                r"市場",
                r"相場",
                r"景気",
                r"トレンド",
                r"分析",
                r"見通し",
                r"予測",
                r"どうなる",
            ],
            "trading_request": [
                r"買う",
                r"売る",
                r"取引",
                r"注文",
                r"執行",
                r"購入",
                "売却",
                r"入札",
                r"決済",
            ],
            "risk_inquiry": [
                r"リスク",
                r"危険性",
                r"安全性",
                r"損切り",
                r"ドローダウン",
                r"損失",
                r"守り",
            ],
            "learning_request": [
                r"教えて",
                r"説明して",
                r"なぜ",
                r"どうして",
                r"意味",
                r"方法",
                r"やり方",
                r"知りたい",
            ],
            "greeting": [
                r"こんにちは",
                r"おはよう",
                r"こんばんは",
                r"ありがとう",
                r"さようなら",
                r"お世話になります",
            ],
        }

        self.entity_patterns = {
            "ticker": r"[0-9]{4}([A-Z.]|\.T)?",
            "price": r"¥?[0-9,]+円?",
            "percentage": r"[0-9]+\.?[0-9]*%",
            "timeframe": r"今日|明日|今週|今月|今年",
            "amount": r"[0-9,]+万?円?",
        }

    def analyze_intent(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        意図とエンティティを分析

        Args:
            text: ユーザー入力テキスト

        Returns:
            (意図, エンティティ辞書）
        """
        text = text.lower()

        # 意図分析
        intent = "unknown"
        max_matches = 0

        for intent_name, patterns in self.intents.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text))
            if matches > max_matches:
                intent = intent_name
                max_matches = matches

        # エンティティ抽出
        entities = {}
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches

        return intent, entities

    def extract_ticker(self, text: str) -> Optional[str]:
        """銘柄コードを抽出"""
        match = re.search(r"([0-9]{4})", text)
        return match.group(1) if match else None

    def extract_amount(self, text: str) -> Optional[int]:
        """金額を抽出"""
        # 万円単位の処理
        match = re.search(r"([0-9,]+)万?円?", text)
        if match:
            amount_str = match.group(1).replace(",", "")
            amount = int(amount_str)
            if "万" in text:
                amount *= 10000
            return amount
        return None


class ResponseGenerator:
    """応答生成クラス"""

    def __init__(self):
        self.response_templates = {
            "greeting": [
                "こんにちは！AI投資アシスタントです。今日の市場状況やポートフォリオについてお手伝いできます。",
                "おはようございます！本日の投資戦略についてご相談しましょう。",
                "こんばんは！市場の終値チェックと明日の戦略をご提案できます。",
            ],
            "portfolio_inquiry": [
                "現在のポートフォリオ状況をお伝えします。総資産: {total_value:,}円、損益: {pnl:+,}円（{pnl_pct:+.1%}）",
                "本日のポートフォリオ成績です。リターン: {daily_return:+.1%}、最大ドローダウン: {max_dd:-.1%}",
            ],
            "market_analysis": [
                "現在の市場分析です。日経平均: {nikkei:+.1%}、米国市場: {sp500:+.1%}、為替: {usdjpy:+.1%}",
                "市場トレンド分析: トレンドは{trend}、ボラティリティは{volatility}水準です。",
            ],
            "trading_request": [
                "{ticker}の{action}注文ですね。現在価格: {price:,}円で執行しますか？",
                "{ticker}を{amount:,}円分{action}します。よろしいですか？",
            ],
            "risk_inquiry": [
                "現在のリスク状況です。ポートフォリオβ: {beta:.2f}、VaR(95%): {var:,}円",
                "リスク分析: 現在のリスクレベルは{risk_level}です。推奨アクション: {recommendation}",
            ],
            "learning_request": [
                "{topic}について説明します。{explanation}",
                "{question}ですね。{answer}",
            ],
            "unknown": [
                "すみません、その質問にはお答えできません。他に質問はありますか？",
                "よく分かりませんでした。ポートフォリオ、市場分析、取引、リスクについてご質問ください。",
            ],
        }

    def generate_response(
        self, intent: str, entities: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """
        応答を生成

        Args:
            intent: 意図
            entities: エンティティ
            context: コンテキスト情報

        Returns:
            生成された応答
        """
        if intent in self.response_templates:
            template = self.response_templates[intent][0]

            # テンプレートに値を埋め込み
            if intent == "portfolio_inquiry":
                return self._format_portfolio_response(template, context)
            elif intent == "market_analysis":
                return self._format_market_response(template, context)
            elif intent == "trading_request":
                return self._format_trading_response(template, entities)
            elif intent == "risk_inquiry":
                return self._format_risk_response(template, context)
            elif intent == "learning_request":
                return self._format_learning_response(template, entities)
            else:
                return template
        else:
            return self.response_templates["unknown"][0]

    def _format_portfolio_response(self, template: str, context: Dict[str, Any]) -> str:
        """ポートフォリオ応答をフォーマット"""
        # サンプルデータ（実際はデータベースから取得）
        portfolio_data = {
            "total_value": 1000000,
            "pnl": 25000,
            "pnl_pct": 2.5,
            "daily_return": 0.8,
            "max_dd": -5.2,
        }

        return template.format(**portfolio_data)

    def _format_market_response(self, template: str, context: Dict[str, Any]) -> str:
        """市場分析応答をフォーマット"""
        # 市場データサンプル
        market_data = {
            "nikkei": 1.2,
            "sp500": 0.8,
            "usdjpy": -0.3,
            "trend": "上昇傾向",
            "volatility": "低",
        }

        return template.format(**market_data)

    def _format_trading_response(self, template: str, entities: Dict[str, Any]) -> str:
        """取引応答をフォーマット"""
        ticker = entities.get("ticker", ["不明"])[0]
        action = "買付" if "買" in entities.get("action", [""]) else "売却"
        price = 15000  # 実際は市場データから取得
        amount = entities.get("amount", [None])[0] or 100000

        return template.format(ticker=ticker, action=action, price=price, amount=amount)

    def _format_risk_response(self, template: str, context: Dict[str, Any]) -> str:
        """リスク応答をフォーマット"""
        risk_data = {
            "beta": 1.05,
            "var": 50000,
            "risk_level": "中程度",
            "recommendation": "現状維持",
        }

        return template.format(**risk_data)

    def _format_learning_response(self, template: str, entities: Dict[str, Any]) -> str:
        """学習応答をフォーマット"""
        # 簡単な説明データベース
        explanations = {
            "ポートフォリオ": "ポートフォリオは複数の資産を組み合わせた投資のことです。分散投資でリスクを低減できます。",
            "リスク": "リスクは投資元本を損失する可能性のことです。リスクとリターンは比例関係にあります。",
            "分散投資": "複数の資産や業種に投資を分けることです。特定の資産の下落リスクを分散できます。",
            "ドローダウン": "資産価値が過去の最高値から下落した割合のことです。投資パフォーマンスの指標の一つです。",
        }

        # エンティティからキーワードを抽出
        keywords = []
        for value_list in entities.values():
            if isinstance(value_list, list):
                keywords.extend(value_list)

        topic = "投資"  # デフォルト
        explanation = "詳しい説明をご用意できません。"

        for kw in keywords:
            if kw in explanations:
                topic = kw
                explanation = explanations[kw]
                break

        return template.format(topic=topic, explanation=explanation)


class AIInvestmentAssistant:
    """AI投資アシスタントメインクラス"""

    def __init__(self):
        self.nlu = NLUProcessor()
        self.response_generator = ResponseGenerator()

        # セッション状態の初期化
        if "conversation_context" not in st.session_state:
            st.session_state.conversation_context = ConversationContext(
                user_id="default_user",
                session_id=str(datetime.now().strftime("%Y%m%d_%H%M%S")),
                conversation_history=[],
                user_preferences={},
            )

        if "messages" not in st.session_state:
            st.session_state.messages = []

    def process_message(self, user_input: str) -> str:
        """
        ユーザーメッセージを処理

        Args:
            user_input: ユーザー入力

        Returns:
            AI応答
        """
        # NLU処理
        intent, entities = self.nlu.analyze_intent(user_input)

        # コンテキスト更新
        context = self._get_current_context()
        context["last_intent"] = intent
        context["last_entities"] = entities

        # 応答生成
        response = self.response_generator.generate_response(intent, entities, context)

        # 会話履歴に保存
        self._save_conversation(user_input, response, intent, entities)

        return response

    def _get_current_context(self) -> Dict[str, Any]:
        """現在のコンテキストを取得"""
        # ポートフォリオ情報
        portfolio_info = {
            "total_value": 1000000,
            "positions": [
                {"ticker": "7203", "name": "トヨタ", "quantity": 100, "value": 1500000},
                {"ticker": "6758", "name": "ソニー", "quantity": 50, "value": 800000},
            ],
        }

        return {
            "portfolio": portfolio_info,
            "market": {"nikkei": 32000, "sp500": 4500, "usdjpy": 150},
        }

    def _save_conversation(
        self, user_input: str, ai_response: str, intent: str, entities: Dict[str, Any]
    ):
        """会話を保存"""
        st.session_state.messages.append(
            {"timestamp": datetime.now(), "type": "user", "content": user_input}
        )

        st.session_state.messages.append(
            {
                "timestamp": datetime.now(),
                "type": "assistant",
                "content": ai_response,
                "intent": intent,
                "entities": entities,
            }
        )

    def show_conversation_history(self):
        """会話履歴を表示"""
        for message in st.session_state.messages:
            if message["type"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    def show_quick_actions(self):
        """クイックアクションボタン"""
        st.subheader("🚀 クイック質問")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💰 ポートフォリオ確認"):
                user_input = "現在のポートフォリオ状況を教えて"
                response = self.process_message(user_input)
                st.rerun()

        with col2:
            if st.button("📈 市場分析"):
                user_input = "今日の市場状況はどうですか？"
                response = self.process_message(user_input)
                st.rerun()

        with col3:
            if st.button("⚠️ リスク確認"):
                user_input = "現在のリスクレベルを教えて"
                response = self.process_message(user_input)
                st.rerun()

    def show_suggested_questions(self):
        """提案質問を表示"""
        st.subheader("💭 このような質問もできます")

        suggested_questions = [
            "7203トヨタを10万円分買って",
            "今のポートフォリオの損益は？",
            "ドローダウンって何？",
            "市場の見通しを教えて",
            "リスクを低くするには？",
        ]

        for question in suggested_questions:
            if st.button(f"💬 {question}", key=f"q_{question[:10]}"):
                response = self.process_message(question)
                st.session_state.last_response = response
                st.rerun()


def main():
    """メイン関数"""
    st.title("🤖 AI投資アシスタント")
    st.markdown("投資について何でも聞いてください。自然な日本語でお答えします。")

    assistant = AIInvestmentAssistant()

    # 会話履歴表示
    if st.session_state.messages:
        assistant.show_conversation_history()

    # クイックアクション
    assistant.show_quick_actions()

    # 提案質問
    assistant.show_suggested_questions()

    # ユーザー入力
    user_input = st.chat_input("メッセージを入力してください...")

    if user_input:
        response = assistant.process_message(user_input)

        # 応答を表示
        with st.chat_message("assistant"):
            st.write(response)

    # サイドバーに会話統計
    with st.sidebar:
        st.subheader("📊 会話統計")

        total_messages = len(st.session_state.messages)
        user_messages = len(
            [m for m in st.session_state.messages if m["type"] == "user"]
        )

        st.metric("総メッセージ数", total_messages)
        st.metric("ユーザー質問数", user_messages)

        if st.session_state.messages:
            last_intent = next(
                (
                    m.get("intent", "unknown")
                    for m in reversed(st.session_state.messages)
                    if m["type"] == "assistant"
                ),
                "unknown",
            )
            st.metric("最後の意図", last_intent)

        # 会話履歴のクリア
        if st.button("🗑️ 会話をクリア"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()
