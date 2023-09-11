#------------------------------------------------------------------------
# pmm: handlers.py
#---------------------
# Action handlers
#------------------------------------------------------------------------

import threading
from logging import getLogger
logger = getLogger(__name__)

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

#from .acommon import getController, getViewController

class Handlers:
    def __init__(self, model, viewModel):
        self.model = model
        self.viewModel = viewModel
        pass

    def selectComponentType(self, ctype):
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
            p.scanData.configFile = configPath
        else:
            logger.warning(f'Cannot find ScanProcessor {scanName}')
        pass

    def selectLogFile(self, scanName, entry, i=0):
        logger.debug('Select log file for scan %s' % scanName)
        dir1 = '.'
        files = QFileDialog.getOpenFileName(None, 'Open scan log', dir1)
        logFile = files[0]
        #ft = files[1]
        proc = None
        if logFile != '':
            entry.setText(logFile)
            proc = self.model.getScanProcessor(scanName)
            logger.debug('ScanProcessor: %s' % str(proc))
        if proc != None:
            proc.setLogFile(logFile, i)

    def selectZoom(self, scanName, e):
        pass

    def processScan(self, scanName):
        self.model.processScan(scanName)

    def processAllScansThread(self):
        self.model.processAllScans()
        #
        scanNames = self.model.scanNames()
        for sn in scanNames:
            p = self.model.getScanProcessor(sn)
            if p:
                stype, tdata = p.tableData()
                if len(tdata)>0:
                    logger.info('Update table %s for %s' % (stype, sn))
                    self.viewModel.updateTable('Table:%s' % stype, tdata)

    def processAllScans(self):
        t = threading.Thread(target=self.processAllScansThread)
        t.start()
    
