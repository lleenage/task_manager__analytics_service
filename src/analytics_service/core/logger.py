"""Logging configuration."""
import logging
import sys
import json

from analytics_service.core.config import settings

# Цвета для локального режима
LOG_COLORS = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[35m"
}
RESET_COLOR = "\033[0m"

class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_color = LOG_COLORS.get(record.levelno, "")
        original_msg = record.msg
        # Красим только сообщение, чтобы не ломать структуру лога полностью
        record.msg = f"{log_color}{record.msg}{RESET_COLOR}"
        result = super().format(record)
        record.msg = original_msg
        return result

class JsonFormatter(logging.Formatter):
    """Форматирует лог в JSON. Идеально для Loki + Promtail."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
        }
        
        # Если в extra передали дополнительные данные (user_id, task_id и т.д.)
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)
            
        # Добавляем исключение, если оно есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Если хендлеры уже есть (логгер уже настроен), не добавляем новые, чтобы не дублировать логи
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # ГЛАВНАЯ МАГИЯ: выбираем форматтер в зависимости от среды
    if getattr(settings, "DOCKER_ENV", False):
        formatter = JsonFormatter("%(message)s")
    else:
        formatter = ColoredFormatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger
