import os

REPLACEMENTS = [
    ("from src.config import settings", "from src.core.config import settings"),
    ("from src.config import config", "from src.core.config import config"),
    ("from src.constants", "from src.core.constants"),
    ("from src.logger_config import logger", "from src.core.logger import logger"),
    ("from src.logger_config import setup_logging", "from src.core.logger import setup_logger"),
    ("from src.log_config import logger", "from src.core.logger import logger"),
    ("from src.logging_config import logger", "from src.core.logger import logger"),
    ("from src.paper_trader", "from src.trading.paper_trader"),
    ("from src.live_trading", "from src.trading.live_trading"),
    ("from src.broker", "from src.trading.broker"),
    ("from src.rakuten_broker", "from src.trading.rakuten_broker"),
    ("from src.error_handling", "from src.utils.error_handling"),
    ("from src.ui_renderers", "from src.ui.ui_renderers"),
    ("from src.simple_dashboard", "from src.ui.simple_dashboard"),
    ("from src.visualizer", "from src.ui.visualizer"),
    ("from src.advanced_risk", "from src.risk.advanced_risk"),
    ("from src.realtime.streamer", "from src.realtime.streamer"), # No change
]

FILES = ["app.py", "fully_automated_trader.py"]

def patch_entry_points():
    for file_path in FILES:
        if not os.path.exists(file_path): continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        for old, new in REPLACEMENTS:
            content = content.replace(old, new)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Patched: {file_path}")

if __name__ == "__main__":
    patch_entry_points()
