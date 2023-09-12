#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# 
# Unit: mm
# Module coordinate system: origin at the middle
#                           x (towards right) and y (towards top)
#--------------------------------------------------------------------
import os, sys
import argparse
import pickle
import math
import copy
import re
import logging

import numpy as np
import scipy.signal as signal

import cv2
from pmm.model import *

logger = logging.getLogger(__name__)

dx20 = (0.39E-3)/2.0

def pixelSizeForZoom(zoom=20):
    if zoom>0:
        return dx20*20/zoom
    return 0

class CvVector:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    #def x(self):
    #    return self.x
    #def y(self):
    #    return self.y
    def shift(self, x, y):
        self.x += x
        self.y += y
    def __add__(self, v):
        return CvVector(self.x + v.x, self.y + v.y)
    def __sub__(self, v):
        return CvVector(self.x - v.x, self.y - v.y)
    def __mul__(self, r):
        return CvVector(self.x*r, self.y*r)
    def __rmul__(self, r):
        return self.__mul__(r)
    def __truediv__(self, r):
        return CvVector(self.x/r, self.y/r)
    def __neg__(self, r):
        return CvVector(-self.x, -self.y)
    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        raise RuntimeError('Index-out-of-bounds {} not in [0, 1]'.format(i))
    def dot(self, v):
        s = self.x*v.x + self.y*v.y
        return s
    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y)
    def normalize(self):
        l2 = self.dot(self)
        l2 = math.sqrt(l2)
        if l2 > 0:
            self.x /= l2
            self.y /= l2
        
class CvPoint:
    def __init__(self, x=0.0, y=0.0):
        self.position = CvVector(x, y)
    def x(self):
        return self.position.x
    def y(self):
        return self.position.y
    def shift(self, x, y):
        self.position.shift(x, y)
    def __add__(self, v):
        return CvPoint(self.x() + v.x(), self.y() + v.y())
    def __sub__(self, v):
        return CvPoint(self.x() - v.x(), self.y() - v.y())
    def __mul__(self, r):
        return CvPoint(self.x()*r, self.y()*r)
    def __rmul__(self, r):
        return self.__mul__(r)
    def __truediv__(self, r):
        return CvPoint(self.x()/r, self.y()/r)
    def __neg__(self):
        return CvPoint(-self.x(), -self.y())
    def __getitem__(self, i):
        if i == 0:
            return self.position.x
        elif i == 1:
            return self.position.y
        raise RuntimeError('Index-out-of-bounds {} not in [0, 1]'.format(i))
    def distance(self, point):
        v = point.position - self.position
        return v.length()
    def __str__(self):
        return 'Point:(x,y)=(%6.1f,%6.1f)' % \
            (self.position.x, self.position.y)

class CvLine:
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end
        self.points = [start]
        self.startVertex = None
        self.endVertex = None
    def setFromX(self, x, theta=math.pi):
        self.start = CvPoint(x, 1.0)
        self.end = CvPoint(x, 3999.0)
    def setFromY(self, y, theta=0.0):
        self.start = CvPoint(1.0, y)
        self.end = CvPoint(5999.0, y)
    def shift(self, x, y, points):
        if self.start not in points:
            self.start.shift(x, y)
        if self.end not in points:
            self.end.shift(x, y)
        pass
    def isValid(self):
        if self.start == None or self.end == None:
            return False
        else:
            return True
    def startAtVertex(self):
        return (self.startVertex!=None)
    def endAtVertex(self):
        return (self.endVertex!=None)
    def center(self):
        c = None
        if self.start and self.end:
            v = (self.start.position + self.end.position)*0.5
            c = CvPoint(v.x, v.y)
        return c
    def direction(self):
        dir = CvVector()
        if self.isValid():
            dxy = self.end.position - self.start.position
            dxy.normalize()
            dir = dxy
        return dir
    def distance(self, point):
        dir = self.direction()
        a = dir.y
        b = -dir.x
        c = -dir.y*self.start.x() + dir.x*self.start.y();
        d = abs(a*point.x() + b*point.y() + c)
        return d
    def distanceTo(self, point):
        dir = self.direction()
        sp = point.position - self.start.position
        ep = point.position - self.end.position
        spLength = sp.length()
        epLength = ep.length()
        l0 = self.length()
        d = 1.0E+10
        if spLength < l0 and epLength < l0:
            d = self.distance(point)
        else:
            d = min(spLength, epLength)
        return d
    def distanceToLine(self, line):
        d = min( (self.start.position-line.start.position).length(), 
                 (self.start.position-line.end.position).length(), 
                 (self.end.position-line.start.position).length(), 
                 (self.end.position-line.end.position).length() )
        return d
    def distanceToLineForMerge(self, line):
        d1, d2, d3, d4 = None, None, None, None
        d = None
        if (self.startAtVertex()==False and line.startAtVertex()==False):
            d1 = (self.start.position-line.start.position).length()
            if d == None or d1 < d: d = d1
        if (self.startAtVertex()==False and line.endAtVertex()==False):
            d2 = (self.start.position-line.end.position).length()
            if d == None or d2 < d: d = d2
        if (self.endAtVertex()==False and line.startAtVertex()==False):
            d3 = (self.end.position-line.start.position).length()
            if d == None or d3 < d: d = d3
        if (self.endAtVertex()==False and line.endAtVertex()==False):
            d4 = (self.end.position-line.end.position).length()
            if d == None or d4 < d: d = d4
        return d
    def length(self):
        dxy = self.end.position - self.start.position
        return math.sqrt(dxy.dot(dxy))
    def intersection(self, line):
        p1 = self.start
        p2 = line.start
        dir1 = self.direction()
        dir2 = line.direction()
        if dir1.length()==0 or dir2.length()==0:
            return None
        a, b, c, d = dir1.x, -dir2.x, dir1.y, -dir2.y
        D = a*d - b*c
        p = d/D
        q = -b/D
        t = p*(p2.x() - p1.x()) + q*(p2.y() - p1.y())
        dir1b = t*dir1
        c = CvPoint(p1.x() + dir1b.x, p1.y() + dir1b.y)
        return c
    def addPoint(self, p):
        np = len(self.points)
        if np < 2:
            self.end = p
        else:
            vps = p.position - self.start.position
            vpe = p.position - self.end.position
            dir1 = self.direction()
            dps = vps.dot(dir1)
            dpe = vpe.dot(dir1)
            if dps > 0 and dpe > 0: # (s - e) p
                self.end = p
            elif dps > 0 and dpe < 0: # (s p e)
                pass
            elif dps < 0 and dpe < 0: # p (s - e)
                self.start = p
            elif dps < 0 and dpe > 0: # impossible
                logger.debug('This should never happen (dps<0 and dpe>0)')
        self.points.append(p)
    def __str__(self):
        s = 'Line:start=%s,end=%s,length=%d' % \
            (str(self.start), str(self.end), self.length())
        return s

class Vertex:
    def __init__(self, hline=None, vline=None):
        self.hline = hline
        self.vline = vline
        self.point = hline.intersection(vline)
    def getPoint(self):
        return self.point

class Circle:
    def __init__(self):
        self.center = None
        self.radius = 0.0
        self.points = []

class PatternStore:
    def __init__(self):
        self.hpoints = []
        self.hsegments = []
        self.hlines = []
        self.vpoints = []
        self.vsegments = []
        self.vlines = []
        self.scanData = []
        self.target = None
        self.vertices = []
        self.circles = []
        pass
    def xy(self):
        pos = None
        if self.target!=None:
            if type(self.target) == CvLine:
                pos = self.target.center()
        return pos

class PatternSelector:
    def __init__(self, targetString=None):
        self.type = '' # Line, Circle, Vertex
        self.lineAngle = None
        self.radius = None
        self.column = None
        self.row = None
        #
        self.deltaAngleMax = 5.0 # degrees
        self.deltaAngleMax = 5.0 # degrees
        self.distanceMax = 20.0
        if targetString != None:
            self.setTarget(targetString)
        self.targetLine = None
        self.targetCircle = None
        self.targetVertex = None

    def setTarget(self, targetString):
        # LineH,col120,row1222, LineV,col120,row1222, Line45deg,col120,row1222
        # Circle,radius200,col1000,row2020
        # Vertex,col1000,row2020
        words = targetString.split(',')
        if words[0].startswith('Line'):
            self.type = 'Line'
            x = words[0][4:]
            if len(x)==1 and x[0] == 'H':
                self.lineAngle = 0.0
            elif len(x)==1 and x[0] == 'V':
                self.lineAngle = 90.0
            elif x.endswith('deg'):
                a = float(x[0:-3])
                self.lineAngle = a
        elif words[0].startswith('Circle'):
            self.type = 'Circle'
        elif words[0].startswith('Vertex'):
            self.type = 'Vertex'
        else:
            logger.debug('Unknown pattern type %s' % words[0])
            return -1
        # words[1:]
        for word in words[1:]:
            if word.startswith('col'):
                a = int(word[3:])
                self.column = a
            elif word.startswith('row'):
                a = int(word[3:])
                self.row = a
            elif word.startswith('radius'):
                a = float(word[3:])
                self.radius = a
            else:
                pass
    def selectTarget(self, vlines, hlines):
        if self.type == 'Line':
            if abs(self.lineAngle)<30.0:
                hline = self.selectLine(hlines)
                self.targetLine = hline
            else:
                vline = self.selectLine(vlines)
                self.targetLine = vline
        elif self.type == 'Vertex':
            hline = self.selectLine(hlines)
            vline = self.selectLine(vlines)
            pass
        elif self.type == 'Circle':
            pass

    def selectLine(self, lines):
        ref = None
        line = None
        dmin = -1.0
        if self.row!=None and self.column!=None:
            ref = CvPoint(self.column, self.row)
        for x in lines:
            c = x.center()
            dp = -1.0
            if ref:
                dp = ref.distance(c)
            elif self.column != None:
                dp = abs(c.x() - self.column)
            elif self.row != None:
                dp = abs(c.y() - self.row)
            if dmin < 0.0 or dp < dmin:
                dmin = dp
                line = x
        return line
    def selectCircle(self, circles):
        circle = None
        if len(circles):
            circle = circles[0]
        return circle
    def selectVertex(self, vertices):
        vertex = None
        ref = None
        dmin = -1.0
        if self.column!=None and self.row!=None:
            ref = CvPoint(self.column, self.row)
        for x in vertices:
            dp = -1.0
            if ref:
                dp = ref.distance(x)
            elif self.column!=None:
                dp = abs(x.x() - self.column)
            elif self.row!=None:
                dp = abs(x.y() - self.row)
            if dmin < 0.0 and dp < dmin:
                dmin = dp
                vertex = x
            break
        return vertex

def diffArray(v, convvec, wsum):
    n = len(v)
    v2 = np.convolve(v, convvec, mode='valid')/wsum
    #v3 = np.append(np.zeros(wsum*2-1), v2)
    v3 = np.append(np.zeros(wsum), v2)
    return v3

def findGap(v, tgap):
    vabs = np.absolute(v)
    cond = np.less(vabs, tgap)
    vzerosup = np.where(cond, 0.0, vabs)
    peaks = signal.argrelextrema(vzerosup, np.greater)
    return list(peaks[0])

def locateEdgePoints1(img, scanAxis, output, wsum=30, tgap=40, 
                      scanInterval=100, scanWidth=10):
    # Parameters
    w = scanWidth # scan band width
    dp = scanInterval # scan band interval
    #wsum = 30 # With to take the sum in the forward/backward regions
    #tgap = 40 # Threshold to identify a gap (max=255)
    #
    x1 = 0
    n = 0
    nrows, ncols = img.shape[0], img.shape[1]
    points = []
    #
    stepdir = 'xxx'
    if scanAxis == 0:
        stepdir = 'row'
        n = img.shape[1]
    elif scanAxis == 1:
        stepdir = 'column'
        n = img.shape[0]
    else:
        return points
    convdiff = np.array([1]*wsum + [-1]*wsum)
    convgap = [0]
    while x1 < n:
        x2 = x1 + w
        if x1 >= n or x2 >= n: break
        #logger.debug('Subimage at %s %d-%d' % (stepdir, x1, x2) )
        subimage = None
        if scanAxis == 0:
            subimage = img[0:nrows, x1:x2]
            xarray = subimage.sum(axis=1)/w
        elif scanAxis == 1:
            subimage = img[x1:x2, 0:ncols]
            xarray = subimage.sum(axis=0)/w
        #print('image r=%d, c=%d, x1=%d, x2=%d axis=%d' % (nrows, ncols, x1, x2, scanAxis), xarray)
        #print(f'check array shapes {xarray.shape}, {convdiff.shape}')
        v2 = diffArray(xarray, convdiff, wsum)
        v3 = findGap(v2, tgap)
        name1 = 'scan%d_x%d' % (scanAxis, x1)
        name2 = 'scan%d_x%d_diff' % (scanAxis, x1)
        name3 = 'scan%d_x%d_gap' % (scanAxis, x1)
        output[name1] = xarray
        output[name2] = v2
        output[name3] = v3
        if len(v3) > 0:
            c = (x1 + x2)/2.0
            if scanAxis == 0:
                for p in v3:
                    points.append( CvPoint(c, p) )
            elif scanAxis == 1:
                for p in v3:
                    points.append( CvPoint(p, c) )
        pass
        x1 += dp
    return points
    
def locateEdgePoints(img, output, wsum, tgap, scanInterval=100, scanWidth=10):
    # scan along the 0-direction (row)
    logger.debug('Locate edge points interval: {}'.format(scanInterval))
    pointsH = locateEdgePoints1(img, 0, output, wsum, tgap, scanInterval, scanWidth)
    # scan along the 1-direction (column)
    pointsV = locateEdgePoints1(img, 1, output, wsum, tgap, scanInterval, scanWidth)
    return (pointsH, pointsV)

def findEdge(img, wsum=200, tgap=15):
    #return cv2.Canny(img, thr1, thr2)
    output = {}
    points1 = locateEdgePoints1(img, 0, output, wsum=wsum, tgap=tgap)
    points2 = locateEdgePoints1(img, 1, output, wsum=wsum, tgap=tgap)
    if len(points1) > len(points2):
        points = points1
    else:
        points = points2
    return points

def findSegments(points, angle, cosAngleMin=0.99, distanceMax=10, connectDistMax=250.0):
    lines = []
    # param
    distMax = distanceMax
    #
    angleRad = angle*math.pi/180.0
    dir0 = CvVector(math.cos(angleRad), math.sin(angleRad))
    points1 = list(points)
    pindices = list(range(len(points) ) )
    while len(points1)>0:
        p = points1.pop()
        dp = CvPoint(p.x()+dir0.x, p.y()+dir0.y)
        line = CvLine(start=p, end=dp)
        i = 0
        def pdist(x):
            return p.distance(x)
        points1.sort(key=pdist)
        while i < len(points1):
            p2 = points1[i]
            dir1 = line.direction()
            dir2 = p2.position - line.start.position
            dir3 = p2.position - line.end.position
            a1, a2, a3 = dir1.length(), dir2.length(), dir3.length()
            #logger.debug(line, p2)
            #logger.debug('line dir %6.3f, %6.3f' % (dir1.x, dir1.y))
            #logger.debug('line dir2 %6.3f, %6.3f' % (dir2.x, dir2.y))
            #logger.debug('line dir3 %6.3f, %6.3f' % (dir3.x, dir3.y))
            #
            closePoint = False
            angleOk = False
            distOk = False
            if line.distanceTo(p2) < connectDistMax:
                closePoint = True
            if a1 > 0 or a2 > 0:
                cosAngle = dir1.dot(dir2)/(a1*a2)
                cosAngle = abs(cosAngle)
                angleOk = cosAngle > cosAngleMin
            dist = line.distance(p2)
            if dist < distMax:
                distOk = True
            if closePoint and angleOk and dist < distMax:
                # Line(p, p2) compatible with the given angle
                if i == 0:
                    points1 = points1[1:]
                elif i == len(points1)-1:
                    points1 = points1[:-1]
                else:
                    v = points1[0:i] + points1[i+1:]
                    points1 = v
                
                line.addPoint(p2)
            else:
                i += 1
        if len(line.points) >= 3:
            lines.append(line)
    return lines

def findVertices(hlines, vlines, connectDistMin=250):
    v = []
    for x in hlines:
        for y in vlines:
            d = x.distanceToLine(y)
            if d < connectDistMin:
                p = x.intersection(y)
                d1 = p.distance(x.start)
                d2 = p.distance(x.end)
                if d1 < d2:
                    x.startVertex = p
                else:
                    x.endVertex = p
                d1 = p.distance(y.start)
                d2 = p.distance(y.end)
                if d1 < d2:
                    y.startVertex = p
                else:
                    y.endVertex = p
                v.append(p)
    return v

def mergeLines(lines, connectDistMax=500, cosAngleMin=0.99, distanceMax=20):
    lines2 = []
    def openEnd(line):
        return (line.startAtVertex()==False or line.endAtVertex()==False)
    #lines1 = list(filter(openEnd, lines))
    lines1 = list(lines)
    while len(lines1)>0:
        x = lines1[0]
        lines1 = lines1[1:]
        x = copy.copy(x)
        i = 0
        dir1 = x.direction()
        while i < len(lines1):
            y = lines1[i]
            #d = x.distanceToLineForMerge(y)
            d = x.distanceToLine(y)
            dir2 = y.direction()
            k = abs(dir1.dot(dir2))
            dp = min(x.distance(y.center()), y.distance(x.center()))
            if d < connectDistMax and k > cosAngleMin and dp < distanceMax:
                lines1.remove(y)
                #
                xlen = x.length()
                d1 = x.start.distance(y.start)
                d2 = x.end.distance(y.start)
                if d1 < xlen and d2 < xlen:
                    pass
                elif d1 > d2:
                    x.end = y.start
                else:
                    x.start = y.start
                #
                xlen = x.length()
                d1 = x.start.distance(y.end)
                d2 = x.end.distance(y.end)
                if d1 < xlen and d2 < xlen:
                    pass
                elif d1 > d2:
                    x.end = y.end
                else:
                    x.start = y.end
                x.points += y.points
            else:
                i += 1
        lines2.append(x)
    return lines2

def selectLine(lines, cosAngleMin=0.99, distanceMax=250, nPointsOnLine=5):
    line1= None
    return line1

def findCorner(img, target, offset, zoom, params):
    hline = findLine(img, target, offset, zoom, params)
    vline = findLine(img, target, offset, zoom, params)
    vertex = Vertex(hline, vline)
    return vertex

def findCircle(img, target, offset, zoom, params):
    ss = (41, 41)
    dp = params.dp
    minDist = params.minDist
    param1 = params.param1
    param2 = params.param2
    radius = 0
    minR, maxR = 0, 0
    i = target.find('radius')
    if i>=0:
        mg = re.search('radius([\d]+)', target)
        if mg!=None:
            radius = int(mg.group(1))
            minR = int(radius/2)
            maxR = radius*2
    #sigmaX, sigmaY = 20, 20
    circles = findCircle1(img, ss, dp, minDist, param1, param2, minR, maxR)
    return circles

def findCircles(img, ss=(5, 5), dp=1, minDist=50, param1=50, param2=30, 
                minR=50, maxR=1000):
    imgbw = img
    if len(img.shape)==3 and img.shape[2] == 3:
        imgbw = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgblur = cv2.GaussianBlur(imgbw, ksize=ss, sigmaX=5)
    circles = cv2.HoughCircles(imgblur, cv2.HOUGH_GRADIENT, \
                               dp=dp, minDist=minDist, param1=param1, param2=param2, minRadius=minR, maxRadius=maxR)
    logger.debug(circles)
    return circles

def findLineCV(img):#, targetName, offset, zoom, params):
    #targetPos = patternPosition(targetName)
    #targetPosLocal = globalToLocal(targetPos, offset, zoom)
    ss = (201, 201)
    thr1, thr2 = 40, 20
    imgbw = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgblur = cv2.GaussianBlur(img, ksize=ss, sigmaX=20, sigmaY=20)
    imgedge = cv2.Canny(imgblur, thr1, thr2, 3)
    lines = cv2.HoughLinesP(imgedge, rho=1, theta=math.pi/360.0, 
                            threshold=40, minLineLength=80, maxLineGap=5)
    return lines

def findLine(img, targetName, offset, zoom, params):
    targetPos = patternPosition(targetName)
    targetPosLocal = globalToLocal(targetPos, offset, zoom)
    wsum = params['wsum']
    tgap = params['tgap']
    distMax = params['distanceMax']
    connectDistMax = params['connectDistMax']
    cosAngleMin = params['cosAngleMin']
    targetString = params['target']
    #
    nrows = img.shape[0]
    ncols = img.shape[1]

    targetSelector = PatternSelector(targetString)
    target_lineV = False
    target_lineH = False
    target_vertex = False
    target_circle = False

    if targetSelector.type == 'Line':
        if abs(targetSelector.lineAngle)<45.0:
            target_lineH = True
        else:
            target_lineH = True
    data = []

    pointsH, pointsV = [], []
    hlines2, vlines2 = [], []
    vertices = []
    if target_lineH or target_vertex:
        pointsH = locateEdgePoints1(img, 0, data, wsum, tgap)
        hlines = findSegments(pointsH, 0.0, cosAngleMin, distMax, \
                              connectDistMax)
        hlines2 = mergeLines(hlines)
    if target_lineV or target_vertex:
        pointsH = locateEdgePoints1(img, 0, data, wsum, tgap)
        vlines = findSegments(pointsV, 90.0, cosAngleMin, distMax, \
                              connectDistMax)
        vlines2 = mergeLines(vlines)

    if target_vertex:
        vertices = findVertices(hlines2, vlines2, connectDistMax*2)

    
    hline, vline = None, None
    target = None
    if targetSelector.type == 'Line':
        if abs(targetSelector.lineAngle)<20.0:
            hline = targetSelector.selectLine(hlines2)
            target = hline
            if hline:
                logger.debug('Target(%s): %s n=%d' % \
                      (targetString, str(hline), len(hline.points)) )
                logger.debug('Target(%s): NOT FOUND' % targetString)
        else:
            vline = targetSelector.selectLine(vlines2)
            if vline:
                logger.debug('Target(%s): %s n=%d' % \
                      (targetString, str(vline), len(vline.points)) )
            else:
                logger.debug('Target(%s): NOT FOUND' % targetString)
            target = vline
    return target

def patternRec1(img0, targetString, rect=(), 
                wsum=20, tgap=20, cosAngleMin=0.1, 
                distanceMax=10, connectDistMax=250, 
                scanInterval=100, 
                scanWidth=10):
    def shiftPoints(v, c, r):
        for p in v:
            p.shift(c, r)
    def shiftLines(v, c, r, points):
        for p in v:
            p.shift(c, r, points)
        pass
    logger.debug('Rect = %s' % str(rect) )
    logger.debug('scanInterval in patternRec1 {}'.format(scanInterval))
    logger.debug('scanWidth in patternRec1 {}'.format(scanWidth))
    if len(rect) > 0 and len(rect)==4:
        c1, r1, c2, r2 = rect
        logger.debug('Call pattern recognition in the sub-region (%d,%d)-(%d,%d)' %\
              (c1, r1, c2, r2) )
        logger.debug(' image shape: %s' % (str(img0.shape)))
        print(r1, r2, c1, c2)
        print(type(r1), type(r2), type(c1), type(c2))
        imgsub = img0[r1:r2, c1:c2]
        targetSub = ''
        col, row = 0, 0
        words = targetString.split(',')
        for word in words:
            mg1 = re.search('col([\d]+)', word)
            mg2 = re.search('row([\d]+)', word)
            if mg1:
                col = int(mg1.group(1))
                targetSub += 'col%d,' % max(0,col-c1)
            elif mg2:
                row = int(mg2.group(1))
                targetSub += 'row%d,' % max(0,row-r1)
            else:
                targetSub += '%s,' % word
        patterns = patternRec1(imgsub, targetSub, rect=(), 
                               wsum=wsum, tgap=tgap, 
                               cosAngleMin=cosAngleMin, 
                               distanceMax=distanceMax, 
                               connectDistMax=connectDistMax, 
                               scanInterval=scanInterval, 
                               scanWidth=scanWidth)
        shiftPoints(patterns.hpoints, c1, r1)
        shiftPoints(patterns.vpoints, c1, r1)
        try:
            logger.debug('Try to shift circles')
            v = []
            logger.debug('N circles %d' % len(patterns.circles))
            for c in patterns.circles:
                x, y, r = c
                logger.debug('shift circle')
                v.append([x+c1, y+r1, r])
            patterns.circles = v
        except:
            pass
        return patterns
    img1 = img0
    if len(img0.shape)==3 and img0.shape[2] == 3:
        img1 = cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY)
    nrows = img1.shape[0]
    ncols = img1.shape[1]
    #logger.debug('nrows/ncols = %d/%d' % (nrows, ncols) )

    target = PatternSelector(targetString)
    patterns = PatternStore()

    if img1.shape[0] == 0 or img1.shape[1] == 0:
        logger.warning('Image shape %s not enough to find patterns' % str(img1.shape) )
        return patterns

    if target.type == 'Circle':
        logger.debug('Find circles')
        circles = findCircles(img1)
        vcircles = []
        try:
            vcircles = circles[0].astype(int)
        except:
            pass
        patterns.circles = vcircles
    else:
        patterns.circles = []

    data = {}
    logger.debug('Find points interval={}'.format(scanInterval))

    target_lineH = False
    target_lineV = False
    target_vertex = False
    if target.type == 'Line':
        if abs(target.lineAngle)<45.0:
            target_lineH = True
        else:
            target_lineV = True
    elif target.type == 'Vertex':
        target_vertex = True
        
    # Patterns
    hlines, hlines2 = [], []
    vlines, vlines2 = [], []
    pointsH, pointsV = [], []
    vertices = []

    # Horizontal lines
    if target_lineH or target_vertex:
        pointsH = locateEdgePoints1(img1, 0, data, wsum, tgap, scanInterval, scanWidth)
        logger.debug('Find H lines ({0} points)'.format(len(pointsH)) )
        hlines = findSegments(pointsH, 0.0, cosAngleMin, \
                              distanceMax, connectDistMax)
        logger.debug('Merge H lines')
        hlines2 = mergeLines(hlines)

    # Vertical lines
    if target_lineV or target_vertex:
        pointsV = locateEdgePoints1(img1, 1, data, wsum, tgap, scanInterval, scanWidth)
        logger.debug('Find V lines ({0} points)'.format(len(pointsV)) )
        vlines = findSegments(pointsV, 90.0, cosAngleMin, \
                              distanceMax, connectDistMax)
        logger.debug('Merge V lines')
        vlines2 = mergeLines(vlines)

    #logger.debug('Number of points (H): %d, lines: %d' % (len(pointsH), len(hlines)))
    #logger.debug('Number of points (V): %d, lines: %d' % (len(pointsV), len(vlines)))

    if target_vertex:
        logger.debug('Find vertices')
        vertices = findVertices(hlines2, vlines2, connectDistMax*2)
        #logger.debug('%d vertices found' % len(vertices))


    #logger.debug('Number of points after merging(H): %d, lines: %d' % \
    #    (len(pointsH), len(hlines2)))
    #logger.debug('Number of points after merging(V): %d, lines: %d' % \
    #      (len(pointsV), len(vlines2)))
    

    hline, vline = None, None
    if target.type == 'Line':
        if abs(target.lineAngle)<45.0:
            hline = target.selectLine(hlines2)
            patterns.target = hline
        else:
            logger.debug('vlines2 : %d' % len(vlines2))
            vline = target.selectLine(vlines2)
            patterns.target = vline
    elif target.type == 'Vertex':
        hline = target.selectLine(hlines2)
        vline = target.selectLine(vlines2)
        if hline!=None and vline!=None:
            vertex = Vertex(hline, vline)
            patterns.target = vertex
    else:
        pass
    patterns.hpoints = pointsH
    patterns.hsegments = hlines
    patterns.hlines = hlines2
    patterns.vpoints = pointsV
    patterns.vsegments = vlines
    patterns.vlines = vlines2
    patterns.scanData = data
    patterns.vertices = vertices
    return patterns

def precScanPoint(sp):
    target = None
    logger.debug('  Analyzing file {}'.format(sp.imgFile) )
    if sp.imgFile!=None and os.path.exists(sp.imgFile):
        img = cv2.imread(sp.imgFile, cv2.IMREAD_COLOR)
        target = patternRec1(img, 'LineH', tgap=50)
    return target

def precScanPoints(spoints):
    logger.debug('Find patterns for {0} images'.format(len(spoints) ) )
    for p in spoints:
        target = precScanPoint(p)
        if target != None:
            p.targetXY = target
            logger.debug(target)

class ImageFrame:
    def __init__(self, offset, zoom=20, width=6000, height=4000):
        global dx20
        self.offset = offset
        self.pixelSize = pixelSizeForZoom(zoom)
        self.width = width
        self.height = height

    def setSize(self, width, height, xlength, ylength):
        self.width = width
        self.height = height
        self.pixelSize = float(xlength)/width
        
    def toGlobal(self, cr):
        c, r = cr[0], cr[1]
        x = self.offset[0] + (c-self.width/2)*self.pixelSize
        y = self.offset[1] - (r-self.height/2)*self.pixelSize
        p = CvPoint(x, y)
        return p

    def toCR(self, point):
        p = (point - self.offset).position/self.pixelSize
        c = int(p[0] + self.width/2)
        r = int(self.height/2 - p[1])
        return CvPoint(c, r)
    
    def trimCR(self, colRow):
        cr = [colRow[0], colRow[1]]
        if cr[0] < 0:
            cr[0] = 0
        elif cr[0] >= self.width:
            cr[0] = self.width - 1
        if cr[1] < 0:
            cr[1] = 0
        elif cr[1] >= self.height:
            cr[1] = self.height - 1
        return cr
    def toPixels(self, length_mm):
        np = int(length_mm/self.pixelSize)
        return np

class ImageAnalyzer:
    def __init__(self):
        pass
        
