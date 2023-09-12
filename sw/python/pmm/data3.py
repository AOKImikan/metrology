#------------------------------------------------------------------------
# pmm: data3.py
#---------------
# Output data from scans
#------------------------------------------------------------------------
import math
import logging
logger = logging.getLogger(__name__)

from .data1 import KeyValueData

class MeasuredValue(KeyValueData):
    sAllowedKeys = [ 'name', 'value', 'error' ]
    
    def __init__(self, name, value, error):
        self.data = {}
        self.setValue('name', name)
        self.setValue('value', value)
        self.setValue('error', error)
    def allowedKeys(self):
        return MeasuredValue.sAllowedKeys


class AveragedValue(MeasuredValue):
    sAllowedKeys = [ 'name', 'value', 'error', 'n', 'values' ]
    def __init__(self, name, values=[]):
        super().__init__(name, 0.0, 0.0)
        self.setValues(values)

    def setData(self, value, error, n, values):
        self.setValue('value', value)
        self.setValue('error', error)
        self.setValue('n', n)
        self.setValue('values', values)

    def setValues(self, values):
        if values == None:
            return
        xvalues = []
        x2values = []
        if len(values)>0 and type(values[0]).__name__ == 'MeasuredValue':
            for mvalue in values:
                x = mvalue.get('value')
                xvalues.append(x)
                x2values.append(x*x)
        else:
            for x in values:
                xvalues.append(x)
                x2values.append(x*x)
        n = len(xvalues)
        if n>0:
            x = sum(xvalues)/n
            dx = math.sqrt(sum(x2values)/n - x*x)
            self.setData(x, dx, n, values)
            #logger.debug(f'{x} +- {dx} ({n}), values={values}')
        else:
            logger.warning('AverageValue %s with no data' % self.get('name'))
            
    def allowedKeys(self):
        return AveragedValue.sAllowedKeys

