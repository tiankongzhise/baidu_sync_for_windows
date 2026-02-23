from loguru import logger
def get_logger(bind:dict[str,str|int|float|bool|None]):
    return logger.bind(**bind)