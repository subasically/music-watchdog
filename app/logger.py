import logging
import sys
import os


def setup_logger():
    logger = logging.getLogger("music_watchdog")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    debug = os.getenv("DEBUG", "false").lower() == "true"

    if debug:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        log_file = os.path.join(os.path.dirname(
            __file__), "music_watchdog.log")
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.setLevel(logging.INFO)
        print("Debug mode is off. Logger set to INFO level.")

    return logger


logger = setup_logger()
