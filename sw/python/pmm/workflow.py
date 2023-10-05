#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# Workflow:
# - Size measurement
#   - Inputs:
#     - Module type and name (Rd53a, ITkPixV1, ..., KEKQ18, ...)
#     - Scan configuration
#       - Tag of each point (pattern location, i.e. AsicT, SensorL, ...)
#     - Scan results
#       - x, y, z, image path (/.../xxx.jpg)
#     - From global configuration
#       - Working directory for the metrology analysis
#   - Arrange images by tags (tag -> list of images)
#   - Processing of each image
#     - Retrieve the module design from module type
#     - Find out the target pattern using the tag and design (TargetData)
#       - Target location and shape
#     - Determine the search region for finding the pattern
#       - Search region in both global (x,y) and (c, r) inside the image
#     - Overlay the detected pattern on an image and create a thumbnail
#       - Thumbnail: size 600x400 (xxx_p1.jpg)
#   - Output
#     - Thumbnail image (xxx_p1.jpg)
#     - Coordinate of the pattern (x, y)
# - Height measurement
#   - Inputs:
#     - Module type and name (Rd53a, ITkPixV1, ..., KEKQ18, ...)
#     - Scan configuration
#       - Tag of each point (pattern location, i.e. AsicT, Pickup1, ...)
#     - Scan results
#       - x, y, z, image path (/.../xxx.jpg)
#     - From global configuration
#       - Working directory for the metrology analysis
#   - Arrange measurements by tags (tag -> list of measurements)
#   - Processing of each tag
#     - Extract the z-measurement and calculate the mean and sigma
#   - Create the summary table
#--------------------------------------------------------------------

import os
import logging
import threading
import math
import statistics

import cv2

from pmm.design import *
from pmm.prec import *
from pmm.params import *
from pmm.model import *
import pmm

logger = logging.getLogger(__name__)

class PatternRecScan:
    def __init__(self, componentType, moduleDir, 
                 scanResults, scanConfig, tagPatternMap, configStore=None):
        self.componentType = componentType
        self.moduleDir = moduleDir
        self.scanResults = scanResults
        self.scanConfig = scanConfig
        self.tagPatternMap = tagPatternMap
        if not os.path.exists(self.moduleDir):
            logger.debug('Create module working directory %s' % self.moduleDir)
            os.mkdir(self.moduleDir)

    def run(self):
        tags = self.scanConfig.allTags()
        self.tagPatternMap.clear()

        if len(tags) == 0:
            tags = ['All']

        if not(os.path.exists(self.moduleDir)):
            logger.debug('Create module working directory %s' % self.moduleDir)
            os.mkdir(self.moduleDir)

        n = len(self.scanConfig.pointConfigList)
        for i in range(n):
            data = self.scanResults.pointResult(i)
            #print('i = ', data)
        for tag in tags:
            logger.info('Pattern tag: %s' % tag)
            self.tagPatternMap[tag] = []
            for i in range(n):
                config = self.scanConfig.pointConfig(i)
                if tag=='All' or (config!=None and tag in config.tags):
                    imagePath = self.scanResults.imagePath(i)
                    data = self.scanResults.pointResult(i)
                    if data!=None:
                        logger.info('  use photo %s' % imagePath)
                        rec = PatternRecImage(self.componentType, tag,
                                              (data.x, data.y), 
                                              imagePath, data.zoom,
                                              self.moduleDir)
                        pos = rec.run()
                        #self.tagPatternMap[tag].append( (rec.imagePath, rec.imageP2Path, pos) )
                        rec.clearLargeData()
                        self.tagPatternMap[tag].append(rec)
            pass
        # Big circle
        # Big slot
        #logger.debug('Tag->Files map at the end of pattern rec.')
        #print(self.tagPatternMap)
        pass

class PatternRecImage:
    def __init__(self, componentType, tag, name, offsetXY, imagePath, zoom, 
                 moduleDir='.'):
        self.componentType = componentType
        self.tag = tag
        self.name = name
        self.offsetXY = offsetXY
        self.imagePath = imagePath
        self.zoom = zoom
        self.moduleDir = moduleDir
        self.patternValid = False
        self.position0 = []
        self.position1 = []
        self.manualCR = []
        #
        self.targetData = None
        self.imageValid = False
        # Large data
        self.image0 = None
        self.imageBW = None
        self.image1 = None

    def persKeys(self):
        keys = [
            'componentType', 'tag', 'name', 'offsetXY', 'imagePath',
            'zoom', 'moduleDir', 'patternValid', 'position0', 'position1',
            'manualCR',
            'targetData', 'imageValid', 
            ]
        return keys
    
    def openImage(self):
        self.imageValid = True
        if os.path.exists(self.imagePath):
            self.image0 = cv2.imread(self.imagePath)
            self.imageBW = cv2.cvtColor(self.image0, cv2.COLOR_BGR2GRAY)
        else:
            self.imageValid = False
            self.image0 = None

    def addManualPoint(self, xy, cr):
        self.position1 = xy
        self.manualCR = cr
        #fpath2b = self.imageP1Path.replace('_p1b.jpg', '_p2b.jpg')
        img = self.genImage2()
        return img
        
    def clearLargeData(self):
        self.imageValid = False
        self.image0 = None
        self.imageBW = None
        self.image1 = None
        # Keep the thumbnail object
        #self.image1b = None

    def position(self):
        p = []
        if len(self.position1) == 2:
            p = self.position1
        elif len(self.position0) == 2:
            p = self.position0
        return p
    
    def run(self):
        pos = []
        self.patternValid = False
        self.openImage()
        region = self.searchRegion()
        region = (0, 0, 6000, 4000)
        if self.targetData:
            if self.targetData.name[-1] == 'T':
                region = (0, 0, 6000, 2000)
            elif self.targetData.name[-1] == 'B':
                region = (0, 2000, 6000, 4000)
            elif self.targetData.name[-1] == 'L':
                region = (0, 0, 3000, 4000)
            elif self.targetData.name[-1] == 'R':
                region = (3000, 0, 6000, 4000)
            
        self.region = region
        logger.info('Run pattern recognition on %s %s' % (self.tag, self.imagePath) )
        if len(region) != 4:
            logger.warning('Cannot determine the search region')
            return pos

        #logger.debug('Search region: (%d, %d) -> (%d, %d)' % tuple(region))
        targetShape = self.targetData.ptype
        #logger.debug(str(region))
        if self.imageValid:
            params = paramStore.getParams(self.tag)
            wsum, tgap = params
            patterns = patternRec1(self.imageBW, targetShape, rect=region, 
                                   wsum=wsum, tgap=tgap)
            self.patterns = patterns
            if self.patterns.target:
                self.patternValid = True
            self.image1 = self.overlay(region, patterns)
            cr = patterns.xy()
            offset = CvPoint(self.offsetXY[0], self.offsetXY[1])
            frame = ImageFrame(offset, self.zoom)
            if cr:
                xy = frame.toGlobal([cr.x(), cr.y()])
                pos = [ xy.x(), xy.y() ]
                logger.debug('  (c,r)=(%d,%d), (x,y)=(%7.3f,%7.3f)' % \
                             (cr.x(), cr.y(),*pos) )
            else:
                logger.debug('  could not find the pattern')
        else:
            logger.warning('Image %s is empty' % self.imagePath)
        self.position0 = pos
        return pos

    def overlay(self, region, patterns):
        color_region = (0, 0, 255)
        color_point = (0, 0, 255)
        image1 = self.image0.copy()
        cv2.rectangle(image1, region[0:2], region[2:4], color_region, 
                      thickness=30)
        p = [0, 0]
        logger.debug('Try to add rec point %s %s' % \
                     (str(self.targetData), str(patterns) ) )
        if self.targetData!=None and patterns.target!=None:
            logger.debug('  TargetData and patterns ok')
            if self.targetData.ptype.startswith('Line'):
                logger.debug('  Target pattern is a line')
                p = patterns.target.center()
                p = ( int(p.x()), int(p.y()) )
                logger.debug('  Line center %d %d, shape=%s' % (p[0], p[1], str(image1.shape) ) )
                radius = 50
                cv2.circle(image1, p, radius, color_point, thickness=-20)
            else:
                logger.warning('  Unknown pattern type %s' % self.targetData.ptype)
        return image1

    def genImage2(self):
        image2 = None
        if len(self.position1) == 2:
            logger.info('Generate image 2')
            radius=100
            color_point = (0xe1, 0x69, 0x41)
            image2 = self.image1.copy()
            cr = tuple(map(lambda x: x*10, self.manualCR))
            cv2.circle(image2, cr, radius, color_point, thickness=-1)
        else:
            logger.info('Use image1 as image2')
            image2 = self.image1
        return image2
        
    def createImageP1(self):
        self.image1 = self.image0.copy()
        
    def searchRegion(self):
        self.targetData = None
        region = []
        #logger.info(f'Get design of component type {self.componentType}')
        module = createModule(self.componentType)
        if self.tag in module.targetData.keys():
            self.targetData = module.targetData[self.tag]

        logger.debug('Process image for tag %s (x,y)=(%6.2f,%6.2f)' %\
                     (self.tag, self.offsetXY[0], self.offsetXY[1]))
        if self.targetData != None and self.tag.find('Jig')<0:
            offset = CvPoint(self.offsetXY[0], self.offsetXY[1])
            frame = ImageFrame(offset, self.zoom)
            tag = 'SearchWindowSize_um%s' % self.tag
            searchWindowSize = paramStore.getParams(tag)
            dx = 0.3 # mm
            if len(searchWindowSize)>0:
                dx = searchWindowSize[0]*0.001
                logger.debug('Setting search window size to %6.3f [um] (%6.3f)' %\
                             (dx, searchWindowSize[0]) )
            x0 = self.targetData.x
            y0 = self.targetData.y
            components = ('Asic','Asic1','Asic2','Asic3','Asic4', 'Sensor', 'Flex')
            vedges = [ a+b for a in components for b in ('L', 'R')]
            hedges = [ a+b for a in components for b in ('T', 'B')]
            p1 = CvPoint(x0 - dx, y0 + dx)
            p2 = CvPoint(x0 + dx, y0 - dx)
            cr1 = frame.trimCR(frame.toCR(p1))
            cr2 = frame.trimCR(frame.toCR(p2))
            
            dxPixels = frame.toPixels(dx)
            if self.tag in vedges:
                r0 = int(frame.height/2)
                cr1[1] = r0 - dxPixels
                cr2[1] = r0 + dxPixels
            elif self.tag in hedges:
                c0 = int(frame.width/2)
                cr1[0] = c0 - dxPixels
                cr2[0] = c0 + dxPixels
            cr1 = frame.trimCR(cr1)
            cr2 = frame.trimCR(cr2)
            region = ( *cr1, *cr2 )
        return region

def patternMeanSigma(tag, patterns):
    mean, sigma = 0.0, 0.0
    xmean, xsigma = 0.0, 0.0
    ymean, ysigma = 0.0, 0.0
    n = 0
    logger.debug('Calculate pattern mean/sigma tag=%s n=%d' % (tag, len(patterns)) )
    for p in patterns:
        xy = p.position()
        if len(xy)!=2: continue
        logger.debug(  '(x,y)=(%7.3f,%7.3f)' % (xy[0], xy[1]) )

        xmean += xy[0]
        xsigma += xy[0]**2
        ymean += xy[1]
        ysigma += xy[1]**2
        n += 1
    if n > 0:
        xmean /= n
        ymean /= n
        xsigma = math.sqrt(abs(xsigma/n - xmean**2))
        ysigma = math.sqrt(abs(ysigma/n - ymean**2))
    if tag.endswith('L') or tag.endswith('R'):
        mean, sigma = float(xmean), float(xsigma)
    elif tag.endswith('T') or tag.endswith('B'):
        mean, sigma = float(ymean), float(ysigma)
    #print('%s => ' % tag, mean, sigma, ' x:', xmean, xsigma, ' y:', ymean, ysigma)
    return (mean, sigma)

def calculateX(pointsL, pointsR, tag=''):
    x = 0.0
    dx = 0.0
    n = 0
    lineL, lineR = None, None
    logger.debug('pointsL: %s' % str(pointsL))
    for p in pointsL:
        logger.debug('n = %d' % len(p.position) )
        logger.debug(p.position)
    if len(pointsL)>=2:
        lineL = pmm.fitLine(pointsL)
        logger.debug('LineL: %s' % str(lineL))
    if len(pointsR)>=2:
        lineR = pmm.fitLine(pointsR)
    if lineL != None and lineR != None:
        # calculate
        xpos = [-20, -10, 0, 10, 20]
        for i in xpos:
            h1 = lineR.direction
            x1 = lineR.xAtY(i)
            points = [x1, i]
            line2 = Line()
            line2.setFromPointDir(points, h1())
            logger.debug('calculate X line %s' % str(line2) )
            point1 = lineL.intersection(line2)
            logger.debug('calculate X intersectionPoint %s'% str(point1) )
            distance1 = lineR.distance(point1)
            logger.debug('calculate X distance1 %7.3f' % distance1 )
            x +=  distance1
            dx += distance1**2
            n += 1
        if n > 0:
            x /= n
            dx = math.sqrt(abs(dx/n - x**2))
        logger.debug('calculate X (meanx, dx) = (%7.3f %7.3f)' % (x, dx) )
    return (x, dx)

def calculateY(pointsT, pointsB, tag=''):
    y = 0.0
    dy = 0.0
    n = 0
    lineT, lineB = None, None
    logger.debug('pointsT: %s' % str(pointsT))
    for p in pointsT:
        logger.debug('n = %d' % len(p.position) )
        logger.debug(p.position)
    if len(pointsT)>=2:
        lineT = pmm.fitLine(pointsT)
        logger.debug('LineT: %s' % str(lineT))
    if len(pointsB)>=2:
        lineB = pmm.fitLine(pointsB)
    if lineT != None and lineB != None:
        # calculate
        ypos = [-20, -10, 0, 10, 20]
        for i in ypos:
            h1 = lineB.direction
            y1 = lineB.yAtX(i)
            points = [i, y1]
            line2 = Line()
            line2.setFromPointDir(points, h1())
            logger.debug('calculate Y line %s'% str(line2) )
            point1 = lineT.intersection(line2)
            logger.debug('calculate Y intersectionPoint %s' % str(point1) )
            distance1 = lineB.distance(point1)
            logger.debug('calculate Y distance1 %7.3f' % distance1 )
            y +=  distance1
            dy += distance1**2
            n += 1
        if n > 0:
            y /= n
            dy = math.sqrt(abs(dy/n - y**2))
        logger.debug('calculate Y (meany, dy) = (%7.3f %7.3f)' % (y, dy) )
    return (y, dy)

def extractPoints(patternResults):
    points = list(map(lambda x: x.position(), patternResults))
    for p in points:
        logger.debug('points from results: %s' % str(p))
    points = list(map(lambda x: Point(x), filter(lambda x: len(x)>0, points)) )
    return points

class PatternRecThread(threading.Thread):
    def __init__(self, tag, imageFile, pointResult):
        super().__init__()
        self.tag = tag
        self.imageFile = imageFile
        self.pointResult = pointResult

    def run(self):
        x = 0
        while True:
            x += 1
            if (x % 10000)==0:
                logger.debug('x = %d' % x)

def workflow_size_Shapes(scanResults, patternResultsMap):
    points = {}
    lines = {}
    tags = [
        'AsicT', 'AsicB', 'AsicL', 'AsicR', 
        'SensorT', 'SensorB', 'SensorL', 'SensorR', 
        'FlexT', 'FlexB', 'FlexL', 'FlexR',
        ]
    keys = patternResultsMap.keys()
    for tag in tags:
        if not tag in keys:
            logger.warning('Key %s does not exist in patternResultsMap' % tag)
            continue
        patterns = patternResults
