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

    def send_slack(self, message: str, title: str = "AGStock Alert") -> bool:
        """Send notification to Slack."""
        if not self.slack_webhook:
            print("Slack webhook not configured. Skipping Slack notification.")
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
        """Notify about a strong trading signal."""
        emoji = "🚀" if action == "BUY" else "📉"
        
        message = f"{emoji} *{action} Signal: {ticker}*\n"
        message += f"Strategy: {strategy}\n"
        message += f"Confidence: {confidence:.1%}\n"
        message += f"Price: ${price:.2f}"
        
        # Slack
        self.send_slack(message, title="Strong Trading Signal")
        
        # Email
        subject = f"{emoji} {action} Signal: {ticker}"
        email_body = f"""
Strong Trading Signal Detected

Ticker: {ticker}
Action: {action}
Strategy: {strategy}
Confidence: {confidence:.1%}
Current Price: ${price:.2f}

This is an automated notification from AGStock AI Trading System.
        """
        self.send_email(subject, email_body.strip())

    def notify_daily_summary(self, signals: List[Dict], portfolio_value: float, daily_pnl: float):
        """Send daily summary notification."""
        num_signals = len(signals)
        
        # Slack message
        slack_msg = f"📊 *Daily Summary*\n\n"
        slack_msg += f"Portfolio Value: ${portfolio_value:,.2f}\n"
        slack_msg += f"Daily P&L: ${daily_pnl:+,.2f} ({daily_pnl/portfolio_value*100:+.2f}%)\n"
        slack_msg += f"New Signals: {num_signals}\n\n"
        
        if signals:
            slack_msg += "*Top Signals:*\n"
            for sig in signals[:5]:  # Top 5
                slack_msg += f"• {sig['ticker']}: {sig['action']} ({sig['strategy']})\n"
        
        self.send_slack(slack_msg, title="Daily Trading Summary")
        
        # Email (HTML format)
        email_subject = f"Daily Trading Summary - {num_signals} New Signals"
        email_html = f"""
<html>
<body>
<h2>📊 Daily Trading Summary</h2>
<table border="1" cellpadding="5">
<tr><td><b>Portfolio Value</b></td><td>${portfolio_value:,.2f}</td></tr>
<tr><td><b>Daily P&L</b></td><td style="color: {'green' if daily_pnl > 0 else 'red'}">${daily_pnl:+,.2f} ({daily_pnl/portfolio_value*100:+.2f}%)</td></tr>
<tr><td><b>New Signals</b></td><td>{num_signals}</td></tr>
</table>

<h3>Top Signals</h3>
<ul>
"""
        for sig in signals[:10]:
            email_html += f"<li><b>{sig['ticker']}</b>: {sig['action']} - {sig['strategy']} (Confidence: {sig.get('confidence', 1.0):.1%})</li>\n"
        
        email_html += """
</ul>
<p><i>This is an automated notification from AGStock AI Trading System.</i></p>
</body>
</html>
"""
        self.send_email(email_subject, email_html, html=True)

    def notify_error(self, error_message: str, context: str = ""):
        """Notify about system errors."""
        message = f"⚠️ *System Error*\n\n"
        if context:
            message += f"Context: {context}\n"
        message += f"Error: {error_message}"
        
        self.send_slack(message, title="AGStock Error Alert")
        
        subject = "⚠️ AGStock System Error"
        self.send_email(subject, f"Context: {context}\n\nError: {error_message}")
