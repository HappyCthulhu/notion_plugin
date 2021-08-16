import sys
from loguru import logger
from pathlib import Path
import traceback


def set_logger():
    logger.remove()

    # настраиваем логгирование
    def debug_only(record):
        # dump_log_in_file(record)
        return record["level"].name == "DEBUG"

    def critical_only(record):
        # dump_log_in_file(record)
        return record["level"].name == "CRITICAL"

    def info_only(record):
        # dump_log_in_file(record)
        return record["level"].name == "INFO"

    logger_format_debug = "<green>{time:DD-MM-YY HH:mm:ss}</> | <bold><blue>{level}</></> | " \
                          "<cyan>{file}:{function}:{line}</> | <blue>{message}</> | <blue>🛠</>"
    logger_format_info = "<green>{time:DD-MM-YY HH:mm:ss}</> | <bold><fg 255,255,255>{level}</></> | " \
                         "<cyan>{file}:{function}:{line}</> | <fg 255,255,255>{message}</> | <fg 255,255,255>✔</>"
    logger_format_critical = "<green>{time:DD-MM-YY HH:mm:ss}</> | <RED><fg 255,255,255>{level}</></> | " \
                             "<cyan>{file}:{function}:{line}</> | <fg 255,255,255><RED>{message}</></> | " \
                             "<RED><fg 255,255,255>❌</></>"

    logger.add(sys.stderr, format=logger_format_debug, level='DEBUG', filter=debug_only)
    logger.add(sys.stderr, format=logger_format_info, level='INFO', filter=info_only)
    logger.add(sys.stderr, format=logger_format_critical, level='CRITICAL', filter=critical_only)
    logger.add(Path('logging_dir', 'log.txt'), encoding='utf-8')

    return logger

def my_exception_hook(type, value, tb):
    traceback_details = '\n'.join(traceback.extract_tb(tb).format())
    error_msg = "Все сломалось\n" \
                f"Type: {type}\n" \
                f"Value: {value}\n" \
                f"Traceback: {traceback_details}"


    with open(Path('logging_dir', 'unexpected_exception.txt'), 'a', encoding='utf-8') as log_file:
        log_file.write(error_msg)

    raise error_msg
    # logger.critical(error_msg)
    # TODO: потюнить вывод непредсказуемой ошибки