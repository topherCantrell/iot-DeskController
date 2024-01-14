
cached_loggers = {}

# There is the "adafruit_logging", but I just need super-simple abilities for now


class Logger:

    def __init__(self, name):
        self._name = name

    def debug(self, message):
        print('* DEBUG', self._name, message)

    def info(self, message):
        print('* INFO', self._name, message)

    def error(self, message):
        print('* ERROR', self._name, message)


def getLogger(name):
    if name in cached_loggers:
        return cached_loggers[name]
    ret = Logger(name)
    cached_loggers[name] = ret
    return ret
