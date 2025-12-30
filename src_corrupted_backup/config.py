import os
from pathlib import Path
from typing import Any, Dict
import yaml


class Config:
    pass


_instance = None
_config: Dict[str, Any] = {}
# Fallback defaults if file missing
# Override with Environment Variables
# Slack
# Discord
# Pushover
# Email
# Global instance
config = Config()
