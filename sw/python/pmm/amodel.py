#------------------------------------------------------------------------
# pmm: amodel.py
#---------------
# Application model
#------------------------------------------------------------------------

import os
import re
import json
import configparser
import threading
import pickle
import logging
logger = logging.getLogger(__name__)

import cv2

from .acommon import createAnalysis, getAnalysisStore

from .data1 import *
from .data2 import *
from .data3 import *
from .pdata import PersistentData
from .analysis import *

#--------------------------------------------------
# ScanProcessor
#--------------------------------------------------
class ScanProcessor:
    def __init__(self, name, scanType, nInputs=1):
        self.name = name
        self.scanType = scanType
        self.nInputs = nInputs
        #
        self.scanData = None
        self.scanData2 = None
        self.analysisList = []
        self.outKeys = []
        self.outData = {}

    def persKeys(self):
        return ['name', 'scanType', 'nInputs', 'scanData', 'scanData2',
                'analysisList', 'outKeys', 'outData']
    
    def shortScanType(self):
        x = self.scanType
        i = self.scanType.rfind('.')
        if i>=0:
            x = self.scanType[i+1:]
        return x

    def scanDataForAnalysis(self):
        if self.scanData and not self.scanData2:
            return self.scanData
        elif self.scanData and self.scanData2:
            return self.scanData
        else:
            return None
        
    def setInput(self, configFile, zoom, logFiles=[]):
        n = len(logFiles)
        if n == 0:
            logger.debug('ScanProcessor, setting scan data without log file.')
            self.scanData = ScanData(configFile, zoom, '')
        elif n <= 2:
            if n >= 1:
                logger.debug('ScanProcessor, setting scan data with 1 log file.')
                self.scanData = ScanData(configFile, zoom, logFiles[0])
            if n >= 2:
                logger.debug('ScanProcessor, setting scan data with 2 log files.')
                self.scanData2 = ScanData(configFile, zoom, logFiles[1])
        else:
            logger.warning('ScanProcessor supports only up to two log files')

    def setLogFile(self, logFile, i=0):
        if i == 0:
            if self.scanData == None:
                self.scanData = ScanData('', 1, '')
            self.scanData.setLogFile(logFile)
        elif i == 1:
            if self.scanData2 == None:
                cfile, zoom = '', 1
                if self.scanData:
                    cfile, zoom = self.scanData.configPath, self.scanData.zoom
                self.scanData2 = ScanData(cfile, zoom, '')
            self.scanData2.setLogFile(logFile)

    def addAnalysis(self, a):
        a.scanProcessor = self
        self.analysisList.append(a)

    def readInput(self):
        status = False
        logger.debug(f'ScanData={self.scanData}, 2={self.scanData2}')
        if self.scanData != None:
            status = self.scanData.read()
            if status == False:
                return status

        if self.scanData2 != None:
            status = self.scanData2.read()
            if status == False:
                return status

        return True

    def run(self):
        status = self.preRun()
        logger.debug('ScanProcessor preRun status %s' %  str(status))
        if status == False:
            return status
        t = threading.Thread(target=self.runThread)
        t.start()
        t.join()
        self.postRun()
        return status
    
    def runThread(self):
        status = True
        logger.debug(f'Run {len(self.analysisList)} analyses')
        self.outData.clear()
        analysis1 = None
        for a in self.analysisList:
            logger.info('Scan %s, run analysis %s' % (self.name, a.name) )
            scanData = self.scanDataForAnalysis()
            a.setScanData(scanData)
            if analysis1:
                a.setInputData(analysis1.inData)
                a.addInputData(analysis1.outData)
                logger.debug(f'Added input data {a.inData.keys()}')
            s = a.run()
            if s == False:
                status =s
                logger.error('Error while running analysis %s' % a.name)
                break
            keys = a.outputKeys()
            #logger.debug(f'  analysis output keys: {keys}, {a.outData}')
            for key in keys:
                if key not in self.outKeys:
                    self.outKeys.append(key)
            for k in keys:
                x = a.outputData(k)
                if x:
                    self.outData[k] = x
            analysis1 = a
            #
        logger.info(f'ScanProcessor[{self.name}] thread finished')
        return status

    def preRun(self):
        status = self.readInput()
        return status

    def postRun(self):
        for k in self.outKeys:
            if not k in self.outData.keys():
                logger.error(f'Post scan: key {k} is not available')
        return True

    def findImageOwner(self, tagImageName):
        tag, imageName = tagImageName.split('/')
        analysis = None
        for a in self.analysisList:
            if hasattr(a, 'tagImageMap') and tag in a.tagImageMap.keys():
                images = a.tagImageMap[tag]
                if imageName in images.keys():
                    analysis = a
                    break
        return analysis

    def reprocess(self):
        logger.info('Reprocess scan')
        self.run()
        pass
    
    def tableData(self):
        st = self.shortScanType()
        v = []
        logger.info(f'Summary table: {self.outKeys}')
        for k in self.outKeys:
            if not k in self.outData.keys():
                continue
            mv = self.outData[k]
            if mv:
                vname = mv.value('name')
                x, dx = mv.value('value'), mv.value('error')
                n = 1
                if mv.hasKey('values'):
                    n = len(mv.value('values'))
                logger.info(f'  {vname}: {x:6.4f} +- {dx:6.4f} ({n})')
                v.append([vname, x, dx])
            else:
                logger.warning('Table data %s is null' % k)
        return (st, v)

    def tagImageMap(self):
        m = {}
        for a in self.analysisList:
            if hasattr(a, 'tagImageMap'):
                m2 = a.tagImageMap
                for k, v in m2.items():
                    m[k] = v
        return m
    pass

#--------------------------------------------------
# AppModel
#--------------------------------------------------
class AppModel:
    def __init__(self):
        self.componentType = ''
        self.testStep = ''
        self.componentName = ''
        self.componentSN = ''
        self.config = None
        self.currentSP = None
        self.scanInputs = {}
        self.scanProcessors = {}

        self.setupAnalysis()
        pass

    def persKeys(self):
        return [ 'componentType', 'testStep', 'componentName',
                 'componentSN', 'config', 'scanInputs', 'scanProcessors' ]

    def readSetups(self, fn):
        self.config = SetupsConfig()
        self.config.read(fn)

    def setupAnalysis(self):
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

    def setComponentType(self, componentType):
        self.componentType = componentType

    def setComponentName(self, name):
        self.componentName = name
        pass
    
    def setComponentSN(self, sn):
        self.componentSN = sn
        pass
    
    def updateScanInputs(self, scanInputs):
        self.scanProcessors.clear()
        for scan in scanInputs:
            nInputs = len(scan.selectButtonTexts)
            logger.debug('Add scan %s: %s' % (scan.scanName, scan.scanType))
            proc = ScanProcessor(scan.scanName, scan.scanType, nInputs)
            configPath = '%s/ScanConfig_%s.txt' %\
                (self.config.configDir(), scan.defaultConfig())
            proc.setInput(configPath, scan.defaultZoom)
            for aname in scan.analysisList:
                analysisObject = createAnalysis(aname, model=self)
                if analysisObject:
                    logger.debug('  Add analysis %s' % aname)
                    proc.addAnalysis(analysisObject)
                else:
                    logger.warning('Cannot find the analysis %s' % aname)
            self.addScanProcessor(scan.scanName, proc)
            p = self.getScanProcessor(scan.scanName)
            logger.info(f'Scan analyses just after: {len(p.analysisList)}')

    def scanNames(self):
        v = []
        for s in self.scanProcessors.keys():
            v.append(s)
        return v

    def setScanConfig(self, scanName, configPath):
        p = self.getScanProcessor(scanName)
        if p:
            logger.debug(f'Setting scan config: {configPath}')
            p.scanData.configFile = configPath
        pass
    
    def addScanProcessor(self, scanName, proc):
        self.scanProcessors[scanName] = proc
         
    def getScanProcessor(self, scanName):
        scan = None
        if scanName in self.scanProcessors.keys():
            scan = self.scanProcessors[scanName]
        return scan

    def currentScanProcessor(self):
        return self.currentSP
    
    def outputDir(self):
        mdir = self.config.moduleDir()
        if not mdir.startswith('/'):
            mdir = os.path.join(os.getcwd(), mdir)
        odir = os.path.join(mdir, self.componentType, self.componentName)
        if not os.path.exists(odir):
            os.mkdir(odir)
        return odir
        
    def scanTypes(self, ctype):
        return self.config.scanTypes(ctype)

    def scanInput(self, ctype, stype):
        return self.config.scanInput(ctype, stype)
    
    def setTestStep(self, step):
        self.testStep = step
    
    def processScan(self, scanName):
        logger.info('Processing scan %s' % scanName)
        p = self.getScanProcessor(scanName)
        if p:
            self.currentSP = p
            status = p.run()
            if status==False:
                self.currentSP = None
                return
        self.currentSP = None
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

    def findImageOwnerAnalysis(self, imageTagName):
        analysis = None
        for sn1, sp1 in self.scanProcessors.items():
            analysis = sp1.findImageOwner(imageTagName)
            if analysis:
                break
        return analysis
    
    def save(self, fname):
        pdata = PersistentData(self)
        fout = open(fname, 'wb')
        pickle.dump(pdata, fout)
        fout.close()
        
                
