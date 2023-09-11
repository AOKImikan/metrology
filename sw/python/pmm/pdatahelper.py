#------------------------------------------------------------------------
# pmm: data1.py
#---------------
# Input data for scans
#------------------------------------------------------------------------
import importlib
import inspect
import logging

logger = logging.getLogger(__name__)

def createObject(typeName):
    x = None
    module = importlib.import_module('pmm')
    cls = getattr(module, typeName)
    if cls:
        clsInit = getattr(cls, '__init__')
        params = inspect.signature(clsInit).parameters
        n = len(params)
        if n == 1:
            x = cls()
        else:
            args = [None]*(n-1)
            x = cls(*args)
    return x

