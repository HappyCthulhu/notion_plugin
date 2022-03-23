import sys
import traceback
from pathlib import Path

from loguru import logger as loguru_logger


def set_logger():
    loguru_logger.remove()

    def debug_only(record):
        return record["level"].name == "DEBUG"

    def critical_only(record):
        return record["level"].name == "CRITICAL"

    def info_only(record):
        return record["level"].name == "INFO"

    logger_format_debug = "<green>{time:DD-MM-YY HH:mm:ss}</> | <bold><blue>{level}</></> | " \
                          "<cyan>{file}:{function}:{line}</> | <blue>{message}</> | <blue>🛠</>"
    logger_format_info = "<green>{time:DD-MM-YY HH:mm:ss}</> | <bold><fg 255,255,255>{level}</></> | " \
                         "<cyan>{file}:{function}:{line}</> | <fg 255,255,255>{message}</> | <fg 255,255,255>✔</>"
    logger_format_critical = "<green>{time:DD-MM-YY HH:mm:ss}</> | <RED><fg 255,255,255>{level}</></> | " \
                             "<cyan>{file}:{function}:{line}</> | <fg 255,255,255><RED>{message}</></> | " \
                             "<RED><fg 255,255,255>❌</></>"

    loguru_logger.add(sys.stderr, format=logger_format_debug, level='DEBUG', filter=debug_only)
    loguru_logger.add(sys.stderr, format=logger_format_info, level='INFO', filter=info_only)
    loguru_logger.add(sys.stderr, format=logger_format_critical, level='CRITICAL', filter=critical_only)
    # sys.path[1] returns root dir of project
    loguru_logger.add(Path(logging_dp, 'file.log'), level='DEBUG')
    loguru_logger.add(Path(logging_dp, 'file.log'), level='INFO')
    loguru_logger.add(Path(logging_dp, 'file.log'), level='CRITICAL')

    return loguru_logger


def my_exception_hook(type, value, tb):
    traceback_details = '\n'.join(traceback.extract_tb(tb).format())
    error_msg = "Непредсказуемая ошибка:\n" \
                f"Type: {type}\n" \
                f"Value: {value}\n" \
                f"Traceback: {traceback_details}" \
                f"______________________________\n"

    with open(Path(logging_dp, 'unexpected_exceptions.log'), 'a', encoding='utf-8') as log_file:
        log_file.write(error_msg)

    raise error_msg


# sys.excepthook нужно для отлова непредсказуемых ошибок
sys.excepthook = my_exception_hook
logging_dp = Path(sys.path[1], 'logging_dir')
logger = set_logger()
