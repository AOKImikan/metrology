#------------------------------------------------------------------------
# pmm: analysis.py
#-----------------
# ScanProcessor and analysis components
#------------------------------------------------------------------------
import os
import logging
import functools
import shutil
import math
import tkinter as tk
import numpy as np

#from PyQt5.QtCore import Slot
from PyQt5.QtGui import QPixmap, QImage

from .data2 import ImageNP, ScanData
from .data3 import *
from .reader import *
from .tools import fitLine, fitPlane
from .model import *
from .prec import *
from .workflow import *
from .fittools import CircleFit, SlotFit, ShapeFit, Circle1, LongCircle
from .fittools2 import OuterlineFit, CellFit
from .imageTool import ImageTool

logger = logging.getLogger(__name__)

def arrayToPixmap(img):
    nrows, ncols, nch = img.shape
    nbytes = nch*ncols
    img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    qimage = QImage(img2.data, ncols, nrows, nbytes, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qimage)
    return pixmap

#--------------------------------------------------
# Analysis base class
#--------------------------------------------------
class Analysis:
    kIdle = 0
    kInputsReady = 2
    kPreRunFinished = 3
    kMainRunFinished = 4
    kPostRunFinished = 5
    
    def __init__(self, name):
        self.name = name
        self.model = None
        self.viewModel = None
        self.scanProcessor = None
        self.inData = {}
        self.outData = {}
        self.outKeys = [] # Ordered keys
        self.defineOutputKeys()
        #
        self.componentType = ''
        self.workDir = '.'
        self.scanData = None
        self.state = Analysis.kIdle

    def persKeys(self):
        return ['name', 'inData', 'outData', 'outKeys',
                'componentType', 'workDir', 'state' ]
    
    def setModel(self, model):
        #logger.info(f'Setting model {model} to analyis, {self.name}')
        self.model = model

    def setViewModel(self, viewModel):
        self.viewModel = viewModel
        
    def defineOutputKeys(self):
        pass

    def findPointsWithTag(self, tag, excludeBadPoint=False):
        v = []
        mm = 1.0E-3
        for p in self.scanData.points:
            tags = p.value('tags')
            if excludeBadPoint and p.get('error'):
                continue
            if tag in tags:
                v.append(p)
        return v

    def selectPoints(self, tag):
        return self.findPointsWithTag(tag)

    def setState(self, s):
        if s == Analysis.kIdle:
            self.state = Analysis.kIdle
        else:
            self.state |= (1<<s)

    def setScanData(self, scanData):
        self.scanData = scanData
        if self.scanData != None:
            self.setState(Analysis.kInputsReady)

    def setInputData(self, inputData):
        self.inData = inputData
        
    def addInputData(self, inputData):
        for k, v in inputData.items():
            self.inData[k] = v
        
    def preRun(self):
        status = True
        self.setState(Analysis.kPreRunFinished)
        return status
        
    def mainRun(self):
        self.setState(Analysis.kMainRunFinished)
        return True
    
    def postRun(self):
        self.setState(Analysis.kPostRunFinished)
        return True
        
    def run(self):
        logger.debug('  %s preRun()...' % self.name)
        status = self.preRun()
        if status == False:
            return status
        # Main analysis
        logger.debug('  %s mainRun()...' % self.name)
        status = self.mainRun()
        if status == False:
            return status
        #
        logger.debug('  %s postRun()...' % self.name)
        status = self.postRun()
        return status

    def outputKeys(self):
        return self.outKeys
        
    def outputData(self, key):
        x = None
        if key in self.outData.keys():
            x = self.outData[key]
        return x

    def propagateChanges(self):
        if self.scanProcessor:
            logger.info('Propagate changes to other analyses')
            self.scanProcessor.run()
        
    def clear(self):
        self.outData.clear()
        self.state = Analysis.kIdle
        pass
    
#--------------------------------------------------
# Various analysis components
#--------------------------------------------------
class ImagePatternAnalysis(Analysis):
    def __init__(self, name):
        super().__init__(name)
        self.outImages = {}
        self.tagPatternsMap = {}
        self.tagImageMap = {}
        self.tagImagePatterns = {}
        self.patternRecDone = False
        #
        self.precTagLineH = functools.partial(self.precTagPattern,
                                              precfunc=self.findLineH,
                                              combineImages=False)
        self.precTagLineV = functools.partial(self.precTagPattern,
                                              precfunc=self.findLineV,
                                              combineImages=False)
        self.precTagCircle = functools.partial(self.precTagPattern,
                                               precfunc=self.findCircle,
                                               combineImages=False)
        self.precTagOuterline = functools.partial(self.precTagPattern,
                                              precfunc=self.findOuterline,
                                              combineImages=False)
        self.precTagBigCircle = functools.partial(self.precTagPattern,
                                                  precfunc=self.findBigCircle,
                                                  combineImages=True)
        self.precTagBigSlot = functools.partial(self.precTagPattern,
                                                  precfunc=self.findBigSlot,
                                                  combineImages=True)

    def persKeys(self):
        keys = super().persKeys()
        keys += [ 'outImages', 'tagImageMap' ]
        return keys

    def mainRun(self):
        logger.debug('ImagePatternAnalysis.mainRun()')
        status = True
        #
        # Big circle
        # Big slot
        #
        return status
    
    ###
    # - findXXX(self, tag, imageNP) -> (shape object, outImage)
    # - findXXX(self, tag, imageNPs) -> (shape object, outImage)
    ###

    def calculateLine(self, tag, xy):
        logger.info(f'Calucalate line for {tag}')
        keys = filter(lambda x: x.startswith(tag), self.outData.keys())
        keys = filter(lambda x: x.endswith(xy), keys)
        values = []
        for key in keys:
            if self.outData[key] != None:
                #logger.info(f'key = {key}')
                values.append(self.outData[key].get('value'))
        self.outData[tag] = AveragedValue(tag, values)
        #
        points = self.pointsWithTagMatch(f'{tag}_(.+)_point')
        #logger.info(f'  Number of points along {tag}: {len(points)}')
        if len(points)>=2:
            line = fitLine(points)
        else:
            line = None
        self.outData[f'{tag}_line'] = line

    def addPatternRecImage(self, tag, name, rec):
        patterns = {}
        if tag in self.tagImagePatterns.keys():
            patterns = self.tagImagePatterns[tag]
        else:
            self.tagImagePatterns[tag] = patterns
        if not name in patterns.keys():
            logger.info(f'Add patternRecImage for {name}')
            patterns[name] = rec
        else:
            logger.warning(f'Pattern rec image {tag}/{name} already exists')
            
    def findLineH(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        rec = PatternRecImage(self.model.componentType, tag, imageNP.name, 
                              imageNP.xyOffset, 
                              imageNP.filePath, imageNP.zoom,
                              outputDir)
        pos = rec.run()
        imageName = f'{imageNP.name}'#_p1'
        #imagePath = os.path.basename(imageNP.filePath)
        #imagePath = os.path.join(outputDir, imagePath)
        #imagePath = imagePath.replace('.jpg', f'_{imageName}.jpg')
        imageNP = ImageNP(imageName, '')
        xy = rec.position()
        point = None
        self.addPatternRecImage(tag, imageNP.name, rec)
        if rec.patternValid:
            point = CvPoint(*xy)
        return point, imageNP

    def findLineV(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        rec = PatternRecImage(self.model.componentType, tag, imageNP.name, 
                              imageNP.xyOffset, 
                              imageNP.filePath, imageNP.zoom,
                              outputDir)
        pos = rec.run()
        imageName = f'{imageNP.name}'#_p1'
        imageNP = ImageNP(imageName, '')
        xy = rec.position()
        point = None
        self.addPatternRecImage(tag, imageNP.name, rec)
        if rec.patternValid:
            point = CvPoint(*xy)
        return point, imageNP

    def findCircle(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        rec = PatternRecImage(self.model.componentType, tag, imageNP.name, 
                              imageNP.xyOffset, 
                              imageNP.filePath, imageNP.zoom,
                              outputDir)
        #pos = rec.run()
        rec.openImage()
        rec.createImageP1()
        #
        xy = rec.position()
        point = None
        self.addPatternRecImage(tag, imageNP.name, rec)
        if rec.patternValid:
            point = CvPoint(*xy)
        return point, ImageNP(imageNP.name, '')
    
    def findOuterline(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        r = 0.0001
        line = CvLine()
        fitter = OuterlineFit()
        fitter.outImageName = f'{figname}.jpg'
        if tag[-1] == 'L':
            image, point, localpoint = fitter.run(imageNP, 'L', r)
            line.setFromX(localpoint[0].x())
            #print(f'localpoint : {localpoint}')
        elif tag[-1] == 'R':
            image, point, localpoint = fitter.run(imageNP, 'R', r)
            line.setFromX(localpoint[0].x())
        elif tag[-1] == 'T':
            image, point, localpoint = fitter.run(imageNP, 'T', r)
            line.setFromY(localpoint[0].y())
        elif tag[-1] == 'B':
            image, point, localpoint = fitter.run(imageNP, 'B', r)
            line.setFromY(localpoint[0].y())
        
        imageName = f'{imageNP.name}_p1'
        imagePath = os.path.basename(imageNP.filePath)
        imagePath = os.path.join(outputDir, imagePath)
        imagePath = imagePath.replace('.jpg', f'_{imageName}.jpg')
        return line, ImageNP(imageName, '')
    
    def findBigCircle(self, tag, imageNPs):
        outputDir = self.model.outputDir()
        fitter = ShapeFit()
        shape = Circle1(parameters=[0.0, 0.0, 1.0E-3])
        fitter.setInitialShape(shape)
        bigImage, circle, pointsGlobal = fitter.run(imageNPs)
        imageNP = ImageNP(tag, '')
        imageNP.image = bigImage
        self.addPatternRecImage(tag, imageNP.name, fitter)
        return (circle, imageNP)
    
    def findBigSlot(self, tag, imageNPs):
        outputDir = self.model.outputDir()
        fitter = ShapeFit()
        shape = LongCircle(parameters=[0.0, 0.0, 1.0E-3, 1.0, -math.pi/4])
        fitter.setInitialShape(shape)
        bigImage, circle, pointsGlobal = fitter.run(imageNPs)
        imageNP = ImageNP(tag, '')
        imageNP.image = bigImage
        self.addPatternRecImage(tag, imageNP.name, fitter)
        return (circle, imageNP)

    def precTagPattern(self, tag, precfunc, combineImages=False, x=None, y=None):
        imageNPs = self.prepareImageNPs(tag)
        self.tagImageMap[tag] = {}

        logger.debug(f'precTagPattern N images: {len(imageNPs)}')
        for x in imageNPs:
            logger.debug(f'Image {x.name}, {x.filePath} ({x.xyOffset})')

        if combineImages:
            logger.debug(f'Pattern rec {tag}')
            shape, outImage = precfunc(tag, imageNPs)
            #logger.debug(f'{outImage.filePath} exists? {os.path.exists(outImage.filePath)}')
            imageQ = arrayToPixmap(outImage.image)
            outImage.imageQ = imageQ

            name2 = f'{tag}/{outImage.name}'
            self.tagImageMap[tag][outImage.name] = outImage
            if shape != None:
                key = f'{tag}_x'
                self.outData[key] = MeasuredValue(key, shape.cx, 0.0)
                key = f'{tag}_y'
                self.outData[key] = MeasuredValue(key, shape.cy, 0.0)
                key = f'{tag}_r'
                self.outData[key] = MeasuredValue(key, shape.r, 0.0)
                key = f'{tag}_shape'
                self.outData[key] = shape
                if type(shape) == LongCircle:
                    key = f'{tag}_l'
                    self.outData[key] = MeasuredValue(key, shape.l, 0.0)
                    key = f'{tag}_alpha'
                    self.outData[key] = MeasuredValue(key, shape.alpha, 0.0)
            else:
                logger.warning(f'Could not find pattern in {outImage.name}')
                self.outData[f'{tag}_x'] = None
                self.outData[f'{tag}_circle'] = None
            if self.viewModel:
                logger.debug(f'Emit signal photoReady for {name2}')
                self.viewModel.sigPhotoReady.emit(name2)
        else:
            for ipoint, imageNP in enumerate(imageNPs):
                logger.debug(f'Pattern rec {imageNP.name}')
                pattern, outImage = precfunc(tag, imageNP, figname=f'{tag}_{ipoint}')
                outImage.xyOffset = imageNP.xyOffset
                if tag in self.tagImagePatterns.keys() and\
                   outImage.name in self.tagImagePatterns[tag].keys():
                    rec = self.tagImagePatterns[tag][outImage.name]
                    if rec:
                        imageQ = ImageTool.arrayToQPixmap(rec.image1)
                        outImage.imageQ = imageQ
                    else:
                        logger.warning('  rec is empty, cannot display photo')

                name2 = f'{tag}/{outImage.name}'
                logger.debug(f'  name2 = {name2}')
                self.tagImageMap[tag][outImage.name] = outImage
                if pattern != None:
                    key = f'{imageNP.name}_x'
                    self.outData[key] = MeasuredValue(key, pattern.x(), 0.0)
                    key = f'{imageNP.name}_y'
                    self.outData[key] = MeasuredValue(key, pattern.y(), 0.0)
                    key = f'{imageNP.name}_point'
                    self.outData[key] = Point([pattern.x(), pattern.y()])
                else:
                    logger.warning(f'Could not find pattern in {outImage.name}')
                    key = f'{imageNP.name}_x'
                    self.outData[key] = None
                    key = f'{imageNP.name}_y'
                    self.outData[key] = None
                    key = f'{imageNP.name}_point'
                    self.outData[key] = None
                logger.debug('  Add photo to the gallery')
                if self.viewModel:
                    logger.debug(f'Emit signal photoReady for {name2}')
                    self.viewModel.sigPhotoReady.emit(name2)
        pass

    def prepareImageNPs(self, tag):
        points = self.findPointsWithTag(tag)
        imageNPs = []
        for i, p in enumerate(points):
            #if p.get('error'): continue
            name = '%s_%d' % (tag, i)
            image = ImageNP(name, p.get('imagePath'))
            image.xyOffset = CvPoint( p.get('x'), p.get('y'))
            #x.xyOffset = [ p.get('x'), p.get('y')]
            imageNPs.append(image)
        return imageNPs
    
    def display(self, tag):
        imageNPs = self.prepareImageNPs(tag)
        m = {}
        for x in imageNPs:
            name2 = f'{tag}/{x.name}'
            m[x.name] = x
            if self.viewModel:
                logger.debug(f'Emit signal photoReady for {name2}')
                self.viewModel.sigPhotoReady.emit(name2)
        self.tagImageMap[tag] = m
        pass
    
    def preRun(self):
        return super().preRun()

    def postRun(self):
        return super().postRun()

    def selectImagePaths(self, tag):
        points = self.selectPoints(tag)
        fnames = list(map(lambda x: x.imagePath, points) )
        return fnames
    
    def pointsWithTagMatch(self, tagString):
        re1 = re.compile(tagString)
        points = []
        for k, v in self.outData.items():
            logger.debug(f'Check {k} against {tagString}')
            mg = re1.match(k)
            if mg and v != None:
                points.append(v)
        return points

    def clear(self):
        super().clear()
        self.outImages = {}
        self.tagPatternsMap = {}
        self.tagImageMap = {}
        self.tagImagePatterns = {}
        self.patternRecDone = False
    pass

class ShapeAnalysis(Analysis):
    def __init__(self, name):
        super().__init__(name)
        self.lines = {}
        self.vertices = {}
        self.squares = {}
        self.circles = {}
        
    def persKeys(self):
        keys = super().persKeys()
        keys += [ 'lines', 'vertices', 'squares', 'circles' ]
        return keys

    def recLine(self, points):
        line = None
        n = len(points)
        if n >= 2:
            line = fitLine(points)
        else:
            logger.warning('Only %d points available while trying to fit a line' % n)
        return line

    def recCorners(self, lineT, lineB, lineL, lineR):
        pTL, pTR, pBR, pBL = [CvPoint()]*4
        return (pTL, pTR, pBR, pBL)

    def recVertex(self, line1, line2):
        vertex = None
        if line1 and line2:
            vertex = line1.intersection(line2)
        return vertex

    def recCircle(self, points):
        circle = None
        return circle

    def recRectangle(self, tag, lines):
        rect = None
        return rect

    def pointsWithTagMatch(self, tagString):
        re1 = re.compile(tagString)
        points = []
        for k, v in self.inData.items():
            logger.debug(f'Check {k} against {tagString}')
            mg = re1.match(k)
            if mg and v != None:
                points.append(v)
        return points
    
    def preparePoints(self, tag):
        v = []
        if 'tagPatternsMap' in self.inData.keys():
            m = self.inData['tagPatternsMap']
            if tag in m.keys():
                v = extractPoints(m[tag])
        return v
    def distanceL(self, line1, line2):
        L = 0.0
        return L

    pass

class SizeAnalysis(ShapeAnalysis):
    def __init__(self, name):
        super().__init__(name)
        
    def mainRun(self):
        return super().mainRun()
    
    def preRun(self):
        return super().preRun()

    def postRun(self):
        return super().postRun()
    
    def lineDiff(self, tag, tag1, tag2, line_vh):
        """tag = tag1 - tag2"""
        key, line1 = f'{tag1}_line', None
        if line1 == None:
            if key in self.outData.keys():
                line1 = self.outData[key]
            elif key in self.inData.keys():
                line1 = self.inData[key]
        key, line2 = f'{tag2}_line', None
        if line2 == None:
            if key in self.outData.keys():
                line2 = self.outData[key]
            elif key in self.inData.keys():
                line2 = self.inData[key]
        #
        if not (line1 and line2):
            self.outData[tag] = None
            logger.warning(f'Cannot calculate the distance between lines')
            logger.warning(f'  Line[{tag1}]={line1}, Line[{tag2}]={line2}')
            return
        x, y = 0.0, 0.0
        if line_vh == 'v':
            x, y = line1.xAtY(0.0), 0.0
            x1, y1 = line1.xAtY(20.0), 20.0
            x2, y2 = line1.xAtY(-20.0), -20.0
            dd = abs(x1 - x2)/2.0
        if line_vh == 'h':
            x, y = 0.0, line1.yAtX(0.0)
            x1, y1 = 20.0, line1.xAtY(20.0)
            x2, y2 = -20.0, line1.xAtY(-20.0)
            dd = abs(y1 - y2)/2.0
        p = Point([x, y])
        d = line2.distance(p)
        logger.debug(f' L-P distance ({line2}-{p.position}): {d}')
        dd = 0.0
        self.outData[tag] = MeasuredValue(tag, d, dd)
    def calculateFmarkDistance(self, tag, tag1, tag2):
        tagx, tagy = f'{tag}_x', f'{tag}_y'
        tag1x, tag1y = f'{tag1}_0_x', f'{tag1}_0_y'
        tag2x, tag2y = f'{tag2}_0_x', f'{tag2}_0_y'
        dx, dy = 0.0, 0.0
        keys = self.inData.keys()
        if tag1x in keys and tag1y in keys and\
           self.inData[tag1x] and self.inData[tag2x]:
            dx = self.inData[tag1x].get('value') - self.inData[tag2x].get('value')
        if tag2x in keys and tag2y in keys and\
           self.inData[tag1y] and self.inData[tag2y]:
            dy = self.inData[tag1y].get('value') - self.inData[tag2y].get('value')
        self.outData[tagx] = MeasuredValue(tagx, dx, 0.0)
        self.outData[tagy] = MeasuredValue(tagy, dy, 0.0)
    pass

class HeightAnalysis(Analysis):
    def __init__(self, name):
        super().__init__(name)
    def fitPlane(self, points):
        points2 = []
        if len(points)>=3:
            logger.debug(f'Fit plane to {len(points)} points')
            for p in points:
                if p.value('error'): continue
                points2.append([p.value('x'), p.value('y'), p.value('z')])
        plane, outliers = fitPlane(points2)
        return plane

    def correctHeight(self, points, refPlane):
        points2 = []
        for p in points:
            z = refPlane.distance(p)
            points2.append(Point([p[0], p[1], z]) )
        return points2

    def calcAverageHeight(self, tag, points, dzcut=-1.0):
        zvalues = list(map(lambda x: x[2], points))
        zvalues.sort()
        if dzcut > 0.0:
            nmax = 0
            imax = -1
            np = len(points)
            zvalues2 = []
            for i0 in range(np):
                v2 = []
                z2 = points[i0][2]
                for i in range(np):
                    z = points[i][2]
                    if z-z2 > 0 and abs(z-z2) < dzcut:
                        v2.append(points[i][2])
                n1 = len(v2)
                if n1 > nmax:
                    nmax = n1
                    imax = i0
                    zvalues2 = v2
            logger.warning(f'  Use {len(zvalues2)} points to calculate the average height of {tag} (<{dzcut})')
            zvalues = zvalues2
        x = AveragedValue(tag, values=zvalues)
        return x

    def calculateJigPlane(self, jigPoints):
        dzcut = 0.025
        ntry = 3
        hvalues = []
        np0 = len(jigPoints)
        while ntry>0:
            height = self.calcAverageHeight('Jig', jigPoints, dzcut)
            n = height.get('n')
            if n == np0:
                hvalues = height.get('values')
                break
            elif height.get('n')>=3:
                logger.warning(f'  Use {n} points to obtain the jig plane (out of {np0}) ntry={ntry}')
                hvalues = height.get('values')
                break
            else:
                logger.warning(f'  Cannot derive the jig plane with {n} points. Increase the dzcut to {dzcut}')
                dzcut *= 2
            ntry -= 1
        points = []
        if len(hvalues)>=3:
            zmin = min(hvalues)
            for p in jigPoints:
                if abs(p[2]-zmin)<dzcut:
                    points.append(p)
        else:
            logger.warning(f'Heights of jig points deviates by more than 100 um, using all points but maybe wrong')
            points = jigPoints
        logger.info(f'Calculate jig plane with {len(points)} points')
        jigPlane = self.fitPlane(points)
        return jigPlane
    
    def mainRun(self):
        points = self.scanData.points
        n = len(points)
        if n == 0:
            logger.warning('%s: the number of points %d is too small. Not processing data' % (self.name, n) )
            return False
        values = {}

        # 1. Jig height
        jigPlane = None
        logger.debug('Find points on the jig')
        jigPoints = self.findPointsWithTag('Jig')
        jigPlane = self.fitPlane(jigPoints)
        self.jigPlane = jigPlane
        if jigPlane:
            logger.debug('jigPlane: c = %5.3f %s' % (jigPlane.c, str(jigPlane)))
            values['Jig'] = MeasuredValue('Jig', jigPlane.c, 0.0)
        
        # 2. Heights of other points from the jig
        tags = [ 'Asic', 'Sensor', 'Flex' ]
        for tag in tags:
            h = self.averageHeightFromJig(tag, jigPlane)
            if h:
                values[tag] = h
        #
        self.outData = values
        return True

    def averageHeightFromJig(self, tag, jigPlane):
        spoints = self.findPointsWithTag(tag)
        zvalues = []
        if len(spoints)>=1:
            for p in spoints:
                if p.value('error'): continue
                p1 = [p.value('x'), p.value('y'), p.value('z')]
                z = jigPlane.distance(p1)
                zvalues.append(z)
        x = AveragedValue(tag, zvalues)
        return x
    pass

class FlatnessVacOnOffAnalysis(Analysis):
    def __init__(self, name):
        self.scanData1 = None
        self.scanData2 = None
    def setScanData1(self, scanData):
        self.scanData1 = scanData
    def setScanData2(self, scanData):
        self.scanData2 = scanData

    def preRun(self):
        points1 = self.scanData1.points
        points2 = self.scanData2.points
        n1, n2 = len(points1), len(points2)
        if n1 != n2:
            logger.warning('FlatnessVacOnOff: different number of points')
            return False
        for i in range(n1):
            pass
        
        return super().preRun()
    
    def run(self):
        pass
    pass

class FlatnessBackSideAnalysis(Analysis):
    def __init__(self, name):
        pass
    def run(self):
        pass
    pass

#--------------------------------------------------
# Size analysis for various types of components
#--------------------------------------------------
# Flex
class FlexPatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
        self.patternRecDone = False
        
    def defineOutputKeys(self):
        #self.outKeys = ['FiducialTL', 'FiducialTR', 'FiducialBL', 'FiducialBR']
        self.outKeys = [
            'FlexL', 'FlexR', 'FlexB', 'FlexT',
            'HoleTL_x', 'HoleTL_y', 'HoleTL_r', 
            'SlotBR_x', 'SlotBR_y', 'SlotBR_r', 'SlotBR_l', 'SlotBR_alpha', 
            ]

    def mainRun(self):
        super().mainRun()
        flexX = 40.0
        flexY = 40.0
        #
        if self.patternRecDone:
            return
        #self.precTagOuterline('FlexL', x=-flexX/2.0)
        #self.precTagOuterline('FlexR', x=flexX/2.0)
        #self.precTagOuterline('FlexT', y=flexY/2.0)        
        #self.precTagOuterline('FlexB', y=-flexY/2.0)
        self.precTagLineV('FlexL', x=-flexX/2.0)
        self.precTagLineV('FlexR', x=flexX/2.0)
        self.precTagLineH('FlexT', y=flexY/2.0)
        self.precTagLineH('FlexB', y=-flexY/2.0)
        self.precTagBigCircle('HoleTL', x=-27.0, y=27.0)
        self.precTagBigSlot('SlotBR', x=27.0, y=-27.0)
        self.patternRecDone = True
        
    def postRun(self):
        logger.info(f'{self.outData.keys()}')
        self.calculateLine('FlexL', 'x')
        self.calculateLine('FlexR', 'x')
        self.calculateLine('FlexT', 'y')
        self.calculateLine('FlexB', 'y')
    pass

class FlexSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)

    def defineOutputKeys(self):
        self.outKeys = [
            'FlexX', 'FlexY', 'HoleTL_diameter', 'SlotBR_width'
        ]
        pass

    def mainRun(self):
        points = self.pointsWithTagMatch('FlexL_(.+)_point')
        self.outData['FlexL_line'] = self.recLine(points)
        points = self.pointsWithTagMatch('FlexR_(.+)_point')
        self.outData['FlexR_line'] = self.recLine(points)
        points = self.pointsWithTagMatch('FlexT_(.+)_point')
        self.outData['FlexT_line'] = self.recLine(points)
        points = self.pointsWithTagMatch('FlexB_(.+)_point')
        self.outData['FlexB_line'] = self.recLine(points)
        #
        logger.info(f'{self.outData["FlexL_line"]}')
        logger.info(f'{self.outData["FlexR_line"]}')
        logger.info(f'{self.outData["FlexT_line"]}')
        logger.info(f'{self.outData["FlexB_line"]}')
        self.lineDiff('FlexX', 'FlexR', 'FlexL', 'v')
        self.lineDiff('FlexY', 'FlexT', 'FlexB', 'h')
        x1 = self.inData['HoleTL_r'].get('value')*2
        e1 = self.inData['HoleTL_r'].get('error')*2
        x2 = self.inData['SlotBR_r'].get('value')*2
        e2 = self.inData['SlotBR_r'].get('error')*2
        self.outData['HoleTL_diameter'] = MeasuredValue('HoleTL_diameter', x1, e1)
        self.outData['SlotBR_width'] = MeasuredValue('SlotBR_width', x2, e2)
        pass

    pass

# Bare module
class BareModulePatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
        self.patternRecDone = False
        
    def defineOutputKeys(self):
        self.outKeys = [
            'FlexT', 'FlexB', 'FlexL', 'FlexR', 
            'SensorT', 'SensorB', 'SensorL', 'SensorR', 
            ]
        pass

    def mainRun(self):
        super().mainRun()
        if self.patternRecDone:
            return
        asicW, asicH = 40.0, 40.0
        sensorW, sensorH = 40.0, 40.0
        #
        #logger.info('BareModulePatternAnalysis')
        self.precTagLineH('AsicT', y=asicH/2.0)
        self.precTagLineH('AsicB', y=-asicH/2.0)
        self.precTagLineV('AsicL', y=-asicW/2.0)
        self.precTagLineV('AsicR', y=asicW/2.0)
        self.precTagLineH('SensorT', y=sensorH/2.0)
        self.precTagLineH('SensorB', y=-sensorH/2.0)
        self.precTagLineV('SensorL', y=-sensorW/2.0)
        self.precTagLineV('SensorR', y=sensorW/2.0)
        self.patternRecDone = True

    def postRun(self):
        self.calculateLine('AsicL', 'x')
        self.calculateLine('AsicR', 'x')
        self.calculateLine('AsicT', 'y')
        self.calculateLine('AsicB', 'y')
        self.calculateLine('SensorL', 'x')
        self.calculateLine('SensorR', 'x')
        self.calculateLine('SensorT', 'y')
        self.calculateLine('SensorB', 'y')

    pass

class BareModuleBackPatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

class BareModuleSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)

    def defineOutputKeys(self):
        self.outKeys = [
            'AsicX', 'AsicY', 'SensorX', 'SensorY', 
            ]
    def mainRun(self):
        points = self.pointsWithTagMatch('AsicL_(.+)_point')
        self.outData['AsicL_line'] = self.recLine(points)
        points = self.pointsWithTagMatch('AsicR_(.+)_point')
        self.outData['AsicR_line'] = self.recLine(points)
        points = self.pointsWithTagMatch('SensorT_(.+)_point')
        self.outData['SensorT_line'] = self.recLine(points)
        points = self.pointsWithTagMatch('SensorB_(.+)_point')
        self.outData['SensorB_line'] = self.recLine(points)
        #
        # Bare module is rotated by 90 degrees
        self.lineDiff('AsicX', 'AsicT', 'AsicB', 'h')
        self.lineDiff('AsicY', 'AsicL', 'AsicR', 'v')
        self.lineDiff('SensorX', 'SensorT', 'SensorB', 'h')
        self.lineDiff('SensorY', 'SensorR', 'SensorL', 'v')
    pass

class BareModuleBackSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

# Assembled module
class ModulePatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
        self.patternRecDone = False

    def defineOutputKeys(self):
        self.outKeys = [
            # Auxiliary data
            'AsicL', 'AsicR', 
            'SensorT', 'SensorB', 
            'FlexL', 'FlexR', 'FlexT', 'FlexB',
            'FmarkTL_0_x', 'FmarkTL_0_y',
            'FmarkBL_0_x','FmarkBL_0_y',
            'FmarkBR_0_x', 'FmarkBR_0_y',
            'FmarkTR_0_x','FmarkTR_0_y',
            'AsicFmarkTL_0_x', 'AsicFmarkTL_0_y',
            'AsicFmarkBL_0_x', 'AsicFmarkBL_0_y',
            'AsicFmarkBR_0_x', 'AsicFmarkBR_0_y',
            'AsicFmarkTR_0_x', 'AsicFmarkTR_0_y', 
            ]
        
    def mainRun(self):
        super().mainRun()
        #logger.info('mainRun in Module pattern analysis')
        asicW, asicH = 20.0, 20.0
        sensorW, sensorH = 20.0, 20.0
        flexW, flexH = 20.0, 20.0
        #
        logger.info(f'ModulePatternAnalysis prec done={self.patternRecDone}')
        if self.patternRecDone:
            logger.info(f'{self.name} skip pattern recognition')
            return
        else:
            logger.info(f'Run pattern recognition for {self.name}')
        self.precTagLineV('AsicL', y=-asicW/2.0)
        self.precTagLineV('AsicR', y=asicW/2.0)
        self.precTagLineH('SensorT', y=sensorH/2.0)
        self.precTagLineH('SensorB', y=-sensorH/2.0)
        self.precTagLineH('FlexT', y=flexH/2.0)
        self.precTagLineH('FlexB', y=-flexH/2.0)
        self.precTagLineV('FlexL', y=-flexW/2.0)
        self.precTagLineV('FlexR', y=flexW/2.0)
        self.precTagCircle('FmarkTL', x=sensorW/2.0, y=sensorH/2.0)
        self.precTagCircle('FmarkBL', x=sensorW/2.0, y=-sensorH/2.0)
        self.precTagCircle('FmarkBR', x=-sensorW/2.0, y=-sensorH/2.0)
        self.precTagCircle('FmarkTR', x=-sensorW/2.0, y=sensorH/2.0)
        self.precTagCircle('AsicFmarkTL', x=asicW/2.0, y=asicH/2.0)
        self.precTagCircle('AsicFmarkBL', x=asicW/2.0, y=-asicH/2.0)
        self.precTagCircle('AsicFmarkBR', x=-asicW/2.0, y=-asicH/2.0)
        self.precTagCircle('AsicFmarkTR', x=-asicW/2.0, y=asicH/2.0)
        self.display('Jig')
        self.display('Pickup1')
        self.display('Pickup2')
        self.display('Pickup3')
        self.display('Pickup4')
        self.patternRecDone = True

    def postRun(self):
        self.calculateLine('AsicL', 'x')
        self.calculateLine('AsicR', 'x')
        #self.calculateLine('AsicT', 'y')
        #self.calculateLine('AsicB', 'y')
        #self.calculateLine('SensorL', 'x')
        #self.calculateLine('SensorR', 'x')
        self.calculateLine('SensorT', 'y')
        self.calculateLine('SensorB', 'y')
        self.calculateLine('FlexL', 'x')
        self.calculateLine('FlexR', 'x')
        self.calculateLine('FlexT', 'y')
        self.calculateLine('FlexB', 'y')
    pass

class ModuleSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)

    def defineOutputKeys(self):
        self.outKeys = [
            'AsicX', 'SensorY', 'FlexX', 'FlexY', 
            #'AsicToFlexL', 'AsicToFlexR', 'SensorToFlexT', 'SensorToFlexB',
            'Angle', 
            'FmarkDistanceTR_x', 'FmarkDistanceTR_y', 
            'FmarkDistanceBL_x', 'FmarkDistanceBL_y', 
            ]
        
    def mainRun(self):
        super().mainRun()
        self.lineDiff('AsicX', 'AsicR', 'AsicL', 'v')
        self.lineDiff('SensorY', 'SensorT', 'SensorB', 'h')
        self.lineDiff('FlexX', 'FlexR', 'FlexL', 'v')
        self.lineDiff('FlexY', 'FlexT', 'FlexB', 'h')
        self.lineDiff('AsicToFlexL', 'FlexL', 'AsicL', 'v')
        self.lineDiff('AsicToFlexR', 'AsicR', 'FlexR', 'v')
        self.lineDiff('SensorToFlexT', 'SensorT', 'FlexT', 'h')
        self.lineDiff('SensorToFlexB', 'FlexB', 'SensorB', 'h')
        self.calculateFmarkDistance('FmarkDistanceTR', 'AsicFmarkTR', 'FmarkTR')
        self.calculateFmarkDistance('FmarkDistanceBL', 'FmarkBL', 'AsicFmarkBL')
        
        #logger.info(f'{self.outData}')
        #

    def postRun(self):
        dir1, dir2 = [0.0, 1.0], [0.0, 1.0]
        if 'FlexL_line' in self.outData.keys():
            line1 = self.outData['FlexL_line']
            dir1 = line1.direction()
        if 'AsicL_line' in self.outData.keys():
            line2 = self.outData['AsicL_line']
            dir2 = line2.direction()
        a, b = dir1[0], dir1[1]
        p, q = dir2[0], dir2[1]
        c = a*p + b*q
        s = -b*p + a*q
        Angle = math.acos(c)*180.0/math.pi
        if s < 0.0: Angle *= -1.0
        e = 0.0
        self.outData['Angle'] = MeasuredValue('Angle', Angle, e)
        pass

    pass

class ModuleRoofPatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

class ModuleBackPatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

class ModuleRoofSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

class ModuleBackSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

#--------------------------------------------------
# Height analysis for various types of components
#--------------------------------------------------
# Flex
class FlexHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    def defineOutputKeys(self):
        self.outKeys = [
            'JigZ', 'Pickup1', 'Pickup2','Pickup3', 'Pickup4', 'PickupZ',
            'HVCapacitorZ', 'ConnectorZ'
            ]
        
    def mainRun(self):
        jigPoints = self.findPointsWithTag('Jig')
        jigPlane = self.calculateJigPlane(jigPoints)
        logger.debug(f'Jig plane {jigPlane}')
        #
        pickupPoints = []
        pickupPoints1 = self.findPointsWithTag('Pickup1')
        pickupPoints2 = self.findPointsWithTag('Pickup2')
        pickupPoints3 = self.findPointsWithTag('Pickup3')
        pickupPoints4 = self.findPointsWithTag('Pickup4')
        hvcapPoints = self.findPointsWithTag('HVCapacitor')
        connPoints = self.findPointsWithTag('Connector')
        #
        pickupPoints1 = self.correctHeight(pickupPoints1, jigPlane)
        pickupPoints2 = self.correctHeight(pickupPoints2, jigPlane)
        pickupPoints3 = self.correctHeight(pickupPoints3, jigPlane)
        pickupPoints4 = self.correctHeight(pickupPoints4, jigPlane)
        hvcapPoints = self.correctHeight(hvcapPoints, jigPlane)
        connPoints = self.correctHeight(connPoints, jigPlane)
        pickupPoints.extend(pickupPoints1)
        pickupPoints.extend(pickupPoints2)
        pickupPoints.extend(pickupPoints3)
        pickupPoints.extend(pickupPoints4)
        #
        logger.info(f'pickup = {list(map(lambda x: x[2], pickupPoints))}')
        pickup1 = AveragedValue('Pickup1', values=list(map(lambda x: x[2], pickupPoints1)))
        pickup2 = AveragedValue('Pickup2', values=list(map(lambda x: x[2], pickupPoints2)))
        pickup3 = AveragedValue('Pickup3', values=list(map(lambda x: x[2], pickupPoints3)))
        pickup4 = AveragedValue('Pickup4', values=list(map(lambda x: x[2], pickupPoints4)))
        #
        
        pickupZ = AveragedValue('PickupZ', values=list(map(lambda x: x[2], pickupPoints)))
        hvcapZ = AveragedValue('HVCapacitorZ', values=list(map(lambda x: x[2], hvcapPoints)))
        connZ = AveragedValue('ConnectorZ', values=list(map(lambda x: x[2], connPoints)))
        self.outData['JigZ'] = MeasuredValue('JigZ', jigPlane.c, 0.0)
        self.outData['Pickup1'] = pickup1
        self.outData['Pickup2'] = pickup2
        self.outData['Pickup3'] = pickup3
        self.outData['Pickup4'] = pickup4
        self.outData['PickupZ'] = pickupZ
        self.outData['HVCapacitorZ'] = hvcapZ
        self.outData['ConnectorZ'] = connZ
        pass
    pass

# Bare module
class BareModuleHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)

    def defineOutputKeys(self):
        self.outKeys = [
            'JigZ', 'AsicZ', 'SensorZ',
            ]
        pass
    
    def mainRun(self):
        jigPoints = self.findPointsWithTag('Jig', True)
        jigPlane = self.calculateJigPlane(jigPoints)
        #
        asicZPoints = self.findPointsWithTag('AsicZ', True)
        sensorZPoints = self.findPointsWithTag('SensorZ', True)
        asicZPoints = self.correctHeight(asicZPoints, jigPlane)
        sensorZPoints = self.correctHeight(sensorZPoints, jigPlane)
        #
        dzcut = 0.050
        self.outData['JigZ'] = MeasuredValue('JigZ', 0.0, 0.0)
        asicZ = self.calcAverageHeight('AsicZ', asicZPoints, dzcut)
        sensorZ = self.calcAverageHeight('SensorZ', sensorZPoints, dzcut)
        self.outData['AsicZ'] = asicZ
        self.outData['SensorZ'] = sensorZ
        pass
    
    pass

class BareModuleBackHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    def defineOutputKeys(self):
        self.outKeys = [
            'JigZ(Back)', 
            'SensorZ(Back)', 'AsicZ(Back)', 
            ]
    def mainRun(self):
        jigPoints = self.findPointsWithTag('Jig', True)
        jigPlane = self.fitPlane(jigPoints)
        #
        asicZPoints = self.findPointsWithTag('AsicZ', True)
        sensorZPoints = self.findPointsWithTag('SensorZ', True)
        asicZPoints = self.correctHeight(asicZPoints, jigPlane)
        sensorZPoints = self.correctHeight(sensorZPoints, jigPlane)
        #
        self.outData['JigZ(Back)'] = MeasuredValue('JigZ(Back)', 0.0, 0.0)
        self.outData['SensorZ(Back)'] = self.calcAverageHeight('SensorZ(Back)', sensorZPoints)
        self.outData['AsicZ(Back)'] = self.calcAverageHeight('AsicZ(Back)', asicZPoints)
    def postRun(self):
        pass
    pass

# Assembled module
class ModuleHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    def defineOutputKeys(self):
        self.outKeys = [
            'JigZ', 'PickupZ',
            'Pickup1Z', 'Pickup2Z', 'Pickup3Z', 'Pickup4Z',
            'HVCapacitorZ', 'ConnectorZ', 
            ]
    def mainRun(self):
        jigPoints = self.findPointsWithTag('Jig')
        jigPlane = self.calculateJigPlane(jigPoints)
        logger.debug(f'Jig plane {jigPlane}')
        #
        pickupPoints = []
        pickupPoints1 = self.findPointsWithTag('Pickup1')
        pickupPoints2 = self.findPointsWithTag('Pickup2')
        pickupPoints3 = self.findPointsWithTag('Pickup3')
        pickupPoints4 = self.findPointsWithTag('Pickup4')
        hvcapPoints = self.findPointsWithTag('HVCapacitor')
        connPoints = self.findPointsWithTag('Connector')
        #
        pickupPoints1 = self.correctHeight(pickupPoints1, jigPlane)
        pickupPoints2 = self.correctHeight(pickupPoints2, jigPlane)
        pickupPoints3 = self.correctHeight(pickupPoints3, jigPlane)
        pickupPoints4 = self.correctHeight(pickupPoints4, jigPlane)
        pickupDz = 0.020
        pickup1Z = self.calcAverageHeight('Pickup1', pickupPoints1, pickupDz)
        pickup2Z = self.calcAverageHeight('Pickup2', pickupPoints2, pickupDz)
        pickup3Z = self.calcAverageHeight('Pickup3', pickupPoints3, pickupDz)
        pickup4Z = self.calcAverageHeight('Pickup4', pickupPoints4, pickupDz)
        pickupPoints.append(pickup1Z.get('value'))
        pickupPoints.append(pickup2Z.get('value'))
        pickupPoints.append(pickup3Z.get('value'))
        pickupPoints.append(pickup4Z.get('value'))
        hvcapPoints = self.correctHeight(hvcapPoints, jigPlane)
        connPoints = self.correctHeight(connPoints, jigPlane)
        #
        logger.info(f'pickup = {pickupPoints}')
        pickupZ = AveragedValue('PickupZ', values=pickupPoints)
        hvcapZ = AveragedValue('HVCapacitorZ', values=list(map(lambda x: x[2], hvcapPoints)))
        connZ = AveragedValue('ConnectorZ', values=list(map(lambda x: x[2], connPoints)))
        self.outData['JigZ'] = MeasuredValue('JigZ', jigPlane.c, 0.0)
        self.outData['Pickup1Z'] = pickup1Z
        self.outData['Pickup2Z'] = pickup2Z
        self.outData['Pickup3Z'] = pickup3Z
        self.outData['Pickup4Z'] = pickup4Z
        self.outData['PickupZ'] = pickupZ
        self.outData['HVCapacitorZ'] = hvcapZ
        self.outData['ConnectorZ'] = connZ
        
    pass

class ModuleRoofHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

class ModuleBackHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass
