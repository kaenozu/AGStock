"""
AGStock 設定ウィザード
3分で最適な設定が完了

使い方:
  python setup_wizard.py
"""

import json
from pathlib import Path
from typing import Dict


class SetupWizard:
    """設定ウィザード"""

    def __init__(self):
        self.config = {}
        self.config_path = Path("config.json")

    def print_header(self, title: str):
        """ヘッダー表示"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def print_step(self, step: int, total: int, question: str):
        """ステップ表示"""
        print(f"\n📋 ステップ {step}/{total}")
        print(f"❓ {question}\n")

    def get_choice(self, options: list, default: int = 0) -> int:
        """選択肢から選ぶ"""
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")

        while True:
            try:
                choice = input(f"\n選択してください (1-{len(options)}) [{default+1}]: ").strip()
                if not choice:
                    return default
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num - 1
                print(f"⚠️  1から{len(options)}の数字を入力してください")
            except ValueError:
                print("⚠️  数字を入力してください")

    def get_number(self, prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
        """数値入力"""
        while True:
            try:
                value = input(f"{prompt} [{default:,}]: ").strip()
                if not value:
                    return default
                num = int(value.replace(",", "").replace("¥", ""))
                if min_val is not None and num < min_val:
                    print(f"⚠️  {min_val:,}以上の値を入力してください")
                    continue
                if max_val is not None and num > max_val:
                    print(f"⚠️  {max_val:,}以下の値を入力してください")
                    continue
                return num
            except ValueError:
                print("⚠️  数字を入力してください")

    def get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Yes/No入力"""
        default_str = "Y/n" if default else "y/N"
        while True:
            choice = input(f"{prompt} ({default_str}): ").strip().lower()
            if not choice:
                return default
            if choice in ["y", "yes", "はい"]:
                return True
            if choice in ["n", "no", "いいえ"]:
                return False
            print("⚠️  y または n を入力してください")

    def step1_experience(self):
        """ステップ1: 投資経験"""
        self.print_step(1, 5, "あなたの投資経験を教えてください")

        options = [
            "初心者 (1年未満) - 安全第一で運用したい",
            "中級者 (1-3年) - バランス重視で運用したい",
            "上級者 (3年以上) - 積極的に運用したい",
        ]

        choice = self.get_choice(options, default=0)

        experience_map = {0: "beginner", 1: "intermediate", 2: "advanced"}

        return experience_map[choice]

    def step2_capital(self, experience: str):
        """ステップ2: 初期資金"""
        self.print_step(2, 5, "初期資金を入力してください")

        default_capital = {"beginner": 500000, "intermediate": 1000000, "advanced": 3000000}

        capital = self.get_number("💰 初期資金 (円)", default=default_capital[experience], min_val=100000)

        return capital

    def step3_risk(self, experience: str):
        """ステップ3: リスク許容度"""
        self.print_step(3, 5, "リスク許容度を選択してください")

        print("💡 リスク許容度とは:")
        print("   - 低: 損失を最小限に抑える (年間目標リターン: 3-5%)")
        print("   - 中: バランス重視 (年間目標リターン: 5-10%)")
        print("   - 高: 積極的な運用 (年間目標リターン: 10%以上)")
        print()

        options = ["低 - 安全第一", "中 - バランス重視", "高 - 積極的"]

        default_risk = {"beginner": 0, "intermediate": 1, "advanced": 2}

        choice = self.get_choice(options, default=default_risk[experience])

        risk_map = {0: "low", 1: "medium", 2: "high"}

        return risk_map[choice]

    def step4_notifications(self):
        """ステップ4: 通知設定"""
        self.print_step(4, 5, "通知方法を選択してください")

        print("💡 重要なシグナルや異常を通知します")
        print()

        options = [
            "LINE - スマホで受け取る (推奨)",
            "Discord - PCで受け取る",
            "メール - メールで受け取る",
            "なし - 通知不要",
        ]

        choice = self.get_choice(options, default=0)

        notification_config = {
            "enabled": choice != 3,
            "line": {"enabled": choice == 0, "token": ""},
            "discord": {"enabled": choice == 1, "webhook_url": ""},
            "email": {"enabled": choice == 2, "smtp_server": "", "to_address": ""},
        }

        # トークン/URL入力
        if choice == 0:
            print("\n💡 LINE Notify トークンの取得方法:")
            print("   1. https://notify-bot.line.me/ にアクセス")
            print("   2. 「マイページ」→「トークンを発行する」")
            print("   3. トークンをコピー")
            print()

            if self.get_yes_no("今すぐトークンを設定しますか?", default=False):
                token = input("LINE Notify トークン: ").strip()
                if token:
                    notification_config["line"]["token"] = token

        elif choice == 1:
            if self.get_yes_no("今すぐDiscord Webhook URLを設定しますか?", default=False):
                url = input("Discord Webhook URL: ").strip()
                if url:
                    notification_config["discord"]["webhook_url"] = url

        return notification_config

    def step5_automation(self, experience: str):
        """ステップ5: 自動化設定"""
        self.print_step(5, 5, "自動化レベルを選択してください")

        print("💡 自動化レベル:")
        print("   - 手動: すべて自分で判断・実行")
        print("   - 半自動: AIが推奨、あなたが承認")
        print("   - 全自動: AIが自動で取引 (上級者向け)")
        print()

        options = [
            "手動 - すべて自分で判断",
            "半自動 - AIの推奨を確認して承認 (推奨)",
            "全自動 - AIに完全おまかせ (上級者向け)",
        ]

        default_auto = {"beginner": 0, "intermediate": 1, "advanced": 1}  # 全自動は明示的に選択させる

        choice = self.get_choice(options, default=default_auto[experience])

        automation_config = {
            "mode": ["manual", "semi_auto", "full_auto"][choice],
            "require_approval": choice != 2,
            "max_daily_trades": [3, 5, 10][choice],
        }

        if choice == 2:
            print("\n⚠️  全自動モードは上級者向けです")
            if not self.get_yes_no("本当に全自動モードにしますか?", default=False):
                automation_config["mode"] = "semi_auto"
                automation_config["require_approval"] = True
                automation_config["max_daily_trades"] = 5
                print("✅ 半自動モードに変更しました")

        return automation_config

    def generate_config(self, experience: str, capital: int, risk: str, notifications: Dict, automation: Dict) -> Dict:
        """設定を生成"""

        # リスクレベルに応じたパラメータ
        risk_params = {
            "low": {
                "stop_loss_pct": 0.03,  # 3%
                "take_profit_pct": 0.05,  # 5%
                "max_position_size": 0.10,  # 10%
                "daily_loss_limit_pct": -3.0,  # -3%
            },
            "medium": {
                "stop_loss_pct": 0.05,  # 5%
                "take_profit_pct": 0.10,  # 10%
                "max_position_size": 0.15,  # 15%
                "daily_loss_limit_pct": -5.0,  # -5%
            },
            "high": {
                "stop_loss_pct": 0.07,  # 7%
                "take_profit_pct": 0.15,  # 15%
                "max_position_size": 0.20,  # 20%
                "daily_loss_limit_pct": -7.0,  # -7%
            },
        }

        params = risk_params[risk]

        config = {
            "user_profile": {"experience": experience, "risk_tolerance": risk, "setup_date": "2025-12-02"},
            "capital": {"initial_capital": capital, "currency": "JPY"},
            "risk": {
                "max_position_size": params["max_position_size"],
                "stop_loss_pct": params["stop_loss_pct"],
                "take_profit_pct": params["take_profit_pct"],
            },
            "auto_trading": {
                "mode": automation["mode"],
                "require_approval": automation["require_approval"],
                "max_daily_trades": automation["max_daily_trades"],
                "daily_loss_limit_pct": params["daily_loss_limit_pct"],
                "max_vix": 40.0,
            },
            "notifications": notifications,
            "assets": {
                "japan_stocks": True,
                "us_stocks": experience != "beginner",
                "europe_stocks": experience == "advanced",
                "crypto": False,
                "fx": False,
            },
            "paper_trading": {"initial_capital": capital, "enabled": True},
        }

        return config

    def show_summary(self, config: Dict):
        """設定サマリー表示"""
        self.print_header("設定完了!")

        print("\n✅ あなたに最適な設定:\n")

        # ユーザープロファイル
        profile = config["user_profile"]
        exp_label = {"beginner": "初心者", "intermediate": "中級者", "advanced": "上級者"}
        risk_label = {"low": "低 (安全第一)", "medium": "中 (バランス)", "high": "高 (積極的)"}

        print(f"👤 投資経験: {exp_label[profile['experience']]}")
        print(f"🎯 リスク許容度: {risk_label[profile['risk_tolerance']]}")
        print(f"💰 初期資金: ¥{config['capital']['initial_capital']:,}")

        # リスク管理
        risk = config["risk"]
        print("\n📊 リスク管理:")
        print(f"   - 損切りライン: {risk['stop_loss_pct']*100:.0f}%")
        print(f"   - 利確ライン: {risk['take_profit_pct']*100:.0f}%")
        print(f"   - 最大ポジションサイズ: {risk['max_position_size']*100:.0f}%")

        # 自動化
        auto = config["auto_trading"]
        mode_label = {"manual": "手動", "semi_auto": "半自動 (推奨確認)", "full_auto": "全自動"}
        print("\n🤖 自動化:")
        print(f"   - モード: {mode_label[auto['mode']]}")
        print(f"   - 最大取引数/日: {auto['max_daily_trades']}回")
        print(f"   - 日次損失制限: {auto['daily_loss_limit_pct']}%")

        # 通知
        notif = config["notifications"]
        if notif["enabled"]:
            if notif["line"]["enabled"]:
                status = "設定済み" if notif["line"]["token"] else "未設定 (後で設定可能)"
                print(f"\n📱 通知: LINE ({status})")
            elif notif["discord"]["enabled"]:
                status = "設定済み" if notif["discord"]["webhook_url"] else "未設定 (後で設定可能)"
                print(f"\n📱 通知: Discord ({status})")
            else:
                print("\n📱 通知: メール (未設定)")
        else:
            print("\n📱 通知: なし")

        # 対象資産
        assets = config["assets"]
        enabled_assets = []
        if assets["japan_stocks"]:
            enabled_assets.append("日本株")
        if assets["us_stocks"]:
            enabled_assets.append("米国株")
        if assets["europe_stocks"]:
            enabled_assets.append("欧州株")

        print(f"\n🌍 対象資産: {', '.join(enabled_assets)}")

        print("\n" + "=" * 60)

    def save_config(self, config: Dict):
        """設定を保存"""
        # 既存の設定があればバックアップ
        if self.config_path.exists():
            backup_path = Path(f"config.json.backup.{int(Path.ctime(self.config_path))}")
            self.config_path.rename(backup_path)
            print(f"\n💾 既存の設定をバックアップしました: {backup_path}")

        # 新しい設定を保存
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(f"✅ 設定を保存しました: {self.config_path}")

    def run(self):
        """ウィザード実行"""
        self.print_header("AGStock 設定ウィザード")
        print("\n👋 ようこそ! 3分で最適な設定を完了します")
        print("   各ステップで質問に答えてください")

        if not self.get_yes_no("\n設定を開始しますか?", default=True):
            print("\n👋 またお会いしましょう!")
            return

        # ステップ実行
        experience = self.step1_experience()
        capital = self.step2_capital(experience)
        risk = self.step3_risk(experience)
        notifications = self.step4_notifications()
        automation = self.step5_automation(experience)

        # 設定生成
        config = self.generate_config(experience, capital, risk, notifications, automation)

        # サマリー表示
        self.show_summary(config)

        # 保存確認
        if self.get_yes_no("\nこの設定で保存しますか?", default=True):
            self.save_config(config)

            print("\n" + "=" * 60)
            print("  🎉 設定完了!")
            print("=" * 60)
            print("\n次のステップ:")
            print("  1. python quick_start.py でアプリを起動")
            print("  2. 朝活ダッシュボードで毎朝確認")
            print("  3. 週末戦略会議で戦略最適化")
            print("\n💡 通知設定を後で変更する場合:")
            print("   config.json を編集してください")
            print("\n🚀 それでは、良い投資ライフを!")
        else:
            print("\n❌ 設定を保存しませんでした")
            if self.get_yes_no("最初からやり直しますか?", default=False):
                self.run()


def main():
    """メイン処理"""
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()
