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

from PyQt5.QtCore import Slot
from PyQt5.QtGui import QPixmap

from .data2 import ImageNP, ScanData
from .data3 import *
from .reader import *
from .tools import fitLine, fitPlane
from .model import *
from .prec import *
from .workflow import *
from .fittools import CircleFit, SlotFit
from .fittools2 import OuterlineFit, CellFit

logger = logging.getLogger(__name__)

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
        logger.info(f'Setting model {model} to analyis, {self.name}')
        self.model = model

    def setViewModel(self, viewModel):
        self.viewModel = viewModel
        
    def defineOutputKeys(self):
        pass

    def findPointsWithTag(self, tag):
        v = []
        for p in self.scanData.points:
            tags = p.value('tags')
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
    
    def mainRunOld(self, tags):
        logger.debug('  mainRunThread of ImagePatternAnalysis')
        status = True
        tags = self.scanData.allTags()
        self.tagPatternsMap.clear()
        
        #
        outputDir = self.model.outputDir()
        #
        #n = len(self.scanData.points)

        images = []
        for tag in tags:
            outdata = self.tagImageMap[tag] = {}
            points = self.scanData.pointsWithTag(tag)

            logger.debug(f'process tag {tag}')
            #if tag.startswith('Hole'):
            if tag == 'HoleTL' or tag == 'HoleBR':
                logger.debug(f'find big circle for {tag}')
                imageNPs = self.prepareImageNPs(tag)
                imageNPMap = {}
                for x in imageNPs:
                    imageNPMap[x.filePath] = x
            else:
                for ipoint, point in enumerate(points):
                    imageName = f'{tag}_{ipoint}'
                    imagePath = point.get('imagePath')
                    zoom = point.get('zoom')
                    if not os.path.exists(imagePath): continue
                    #image = cv2.imread(imagePath, cv2.IMREAD_COLOR)
                    outImage = ImageNP(imageName, imagePath)
                    imageQ = QPixmap(imagePath)
                    outImage.imageQ = imageQ
                    outdata[imageName] = outImage
                    if self.viewModel:
                        logger.debug(f'Emit signal photoReady for {imageName}')
                        self.viewModel.sigPhotoReady.emit(f'{tag}/{imageName}')
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
                logger.info(f'key = {key}')
                values.append(self.outData[key].get('value'))
        self.outData[tag] = AveragedValue(tag, values)
        #
        points = self.pointsWithTagMatch(f'{tag}_(.+)_point')
        logger.info(f'  Number of points along {tag}: {len(points)}')
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
        imageName = f'{imageNP.name}_p1'
        imagePath = os.path.basename(imageNP.filePath)
        imagePath = os.path.join(outputDir, imagePath)
        imagePath = imagePath.replace('.jpg', f'_{imageName}.jpg')
        xy = rec.position()
        point = None
        self.addPatternRecImage(tag, imageNP.name, rec)
        if rec.patternValid:
            point = CvPoint(*xy)
        return point, ImageNP(imageName, imagePath)

    def findLineV(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        rec = PatternRecImage(self.model.componentType, tag, imageNP.name, 
                              imageNP.xyOffset, 
                              imageNP.filePath, imageNP.zoom,
                              outputDir)
        pos = rec.run()
        imageName = f'{imageNP.name}_p1'
        imagePath = os.path.basename(imageNP.filePath)
        imagePath = os.path.join(outputDir, imagePath)
        imagePath = imagePath.replace('.jpg', f'_{imageName}.jpg')
        xy = rec.position()
        point = None
        self.addPatternRecImage(tag, imageNP.name, rec)
        if rec.patternValid:
            point = CvPoint(*xy)
        return point, ImageNP(imageName, imagePath)

    def findCircle(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        rec = PatternRecImage(self.model.componentType, tag, imageNP.name, 
                              imageNP.xyOffset, 
                              imageNP.filePath, imageNP.zoom,
                              outputDir)
        #pos = rec.run()
        imageName = f'{imageNP.name}_p1'
        imagePath = os.path.basename(imageNP.filePath)
        imagePath = os.path.join(outputDir, imagePath)
        imagePath = imagePath.replace('.jpg', f'_{imageName}.jpg')
        #
        rec.openImage()
        rec.createImageP1()
        #
        xy = rec.position()
        point = None
        self.addPatternRecImage(tag, imageNP.name, rec)
        if rec.patternValid:
            point = CvPoint(*xy)
        return point, ImageNP(imageName, imagePath)
    
    def findOuterline(self, tag, imageNP, figname):
        outputDir = self.model.outputDir()
        r = 0.0001
        line = CvLine()
        fitter = OuterlineFit()
        fitter.outImageName = f'{figname}.jpg'
        if tag[-1] == 'L':
            image, point, localpoint = fitter.run(imageNP, 'L', r)
            line.setFromX(localpoint[0].x())
            print(f'localpoint : {localpoint}')
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
        return line, ImageNP(imageName, imagePath)
    
    def findBigCircle(self, tag, imageNPs):
        outputDir = self.model.outputDir()
        fitter = CircleFit()
        fitter.setOutputDir(outputDir)
        bigImage, circle, pointsGlobal = fitter.run(imageNPs)
        return (circle, bigImage)
    
    def findBigSlot(self, tag, imageNPs):
        outputDir = self.model.outputDir()
        fitter = SlotFit()
        fitter.setOutputDir(outputDir)
        bigImage, circle, pointsGlobal = fitter.run(imageNPs)
        return (circle, bigImage)

    def precTagPattern(self, tag, precfunc, combineImages=False, x=None, y=None):
        imageNPs = self.prepareImageNPs(tag)
        self.tagImageMap[tag] = {}

        logger.debug(f'precTagPattern N images: {len(imageNPs)}')
        for x in imageNPs:
            logger.debug(f'Image {x.name}, {x.filePath} ({x.xyOffset})')

        if combineImages:
            logger.debug(f'Pattern rec {tag}')
            circle, outImage = precfunc(tag, imageNPs)
            logger.debug(f'{outImage.filePath} exists? {os.path.exists(outImage.filePath)}')
            imageQ = QPixmap(outImage.filePath)
            outImage.imageQ = imageQ

            name2 = f'{tag}/{outImage.name}'
            self.tagImageMap[tag][outImage.name] = outImage
            if circle != None:
                key = f'{tag}_x'
                self.outData[key] = MeasuredValue(key, circle[0], 0.0)
                key = f'{tag}_y'
                self.outData[key] = MeasuredValue(key, circle[1], 0.0)
                key = f'{tag}_r'
                self.outData[key] = MeasuredValue(key, circle[2], 0.0)
                key = f'{tag}_circle'
                self.outData[key] = circle
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
                logger.debug(f'{outImage.filePath} exists? {os.path.exists(outImage.filePath)}')
                outImage.xyOffset = imageNP.xyOffset
                imageQ = QPixmap(outImage.filePath)
                outImage.imageQ = imageQ

                name2 = f'{tag}/{outImage.name}'
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
                if self.viewModel:
                    logger.debug(f'Emit signal photoReady for {name2}')
                    self.viewModel.sigPhotoReady.emit(name2)
        pass

    def prepareImageNPs(self, tag):
        points = self.findPointsWithTag(tag)
        imageNPs = []
        for i, p in enumerate(points):
            if p.get('error'): continue
            name = '%s_%d' % (tag, i)
            image = ImageNP(name, p.get('imagePath'))
            image.xyOffset = CvPoint( p.get('x'), p.get('y'))
            #x.xyOffset = [ p.get('x'), p.get('y')]
            imageNPs.append(image)
        return imageNPs
    
    def runPatternRec(self, tags):
        if len(tags) == 0:
            tags = ['All']
        outputDir = self.model.outputDir()
        #
        n = len(self.scanData.points)
        for tag in tags:
            logger.info('Pattern tag: %s' % tag)
            self.tagPatternsMap[tag] = []
            for i in range(n):
                point = self.scanData.points[i]
                if point.value('error'): continue
                if tag=='All' or tag in point.value('tags'):
                    imagePath = point.get('imagePath')
                    zoom = point.get('zoom')
                    logger.info('  use photo %s' % imagePath)
                    rec = PatternRecImage(model.componentType, tag,
                                          (point.get('x'), point.get('y')), 
                                          imagePath, zoom,
                                          outputDir)
                    pos = rec.run()
                    rec.clearLargeData()
                    self.tagPatternsMap[tag].append(rec)
                    if self.viewModel:
                        logger.debug(f'Emit sigPhotoReady for {imagePath}')
                        self.viewModel.sigPhotoReady.emit(imagePath)
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

    def defineOutputKeys(self):
        #self.outKeys = ['FiducialTL', 'FiducialTR', 'FiducialBL', 'FiducialBR']
        self.outKeys = ['FlexL', 'FlexR', 'FlexB', 'FlexT', ]
        #self.outKeys = ['HoleTL', 'HoleBR']

    def mainRun(self):
        super().mainRun()
        flexX = 40.0
        flexY = 40.0
        #
        #self.precTagBigCircle('HoleTL', x=-27.0, y=27.0)
        #self.precTagBigSlot('HoleBR', x=27.0, y=-27.0)
        #self.precTagOuterline('FlexL', x=-flexX/2.0)
        #self.precTagOuterline('FlexR', x=flexX/2.0)
        #self.precTagOuterline('FlexT', y=flexY/2.0)        
        #self.precTagOuterline('FlexB', y=-flexY/2.0)
        self.precTagLineV('FlexL', x=-flexX/2.0)
        self.precTagLineV('FlexR', x=flexX/2.0)
        self.precTagLineH('FlexT', y=flexY/2.0)
        self.precTagLineH('FlexB', y=-flexY/2.0)

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
            'FlexX', 'FlexY',
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
        pass

    pass

# Bare module
class BareModulePatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        super().__init__(name)
        self.patternRecDone = False
        
    def defineOutputKeys(self):
        self.outKeys = [
            ]
        pass

    def mainRun(self):
        super().mainRun()
        asicW, asicH = 40.0, 40.0
        sensorW, sensorH = 40.0, 40.0
        if self.patternRecDone:
            return
        #
        #self.precTagLineH('AsicT', y=asicH/2.0)
        #self.precTagLineH('AsicB', y=-asicH/2.0)
        self.precTagLineV('AsicL', y=-asicW/2.0)
        self.precTagLineV('AsicR', y=asicW/2.0)
        self.precTagLineH('SensorT', y=sensorH/2.0)
        self.precTagLineH('SensorB', y=-sensorH/2.0)
        #self.precTagLineV('SensorL', y=-sensorW/2.0)
        #self.precTagLineV('SensorR', y=sensorW/2.0)
        #self.precTagCircle('FmarkTL', x=sensorW/2.0, y=sensorH/2.0)
        #self.precTagCircle('FmarkTB', x=sensorW/2.0, y=-sensorH/2.0)
        #self.precTagCircle('FmarkRB', x=-sensorW/2.0, y=-sensorH/2.0)
        #self.precTagCircle('FmarkRL', x=-sensorW/2.0, y=sensorH/2.0)
        #self.precTagCircle('AsicFmarkTL', x=asicW/2.0, y=asicH/2.0)
        #self.precTagCircle('AsicFmarkTB', x=asicW/2.0, y=-asicH/2.0)
        #self.precTagCircle('AsicFmarkRB', x=-asicW/2.0, y=-asicH/2.0)
        #self.precTagCircle('AsicFmarkRL', x=-asicW/2.0, y=asicH/2.0)
        self.patternRecDone = True

    def postRun(self):
        self.calculateLine('FlexL', 'x')
        self.calculateLine('FlexR', 'x')
        self.calculateLine('FlexT', 'y')
        self.calculateLine('FlexB', 'y')

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
            'AsicX', 'SensorY', 
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
        self.lineDiff('AsicX', 'AsicR', 'AsicL', 'v')
        self.lineDiff('SensorY', 'SensorT', 'SensorB', 'h')
    pass

class BareModuleBackSizeAnalysis(SizeAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

# Assembled module
class ModulePatternAnalysis(ImagePatternAnalysis):
    def __init__(self, name):
        logger.debug('ModulePatternAnalysis ctor')
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
        logger.debug('mainRun in Module pattern analysis')
        asicW, asicH = 20.0, 20.0
        sensorW, sensorH = 20.0, 20.0
        flexW, flexH = 20.0, 20.0
        #
        if self.patternRecDone:
            logger.info(f'{self.name} skip pattern recognition')
            return
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
        self.patternRecDone = True

    def postRun(self):
        logger.info(f'ModulePatternAnalysis {self.outData}')
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
            'AsicToFlexL', 'AsicToFlexR', 'SensorToFlexT', 'SensorToFlexB',
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
        self.calculateFmarkDistance('FmarkDistanceBL', 'AsicFmarkBL', 'FmarkBL')
        logger.info(f'ModuleSizeAnalysis... keys={self.outData.keys()}')
        logger.info(f'{self.outData}')
        #Angle = self.outData['FlexL_line'].angle(self.outData['AsicL_line'])*180/math.pi
        Angle = 0.0
        e = 0.0
        self.outData['Angle'] = MeasuredValue('Angle', Angle, e)
        #

    def postProcess(self):
        keys = list(self.tagPatternsMap.keys())
        keys.sort()
        valueMap = {}
        sigmaMap = {}
        for k in keys:
            mean, sigma = patternMeanSigma(k, self.tagPatternsMap[k])
            valueMap[k] = mean
            sigmaMap[k] = sigma
        self.sizeValueMap = valueMap
        self.sizeSigmaMap = sigmaMap
        print(valueMap)
        if self.moduleType != 'Rd53AModule':
            return 1
        # Line reconstruction
        pointsL = map(lambda x: x.position(), self.tagPatternsMap['FlexL'])
        pointsB = map(lambda x: x.position(), self.tagPatternsMap['FlexB'])
        pointsL = list(map(lambda x: CvPoint(*x), pointsL))
        pointsB = list(map(lambda x: CvPoint(*x), pointsB))
        print('Before fitLine')
        angle = 90.0
        if False and len(pointsL)>2 and len(pointsB)>2:
            lineL = fitLine(pointsL)
            lineB = fitLine(pointsB)
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
            #m['AsicY'] = (valueMap['AsicT'] - valueMap['AsicB'], 0.0)
            m['FlexX'] = (valueMap['FlexR'] - valueMap['FlexL'], 0.0)
            m['FlexY'] = (valueMap['FlexT'] - valueMap['FlexB'], 0.0)
            #m['SensorX'] = (valueMap['SensorR'] - valueMap['SensorL'], 0.0)
            m['SensorY'] = (valueMap['SensorT'] - valueMap['SensorB'], 0.0)
            m['Angle'] = (angle, 0.0)
        #

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
            'JigZ', 'PickupZ', 'HVCapacitorZ', 'HVConnectorZ'
            ]
        
    def mainRun(self):
        jigPoints = self.findPointsWithTag('Jig')
        jigPlane = self.fitPlane(jigPoints)
        logger.debug(f'Jig plane {jigPlane}')
        #
        pickupPoints = []
        pickupPoints.extend(self.findPointsWithTag('Pickup1'))
        pickupPoints.extend(self.findPointsWithTag('Pickup2'))
        pickupPoints.extend(self.findPointsWithTag('Pickup3'))
        pickupPoints.extend(self.findPointsWithTag('Pickup4'))
        hvcapPoints = self.findPointsWithTag('HVCapacitor')
        hvconnPoints = self.findPointsWithTag('HVConnector')
        #
        pickupPoints = self.correctHeight(pickupPoints, jigPlane)
        hvcapPoints = self.correctHeight(hvcapPoints, jigPlane)
        hvconnPoints = self.correctHeight(hvconnPoints, jigPlane)
        #
        logger.info(f'pickup = {list(map(lambda x: x[2], pickupPoints))}')
        pickupZ = AveragedValue('PickupZ', values=list(map(lambda x: x[2], pickupPoints)))
        hvcapZ = AveragedValue('HVCapacitorZ', values=list(map(lambda x: x[2], hvcapPoints)))
        hvconnZ = AveragedValue('HVConnectorZ', values=list(map(lambda x: x[2], hvconnPoints)))
        self.outData['JigZ'] = MeasuredValue('JigZ', jigPlane.c, 0.0)
        self.outData['PickupZ'] = pickupZ
        self.outData['HVCapacitorZ'] = hvcapZ
        self.outData['HVConnectorZ'] = hvconnZ
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
        jigPoints = self.findPointsWithTag('Jig')
        jigPlane = self.fitPlane(jigPoints)
        #
        asicZPoints = self.findPointsWithTag('AsicZ')
        sensorZPoints = self.findPointsWithTag('SensorZ')
        asicZPoints = self.correctHeight(asicZPoints, jigPlane)
        sensorZPoints = self.correctHeight(sensorZPoints, jigPlane)
        #
        self.outData['JigZ'] = MeasuredValue('JigZ', 0.0, 0.0)
        self.outData['AsicZ'] = AveragedValue('AsicZ', values=list(map(lambda x: x[2], asicZPoints)))
        self.outData['SensorZ'] = AveragedValue('SensorZ', values=list(map(lambda x: x[2], sensorZPoints)))
        pass
    
    pass

class BareModuleBackHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

# Assembled module
class ModuleHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    def defineOutputKeys(self):
        self.outKeys = [
            'JigZ', 'PickupZ',
            #'Pickup1', 'Pickup2', 'Pickup3', 'Pickup4',
            'HVCapacitorZ', 'HVConnectorZ', 
            ]
    def mainRun(self):
        jigPoints = self.findPointsWithTag('Jig')
        jigPlane = self.fitPlane(jigPoints)
        logger.debug(f'Jig plane {jigPlane}')
        #
        pickupPoints = []
        pickupPoints.extend(self.findPointsWithTag('Pickup1'))
        pickupPoints.extend(self.findPointsWithTag('Pickup2'))
        pickupPoints.extend(self.findPointsWithTag('Pickup3'))
        pickupPoints.extend(self.findPointsWithTag('Pickup4'))
        hvcapPoints = self.findPointsWithTag('HVCapacitor')
        hvconnPoints = self.findPointsWithTag('HVConnector')
        #
        pickupPoints = self.correctHeight(pickupPoints, jigPlane)
        hvcapPoints = self.correctHeight(hvcapPoints, jigPlane)
        hvconnPoints = self.correctHeight(hvconnPoints, jigPlane)
        #
        logger.info(f'pickup = {list(map(lambda x: x[2], pickupPoints))}')
        pickupZ = AveragedValue('PickupZ', values=list(map(lambda x: x[2], pickupPoints)))
        hvcapZ = AveragedValue('HVCapacitorZ', values=list(map(lambda x: x[2], hvcapPoints)))
        hvconnZ = AveragedValue('HVConnectorZ', values=list(map(lambda x: x[2], hvconnPoints)))
        self.outData['JigZ'] = MeasuredValue('JigZ', jigPlane.c, 0.0)
        self.outData['PickupZ'] = pickupZ
        self.outData['HVCapacitorZ'] = hvcapZ
        self.outData['HVConnectorZ'] = hvconnZ
        
    pass

class ModuleRoofHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass

class ModuleBackHeightAnalysis(HeightAnalysis):
    def __init__(self, name):
        super().__init__(name)
    pass
