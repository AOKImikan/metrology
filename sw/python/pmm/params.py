#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# params:
#--------------------------------------------------------------------

class ParameterStore:
    def __init__(self):
        self.setupParams()
        
    def setupParams(self):
        # (wsum, tgap)
        self.paramsMap = {
            #
            'SearchWindowSize_um:AsicT': (300,), 
            'SearchWindowSize_um:AsicB': (300,), 
            'SearchWindowSize_um:AsicL': (300,), 
            'SearchWindowSize_um:AsicR': (300,), 
            #
            'SearchWindowSize_um:SensorT': (400,), 
            'SearchWindowSize_um:SensorB': (400,), 
            'SearchWindowSize_um:SensorL': (400,), 
            'SearchWindowSize_um:SensorR': (400,), 
            #
            'SearchWindowSize_um:FlexT': (300,), 
            'SearchWindowSize_um:FlexB': (300,), 
            'SearchWindowSize_um:FlexL': (300,), 
            'SearchWindowSize_um:FlexR': (300,), 
            #
            'AsicT': (30, 40), 
            'AsicB': (30, 40), 
            'AsicL': (30, 40), 
            'AsicR': (30, 40),
            #
            'SensorT': (30, 50), 
            'SensorB': (30, 50), 
            'SensorL': (30, 50), 
            'SensorR': (30, 50), 
            #
            'FlexT': (100, 50), 
            'FlexB': (100, 50), 
            'FlexL': (100, 50), 
            'FlexR': (100, 50),
            'FmarkTL': (50, 30), 
            'FmarkBL': (50, 30), 
            'FmarkBR': (50, 30), 
            'FmarkTR': (50, 30), 
            'AsicFmarkTL': (50, 30), 
            'AsicFmarkBL': (50, 30), 
            'AsicFmarkBR': (50, 30), 
            'AsicFmarkTR': (50, 30), 
            }
    def getParams(self, tag):
        params = ()
        if tag in self.paramsMap.keys():
            params = self.paramsMap[tag]
        return params

paramStore = ParameterStore()

