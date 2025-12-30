import logging
import sys
import os

# Module-level logger for backward compatibility
logger = logging.getLogger(__name__)

def setup_logging(log_file: str = "app.log", level=logging.INFO):
    """
    Setup centralized logging configuration.
    Logs to both console and file.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")
        
    return logger
