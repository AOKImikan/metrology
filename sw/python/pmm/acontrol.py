#------------------------------------------------------------------------
# pmm: acontrol.py
#-----------------
# Application control
#------------------------------------------------------------------------
import logging

from .acommon import getModel, getViewController, getAnalysisStore
from .amodel import AppModel
from .analysis import *

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, data):
        self.data = data
        self.vcontroller = None

    def initialize(self):
        store = getAnalysisStore()
        # Base analysis classes
        store.add('FlatnessVacOnOffAnalysis', FlatnessVacOnOffAnalysis)
        store.add('FlatnessBackSideAnalysis', FlatnessBackSideAnalysis)
        # Flex
        store.add('FlexPatternAnalysis', FlexPatternAnalysis)
        store.add('FlexSizeAnalysis', FlexSizeAnalysis)
        # Bare module
        store.add('BareModulePatternAnalysis', BareModulePatternAnalysis)
        store.add('BareModuleSizeAnalysis', BareModuleSizeAnalysis)
        store.add('BareModuleBackPatternAnalysis', BareModuleBackPatternAnalysis)
        store.add('BareModuleBackSizeAnalysis', BareModuleBackSizeAnalysis)
        # Assembled module
        store.add('ModulePatternAnalysis', ModulePatternAnalysis)
        store.add('ModuleSizeAnalysis', ModuleSizeAnalysis)
        store.add('ModuleRoofPatternAnalysis', ModuleRoofPatternAnalysis)
        store.add('ModuleRoofSizeAnalysis', ModuleRoofSizeAnalysis)
        store.add('ModuleBackPatternAnalysis', ModuleBackPatternAnalysis)
        store.add('ModuleBackSizeAnalysis', ModuleBackSizeAnalysis)
        #
        store.add('FlexHeightAnalysis', FlexHeightAnalysis)
        store.add('BareModuleHeightAnalysis', BareModuleHeightAnalysis)
        store.add('BareModuleBackHeightAnalysis', BareModuleBackHeightAnalysis)
        store.add('ModuleHeightAnalysis', ModuleHeightAnalysis)
        store.add('ModuleRoofHeightAnalysis', ModuleRoofHeightAnalysis)
        store.add('ModuleBackHeightAnalysis', ModuleBackHeightAnalysis)

        pass

    def scanTypes(self, ctype):
        return self.data.config.scanTypes(ctype)

    def scanNamamoes(self):
        return self.data.scanNames()
    
    def scanInput(self, ctype, stype):
        return self.data.config.scanInput(ctype, stype)
    
    def setComponentType(self, cType):
        self.data.setComponentType(cType)
    
    def setTestStep(self, step):
        self.data.testStep = step
    
    def setComponentName(self, name):
        self.data.componentName = name
        pass
    
    def setComponentSN(self, sn):
        self.data.componentSN = sn
        pass
    
    def updateScanInputs(self, scanInputs):
        self.data.updateScanInputs(scanInputs)
        pass

    def addScanProcessor(self, scanName, proc):
        self.data.addScanProcessor(scanName, proc)
        pass
    
    def getScanProcessor(self, scanName):
        return self.data.getScanProcessor(scanName)
        pass

    def processScan(self, scanName):
        logger.info('Processing scan %s' % scanName)
        p = self.getScanProcessor(scanName)
        if p:
            status = p.run()
            if status==False:
                return
        pass
    
    def processAllScans(self):
        scanNames = self.scanNames()
        logger.info('Process all scans (%d)' % len(scanNames))
        for sn in scanNames:
            self.processScan(sn)
        pass

    def findImageNP(self, imageTagName):
        x = None
        scanNames = self.scanNames()
        tag, name = imageTagName.split('/')
        for sn in scanNames:
            proc = self.getScanProcessor(sn)
            if proc == None: continue
            tagImages = proc.tagImageMap()
            if tag in tagImages.keys() and name in tagImages[tag].keys():
                x = tagImages[tag][name]
        return x
            
                
