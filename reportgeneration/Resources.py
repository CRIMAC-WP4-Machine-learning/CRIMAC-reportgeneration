import os

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


class Resources(Singleton):
    tmpDir = None

    def init(self):
        pass

    def setTmpDir(self, tmp):
        self.tmpDir = tmp

    def getTmpDir(self):
        return self.tmpDir