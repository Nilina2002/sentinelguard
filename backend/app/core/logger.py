import logging
import sys
from logging.handlers import RotatingFileHandler
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
            "module": record.module,
        }
        return json.dumps(log_record)

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())

    # File handler
    file_handler = RotatingFileHandler(
        "app.log", maxBytes=5_000_000, backupCount=3
    )
    file_handler.setFormatter(JsonFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
