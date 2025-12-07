from src.notifier import Notifier

n = Notifier()
print(f"Has notify_slack: {hasattr(n, 'notify_slack')}")
print(f"Methods: {[m for m in dir(n) if not m.startswith('__')]}")

try:
    n.notify_slack("Test message")
except Exception as e:
    print(f"Error calling notify_slack: {e}")
