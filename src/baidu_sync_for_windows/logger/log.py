from loguru import logger
import sys
from baidu_sync_for_windows.config import get_config
config = get_config()
logger.remove()
def add_log_level():
    levels = {
        'module_base_info': 11,
        'module_info': 12,
        'service_info': 21,
    }
    for level,no in levels.items():
        logger.level(level.upper(),no=no)
def add_log_handler():
    logger.add(sys.stdout, level=config.logger.console_level)
    logger.add('logs/baidu_sync_for_windows.log',level='TRACE',rotation='100 MB',retention='7 days',compression='zip')
    logger.add('logs/error.log',level='ERROR',rotation='100 MB',retention='7 days',compression='zip')
    logger.add('logs/service_info.log',level='SERVICE_INFO',rotation='100 MB',retention='7 days',compression='zip',filter=lambda record: record['level'].name == 'SERVICE_INFO')
add_log_level()
add_log_handler()
def get_logger(bind:dict[str,str|int|float|bool|None]):
    return logger.bind(**bind)