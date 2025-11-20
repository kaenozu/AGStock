import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import requests

class Notifier:
    def __init__(self):
        # Slack Webhook URL (set via environment variable)
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        
        # Email settings (set via environment variables)
        self.email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_to = os.getenv("EMAIL_TO")

    def notify_slack(self, message: str, title: str = "AGStock Alert") -> bool:
        """Send notification to Slack."""
        if not self.slack_webhook:
            # print("Slack webhook not configured. Skipping Slack notification.")
            return False
            
        payload = {
            "text": f"*{title}*\n{message}"
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                print("✓ Slack notification sent")
                return True
            else:
                print(f"✗ Slack notification failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Slack notification error: {e}")
            return False

    def notify_discord(self, message: str):
        """Send notification via Discord Webhook."""
        from src.config import config
        webhook_url = config.get("notifications.discord.webhook_url")
        if not webhook_url:
            return
            
        payload = {"content": message}
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")

    def notify_pushover(self, message: str):
        """Send notification via Pushover."""
        from src.config import config
        user_key = config.get("notifications.pushover.user_key")
        api_token = config.get("notifications.pushover.api_token")
        
        if not user_key or not api_token:
            return
            
        payload = {
            "token": api_token,
            "user": user_key,
            "message": message
        }
        try:
            requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=5)
        except Exception as e:
            print(f"Failed to send Pushover notification: {e}")

    def send_email(self, subject: str, body: str, html: bool = False) -> bool:
        """Send email notification."""
        if not self.email_enabled or not self.email_from or not self.email_to:
            print("Email not configured. Skipping email notification.")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            msg.attach(part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
                
            print("✓ Email notification sent")
            return True
        except Exception as e:
            print(f"✗ Email notification error: {e}")
            return False

    def notify_strong_signal(self, ticker: str, action: str, confidence: float, price: float, strategy: str):
        """Notify when a strong signal is detected."""
        message = f"🚀 STRONG SIGNAL: {action} {ticker}\nPrice: {price}\nConfidence: {confidence:.2f}\nStrategy: {strategy}"
        
        self.notify_slack(message)
        self.notify_discord(message)
        self.notify_pushover(message)
        
        if self.email_enabled:
            subject = f"AGStock Alert: {action} {ticker}"
            self.send_email(subject, message)

    def notify_daily_summary(self, signals: list, portfolio_value: float, daily_pnl: float):
        """Send daily summary."""
        num_signals = len(signals)
        signal_text = "\n".join([f"- {s['action']} {s['ticker']} ({s['strategy']})" for s in signals]) if signals else "No trades today."
        
        message = f"""📊 Daily Summary
Portfolio Value: ¥{portfolio_value:,.0f}
Daily P&L: ¥{daily_pnl:,.0f}

Signals:
{signal_text}
"""
        self.notify_slack(message)
        self.notify_discord(message)
        self.notify_pushover(message)
        
        if self.email_enabled:
            self.send_email("AGStock Daily Summary", message)

    def notify_error(self, error_msg: str):
        """Notify system error."""
        message = f"⚠️ System Error: {error_msg}"
        self.notify_slack(message)
        self.notify_discord(message)
        self.notify_pushover(message)
        
        if self.email_enabled:
            self.send_email("AGStock Error", message)
