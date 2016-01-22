"""This module provides logging facilities for the albo program.

The basis for this module is the logging module from the standard library.
Added features are global setting of log level and easy setting of nipype log
level.
"""
import logging
import nipype
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

import nipype

loggers = []

formatter = logging.Formatter(
    '%(levelname)s: %(message)s')
file_formatter = logging.Formatter(
    '%(asctime)s %(name)s %(levelname)s:\n\t%(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

nipype_stream_handler = logging.StreamHandler()
nipype_stream_handler.setFormatter(formatter)

file_handler = None
global_log_file = None


for logger in nipype.logging.loggers.values():
    logger.propagate = False
    logger.addHandler(nipype_stream_handler)


def init(verbose=False, debug=False):
    """Initialize logging system."""
    if debug:
        set_global_level(logging.DEBUG)
        set_nipype_level(logging.DEBUG)
    elif verbose:
        set_global_level(logging.INFO)
        set_nipype_level(logging.INFO)
    else:
        set_global_level(logging.INFO)
        set_nipype_level(logging.WARNING)


def get_logger(name):
    """Return a logger with the given name.

    See documentation of standard library module logging for further info.
    """
    logger = logging.getLogger(name)
    logger.setLevel(DEBUG)
    logger.propagate = False

    logger.addHandler(stream_handler)
    if file_handler is not None:
        logger.addHandler(file_handler)

    loggers.append(logger)
    return logger


def set_global_level(level):
    """Set the log level for all loggers created by this module."""
    if not isinstance(level, int):
        level = _str2level(level)

    stream_handler.setLevel(level)


def set_nipype_level(level):
    """Set the log level for all loggers of the nipype framework."""
    if not isinstance(level, int):
        level = _str2level(level)

    nipype_stream_handler.setLevel(level)


def set_global_log_file(path):
    """Redirect all logging to a file at the given location."""
    global file_handler, global_log_file

    global_log_file = path
    file_handler = logging.FileHandler(path)
    file_handler.setLevel(INFO)
    file_handler.setFormatter(file_formatter)

    for logger in loggers:
        logger.addHandler(file_handler)
    for logger in nipype.logging.loggers.values():
        logger.addHandler(file_handler)


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
