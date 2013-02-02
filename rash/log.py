import logging


def loglevel(level):
    """
    Convert any representation of `level` to an int appropriately.

    :type level: int or str
    :rtype: int

    >>> loglevel('DEBUG') == logging.DEBUG
    True
    >>> loglevel(10)
    10
    >>> loglevel(None)
    Traceback (most recent call last):
      ...
    ValueError: None is not a proper log level.

    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    elif isinstance(level, int):
        pass
    else:
        raise ValueError('{0!r} is not a proper log level.'.format(level))
    return level


logger = logging.getLogger('rash')


def setup_daemon_log_file(conf):
    """
    Attach file handler to RASH logger.

    :type conf: rash.config.ConfigStore

    """
    level = loglevel(conf.daemon_log_level)
    handler = logging.FileHandler(filename=conf.daemon_log_path)
    handler.setLevel(level)
    logger.setLevel(level)
    logger.addHandler(handler)
