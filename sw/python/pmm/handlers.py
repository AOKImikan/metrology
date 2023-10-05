#------------------------------------------------------------------------
# pmm: handlers.py
#---------------------
# Action handlers
#------------------------------------------------------------------------
import os
import threading
import logging

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

logger = logging.getLogger(__name__)

#from .acommon import getController, getViewController

class Handlers:
    def __init__(self, model, viewModel):
        self.model = model
        self.viewModel = viewModel
        pass

    def setComponentType(self, ctype):
        logger.info('Selected component type %s' % ctype)
        #
        stypes = self.model.scanTypes(ctype)
        scanInputs = []
        logger.debug('scan types: %s' % str(stypes))
        for stype in stypes:
            y = self.model.scanInput(ctype, stype)
            if y:
                scanInputs.append(y)
                self.model.setComponentType(ctype)
                self.model.updateScanInputs(scanInputs)
                #
        if self.viewModel:
            self.viewModel.updateScansFrame(scanInputs)
        pass

    def useScanConfig(self, configName, scanName):
        configPath = '%s/ScanConfig_%s.txt' %\
            (self.model.config.configDir(), configName)
        #self.model.setScanConfig(scanName, configPath)
        p = self.model.getScanProcessor(scanName)
        if p:
            logger.info(f'Use scanConfig {configName} for {scanName} ({configPath})')
            p.scanData.setConfigFile(configPath)
        else:
            logger.warning(f'Cannot find ScanProcessor {scanName}')
        pass

    def selectLogFile(self, scanName, entry, i=0):
        logger.debug('Select log file for scan %s' % scanName)
        dir1 = self.model.dataDir
        files = QFileDialog.getOpenFileName(None, 'Open scan log', dir1)
        logFile = files[0]
        self.model.dataDir = os.path.dirname(logFile)
        #ft = files[1]
        proc = None
        if logFile != '':
            entry.setText(logFile)
            proc = self.model.getScanProcessor(scanName)
            logger.debug('ScanProcessor: %s' % str(proc))
        if proc != None:
            proc.setLogFile(logFile, i)

    def logFileUpdated(self, scanName, ilog, logFile):
        logger.info(f'Log file for {scanName} is updated to {logFile}')
        proc = self.model.getScanProcessor(scanName)
        if proc != None:
            proc.setLogFile(logFile, ilog)
            proc.clear()
        self.viewModel.sigClearGallery.emit()
        self.updateModuleInfo(logFile)

    def updateModuleInfo(self, logFile):
        if logFile.startswith('/nas/PreProduction'):
            dnames = logFile.split('/')
            componentType = dnames[3]
            serialNumber = dnames[4]
            stage = dnames[5]
            if stage in ('ASSEMBLY', 'Module'):
                stage = 'MODULE_ASSEMBLY'
            elif stage in ('WIREBONDING'):
                stage = 'MODULE_WIREBONDING'
            elif stage in ('BareModule'):
                stage = 'BAREMODULERECEPTION'
            elif stage in ('PCB'):
                stage = 'PCB_RECEPTION_MODULE_SITE'
            self.viewModel.setStage(stage)
            self.viewModel.setSerialNumber(serialNumber)
        elif logFile.startswith('/ATLASProduction/ITkPixel/PreProduction'):
            dnames = logFile.split('/')
            componentType = dnames[4]
            serialNumber = dnames[5]
            stage = dnames[6]
            if stage in ('ASSEMBLY', 'Module'):
                stage = 'MODULE_ASSEMBLY'
            elif stage in ('WIREBONDING'):
                stage = 'MODULE_WIREBONDING'
            elif stage in ('BareModule'):
                stage = 'BAREMODULERECEPTION'
            elif stage in ('PCB'):
                stage = 'PCB_RECEPTION_MODULE_SITE'
            self.viewModel.setStage(stage)
            self.viewModel.setSerialNumber(serialNumber)
        else:
            dnames = logFile.split('/')
            sn = ''
            for dname in dnames:
                i = dname.find('20UPG')
                if i>=0 and len(dname)>=(i+14):
                    sn = dname[i:i+14]
                    break
            self.viewModel.setSerialNumber(sn)
            
    def selectZoom(self, scanName, e):
        pass

    def processScan(self, scanName):
        self.model.processScan(scanName)

    def processAllScansThread(self):
        self.model.processAllScans()
        #
        scanNames = self.model.scanNames()
        updatedTables = []
        height_nrows = 0
        for sn in scanNames:
            p = self.model.getScanProcessor(sn)
            if p:
                stype, tdata = p.tableData()
                tname = f'Table:{stype}'
                if not tname in updatedTables:
                    self.viewModel.clearTable(tname)
                    updatedTables.append(tname)
                if len(tdata)>0:
                    logger.info('Update table %s for %s' % (stype, sn))
                    if tname == 'Table:Height':
                        self.viewModel.updateTable(tname, tdata, rowOffset=height_nrows)
                        height_nrows += len(tdata)
                    else:
                        self.viewModel.updateTable(tname, tdata)
        self.model.save()
        
    def processAllScans(self):
        t = threading.Thread(target=self.processAllScansThread)
        t.start()

    def testStepChanged(self, x):
        logger.debug('TestStep changed')
        self.model.setTestStep(x)
        pass

    def componentNameChanged(self, x):
        logger.debug('ComponentName changed')
        self.model.setComponentName(x)
        pass
    
    def updateTestSteps(self):
        steps = self.model.config.testSteps()
        self.viewModel.view.setTestSteps(steps)
    
    def updateComponentTypes(self):
        ctypes = self.model.config.componentTypes()
        self.viewModel.view.setComponentTypes(ctypes)
    
    def saveFile(self):
        self.model.save()
        
