import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.utils.logger import setup_logger, get_logger
from src.paths import LOGS_DIR

def test_logger():
    print("Testing Logger...")
    log_file = "test_setup.log"
    # Test Normal Mode
    logger = setup_logger("test_normal", log_file_name=log_file, json_mode=False)
    logger.info("Normal log message")
    
    # Test JSON Mode
    json_log_file = "test_json.log"
    logger_json = setup_logger("test_json", log_file_name=json_log_file, json_mode=True)
    logger_json.info("JSON log message")
    
    assert (LOGS_DIR / log_file).exists()
    assert (LOGS_DIR / json_log_file).exists()
    
    with open(LOGS_DIR / json_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        print(f"JSON Log format check: {line.strip()}")
        assert '"message": "JSON log message"' in line
        assert '"level": "INFO"' in line
        
    print("✅ Logger OK")

if __name__ == "__main__":
    test_logger()
