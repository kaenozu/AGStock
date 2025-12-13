import json
import logging
import logging.handlers
import os
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(
    log_file: str = "app.log",
    level=logging.INFO,
    json_format: bool = False,
    rotate_daily: bool = False,
    console_json: bool = False,
):
    """
    Setup centralized logging configuration.
    Logs to both console and file.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.propagate = False

    # Formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def _already_has(handler_type, stream=None, filename=None):
        for h in logger.handlers:
            if not isinstance(h, handler_type):
                continue
            if stream is not None and getattr(h, "stream", None) != stream:
                continue
            if filename is not None and getattr(h, "baseFilename", None) != filename:
                continue
            return True
        return False

    # Console Handler
    if not _already_has(logging.StreamHandler, stream=sys.stdout):
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = JsonFormatter() if console_json else formatter
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File Handler (optionally rotating)
    try:
        filename = os.path.abspath(log_file)
        if not _already_has(logging.FileHandler, filename=filename):
            if rotate_daily:
                file_handler = logging.handlers.TimedRotatingFileHandler(
                    filename, when="midnight", backupCount=7, encoding="utf-8"
                )
            else:
                file_handler = logging.FileHandler(filename, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    return logger


# Create a default logger instance
logger = setup_logging()
