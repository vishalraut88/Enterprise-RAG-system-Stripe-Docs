import logging
import sys
from config.settings import settings



LOG_LEVEL = settings.LOG_LEVEL.upper()

def configure_logging():

    if logging.getLogger().hasHandlers():
        return

    logging.basicConfig(level=LOG_LEVEL,
                        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        stream=sys.stdout
                        )
    

def get_logger(name):
    configure_logging()
    return logging.getLogger(name)
