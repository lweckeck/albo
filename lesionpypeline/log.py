"""This module provides logging facilities for the lesionpypeline program.

The basis for this module is the logging module from the standard library.
Added features are global setting of log level and easy setting of nipype log
level.
"""
import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

import nipype

loggers = []


def get_logger(name):
    """Return a logger with the given name.

    See documentation of standard library module logging for further info.
    """
    logger = logging.getLogger(name)
    loggers.append(logger)

    return logger


def set_global_level(level):
    """Set the log level for all loggers created by this module."""
    if not isinstance(level, int):
        level = _str2level(level)
    for logger in loggers:
        logger.setLevel(level)


def set_nipype_level(level):
    """Set the log level for all loggers of the nipype framework."""
    if not isinstance(level, int):
        level = _str2level(level)
    for logger in nipype.logging.loggers.values():
        logger.setLevel(level)


def _str2level(string):
    string = string.upper()

    if string in {'DEBUG'}:
        return DEBUG
    elif string in {'INFO'}:
        return INFO
    elif string in {'WARN', 'WARNING'}:
        return WARNING
    elif string in {'ERROR'}:
        return ERROR
    elif string in {'CRITICAL'}:
        return CRITICAL
    else:
        raise ValueError('{} could not be mapped to a log level!')
