#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
import logging
from pmm.design import *
from pmm.workflow import *
from pmm.ModuleAnalysis import *

logger = logging.getLogger(__name__)

class GuiHandlers:
    def __init__(self, window, data, configStore):
        self.data = data
        self.configStore = configStore
        self.analysis = ModuleAnalysis(self.data)
        self.window = window
        pass

    def selectComponentType(self, x):
        logger.info('Component type is %s' % x)
        self.window.data.moduleType = x
        self.window.moduleDesign = createModule(self.window.data.moduleType)
        cvConfig = self.window.configStore.componentViewConfig
        self.window.componentView = cvConfig.componentView(self.window.data.moduleType)
        self.window.buildInputBoxes(self.window.frameScans.layout())
        pass
    
    def selectStep(self):
        pass
    
    def setModuleName(self):
        pass
    
    def selectConfigFile(self):
        pass
    
    def selectLogFile(self):
        pass
    
    def processHeight(self):
        pass

    def processSize(self):
        #if self.analysis:
        #    logger.debug('Call ModuleAnalysis.processSize')
        #    self.analysis.processSize()
        logger.debug('Update size scan results (from GuiHandlers)')
        self.data.patternResultsMap = {}
        worker = PatternRecScan(self.data.moduleType, 
                                self.data.moduleDir(self.configStore.workDir), 
                                self.data.scanResults.size(), 
                                self.data.sizeScanConfig, 
                                self.data.patternResultsMap,
                                configStore=self.configStore)
        t1 = threading.Thread(target=worker.run)
        t1.start()
        logger.debug('Try to join')
        t1.join()
        logger.debug('Joined thread')
        #logger.debug(str(self.patternResultsMap))
        self.window.updatePhotoDetail(self.window.photoPanel, self.data.patternResultsMap)
        self.window.updateSizeScanTable()
        pass

    def processFlatness(self):
        pass

    def saveJson(self):
        pass
    
        
