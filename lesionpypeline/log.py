"""TODO"""
import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

import nipype

loggers = []


def get_logger(name):
    logger = logging.getLogger(name)
    loggers.append(logger)

    return logger


def set_global_level(level):
    for logger in loggers:
        logger.setLevel(level)


def set_nipype_level(level):
    for logger in nipype.logging.loggers.values():
        logger.setLevel(level)
