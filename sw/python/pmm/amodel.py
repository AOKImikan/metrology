#------------------------------------------------------------------------
# pmm: amodel.py
#---------------
# Application model
#------------------------------------------------------------------------

import os
import re
import datetime
import threading
import json
import pickle
import logging
import distutils.dir_util

import cv2

from .acommon import createAnalysis, getAnalysisStore
from .data1 import *
from .data2 import *
from .data3 import *
from .pdata import PersistentData
from .analysis import *
from .tools import roundF
from .design import createModule

logger = logging.getLogger(__name__)

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
        if st == 'BackHeight': st = 'Height'
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

    def clear(self):
        for a in self.analysisList:
            a.clear()
    pass

#--------------------------------------------------
# AppModel
#--------------------------------------------------
class AppModel:
    def __init__(self):
        self.componentType = ''
        self.testStep = 'UNKNOWN'
        self.componentName = 'UNKNOWN'
        self.componentSN = ''
        #
        self.config = None
        self.siteConfig = None
        self.dataDir = '.'
        self.scanWorkDir = ''
        #
        self.currentSP = None
        self.scanInputs = {}
        self.scanProcessors = {}
        #

        self.setupAnalyses()
        self.moduleDesign = None
        
        pass

    def persKeys(self):
        return [ 'componentType', 'testStep', 'componentName',
                 'componentSN', 'config', 
                 'dataDir', 'scanWorkDir', 
                 'scanInputs', 'scanProcessors' ]

    def readSetups(self, fn):
        self.config = SetupsConfig()
        self.config.read(fn)

    def readSiteConfig(self, fn):
        self.siteConfig = readSiteConfig(fn)
        
    def updateModuleDesign(self):
        self.moduleDesign = createModule(self.componentType)
        return self.moduleDesign
    
    def setupAnalyses(self):
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
        self.clear()
        for sp in self.scanProcessors.values():
            sp.clear()

    def setComponentName(self, name):
        self.componentName = name
        self.clear()
        for sp in self.scanProcessors.values():
            sp.clear()
        pass
    
    def setComponentSN(self, sn):
        self.componentSN = sn
        self.clear()
        for sp in self.scanProcessors.values():
            sp.clear()
        pass
    
    def updateScanInputs(self, scanInputs):
        self.scanProcessors.clear()
        for scan in scanInputs:
            nInputs = len(scan.selectButtonTexts)
            logger.info('Add scan %s: %s' % (scan.scanName, scan.scanType))
            proc = ScanProcessor(scan.scanName, scan.scanType, nInputs)
            configPath = '%s/ScanConfig_%s.txt' %\
                (self.config.configDir(), scan.defaultConfig())
            proc.setInput(configPath, scan.defaultZoom)
            for aname in scan.analysisList:
                analysisObject = createAnalysis(aname, model=self)
                if analysisObject:
                    logger.info('  Add analysis %s' % aname)
                    proc.addAnalysis(analysisObject)
                else:
                    logger.warning('Cannot find the analysis %s' % aname)
            self.addScanProcessor(scan.scanName, proc)
            p = self.getScanProcessor(scan.scanName)
            #logger.info(f'Scan analyses just after: {len(p.analysisList)}')

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

    def itkComponentType(self):
        ct = 'UNKNOWN'
        if self.componentType.find('Flex')>=0:
            ct = 'PCB'
        elif self.componentType.find('BareModule')>=0:
            ct = 'BARE_MODULE'
            #ct = 'BareModule'
        elif self.componentType.find('Module')>=0:
            ct = 'MODULE'
            #ct = 'Module'
        return ct

    def shortStageName(self):
        x = self.testStep
        if self.testStep == 'MODULE_ASSEMBLY':
            x = 'ASSEMBLY'
        elif self.testStep == 'MODULE_WIREBONDING':
            x = 'MODULE_WIREBONDING'
        return x
    
    def workDir(self):
        mdir = ''
        if 'workDir' in self.siteConfig.keys():
            mdir = self.siteConfig['workDir']
        if mdir == '':
            mdir = self.config.moduleDir()
        if mdir == '':
            mdir = '.'
        return mdir

    def workDirCandidate(self, dir0):
        dbase = 'MetrologyCheck'
        dbase = ''
        #
        ct = self.itkComponentType()
        odir = os.path.join(dir0, ct, self.componentName, self.testStep)
        number = '001'
        if os.path.exists(odir):
            dirs = os.listdir(odir)
            n = len(dbase)
            dirs = list(filter(lambda x: x.startswith(dbase), dirs))
            dirs = list(filter(lambda x: x[n:n+3].isdecimal(), dirs))
            dirs.sort()
            if len(dirs) == 0:
                number = '001'
            else:
                wdn = os.path.join(odir, dirs[-1])
                files = os.listdir(wdn)
                if len(files) == 0:
                    number = dirs[-1].replace(dbase, '')
                else:
                    n1 = dirs[-1].replace(dbase, '')
                    if n1 == '':
                        n1 = 1
                    else:
                        n1 = int(n1) + 1
                    number = f'{n1:03d}'
        wdir = os.path.join(odir, f'{dbase}{number}')
        return wdir
    
    def archiveDir(self):
        adir = ''
        if 'archiveDir' in self.siteConfig.keys():
            adir = self.siteConfig['archiveDir']
        if not adir.startswith('/'):
            adir = os.path.join(os.getcwd(), mdir)
        adir = self.workDirCandidate(adir)
        return adir
    
    def outputDir(self):
        if self.scanWorkDir != '':
            return self.scanWorkDir
        mdir = self.workDir()
        if not mdir.startswith('/'):
            mdir = os.path.join(os.getcwd(), mdir)
        mdir = self.workDirCandidate(mdir)
        self.scanWorkDir = mdir
        return mdir
        
    def scanTypes(self, ctype):
        return self.config.scanTypes(ctype)

    def scanInput(self, ctype, stype):
        return self.config.scanInput(ctype, stype)
    
    def setTestStep(self, step):
        logger.info(f'Set test step to {step}')
        self.testStep = step
        for sp in self.scanProcessors.values():
            sp.clear()

    def makeDirs(self, dname, mode):
        umask1 = os.umask(0)
        try:
            os.makedirs(dname, mode=mode)
        except PermissionError as e:
            logger.error(f'Error occured while trying to create the directory {dname}')
            logger.error(e)
        os.umask(umask1)
        
    def moveToOutputDir(self):
        dn = self.outputDir()
        if not os.path.exists(dn):
            self.makeDirs(dn, 0o777)
        os.chdir(dn)
        
    def processScan(self, scanName):
        logger.info('Processing scan %s' % scanName)
        dn0 = os.getcwd()
        self.moveToOutputDir()
        p = self.getScanProcessor(scanName)
        if p:
            self.currentSP = p
            status = p.run()
            if status==False:
                self.currentSP = None
                return
        os.chdir(dn0)
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

    def officialComponentType(self):
        x = ''
        if self.componentType in ('ITkPixV1xBareModule', 'Rd53aBareModule'):
            x = 'BARE_MODULE'
        elif self.componentType in ('ITkPixV1xFlex', 'Rd53aFlex'):
            x = 'PCB'
        elif self.componentType in ('ITkPixV1xModule', 'Rd53aModule'):
            x = 'MODULE'
        return x
    
    def officialStage(self):
        x = self.testStep
        if self.testStep == 'MODULE_ASSEMBLY':
            x = 'MODULE/ASSEMBLY'
        return x

    def spByType(self, shortScanType):
        sp = None
        for k, sp1 in self.scanProcessors.items():
            if k.find(shortScanType)>=0:
                sp = sp1
                break
        return sp
    
    def bareModuleDataForDB(self):
        data = {}
        pa = self.spByType('Size').analysisList[0]
        sa = self.spByType('Size').analysisList[1]
        ha = self.spByType('Height').analysisList[0]
        bha = self.spByType('BackHeight').analysisList[0]
        #
        bmZ = ha.outData['SensorZ'].get('value') 
        bmZsigma = ha.outData['SensorZ'].get('error')
        asicZ = ha.outData['AsicZ'].get('value')
        asicZSigma = ha.outData['AsicZ'].get('error')
        sensorX = sa.outData['SensorX'].get('value')
        sensorY = sa.outData['SensorY'].get('value')
        asicX = sa.outData['AsicX'].get('value')
        asicY = sa.outData['AsicY'].get('value')
        sensorZ = 0.0
        sensorZsigma = 0.0
        if 'SensorZ(Back)' in bha.outData.keys():
            sensorZ = bha.outData['SensorZ(Back)'].get('value') 
            sensorZsigma = bha.outData['SensorZ(Back)'].get('error')
        now = datetime.datetime.now().astimezone()
        institution = 'HERE'
        if self.siteConfig and 'institution' in self.siteConfig.keys():
            institution = self.siteConfig['institution']
        #
        institution = 'KEK'
        if 'institution' in self.siteConfig.keys():
            institution = self.siteConfig['institution']
        data['institution'] = institution
        data['component'] = self.componentName
        data['componentType'] = self.officialComponentType()
        data['stage'] = self.officialStage()
        data['testType'] = 'QUAD_BARE_MODULE_METROLOGY'
        data['date'] = now.isoformat(timespec='milliseconds')
        fmt = '5.3f'
        results = {}
        um, fmt2 = 1.0E+3, '5.1f'
        results['SENSOR_X'] = roundF(sensorX, fmt)
        results['SENSOR_Y'] = roundF(sensorY, fmt)
        results['FECHIPS_X'] = roundF(asicX, fmt)
        results['FECHIPS_Y'] = roundF(asicY, fmt)
        results['FECHIP_THICKNESS'] = roundF(asicZ*um, fmt2)
        results['FECHIP_THICKNESS_STD_DEVIATION'] = roundF(asicZSigma*um, fmt2)
        results['BAREMODULE_THICKNESS'] = roundF(bmZ*um, fmt2)
        results['BAREMODULE_THICKNESS_STD_DEVIATION'] = roundF(bmZsigma*um, fmt2)
        results['SENSOR_THICKNESS'] = roundF(sensorZ*um, fmt2)
        results['SENSOR_THICKNESS_STD_DEVIATION'] = roundF(sensorZsigma*um, fmt2)
        data['results'] = results
        data['passed'] = True
        data['problems'] = False
        data['runNumber'] = "1"
        return data

    def flexDataForDB(self):
        data = {}
        pa = self.spByType('Size').analysisList[0]
        sa = self.spByType('Size').analysisList[1]
        ha = self.spByType('Height').analysisList[0]
        #
        flexX = sa.outData['FlexX'].get('value')
        flexY = sa.outData['FlexY'].get('value')
        Zvalues = ha.outData['PickupZ'].get('values')
        Zsigmas = [0.002]*4
        pickupZ = ha.outData['PickupZ'].get('value')
        sigmaZ = ha.outData['PickupZ'].get('error')
        hvcapZ = ha.outData['HVCapacitorZ'].get('value')
        connZ = ha.outData['ConnectorZ'].get('value')
        diameterA = sa.outData['HoleTL_diameter'].get('value')
        widthB = sa.outData['SlotBR_width'].get('value')
        now = datetime.datetime.now().astimezone()
        institution = ''
        if self.siteConfig and 'institution' in self.siteConfig.keys():
            institution = self.siteConfig['institution']
        #
        institution = 'KEK'
        if 'institution' in self.siteConfig.keys():
            institution = self.siteConfig['institution']
        data['institution'] = institution
        data['component'] = self.componentName
        data['componentType'] = self.officialComponentType()
        data['stage'] = self.officialStage()
        data['testType'] = 'METROLOGY'
        data['date'] = now.isoformat(timespec='milliseconds')
        fmt = '5.3f'
        results = {}
        results['X_DIMENSION'] = roundF(flexX, fmt)
        results['Y_DIMENSION'] = roundF(flexY, fmt)
        results['X-Y_DIMENSION_WITHIN_ENVELOP'] = True
        #results['AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS'] = roundF(Zvalues, fmt)
        #results['STD_DEVIATION_THICKNESS_FECHIP_PICKUP_AREAS'] = roundF(Zsigmas, fmt)
        results['AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS'] = roundF(pickupZ, fmt)
        results['STD_DEVIATION_THICKNESS_FECHIP_PICKUP_AREAS'] = roundF(sigmaZ, fmt)
        results['HV_CAPACITOR_THICKNESS'] = roundF(hvcapZ, fmt)
        results['HV_CAPACITOR_THICKNESS_WITHIN_ENVELOP'] = True
        results['AVERAGE_THICKNESS_POWER_CONNECTOR'] = roundF(connZ, fmt)
        results['DIAMETER_DOWEL_HOLE_A'] = roundF(diameterA, fmt)
        results['WIDTH_DOWEL_SLOT_B'] = roundF(widthB, fmt)
        data['results'] = results
        data['passed'] = True
        data['problems'] = False
        data['runNumber'] = "1"
        return data

    def moduleDataForDB(self):
        data = {}
        pa = self.spByType('Size').analysisList[0]
        sa = self.spByType('Size').analysisList[1]
        ha = self.spByType('Height').analysisList[0]
        #
        pickupZvalues = ha.outData['PickupZ'].get('values')
        sigmaZ = 0.002
        now = datetime.datetime.now().astimezone()
        institution = ''
        if self.siteConfig and 'institution' in self.siteConfig.keys():
            institution = self.siteConfig['institution']
        #
        institution = 'KEK'
        if 'institution' in self.siteConfig.keys():
            institution = self.siteConfig['institution']
        data['institution'] = institution
        data['component'] = self.componentName
        data['componentType'] = self.officialComponentType()
        data['stage'] = self.officialStage()
        data['testType'] = 'QUAD_MODULE_METROLOGY'
        data['date'] = now.isoformat(timespec='milliseconds')
        fmt = '5.3f'
        results = {}
        results['PCB_BAREMODULE_POSITION_TOP_RIGHT'] = [
            roundF(sa.outData['FmarkDistanceTR_x'].get('value'), fmt), 
            roundF(sa.outData['FmarkDistanceTR_y'].get('value'), fmt) 
        ]
        results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT'] = [
            roundF(sa.outData['FmarkDistanceBL_x'].get('value'), fmt), 
            roundF(sa.outData['FmarkDistanceBL_y'].get('value'), fmt)
        ]
        results['ANGLE_PCB_BM'] = roundF(sa.outData['Angle'].get('value'), fmt)
        results['AVERAGE_THICKNESS'] = pickupZvalues
        results['STD_DEVIATION_THICKNESS'] = [sigmaZ]*4
        results['THICKNESS_VARIATION_PICKUP_AREA'] = roundF(max(pickupZvalues)-min(pickupZvalues), fmt)
        results['THICKNESS_INCLUDING_POWER_CONNECTOR'] = roundF(ha.outData['ConnectorZ'].get('value'), fmt)
        results['HV_CAPACITOR_THICKNESS'] = roundF(ha.outData['HVCapacitorZ'].get('value'), fmt)
        data['results'] = results
        data['passed'] = True
        data['problems'] = False
        data['runNumber'] = "1"
        return data

    def clear(self):
        self.scanWorkDir = ''
        pass
    
    def saveJson(self):
        outputDir = self.outputDir()
        fn = f'{outputDir}/db.json'
        data = {}
        #fn = fn.replace('./BARE_MODULE', 'pmmWork/BARE_MODULE')
        
        try:
            if self.componentType == 'ITkPixV1xBareModule':
                data = self.bareModuleDataForDB()
            elif self.componentType == 'ITkPixV1xFlex':
                data = self.flexDataForDB()
            elif self.componentType == 'ITkPixV1xModule':
                data = self.moduleDataForDB()
            with open(fn, 'w') as fout:
                logger.info(f'Saved the results in ${fn} (to be uploaded to the ProdDB)')
                json.dump(data, fout, indent=2)
        except KeyError as e:
            logger.error('Exeption while generating JSON file for DB upload. Probably some parameters were not calculated properly.')
            logger.error(f'{e}')
        return fn
    
    def save(self):
        pdata = PersistentData(self)
        dn = self.outputDir()
        fname = os.path.join(dn, 'data.pickle')
        # Save current state to the working directory
        if not os.path.exists(dn):
            self.makeDirs(dn, 0o777)
        self.saveJson()
        logger.info(f'Save application data to {fname}')
        fout = open(fname, 'wb')
        pickle.dump(pdata, fout)
        fout.close()
        
        # Copy the working directory to the archive area
        docopy = False
        if docopy:
            dest = self.archiveDir()
            logger.info(f'Copy the working directory to {dest}')
            if not os.path.exists(dest):
                self.makeDirs(dn, 0o777)
            distutils.dir_util.copy_tree(dn, dest)
        else:
            #logger.info(f'Working directory at {dn}. It still has to be copied to the archive area')
            pass
            #logger.info(f'  > mkdir -p {dest}')
            #logger.info(f'  > cp -r {dn} {dest}')
            
            
        
