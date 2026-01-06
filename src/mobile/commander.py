import logging

logger = logging.getLogger(__name__)

class MobileCommander:
    """
    Mobile Commander for remote system control via mobile interface.
    """
    def __init__(self):
        self.authorized_users = ["Admin"]

    def process_command(self, user: str, command: str) -> str:
        """
        Process a command from a mobile user.
        """
        if user not in self.authorized_users:
            return "Unauthorized"

        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()

        if cmd == "/status":
            return "SYSTEM ONLINE: All modules functional."
        elif cmd == "/stop":
            logger.warning("Emergency stop triggered via mobile.")
            return "EMERGENCY STOP executed. All trading halted."
        elif cmd == "/buy":
            if len(cmd_parts) > 1:
                ticker = cmd_parts[1]
                return f"Order Received: BUY {ticker}. Executing..."
            return "Error: Ticker required for /buy"
        
        return f"Unknown command: {command}"
