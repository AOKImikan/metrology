#------------------------------------------------------------------------
# pmm: data1.py
#---------------
# Input data for scans
#------------------------------------------------------------------------
from .pdatahelper import createObject
import logging

logger = logging.getLogger(__name__)

class PersistentData:
    def __init__(self, x=None):
        self.typeName = ''
        self.data = None
        #
        self.serialize(x)
    def serialize(self, x):
        self.typeName = type(x).__name__
        self.data = {}
        if hasattr(x, 'persKeys'):
            keys = x.persKeys()
            for key in keys:
                if hasattr(x, key):
                    x2 = getattr(x, key)
                    x3 = PersistentData(x2)
                    self.data[key] = x3
        elif self.typeName == 'list':
            self.data = []
            for x2 in x:
                p2 = PersistentData(x2)
                self.data.append(p2)
        elif self.typeName == 'dict':
            self.data = {}
            for k2, x2 in x.items():
                p2 = PersistentData(x2)
                self.data[k2] = p2
        else:
            self.typeName = ''
            self.data = x
    def deserialize(self):
        y = None
        if self.typeName == 'list':
            y = self.data
            for i, z in enumerate(y):
                if type(z).__name__ == 'PersistentData':
                    z2 = z.deserialize()
                    y[i] = z2
        elif self.typeName == 'dict':
            y = self.data
            for k, z in y.items():
                if type(z).__name__ == 'PersistentData':
                    z2 = z.deserialize()
                    y[k] = z2
        elif self.typeName == '':
            y = self.data
        else:
            y = createObject(self.typeName)
            for key, x in self.data.items():
                if type(x).__name__ == 'PersistentData':
                    c = x.deserialize()
                    setattr(y, key, c)
                else:
                    setattr(y, key, x)
        return y
    pass
