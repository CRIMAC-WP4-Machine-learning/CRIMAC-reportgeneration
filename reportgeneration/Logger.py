import os
import warnings
import platform
import logging
from logging.handlers import RotatingFileHandler

try:
    LOG_FILENAME = os.path.splitext(__file__)[0] + ".log"
except:
    LOG_FILENAME = __file__ + ".log"

class Singleton(object):
    """
    Singleton interface:
    http://www.python.org/download/releases/2.2.3/descrintro/#__new__
    """
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        pass

class LoggerManager(Singleton):
    """
    Logger Manager.
    Handles all logging files.
    """
    def init(self, loggername, loggerFilePath):
        self.loggerFileName = None
        if loggerFilePath is None:
            try:
                loggerFilePath = os.sep.join(__file__.split(os.sep)[:-1])
            except:
                loggerFilePath ='.'

        if not os.path.isdir(loggerFilePath):
            os.mkdir(loggerFilePath)

        self.loggerFileName = loggerFilePath + os.path.sep + 'Log.log'

        # Create logger config director if not exists

        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)-8s: %(message)s',datefmt='%F %H:%M:%S'
        )

        rhandler = None
        consoleHandler = None
        try:
            rhandler = RotatingFileHandler(
                    self.loggerFileName,
                    mode='a',
                    maxBytes = 10 * 1024 * 1024,
                    backupCount=5
                )
            rhandler.setFormatter(formatter)
            self.logger.addHandler(rhandler)
        except:
            raise IOError("Couldn't create/open file \"" + \
                          self.loggerFileName + "\". Check permissions.")

        try:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(formatter)
            self.logger.addHandler(consoleHandler)
        except:
            raise IOError('Could not open console logging')

        if platform.system() != 'Windows' :
            try:
                sysHandler = logging.handlers.SysLogHandler('/dev/log')
                sysHandler.setFormatter(formatter)
                self.logger.addHandler(sysHandler)
            except:
                warnings.warn('Could not log to syslog')

    def debug(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.debug(msg)

    def error(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.error(msg)

    def info(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.info(msg)

    def warning(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.warning(msg)

class Logger(object):
    """
    Logger object.
    """
    def __init__(self, loggername="root", loggerFileName=None):
        self.lm = LoggerManager(loggername, loggerFileName) # LoggerManager instance
        self.loggername = loggername # logger name

    def debug(self, msg):
        self.lm.debug(self.loggername, msg)

    def error(self, msg):
        self.lm.error(self.loggername, msg)

    def info(self, msg):
        self.lm.info(self.loggername, msg)

    def warning(self, msg):
        self.lm.warning(self.loggername, msg)

if __name__ == '__main__':

    logger = Logger()
    logger.debug("this testname.")