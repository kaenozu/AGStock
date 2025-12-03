"""
SmartNotifier - シンプルな通知ユーティリティ

LINE Notify / Discord Webhook への送信を共通化し、
テキストベースのサマリー送信もサポートする。
"""
from __future__ import annotations

import json
from typing import Dict, Optional

import requests


class SmartNotifier:
    """通知チャネルをまとめたユーティリティクラス。"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        notifications = self.config.get("notifications", {})

        line_cfg = notifications.get("line", {})
        discord_cfg = notifications.get("discord", {})

        self.line_token: Optional[str] = line_cfg.get("token") if line_cfg.get("enabled") else None
        self.discord_webhook: Optional[str] = (
            discord_cfg.get("webhook_url") if discord_cfg.get("enabled") else None
        )

    def _load_config(self, path: str) -> Dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def send_line_notify(self, message: str, token: Optional[str] = None, image_path: Optional[str] = None) -> bool:
        """LINE Notify でメッセージ送信（画像対応）。"""
        auth_token = token or self.line_token
        if not auth_token:
            return False

        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {"message": message}
        files = {}
        
        if image_path:
            try:
                files = {'imageFile': open(image_path, 'rb')}
            except Exception as e:
                print(f"Failed to load image for LINE: {e}")

        try:
            response = requests.post(url, headers=headers, data=payload, files=files if files else None, timeout=10)
            
            # Close file if opened
            if files:
                files['imageFile'].close()
                
            return response.status_code == 200
        except Exception:
            return False

    def send_discord_webhook(self, message: str, webhook_url: Optional[str] = None, image_path: Optional[str] = None) -> bool:
        """Discord Webhook でメッセージ送信（画像対応）。"""
        url = webhook_url or self.discord_webhook
        if not url:
            return False

        try:
            # Discord Webhook with image requires multipart/form-data
            if image_path:
                with open(image_path, 'rb') as f:
                    files = {
                        'file': (image_path.split('/')[-1], f, 'image/png')
                    }
                    # Payload must be sent as 'payload_json' when using multipart
                    payload = {"content": message}
                    response = requests.post(url, data={'payload_json': json.dumps(payload)}, files=files, timeout=10)
            else:
                response = requests.post(url, json={"content": message}, timeout=10)
                
            return response.status_code in (200, 204)
        except Exception as e:
            print(f"Discord send failed: {e}")
            return False

    def send_daily_summary_rich(self, summary: Dict, image_path: Optional[str] = None) -> None:
        """日次サマリーを各チャネルに送信（画像付き）。"""
        lines = [
            "\ud83d\udcca AGStock 日次サマリー",
            f"日付: {summary.get('date', 'N/A')}",
            f"総資産: \uffe5{summary.get('total_value', 0):,.0f}",
            f"日次損益: \uffe5{summary.get('daily_pnl', 0):+,.0f}",
            f"勝率: {summary.get('win_rate', 0):.1%}",
            f"アドバイス: {summary.get('advice', 'N/A')}",
        ]

        signals = summary.get("signals") or []
        if signals:
            lines.append("\nシグナル:")
            for sig in signals:
                lines.append(f"- {sig.get('action', '')} {sig.get('ticker', '')} ({sig.get('name', '')})")

        message = "\n".join(lines)

        # どちらか送れるチャネルに送信
        self.send_line_notify(message, image_path=image_path)
        self.send_discord_webhook(message, image_path=image_path)
