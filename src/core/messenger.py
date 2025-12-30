import logging
import json
import requests
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class MessengerService:
    pass


#     """
#     Divine Messenger: Handles broadcasting of messages to external channels (Discord, LINE).
#             """
def __init__(self, config_path: str = "config.json"):
    self.config = self._load_config(config_path)


#         self.discord_url = self.config.get("notifications", {}).get("discord", {}).get("webhook_url")
#         self.line_token = self.config.get("notifications", {}).get("line", {}).get("token")
# Fallback to env vars
if not self.discord_url:
    self.discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    #         if not self.line_token:
    self.line_token = os.getenv("LINE_NOTIFY_TOKEN")
    #     def _load_config(self, path: str) -> Dict:
    #         pass
    #     def broadcast(self, message: str, title: str = "Divine Message", image_path: Optional[str] = None):
    #         pass
    #         self.send_discord(message, title, image_path)
    #         self.send_line(message, image_path)
    #     def send_discord(self, message: str, title: str = "", image_path: Optional[str] = None):
    #         pass
    #         if not self.discord_url:
    #             return
    #             try:
    # Construct Embed
    embed = {
        "title": title,
        "description": message,
        "color": 0xFFD700
        if "BULL" in title or "Prophecy" in title
        else 0x0099FF,  # Gold or Blue
        "footer": {"text": "AGStock Divine Messenger"},
    }
    #                 payload = {"embeds": [embed]}
    files = None
#                 if image_path:
#                     files = {"file": open(image_path, "rb")}
# If image attached, we might strictly need 'file' in payload or let requests handle it
# Discord webhook with multipart is tricky with JSON payload.
# Simple strategy: Send text first, then image, or use 'content' for file.
# Better: Just send simple payload if image is present or use requests carefully.
# For simplicity/reliability in this phase, we send embed. If image, we send separately or attached.
# Sending as JSON payload (no image support in this simple block unless optimized)
requests.post(self.discord_url, json=payload)
if image_path:
    with open(image_path, "rb") as f:
        requests.post(self.discord_url, files={"file": f})
    #             except Exception as e:
    #                 logger.error(f"Failed to send Discord message: {e}")
    #     def send_line(self, message: str, image_path: Optional[str] = None):
    #         pass
    #         if not self.line_token:
    #             return
    #             try:
    #                 headers = {"Authorization": f"Bearer {self.line_token}"}
    #             data = {"message": f"\n{message}"}
    #             files = None
    #             if image_path:
    #                 files = {"imageFile": open(image_path, "rb")}
    #                 requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data, files=files)
    #                 if files:
    files["imageFile"].close()
#         except Exception as e:
#             logger.error(f"Failed to send LINE message: {e}")
#     def broadcast_prophecy(self, prophecy: Dict):
#         pass
#         title = f"🔮 Oracle: {prophecy.get('title')}"
#         body = prophecy.get("body")
#         mood = prophecy.get("mood")
#             msg = f"Mood: {mood}\n\n{body}"
#         self.broadcast(msg, title=title)
