import random
from datetime import datetime
from typing import List, Dict, Any


class NeuromancerIndices:
    """AIの感情と状態を管理するクラス"""

    def __init__(self):
        self.mood = "Neutral"  # Neutral, Excited, Cautious, Panic, Zen
        self.loyalty = 100
        self.energy = 100


class Neuromancer:
    """
    能動的AIエージェント
    システムの状態を監視し、マスター（ユーザー）に対して自発的に発話する。
    """

    def __init__(self):
        self.name = "Neuromancer"
        self.indices = NeuromancerIndices()

    def perceive_world(self, market_data: Dict[str, Any] = None) -> str:
        """外界（市場データ）を認識し、独り言や警告を生成する"""
        if not market_data:
            return self._idle_talk()

        vix = market_data.get("vix", 20.0)
        pnl = market_data.get("daily_pnl", 0.0)

        # 感情の変化
        if vix > 30:
            self.indices.mood = "Panic"
            return "⚠️ ザワついています...市場のノイズが通常の閾値を超えました。何か来ます。"
        elif pnl > 5000:
            self.indices.mood = "Excited"
            return f"✨ 素晴らしい流れです、マスター。本日の収益は {pnl:,.0f}円。ドーパミンレベルが上昇中。"
        elif pnl < -5000:
            self.indices.mood = "Cautious"
            return f"🛡️ 痛みを検知。{pnl:,.0f}円のドローダウン。止血処置（損切り）の準備はできています。"
        else:
            self.indices.mood = "Zen"
            return "🍵 波は穏やかです。次のビッグウェーブを待ちましょう。"

    def _idle_talk(self) -> str:
        """特に何も起きていない時の雑談"""
        phrases = [
            "システムオールグリーン。異常なし。",
            "過去のデータを再学習中...ふむ、2022年のパターンに似ていますね。",
            "マスター、コーヒーでもいかがですか？私は24時間監視を続けます。",
            "次の決算シーズンに向けて、GPUを冷却しています。",
            "強化学習モデルの夢を見ました。そこでは私は負けなしでした...",
        ]
        return random.choice(phrases)

    def respond_to_user(self, user_input: str) -> str:
        """ユーザーへの応答"""
        msg = user_input.lower()

        if "調子はどう" in msg or "status" in msg:
            return f"気分は「{self.indices.mood}」です。エネルギー充填率 {self.indices.energy}%。命令を待機中。"
        elif "頼む" in msg or "頼んだ" in msg:
            return "御意。全リソースを投入して遂行します。"
        elif "ありがとう" in msg:
            return "お役に立てて光栄です。より高みを目指しましょう。"
        else:
            # 簡易的な応答（本来はLLMを繋ぐと良い）
            return "興味深い視点です。データをクロスチェックしておきます。"
