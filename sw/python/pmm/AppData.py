import os
import logging
import pickle
from functools import partial
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import math

from pmm.model import *
from pmm.reader import *
from pmm.design import *
from pmm.prec import *
from pmm.workflow import *
from pmm.tools import *
import pmm

logger = logging.getLogger(__name__)


class AppData:
    def __init__(self, appDataPath='.'):
        self.appDataPath = appDataPath

        self.moduleType = 'Rd53aModule'
        self.testStep = 'Unknown'
        self.moduleName = 'module'

        self.pickupScanConfigName = ''
        self.heightScanConfigName = ''
        self.sizeScanConfigName = ''
        self.flatnessScanConfigName = ''

        self.pickupScanConfig = None
        self.heightScanConfig = None
        self.sizeScanConfig = None
        self.flatnessScanConfig = None

        self.pickupZoom = 10
        self.heightZoom = 20
        self.sizeZoom = 20
        self.flatnessZoom = 20

        self.pickupLogFile = ''
        self.heightLogFile = ''
        self.sizeLogFile = ''
        self.flatnessVacOnLogFile = ''
        self.flatnessVacOffLogFile = ''

        self.scanResults = MetrologyScanResults()
        self.patternResultsMap = {}
        self.summary = MetrologySummary()

    def testStepShort(self):
        x = 'Unknown'
        words = self.testStep.split(' ')
        print(words)
        if len(words)>0:
            x = words[0]
        print('Short step is %s' % x)
        return x
    
    def readScanResults(self, ctag):
        pass
    def readScanConfig(self, ctag):
        pass
    def processHeightResults(self):
        results = self.scanResults.height()
        config = self.heightScanConfig
        logger.info('Process height scan results')
        if results == None:
            logger.warning('Cannot process height results, none available')
            return -1
        if config == None:
            logger.warning('Cannot process height results, no config')
            return -2
        values = {}
        logger.debug('N data points: %d' % results.nPoints())
        logger.debug('N scan points: %d' % config.nPoints())
        n = min(results.nPoints(), config.nPoints())
        jigPoints = []
        for i in range(n):
            p = results.pointResult(i)
            c = config.pointConfig(i)
            if len(c.uses)>0 and not 'height' in c.uses: continue
            if not p.isValid: continue
            if len(c.tags)==1:
                tag = c.tags[0]
                logger.debug('%s z=%6.3f' % (tag, p.z))
                if tag not in values.keys():
                    values[tag] = (p.z, p.z*p.z, 1)
                else:
                    x, dx, n = values[tag]
                    x += p.z
                    dx += p.z * p.z
                    n += 1
                    values[tag] = (x, dx, n)
                if tag == 'Jig':
                    jigPoints.append([p.x, p.y, p.z])
        #
        jigPlane = None
        logger.info('N jig points: %d' % (len(jigPoints)))
        if len(jigPoints)>=3:
            jigPlane = pmm.fitPlane(jigPoints)[0]
            n = min(results.nPoints(), config.nPoints())
            for i in range(n):
                p = results.pointResult(i)
                c = config.pointConfig(i)
                if len(c.uses)>0 and not 'height' in c.uses: continue
                if not p.isValid: continue
                if c.tags[0].startswith('Pickup'):
                    p2 = [ p.x, p.y, p.z]
                    d = jigPlane.distance(p2)
                    logger.info('%s %6.3f %6.3f %6.3f, %6.3f' % (c.tags[0], p.x, p.y, p.z, d))
         
        for k in values.keys():
            x, dx, n = values[k]
            x /= n
            x2 = dx/n
            dx = math.sqrt(abs(x2 - x*x))
            # Subtract jig height
            values[k] = (x, dx, n)
        zjig = values['Jig'][0]
        for k in values.keys():
            if k == 'Jig': continue
            x, dx, n = values[k]
            x -= zjig
            values[k] = (x, dx, n)
        logger.debug(str(values))
        self.summary.heightMap = values
        return 0
    def processPickupResults(self):
        results = self.scanResults.pickup()
        config = self.pickupScanConfig
        logger.info('Process pickup scan results')
        if results == None:
            logger.warning('Cannot process pickup results, none available')
            return -1
        if config == None:
            logger.warning('Cannot process pickup results, no config')
            return -2
        values = {}
        logger.debug('N data points: %d' % results.nPoints())
        logger.debug('N scan points: %d' % config.nPoints())
        n = min(results.nPoints(), config.nPoints())
        for i in range(n):
            p = results.pointResult(i)
            c = config.pointConfig(i)
            if len(c.uses)>0 and not 'height' in c.uses: continue
            if not p.isValid: continue
            if len(c.tags)==1:
                tag = c.tags[0]
                if tag not in values.keys():
                    values[tag] = (p.z, p.z*p.z, 1)
                else:
                    x, dx, n = values[tag]
                    x += p.z
                    dx += p.z * p.z
                    n += 1
                    values[tag] = (x, dx, n)
        for k in values.keys():
            x, dx, n = values[k]
            x /= n
            x2 = dx/n
            dx = math.sqrt(abs(x2 - x*x))
            values[k] = (x, dx, n)
        zjig = values['Jig'][0]
        for k in values.keys():
            if k == 'Jig': continue
            x, dx, n = values[k]
            x -= zjig
            values[k] = (x, dx, n)
        logger.debug(str(values))
        self.summary.pickupMap = values
        return 0
    def postProcessSizeResults(self):
        keys = list(self.patternResultsMap.keys())
        keys.sort()
        valueMap = {}
        sigmaMap = {}
        for k in keys:
            mean, sigma = patternMeanSigma(k, self.patternResultsMap[k])
            valueMap[k] = mean
            sigmaMap[k] = sigma
        # New calculation
        m = self.patternResultsMap
        # Calculate distance between lines more precisely
        if 'FlexT' in keys:
            pointsFlexT = extractPoints(m['FlexT'])
            pointsFlexB = extractPoints(m['FlexB'])
            valueMap['FlexY'], sigmaMap['FlexY'] = calculateY(pointsFlexT, pointsFlexB)
        if 'FlexL' in keys:
            pointsFlexL = extractPoints(m['FlexL'])
            pointsFlexR = extractPoints(m['FlexR'])
            valueMap['FlexX'], sigmaMap['FlexX'] = calculateX(pointsFlexL, pointsFlexR)
        if 'AsicT' in keys:
            pointsAsicT = extractPoints(m['AsicT'])
            pointsAsicB = extractPoints(m['AsicB'])
            valueMap['AsicY'], sigmaMap['AsicY'] = calculateY(pointsAsicT, pointsAsicB)
        if 'AsicL' in keys:
            pointsAsicL = extractPoints(m['AsicL'])
            pointsAsicR = extractPoints(m['AsicR'])
            valueMap['AsicX'], sigmaMap['AsicX'] = calculateX(pointsAsicL, pointsAsicR)
        if 'SensorT' in keys:
            pointsSensorT = extractPoints(m['SensorT'])
            pointsSensorB = extractPoints(m['SensorB'])
            valueMap['SensorY'], sigmaMap['SensorY'] = calculateY(pointsSensorT, pointsSensorB)
        if 'SensorL' in keys:
            pointsSensorL = extractPoints(m['SensorL'])
            pointsSensorR = extractPoints(m['SensorR'])
            valueMap['SensorX'], sigmaMap['SensorX'] = calculateX(pointsSensorL, pointsSensorR)
        #
        self.sizeValueMap = valueMap
        self.sizeSigmaMap = sigmaMap
        print(valueMap)
        if self.moduleType != 'Rd53AModule':
            return 1
        # Line reconstruction
        pointsL = map(lambda x: x.position(), self.patternResultsMap['FlexL'])
        pointsB = map(lambda x: x.position(), self.patternResultsMap['FlexB'])
        pointsL = list(map(lambda x: CvPoint(*x), pointsL))
        pointsB = list(map(lambda x: CvPoint(*x), pointsB))
        print('Before fitLine')
        angle = 90.0
        if False and len(pointsL)>2 and len(pointsB)>2:
            lineL = pmm.fitLine(pointsL)
            lineB = pmm.fitLine(pointsB)
            print('LineL = ', lineL)
            print('LineB = ', lineB)
            dirL = CvVector(*(lineL.direction()))
            dirB = CvVector(*(lineB.direction()))
            print('dirL = ', dirL)
            if dirL.y<0.0: dirL *= -1.0
            if dirB.x<0.0: dirB *= -1.0
            angle = math.acos(dirL.dot(dirB))*180.0/math.pi
        print('Angle = %6.4f' % angle)
        #
        if self.moduleType == 'Rd53AModule':
            m = self.summary.sizeMap
            m['AsicToFlexL'] = (valueMap['FlexL'] - valueMap['AsicL'], 0.0)
            m['AsicToFlexR'] = (valueMap['AsicR'] - valueMap['FlexR'], 0.0)
            m['SensorToFlexT'] = (valueMap['SensorT'] - valueMap['FlexT'], 0.0)
            m['SensorToFlexB'] = (valueMap['FlexB'] - valueMap['SensorB'], 0.0)
            m['AsicX'] = (valueMap['AsicR'] - valueMap['AsicL'], 0.0)
            m['AsicY'] = (valueMap['AsicT'] - valueMap['AsicB'], 0.0)
            m['FlexX'] = (valueMap['FlexR'] - valueMap['FlexL'], 0.0)
            m['FlexY'] = (valueMap['FlexT'] - valueMap['FlexB'], 0.0)
            m['SensorX'] = (valueMap['SensorR'] - valueMap['SensorL'], 0.0)
            m['SensorY'] = (valueMap['SensorT'] - valueMap['SensorB'], 0.0)
            m['Angle'] = (angle, 0.0)
        #

    def postProcessFlatnessResults(self):
        resultsOn = self.scanResults.flatnessVacOnResults
        resultsOff = self.scanResults.flatnessVacOffResults
        config = self.flatnessScanConfig
        if resultsOn == None:
            logger.warning('Cannot process flatness (vac. ON) results, none available')
            return -1
        if resultsOff == None:
            logger.warning('Cannot process flatness (vac. OFF) results, none available')
            return -2
        #if config == None:
        #    logger.warning('Cannot process flatness results, no config')
        #    return -3
        #
        n = resultsOn.nPoints()
        points = []
        outlier_thr = 0.3 # [mm]
        print(dir())
        for i in range(n):
            pOn = resultsOn.pointResult(i)
            pOff = resultsOff.pointResult(i)
            #c = config.pointConfig(i)
            point = [ pOn.x, pOn.y, pOff.z - pOn.z ]
            points.append(point)
        plane, outliers = pmm.fitPlane(points, outlier_thr)
        pmm.summaryPointsOnPlane(points, plane, [], 'Planarity vac. diff', 'planarity_vacDiff')
        zmin = -0.01
        zmax = 0.02
        dz = list(map(lambda p: plane.distance(p), points) )
        zmean = sum(dz)/n
        vx, vy, vz = 0.0, 0.0, 1.0
        self.summary.flatnessMap['zMax'] = zmax
        self.summary.flatnessMap['zMin'] = zmin
        self.summary.flatnessMap['z(average)'] = zmean
        self.summary.flatnessMap['dz(max-min)'] = abs(zmax - zmin)
        self.summary.flatnessMap['planeAxisX'] = vx
        self.summary.flatnessMap['planeAxisY'] = vy
        self.summary.flatnessMap['planeAxisZ'] = vz
        self.summary.flatnessMap['angleX'] = math.atan2(vx, vz)
        self.summary.flatnessMap['angleY'] = math.atan2(vy, vz)
        return 0

    def summaryJson(self):
        rawData = [
            self.heightLogFile, 
            self.sizeLogFile, 
            self.flatnessVacOnLogFile, 
            self.flatnessVacOffLogFile, 
        ]
        rawData = ','.join(rawData)
        jsonData = {
            "moduleName": self.moduleName, 
        }
        um = 1.0E+3
        if len(self.summary.sizeMap)>0:
            jsonData.update({
                "DISTANCE_TOP": self.summary.sizeMap['SensorToFlexT'][0]*um, 
                "DISTANCE_BOTTOM": self.summary.sizeMap['SensorToFlexB'][0]*um, 
                "DISTANCE_LEFT": self.summary.sizeMap['AsicToFlexL'][0]*um, 
                "DISTANCE_RIGHT": self.summary.sizeMap['AsicToFlexR'][0]*um, 
                "ANGLE_BARE_VS_FLEX": self.summary.sizeMap['Angle'][0],
            })
        if len(self.summary.heightMap)>0:
            jsonData.update({
                "Z_AVERAGE_PICKUP_POINTS": [
                    self.summary.pickupMap['Pickup1'][0]*um, 
                    self.summary.pickupMap['Pickup2'][0]*um, 
                    self.summary.pickupMap['Pickup3'][0]*um, 
                    self.summary.pickupMap['Pickup4'][0]*um, 
                ],
                "Z_STDDEV_PICKUP_POINTS": [
                    self.summary.pickupMap['Pickup1'][1]*um, 
                    self.summary.pickupMap['Pickup2'][1]*um, 
                    self.summary.pickupMap['Pickup3'][1]*um, 
                    self.summary.pickupMap['Pickup4'][1]*um, 
                ],
                "THICKNESS_HV_CAP": self.summary.pickupMap['HVCapacitor'][0]*um, 
                "THICKNESS_DATA_CONN": self.summary.pickupMap['Connector'][0]*um,
                "THICKNESS_LEFT_EDGE": self.summary.pickupMap['FlexLSide'][0]*um, 
                "THICKNESS_RIGHT_EDGE": self.summary.pickupMap['FlexRSide'][0]*um, 
            })
            zvalues = jsonData["Z_AVERAGE_PICKUP_POINTS"]
            zsigmas = jsonData["Z_STDDEV_PICKUP_POINTS"]
            z_average = sum(zvalues)/len(zvalues)
            z_stddev = math.sqrt(sum(map(lambda x: x*x, zsigmas)))/len(zsigmas)
            jsonData.update({
                "Z_AVERAGE": z_average,
                "Z_STDDEV": z_stddev
                })
        if len(self.summary.flatnessMap)>0:
            jsonData.update({
                "BACKSIDE_COPLANARITY": self.summary.flatnessMap['dz(max-min)'], 
                "ANGLE": [
                    self.summary.flatnessMap['angleX'], 
                    self.summary.flatnessMap['angleY']
                ]
            })
        jsonData.update({
            "Raw data (file)": rawData
        })
        return jsonData

    def save(self, fname=''):
        # Keep away temporally data from persistifying
        scanResults = self.scanResults
        self.scanResults = None
        configs = [
            self.pickupScanConfig, 
            self.heightScanConfig, 
            self.sizeScanConfig, 
            self.flatnessScanConfig
            ]
        self.pickupScanConfig = None
        self.heightScanConfig = None
        self.sizeScanConfig = None
        self.flatnessScanConfig = None
        for k, v in self.patternResultsMap.items():
            for i in range(len(v)):
                v[i].image1b = None
        #
        if fname == '':
            fname = os.path.join(self.appDataPath, '%s.pickle' %
                                 self.fullName())
        f = open(fname, 'wb')
        pickle.dump(self, f)
        f.close()
        # Restore temporally data
        self.scanResults = scanResults
        self.pickupScanConfig = configs[0]
        self.heightScanConfig = configs[1]
        self.sizeScanConfig = configs[2]
        self.flatnessScanConfig = configs[3]

    def moduleDir(self, workDir):
        fn = '%s/modules/%s_%s' % (workDir, self.moduleName, self.testStepShort())
        return fn
        
    def fullName(self):
        fn = '%s_%s_%s' % (self.moduleName,
                           self.testStepShort(),
                           self.moduleType)
        return fn
    
def loadAppData(fname):
    data = None
    if os.path.exists(fname):
        f = open(fname, 'rb')
        data = pickle.load(f)
        f.close()
    else:
        logger.warning('Cannot find file %s' % fname)
    return data
