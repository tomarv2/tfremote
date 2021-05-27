"""Centralized logging"""
import logging
import os


def configure_logging():
    """
    Centralized logging, default log level is WARNING
    :return: None
    """
    l = logging.getLogger()
    if os.environ.get("TF_LOG_LEVEL"):
        level = os.environ.get("TF_LOG_LEVEL").upper()
    else:
        level = "WARNING"
    if level == "DEBUG":
        # log level:logged message:full module path:function invoked:line number of logging call
        LOGFORMAT = "%(levelname)s: %(message)s: %(pathname)s: %(funcName)s: %(lineno)d"
        logging.basicConfig(level=level, format=LOGFORMAT)
        l.setLevel(level)
    else:
        logging.basicConfig(level=level)
        l.setLevel(level)
