#-----------------------------------------------------------------------
# pmm: fittools.py
#-----------------------------------------------------------------------
import os, sys
import argparse
import re
from functools import partial
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import linalg
from mpl_toolkits.mplot3d import axes3d
from scipy.stats import norm
import tkinter as tk
from PIL import Image, ImageTk
import logging

from .model import *
from .reader import *
from .view import *
from .gui import *
from .acommon import *
from .data2 import ImageNP, ScanData

logger = logging.getLogger(__name__)

class Shape:
    def __init__(self):
        self.parameters = []
        self.pressures = [0.0]*100
        self.parametersUpdated = False
        pass

    def initialValue(self, points):
        pass

    def distance(self, points):
        v = list(map(lambda p: self.distanceP(p), points))
        d = 1.0E+6
        if len(v)>0:
            d = min(v)
        logger.debug(f'Distance to generic shape {len(v)} points -> {d}')
        return d
    
    def dircheck(self, p, vref, cosThetaCut):
        pp = np.array( (p[0]-self.cx, p[1]-self.cy) )
        pp /= math.sqrt(pp.dot(pp))
        #logger.debug(f'  dircheck pp={pp} innerProduct={vref.dot(pp)}')
        return vref.dot(pp) > cosThetaCut
    
    def updatePressures(self, points):
        n = len(self.pressures)
        dtheta = 2.0*math.pi/n
        dcos = math.cos(dtheta/2.0)
        logger.debug(f'  Update pressures from {len(points)} points')
        for i in range(n):
            theta = (i+0.5)*dtheta
            thetavec = np.array( (math.cos(theta), math.sin(theta)) )
            func = partial(self.dircheck, vref=thetavec, cosThetaCut=dcos)
            plist = list(filter(func, points))
            if len(plist)>0:
                logger.debug(f'    Angle [{i}]->{theta}, npoints={len(plist)}')
            self.pressures[i] = len(plist)
        self.parametersUpdated = False

    def pressureBalanced(self, points, npcut=1):
        if self.parametersUpdated:
            self.updatePressures(points)
        n = len(self.pressures)
        n1 = int(n/8)
        n2 = int(n/4)
        n3 = n1*3
        logger.debug(f'Pressure list: {self.pressures}')
        imbalance = False
        for i, npoints in enumerate(self.pressures):
            if npoints >= npcut:
                imb = True
                logger.debug(f'check pressure balance for i={i}')
                for j in range(0, n2):
                    k = (i+n3+j)%n
                    if self.pressures[k] >= npcut:
                        imb = False
                        logger.debug(f'  found balancing pressure at {k}')
                        break
                if imb:
                    logger.debug(f'  no balancing pressure was found')
                    imbalance = True
                    break
        nsegments = len(list(filter(lambda x: x>=npcut, self.pressures)))
        return ( (not imbalance), nsegments)
    
    def pressureDirection(self, points, npcut=1):
        if self.parametersUpdated:
            self.updatePressures(points)
        v = np.zeros( (2) )
        n = len(self.pressures)
        dtheta = 2.0*math.pi/n
        for i, npoints in enumerate(self.pressures):
            if npoints >= npcut:
                theta = (i+0.5)*dtheta
                logger.debug(f'Pressure from theta={theta}')
                v -= [math.cos(theta), math.sin(theta)]
        logger.debug(f'  pressure vector: {v}')
        v /= np.sqrt(v.dot(v))
        return v
    
    def radius(self):
        return 1.0

    def distanceP(self, point):
        return 0.0
    
    def expand(self, scale):
        self.parametersUpdated = True
        pass
    
    def expandTo(self, d):
        self.parametersUpdated = True
        pass
    
    def expandBy(self, d):
        self.parametersUpdated = True
        pass
    
    def shrink(self, scale):
        self.parametersUpdated = True
        pass

    def shrinkTo(self, d):
        self.parametersUpdated = True
        pass

    def shrinkBy(self, d):
        self.parametersUpdated = True
        pass

    def moveBy(self, dx):
        self.parametersUpdated = True
        pass

    def innerPoints(self, points):
        inpoints = list(filter(lambda p: p.distanceP(p)<0.0, points))
        return inpoints

    def resize(self, points, resolution=0.0):
        pass
    
    def nearByPoints(self, points, dcut=1.0):
        v = list(filter(lambda p: self.distanceP(p)<dcut, points))
        return v
    
    def fit(self, points):
        pass

    def draw(self, canvas, frame):
        pass
    
class Circle1(Shape):
    def __init__(self, parameters=[]):
        super().__init__()
        self.cx = 0.0
        self.cy = 0.0
        self.r = 0.0
        if len(parameters) == 3:
            self.cx = parameters[0]
            self.cy = parameters[1]
            self.r = parameters[2]
        pass
    
    def radius(self):
        return self.r

    def initialValue(self, points):
        n = len(points)
        self.cx = sum(map(lambda xy: xy[0], points))/n
        self.cy = sum(map(lambda xy: xy[1], points))/n
        self.r = 0.1
        pass

    def distanceP(self, point):
        d = math.sqrt( (point[0]-self.cx)**2 + (point[1]-self.cy)**2) - self.r
        return d
    
    def distance(self, points):
        n = len(points)
        d = -1
        if n>0:
            vc = np.array([self.cx, self.cy]*n).reshape(n, 2)
            vdiff = points-vc
            vdistance = np.sqrt(vdiff[:,0]**2 + vdiff[:,1]**2)
            d = np.min(vdistance)
        return d
    
    def expand(self, scale):
        self.r *= scale
        self.parametersUpdated = True
    
    def expandTo(self, d):
        self.r = d
        self.parametersUpdated = True
    
    def expandBy(self, d):
        #logger.debug(f'   ExpandBy r={self.r} {type(self.r)} {type(d)}')
        self.r = self.r + d
        #logger.debug(f'   ExpandBy after r={self.r}')
        self.parametersUpdated = True
    
    def shrink(self, scale):
        self.r *= scale
        self.parametersUpdated = True

    def shrinkTo(self, d):
        self.r = d
        self.parametersUpdated = True

    def shrinkBy(self, d):
        self.r -= d
        self.parametersUpdated = True

    def resize(self, points, resolution=0.0):
        if len(points)==0:
            return
        d = self.distance(points)
        if d < 0.0:
            self.shrinkBy(-d)
        else:
            self.expandTo(d)
        self.parametersUpdated = True

    def moveBy(self, dx):
        self.cx += dx[0]
        self.cy += dx[1]
        self.parametersUpdated = True

    def fit(self, points):
        pass

    def draw(self, canvas, frame):
        logger.debug(f'Overlay shape: xy=({self.cx},{self.cy}), r={self.r}')
        cr = frame.xyToCR( (self.cx, self.cy))
        r = frame.toPixelLength(self.r)
        color1 = (100, 200, 100)
        cv2.circle(canvas, center=cr, radius=r, color=color1,
                   thickness=2, lineType=8)
        cv2.circle(canvas, center=cr, radius=7, color=color1, thickness=-1)

class LongCircle(Shape):
    def __init__(self, parameters=[]):
        super().__init__()
        self.cx = 0.0
        self.cy = 0.0
        self.r = 0.0
        self.l = 0.0
        self.alpha = 0.0
        if len(parameters) == 5:
            self.cx = parameters[0]
            self.cy = parameters[1]
            self.r = parameters[2]
            self.l = parameters[3]
            self.alpha = parameters[4]
        pass
    
    def initialValue(self, points):
        n = len(points)
        self.cx = sum(map(lambda xy: xy[0], points))/n
        self.cy = sum(map(lambda xy: xy[1], points))/n
        self.r = 0.1
        self.l = 1.0
        self.alpha = -math.pi/4
        pass

    def radius(self):
        return self.r

    def width(self):
        return 2.0*self.r
    
    def centerCircleL(self):
        cx1 = self.cx - 0.5*self.l*math.cos(self.alpha)
        cy1 = self.cy - 0.5*self.l*math.sin(self.alpha)
        return (cx1, cy1)
    
    def centerCircleR(self):
        cx1 = self.cx + 0.5*self.l*math.cos(self.alpha)
        cy1 = self.cy + 0.5*self.l*math.sin(self.alpha)
        return (cx1, cy1)
    
    def selectorForSubShape(self, subShape):
        theta = 0.0
        dtheta = 0.0
        beta = math.atan2(self.r, self.l/2.0)
        #logger.debug(f'r={self.r}, l/2={self.l/2}')
        if subShape == 'CircleL':
            theta = math.pi + self.alpha
            dtheta = beta
        elif subShape == 'CircleR':
            theta = self.alpha
            dtheta = beta
        elif subShape == 'LineT':
            theta = math.pi/2.0 + self.alpha
            dtheta = math.pi/2.0 - beta
        elif subShape == 'LineB':
            theta = -math.pi/2.0 + self.alpha
            dtheta = math.pi/2.0 - beta
        vref = np.array( (math.cos(theta), math.sin(theta) ) )
        cosThetaCut = math.cos(dtheta)
        #logger.debug(f'Selector for {subShape} theta={theta}, cosThetaCut={cosThetaCut} beta={beta}')
        selector = partial(self.dircheck, vref=vref, cosThetaCut=cosThetaCut)
        return selector

    def selectPoints(self, points, subShape):
        selector = self.selectorForSubShape(subShape)
        v = list(filter(selector, points))
        logger.debug(f'  Selected {len(v)} points around {subShape}')
        return v
    
    def distanceP_circleL(self, point):
        d = 1.0E+6
        selector = self.selectorForSubShape('CircleL')
        #logger.debug(f'selector for CircleL point={point}')
        if selector(point):
            cA = self.centerCircleL()
            d = math.sqrt( (point[0]-cA[0])**2 + (point[1]-cA[1])**2) - self.r
            #logger.debug(f'Selector succeeded {cA} {d}')
        else:
            #logger.debug('Selector failed')
            pass
        return d

    def distanceP_circleR(self, point):
        d = 1.0E+6
        selector = self.selectorForSubShape('CircleR')
        if selector(point):
            cA = self.centerCircleR()
            d = math.sqrt( (point[0]-cA[0])**2 + (point[1]-cA[1])**2) - self.r
        return d

    def distanceP_lineT(self, point):
        d = 1.0E+6
        selector = self.selectorForSubShape('LineT')
        theta = math.pi/2.0 + self.alpha
        vref = np.array( (math.cos(theta), math.sin(theta)) )
        if selector(point):
            pp = np.array( (point[0]-self.cx, point[1]-self.cy) )
            d = vref.dot(pp) - self.r
        return d

    def distanceP_lineB(self, point):
        d = 1.0E+6
        selector = self.selectorForSubShape('LineB')
        theta = -math.pi/2.0 + self.alpha
        vref = np.array( (math.cos(theta), math.sin(theta)) )
        if selector(point):
            pp = np.array( (point[0]-self.cx, point[1]-self.cy) )
            d = vref.dot(pp) - self.r
        return d

    def distanceP_circle(self, point):
        d1 = self.distanceP_circleL(point)
        d2 = self.distanceP_circleR(point)
        return min(d1, d2)

    def distanceP_line(self, point):
        d1 = self.distanceP_lineT(point)
        d2 = self.distanceP_lineB(point)
        return min(d1, d2)

    def distanceP(self, point):
        d1 = self.distanceP_circle(point)
        d2 = self.distanceP_line(point)
        return min(d1, d2)
    
    def expand(self, scale):
        self.r *= scale
        self.l *= scale
        self.parametersUpdated = True
    
    def expandTo(self, d):
        self.r = d
        self.parametersUpdated = True
    
    def expandBy(self, d):
        self.r += d
        self.parametersUpdated = True
    
    def shrink(self, scale):
        self.r *= scale
        self.l *= scale
        self.parametersUpdated = True

    def shrinkTo(self, d):
        self.r = d
        self.parametersUpdated = True

    def shrinkBy(self, d):
        self.r -= d
        self.parametersUpdated = True

    def resize(self, points, resolution):
        dl, dc = 0.0, 0.0
        pointsLT = self.selectPoints(points, 'LineT')
        pointsLB = self.selectPoints(points, 'LineB')
        pointsL = pointsLT + pointsLB
        if len(pointsL)>0:
            dl = self.distance(pointsL)
        pointsCL = self.selectPoints(points, 'CircleL')
        pointsCR = self.selectPoints(points, 'CircleR')
        pointsC = pointsCL + pointsCR
        if len(pointsC)>0:
            dc = self.distance(pointsC)
        #
        logger.debug(f'LongCircle resizing: dl={dl}, dc={dc}, r={self.r}, l={self.l} alpha={self.alpha}')
        if dc < 0.0 and dc < 0.0:
            if dl < 0.0 and dc < 0.0:
                if dl < dc:
                    logger.info(f'decrease r by {2*resolution}')
                    self.r -= 2*resolution
                elif dc < dl:
                    logger.info(f'decrease l by {2*resolution}')
                    self.l -= 2*resolution
            elif dl < 0.0:
                logger.info(f'decrease r by {2*resolution}')
                self.r -= 2*resolution
            elif dc < 0.0:
                logger.info(f'decrease l by {2*resolution}')
                self.l -= 2*resolution
                pass
        elif dc < 0.0 and dl > 0.0:
            logger.info(f'decrease l by {2*resolution}')
            self.l -= 2*resolution            
        elif dl < 0.0 and dc > 0.0:
            logger.info(f'decrease rby {2*resolution}')
            self.r -= 2*resolution            
        elif dl > 0.0:
            logger.info(f'increase r by {2*resolution}')
            self.r += resolution
        elif dc > 0.0:
            logger.info(f'increase l by {resolution}')
            #self.l += resolution
            pass
        # if dl < 0.0 or dc < 0.0:
        #     if dl < 0.0:
        #         self.r -= resolution
        #     #if dc < 0.0:
        #     #    #self.l -= resolution
        #     logger.debug('Shrink')
        # else:
        #     logger.debug('Expand')
        #     if dl < dc:
        #         logger.debug('Increase r')
        #         self.r += dl/2.0
        #     elif dc < dl:
        #         logger.debug('Increase l')
        #         #self.l += dc/2.0
        logger.debug(f'  -> after resizing: r={self.r}, l={self.l}')
        self.parametersUpdated = True
        
    def moveBy(self, dx):
        self.cx += dx[0]
        self.cy += dx[1]
        self.parametersUpdated = True

    def fit(self, points):
        pass

    def draw(self, canvas, frame):
        logger.debug(f'Overlay LongCircle: xy=({self.cx},{self.cy}), r={self.r}, l={self.l}, alpha={self.alpha}')
        color1 = (100, 200, 100)
        cr = frame.xyToCR( (self.cx, self.cy))
        r = frame.toPixelLength(self.r)
        l = frame.toPixelLength(self.l)
        # Circles
        cx1 = self.cx - 0.5*self.l*math.cos(self.alpha)
        cy1 = self.cy - 0.5*self.l*math.sin(self.alpha)
        cx2 = self.cx + 0.5*self.l*math.cos(self.alpha)
        cy2 = self.cy + 0.5*self.l*math.sin(self.alpha)
        cr1 = frame.xyToCR( (cx1, cy1) )
        cr2 = frame.xyToCR( (cx2, cy2) )
        cv2.circle(canvas, center=cr1, radius=r, color=color1, 
                   thickness=2, lineType=8)
        cv2.circle(canvas, center=cr2, radius=r, color=color1, 
                   thickness=2, lineType=8)
        cv2.circle(canvas, center=cr, radius=7, color=color1, thickness=-1)

        # Lines
        px1 = self.cx - 0.5*self.l*math.cos(self.alpha)-self.r*math.sin(self.alpha)
        py1 = self.cy - 0.5*self.l*math.sin(self.alpha)+self.r*math.cos(self.alpha)
        px2 = self.cx + 0.5*self.l*math.cos(self.alpha)-self.r*math.sin(self.alpha)
        py2 = self.cy + 0.5*self.l*math.sin(self.alpha)+self.r*math.cos(self.alpha)
        px3 = self.cx - 0.5*self.l*math.cos(self.alpha)+self.r*math.sin(self.alpha)
        py3 = self.cy - 0.5*self.l*math.sin(self.alpha)-self.r*math.cos(self.alpha)
        px4 = self.cx + 0.5*self.l*math.cos(self.alpha)+self.r*math.sin(self.alpha)
        py4 = self.cy + 0.5*self.l*math.sin(self.alpha)-self.r*math.cos(self.alpha)
        cr1 = frame.xyToCR( (px1, py1) )
        cr2 = frame.xyToCR( (px2, py2) )
        cv2.line(canvas, cr1, cr2, color=color1, thickness=2)
        cr1 = frame.xyToCR( (px3, py3) )
        cr2 = frame.xyToCR( (px4, py4) )
        cv2.line(canvas, cr1, cr2, color=color1, thickness=2)

class CombinedImageFrame:
    def __init__(self, images, nrows=0, ncolumns=0):
        self.subImages = images
        self.nrows = 1000
        self.ncolumns = 1000
        self.width = 0
        self.height = 0
        self.offset = []
        self.canvas = None
        self.canvasOk = False
        if nrows == 0 and ncolumns == 0:
            self.nrows = 1000
            self.ncolumns = 1000
        else:
            self.nrows = nrows
            self.ncolumns = ncolumns
        self.checkFrame()
        pass

    def pixelSizesXY(self):
        return ( (self.width/self.ncolumns, self.height/self.nrows) )

    def checkFrame(self):
        xmin = min(map(lambda x: x.xyOffset[0]-x.physicalWidth()/2, self.subImages))
        xmax = max(map(lambda x: x.xyOffset[0]+x.physicalWidth()/2, self.subImages))
        ymin = min(map(lambda x: x.xyOffset[1]-x.physicalHeight()/2, self.subImages))
        ymax = max(map(lambda x: x.xyOffset[1]+x.physicalHeight()/2, self.subImages))
        dx = xmax - xmin
        dy = ymax - ymin
        if self.nrows == self.ncolumns:
            if dx > dy:
                ymax += (dx-dy)
            elif dy > dx:
                xmax += (dy-dx)
        self.offset = [ (xmax + xmin)/2.0, (ymax + ymin)/2.0]
        self.width = xmax - xmin
        self.height = ymax - ymin
        logger.debug(f'CombinedImageFrame: ({xmin}:{xmax}, {ymin}:{ymax})')
        logger.debug(f'  width={self.width}, height={self.height}')
        logger.debug(f'  offset={self.offset}')
        logger.debug(f'  ncolumns={self.ncolumns}, nrows={self.nrows}')
        
    def createCanvas(self):
        self.canvas = np.ones( (self.nrows, self.ncolumns, 3), np.uint8)*200
        self.canvasOk = True
        return self.canvas

    def xyToCR(self, xy):
        psizes = self.pixelSizesXY()
        c = int(self.ncolumns/2 + (xy[0]-self.offset[0])/psizes[0])
        r = int(self.nrows/2 - (xy[1]-self.offset[1])/psizes[1])
        return (c, r)

    def crToXY(self, cr):
        psizes = self.pixelSizesXY()
        x = self.offset[0] + (cr[0]-self.ncolumns/2)*psizes[0]
        y = self.offset[1] - (cr[1]-self.nrows/2)*psizes[1]
        return (x, y)

    def toPixelLength(self, l):
        psizes = self.pixelSizesXY()
        return int(l/psizes[0])

    def toGlobalLength(self, l):
        psizes = self.pixelSizesXY()
        return l*psizes[0]
        
    def overlayImages(self, image):
        xmin = image.xyOffset[0] - image.physicalWidth()/2.0
        xmax = image.xyOffset[0] + image.physicalWidth()/2.0
        ymin = image.xyOffset[1] - image.physicalHeight()/2.0
        ymax = image.xyOffset[1] + image.physicalHeight()/2.0
        dx = xmax - xmin
        dy = ymax - ymin
        c1 = int(self.ncolumns/self.width*dx)
        r1 = int(self.nrows/self.height*dy)
        img = image.readImage()
        img = cv2.resize(img, (c1, r1) )
        psizes = self.pixelSizesXY()
        c2 = int(self.ncolumns/2 + (xmin - self.offset[0])/psizes[0])
        r2 = int(self.nrows/2 - (ymax - self.offset[1])/psizes[1])
        logger.debug(f'  image offset={image.xyOffset}')
        logger.debug(f'    superimpose to {r2}:{r2+r1},{c2}:{c2+c1}')
        self.canvas[r2:r2+r1,c2:c2+c1,:] = img

    def overlayPoints(self, points):
        for p in points:
            cr = self.xyToCR(p)
            #logger.debug(f'  p={p} ->  {cr}')
            cv2.circle(self.canvas, center=cr, radius=5, color=(100, 150, 200),
                       thickness=-1)
            
    def overlayShape(self, shape):
        if shape:
            shape.draw(self.canvas, self)
        
    def createImage(self):
        self.createCanvas()
        for x in self.subImages:
            self.overlayImages(x)
        return self.canvas
    
class ShapeFit:
    def __init__(self):
        self.outputDir = '.'
        self.shape = None
        self.imageFrame = None

    def setOutputDir(self, dname):
        self.outputDir = dname

    def setInitialShape(self, shape):
        self.shape = shape
        
    def readLog(self, logname):
        imageXY = {}
        dn = os.path.dirname(logname)
        images = list(filter(lambda x: x.endswith('.jpg'), os.listdir(dn)))
        if os.path.exists(logname):
            re1 = re.compile('Photo at \(([\d+-.]+), ([\d+-.]+)\)')
            re2 = re.compile('file=(.+\.jpg)')
            re1 = re.compile('([\d+-.]+) ([\d+-.]+) ([\d+-.]+)')
            f = open(logname, 'r')
            ip = 0
            for line in f.readlines():
                if len(line)==0 or line[0]=='#': continue
                mg1 = re1.search(line)
                x, y, z = -2.0E+6, -2.0E+6, 0.0
                fname = images[ip]
                if mg1:
                    mm = 0.001
                    x, y = float(mg1.group(1))*mm, -float(mg1.group(2))*mm
                    ip += 1
                if fname!='' and x > -1.0E+6:
                    i = fname.rfind('\\')
                    fname = fname[i+1:]
                    imageXY[fname] = (x, y)
        return imageXY

    def findEdge(self, img, wsum, tgap, thr1=50, thr2=100):
        #return cv2.Canny(img, thr1, thr2)
        output = {}
        points1 = locateEdgePoints1(img, 0, output, wsum=wsum, tgap=tgap)
        points2 = locateEdgePoints1(img, 1, output, wsum=wsum, tgap=tgap)
        if len(points1) > len(points2):
            points = points1
        else:
            points = points2
        return points

    def findEdgePoints(self, wsum=200, tgap=12):
        points = []
        for imageData in self.imageFrame.subImages:
            if type(imageData)!=type(None):
                frame = CombinedImageFrame([imageData], 4000, 6000)
                #points.append(frame.offset)
                #continue
                imgbw = cv2.cvtColor(imageData.image, cv2.COLOR_BGR2GRAY)
                vp = self.findEdge(imgbw, wsum=200, tgap=8)
                vp = list(map(lambda cr: frame.crToXY(cr), vp))
                points.extend(vp)
        return points
    
    def combineImages(self, images):
        self.imageFrame = CombinedImageFrame(images)
        self.imageFrame.createImage()

    def run(self, images, expand=True):
        dr = [0.1, 0.04, 0.01, 0.004, 0.001]
        idr, ndr = 0, len(dr)
        #
        self.combineImages(images)
        points = self.findEdgePoints(wsum=100, tgap=10)
        logger.debug(f'ShapeFit found {len(points)} edge points')
        self.shape.initialValue(points)
        self.imageFrame.overlayPoints(points)
        self.shape.resize(points, dr[idr])
        dc2 = 0.0
        npcutIn = 2
        nsegCut = 3
        for itry in range(200):
            points2 = self.shape.nearByPoints(points, dr[idr])
            self.shape.resize(points2, dr[idr])
            logger.debug(f'  {len(points2)} near-by points')
            balanced, nsegments = self.shape.pressureBalanced(points2)
            if balanced and nsegments >= nsegCut:
                logger.debug(f'Pressure balanced {itry} idr={idr}, stop optimization')
                #self.shape.fit(points2)
                if idr == ndr-1:
                    break
                else:
                    idr += 1
            elif balanced == 2:
                self.shape.shrink(0.9)
            elif nsegments == 0:
                self.shape.expandBy(dr[idr])
            else:
                logger.debug(f'Pressure imbalance {itry} idr={idr}')
                dc = self.shape.pressureDirection(points2)*dr[idr]
                dc1 = np.sqrt(np.sum(dc*dc))
                logger.debug(f'  dc={dc}, dc1={dc1}, dc2={dc2}')
                logger.debug(f'  ShapeFit moveBy {dc}')
                self.shape.moveBy(dc/2.0)
                dc2 = dc1
        logger.info(f'Shape fit finished after {itry} iterations')
        self.imageFrame.overlayShape(self.shape)
        return (self.imageFrame.canvas, self.shape, points2)

class CircleFit:
    def __init__(self):
        self.outputDir = '.'
        pass

    def setOutputDir(self, dname):
        self.outputDir = dname
        
    def readLog(self, logname):
        imageXY = {}
        dn = os.path.dirname(logname)
        images = list(filter(lambda x: x.endswith('.jpg'), os.listdir(dn)))
        if os.path.exists(logname):
            re1 = re.compile('Photo at \(([\d+-.]+), ([\d+-.]+)\)')
            re2 = re.compile('file=(.+\.jpg)')
            re1 = re.compile('([\d+-.]+) ([\d+-.]+) ([\d+-.]+)')
            f = open(logname, 'r')
            ip = 0
            for line in f.readlines():
                if len(line)==0 or line[0]=='#': continue
                mg1 = re1.search(line)
                #mg2 = re2.search(line)
                #fname, x, y = '', -2.0E+6, -2.0E+6
                x, y, z = -2.0E+6, -2.0E+6, 0.0
                fname = images[ip]
                if mg1:
                    mm = 0.001
                    x, y = float(mg1.group(1))*mm, float(mg1.group(2))*mm
                    ip += 1
                #if mg2:
                #    fname = mg2.group(1)
                if fname!='' and x > -1.0E+6:
                    i = fname.rfind('\\')
                    fname = fname[i+1:]
                    imageXY[fname] = (x, y)
        return imageXY
    
    def decodeFileArg(self, fileInfo):
        words = fileInfo.split(',')
        if len(words)==3:
            fname = words[0]
            x = float(words[1])
            y = float(words[2])
            return (fname, x, y)
        else:
            return None
    
    def toGlobal(self, x, y, w, h, w0, BL):
        dw, dh = w0/w, w0/h
        c = int( (x - BL[0])/dw)
        r = int(h - ( (y - BL[1])/dh) )
        return (c, r)

    def toGlobal2(self, x, y, l, w, h, w0, BL):
        dw, dh = w0/w, w0/h
        c = int( (x - BL[0])/dw)
        r = int(h - ( (y - BL[1])/dh) )
        l2 = l/dw
        #print('l=', l, ', dw=', dw, ' => ', l2)
        return (c, r, l2)

    def calcScale(self, w, h, xy):
        w0 = 15.0 # Real physical size
        #x0, y0 = -30.0, -30.0
        x0, y0 = -30.0, 15.0
        
        w1 = dx20*6000 # Physical size of the region in the image
        wp = 600
        hp = 400
        scale = w1/w0
        x, y = xy[0], xy[1]
    
        dw, dh = w0/w, w0/h
        x, y = xy
        c, r = self.toGlobal(x, y, w, h, w0, (x0, y0))
        #c = int( (x - x0)/dw)
        #r = int(h - ( (y - y0)/dh) )
        #print('c, r = ', c, r)
        return (scale, c, r)


    def createCanvas(self, imageFiles, points, circle, imageXY):
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b'
        w, h = 600, 600
        w1 = w
        h1 = w*4000/6000.0
        
        root = tk.Tk()
        root.title('Module area')
        root.geometry('%dx%d' % (w, h))
        
        canvas = tk.Canvas(root, width=w, height=h, background='lightgreen')
        canvas.grid(row=1, column=1)
    
        print(imageFiles)
        print(imageXY)
        
        images = []
        for fn in imageFiles:
            fn1 = fn.replace('_p.png', '.jpg')
            scale, c, r = self.calcScale(w, h, imageXY[fn])
            print('Add image %s' % fn, imageXY[fn])
            img = Image.open(fn)
            img = img.resize( (int(scale*w1), int(scale*h1) ) )
            img = ImageTk.PhotoImage(img)
            images.append(img)
            canvas.create_image(c, r, image=img, anchor=tk.CENTER)
    
        a, b, r = circle
        a, b, r = self.toGlobal2(a, b, r, w=w, h=h, w0=15.0, BL=(-30.0, 15.0))
        canvas.create_oval(a-r, b-r, a+r, b+r, outline='blue', width=2)
        canvas.update()
        canvas.postscript(file="./plot/slot_%s_TL.ps"%figPrefix, colormode='color')
        
        figname = f'bigCircle'
        canvas.postscript(file=f'{figname}.ps', colormode='color')
        os.system(f'convert {figname}.ps {figname}.jpg')
        root.mainloop()
        return canvas
    
    def findEdge(self, img, wsum, tgap, thr1=50, thr2=100):
        #return cv2.Canny(img, thr1, thr2)
        output = {}
        points1 = locateEdgePoints1(img, 0, output, wsum=wsum, tgap=tgap)
        points2 = locateEdgePoints1(img, 1, output, wsum=wsum, tgap=tgap)
        if len(points1) > len(points2):
            points = points1
        else:
            points = points2
        return points
    
    def findCircle(self, points):
        figPrefix='JPFlex30_b_TL'    
        goodPoints1 = []
        goodPoints2 = []
        data1 = []
        data2 = []
        #thr1 = 0.12
        thr1 = 0.5
        thr2 = 0.05
        d1 = 0
        d2 = 0
        
        ###
        pars1 = self.findCircle1(points)
        for i, p in enumerate(points):
            d1_m = (self.distancePointToCircle(*pars1, p))
            d1 = abs(d1_m)
            #print('  Distance from circle to point[%d]=%7.4f' % (i, d1_m) )
            if d1 < thr1:
                goodPoints1.append(p)
                entry1 = d1_m
                data1.append(entry1)
    
        n1 = len(data1)
        #mean1 = statistics.mean(data1)
        #stdev1 = statistics.stdev(data1)
        #print('mean of distance1 = %f'%mean1)
        print('findCircle1: pars1, ', len(goodPoints1))
        print(pars1)
    
        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(points):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
            vx = np.array(vx1)
            vy = np.array(vy1)
            

        pars2 = self.findCircle2(goodPoints1)
        for i, p in enumerate(goodPoints1):
            d2_m = (self.distancePointToCircle(*pars2, p))
            d2 = abs(d2_m)
            #print('  Distance from circle to goodpoint1[%d]=%7.4f' % (i, d2_m) )
            if d2 < thr2:
                goodPoints2.append(p)
                data2.append(d2_m)
    
        n2 = len(data2)
        #mean2 = statistics.mean(data2)
        #stdev2 = statistics.stdev(data2)
        #print('mean of distance2 = %f'%mean2)
        print('pars2')
        print(pars2)
    
        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(goodPoints1):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
            vx = np.array(vx1)
            vy = np.array(vy1)
        
        circle = tuple(pars2)
        return circle
    
    
    def findCircle1(self, points):
        if len(points) == 0:
            return [-27.0, 27.0, 1.5]
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        if num > 0:
            xpos = xsum/num
            ypos = ysum/num
        else:
            xpos, ypos = 0.0, 0.0
        print('xpos, ypos', xpos, ypos)
        pars1 = [xpos, ypos, 1.45]
        pars = [xpos, ypos, 1.45]
        f = [ 0.0, 0.0, 0.0]
        alpha = 0.001
        data = []
        #print('Initial values: ', pars)
        
        for i in range(3):
            f[0] = -self.dCda(pars1[0], pars1[1], pars1[2], points)
            f[1] = -self.dCdb(pars1[0], pars1[1], pars1[2], points)
            f[2] = -self.dCdr(pars1[0], pars1[1], pars1[2], points)
            #print(f)
            fnorm = 0.0
            for k in range(3):
                fnorm += f[k]**2
                fnorm = math.sqrt(fnorm)
            for k in range(3):
                f[k] = f[k]/fnorm
            for k in range(3):
                pars[k] = pars1[k] + alpha*f[k]
                pars[0] = -27.0
                pars[1] = 27.0
                pars[2] = 1.45
                pars1 = pars
                circle = tuple(pars)
                
        print(f'parameters after findCircle1 {pars}')
        return pars
    
    
    def fitStep(self, n, alpha, pars1, points):
        pars, f = [0.0, 0.0, 0.0],  [0.0, 0.0, 0.0]
                        
        for i in range(n):
            f[0] = -self.dCda(pars1[0], pars1[1], pars1[2], points)
            f[1] = -self.dCdb(pars1[0], pars1[1], pars1[2], points)
            f[2] = -self.dCdr(pars1[0], pars1[1], pars1[2], points)
            print(f, len(points))
            fnorm = 0.0
            for k in range(3):
                fnorm += f[k]**2
                fnorm = math.sqrt(fnorm)
            for k in range(3):
                f[k] = f[k]/fnorm
            for k in range(3):
                pars[k] = pars1[k] + alpha*f[k]
            entry1 = pars[0]
            entry2 = pars[1]
            entry3 = pars[2]
            pars1 = pars
       
        return pars
    
    
    def findCircle2(self, points):
        if len(points) == 0:
            return [-27.0, 27.0, 1.5]
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b_TL'
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        if num > 0:
            xpos = xsum/num
            ypos = ysum/num
        else:
            xpos, ypos = 0.0, 0.0
        print('xpos, ypos', xpos, ypos)
        pars1 = [xpos, ypos, 1.5]
        f = [ 0.0, 0.0, 0.0]
            
        print('Initial values: ', pars1, ' N points', len(points))
    
        pars_1= self.fitStep(100, 0.01, pars1, points)
        pars= self.fitStep(100, 0.001, pars_1, points)
        print(f'In findCircle2 pars_1: {pars_1}')
        print(f'In findCircle2 pars: {pars}')
                
        circle = tuple(pars)
        return pars

    def showImage(self, wn, img, points, toShow=True, fout=None):
        img2 = img.copy()
        if points!=None:
            for p in points:
                col = int(p.x())
                row = int(p.y())
                cv2.circle(img2, (col, row), 100, color=(0,0,255), thickness=-1)
        if toShow:
            window = cv2.namedWindow(wn, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(wn, 600, 400)
            cv2.imshow(wn, img2)
            cv2.waitKey(0)
        if fout!=None and fout!='':
            cv2.imwrite(fout, img2)
            
    def extractPoints(self, fn, xy, wsum, tgap):
        img = None
        x, y = xy[0], xy[1]
        if os.path.exists(fn):
            print('Open image %s taken at (%6.3f, %6.3f)' % (fn, x, y) )
            img = cv2.imread(fn, cv2.IMREAD_COLOR)
            img0 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img1 = cv2.GaussianBlur(img0, (5, 5), 0) #11, 11
            points = self.findEdge(img1, wsum, tgap, 10, 15)
        else:
            print('Image path %s does not exist' % fpath)
            return
        
        print('N points: %d' % len(points))
        fn2 = os.path.basename(fn).replace('.jpg', '_p.png')
        self.showImage('Points', img, points, toShow=False, fout=fn2)
        return points
    
    def dCda(self, a, b, r, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            sum3 = 0.0
        for p in points:
            sum3 += (a-p.x())/math.sqrt( (a-p.x())**2 + (b-p.y())**2)
            c = n*a - xsum - r*sum3
        return c
    
    def dCdb(self, a, b, r, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            ysum += p.y()
            sum3 = 0.0
        for p in points:
            sum3 += (b-p.y())/math.sqrt( (a-p.x())**2 + (b-p.y())**2)
            c = n*b - ysum - r*sum3
        return c
    
    def dCdr(self, a, b, r, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        for p in points:
            sum1 += math.sqrt( (a-p.x())**2 + (b-p.y())**2)
            c = n*r - sum1
        return c
    
    def distancePointToCircle(self, a, b, r, point):
        d = (math.sqrt( (a-point.x())**2 + (b-point.y())**2) - r)
        return d

    def run(self, images):        
        bigImage = None
        circle = None
        points = []
        imageFiles = []
        imageXY = {}
    
        dir0 = os.getcwd()
        os.chdir(self.outputDir)

        for i, image in enumerate(images):
            fpath = image.filePath
            x, y = image.xyOffset[0], image.xyOffset[1]
            pointsLocal = self.extractPoints(fpath, (x, y), wsum=200, tgap=12) #tgap
            print(f'local points size: {len(pointsLocal)}')
            frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
            for p in pointsLocal:
                points.append(frame.toGlobal(p))
            fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
            imageFiles.append(fpath2)
            imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')
        circle = self.findCircle(points)

        canvas = self.createCanvas(imageFiles, points, circle, imageXY)
        figname = f'bigCircle'
        #bigImage = ImageNP(figname, os.path.join(os.getcwd(), f'figname.pdf'))        
        #bigImage = ImageNP(figname, os.path.join(moduleDir, figname+'.jpg'))
        bigImage = ImageNP(figname, os.path.join(os.getcwd(), figname+'.jpg'))
        os.chdir(dir0)
        
        return (bigImage, circle, points)


class SlotFit:
    def __init__(self):
        self.outputDir = '.'
        pass

    def setOutputDir(self, dname):
        self.outputDir = dname

    def decodeFileArg(self, fileInfo):
        words = fileInfo.split(',')
        if len(words)==3:
            fname = words[0]
            x = float(words[1])
            y = float(words[2])
            return (fname, x, y)
        else:
            return None

    def toGlobal2(self, x, y, cr, sl1, sl2, sl3, theta, w, h, w0, BL):
        dw, dh = w0/w, w0/h
        c = int( (x - BL[0])/dw)
        r = int(h - ( (y - BL[1])/dh) )
        l2 = cr/dw
        l3 = sl1/dw
        l4 = sl2/dw
        l5 = sl3/dw
        print('l2=', l2, ', dw=', dw, ' => ', l3)
        return (c, r, l2, l3, l4, l5)

    def calcScale(self, w, h, xy):
        w0 = 15.0 # Real physical size
        x0, y0 = 15.0, -30.0
        
        w1 = dx20*6000 # Physical size of the region in the image
        wp = 600
        hp = 400
        scale = w1/w0
        x, y = xy[0], xy[1]
        
        dw, dh = w0/w, w0/h
        x, y = xy
        c, r = CircleFit().toGlobal(x, y, w, h, w0, (x0, y0))

        print('c, r = ', c, r)
        return (scale, c, r)

    def createCanvas(self, imageFiles, points, circle, imageXY):
        #title=args.FlexNumber
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b_BR'
        w, h = 600, 600
        w1 = w
        h1 = w*4000/6000.0
        l3 = 0
        
        root = tk.Tk()
        root.title('Module area')
        root.geometry('%dx%d' % (w, h))
        
        canvas = tk.Canvas(root, width=w, height=h, background='lightgreen')
        canvas.grid(row=1, column=1)
        
        images = []
        for fn in imageFiles:
            fn1 = fn.replace('_p.png', '.jpg')
            scale, c, r = self.calcScale(w, h, imageXY[fn])
            print('Add image %s' % fn, imageXY[fn])
            img = Image.open(fn)
            img = img.resize( (int(scale*w1), int(scale*h1) ) )
            img = ImageTk.PhotoImage(img)
            images.append(img)
            canvas.create_image(c, r, image=img, anchor=tk.CENTER)

        a, b, r, l1, l2, theta = circle
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        a, b, r, l1, l2, l3 = self.toGlobal2(a, b, r, l1, l2, l3, theta=3*math.pi/4, w=w, h=h, w0=15.0, BL=(15.0, -30.0))
        
        canvas.create_oval(a-r-l2*math.cos(theta)/2, b-r+l2*math.sin(theta)/2, a+r-l2*math.cos(theta)/2, b+r+l2*math.sin(theta)/2, outline='blue', width=2)
        canvas.create_oval(a-r+l2*math.cos(theta)/2, b-r-l2*math.sin(theta)/2, a+r+l2*math.cos(theta)/2, b+r-l2*math.sin(theta)/2, outline='cyan', width=2)
        canvas.create_line(a-l1*math.cos(theta)/2+l3/2*math.sin(theta), b+l1*math.sin(theta)/2+l3/2*math.cos(theta), a+l1*math.cos(theta)/2+l3/2*math.sin(theta), b-l1*math.sin(theta)/2+l3/2*math.cos(theta), fill='green', width=2)
        canvas.create_line(a-l1*math.cos(theta)/2-l3/2*math.sin(theta), b+l1*math.sin(theta)/2-l3/2*math.cos(theta), a+l1*math.cos(theta)/2-l3/2*math.sin(theta), b-l1*math.sin(theta)/2-l3/2*math.cos(theta), fill='orange', width=2)
        
        canvas.update()
        canvas.postscript(file="./plot/slot_%s_BR.ps"%figPrefix, colormode='color')
        
        figname = f'bigSlot'
        canvas.postscript(file=f'{figname}.ps', colormode='color')
        os.system(f'convert {figname}.ps {figname}.jpg')
        root.mainloop()
        
        return images, circle

    
    def findCircle(self, points):
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b_BR'
        goodPoints1, goodPoints2, goodPoints3 = [], [], []
        data1, data2, data3 = [], [], []
        #thr1 = 0.22
        thr1 = 1.0
        thr2 = 0.80 #7
        thr3 = 0.5 #5
        d1, d2, d3 = 0, 0, 0
        
        ###
        pars1 = self.findCircle1(points)
        d1_dC1, d1_dC2, d1_dL1, d1_dL2 = [], [], [], []
        for i, p in enumerate(points):
            d1_m, pos1 = self.distancePointToCircle(*pars1, p)
            d1 = abs(d1_m)
            #print(pos1)
            #print('  Distance from circle to point[%d]=%7.4f' % (i, d1_m) )
            if d1 < thr1:
                goodPoints1.append(p)
            entry1 = d1_m
            if (pos1 == 'dC1'):
                d1_dC1.append(d1_m)
            elif (pos1 == 'dC2'):
                d1_dC2.append(d1_m)
            elif (pos1 == 'dL1'):
                d1_dL1.append(d1_m)
            else:
                d1_dL2.append(d1_m)
            data1.append(entry1)

        n1 = len(data1)
        #mean1 = statistics.mean(data1)
        #stdev1 = statistics.stdev(data1)
        #print('mean of distance1 = %f'%mean1)
        print('pars1')
        print(pars1)

        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(points):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
        vx = np.array(vx1)
        vy = np.array(vy1)

        ###
        pars2 = self.findCircle2(goodPoints1)
        d2_dC1, d2_dC2, d2_dL1, d2_dL2 = [], [], [], []
        
        for i, p in enumerate(goodPoints1):
            d2_m, pos2 = (self.distancePointToCircle(*pars2, p))
            d2 = abs(d2_m)
            #print(pos2)
            #print('  Distance from circle to goodpoint1[%d]=%7.4f' % (i, d2_m) )
            if d2 < thr2:
                goodPoints2.append(p)
            if (pos2 == 'dC1'):
                d2_dC1.append(d2_m)
            elif (pos2 == 'dC2'):
                d2_dC2.append(d2_m)
            elif (pos2 == 'dL1'):
                d2_dL1.append(d2_m)
            else:
                d2_dL2.append(d2_m)
            data2.append(d2_m)
            
        n2 = len(data2)
        #mean2 = statistics.mean(data2)
        #stdev2 = statistics.stdev(data2)
        #print('mean of distance2 = %f'%mean2)
        print('pars2')
        print(pars2)
        
        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(goodPoints1):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
        vx = np.array(vx1)
        vy = np.array(vy1)
    
        ###
        pars3 = self.findCircle2(goodPoints2)
        d3_dC1, d3_dC2, d3_dL1, d3_dL2 = [], [], [], []
    
        for i, p in enumerate(goodPoints2):
            d3_m, pos3 = self.distancePointToCircle(*pars3, p)
            d3 = abs(d3_m)
            print(pos3)
            print('  Distance from circle to goodpoint2[%d]=%7.4f' % (i, d3_m) )
            if d3 < thr3:
                goodPoints3.append(p)
            if (pos3 == 'dC1'):
                d3_dC1.append(d3_m)
            elif (pos3 == 'dC2'):
                d3_dC2.append(d3_m)
            elif (pos3 == 'dL1'):
                d3_dL1.append(d3_m)
            else:
                d3_dL2.append(d3_m)
            data3.append(d3_m)
    
        n3 = len(data3)
        #mean3 = statistics.mean(data3)
        #stdev3 = statistics.stdev(data3)
        #print('mean of distance3 = %f'%mean3)
        print('pars3')
        print(pars3)

        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(goodPoints2):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
        vx = np.array(vx1)
        vy = np.array(vy1)
          
        circle = tuple(pars3)
        return circle
    


    def findCircle1(self, points):
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
                
        pars1 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars2 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars3 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars4 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars1 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars2 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars3 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars4 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        
        f = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        alpha1 = 0.001
        alpha2 = 0.0001
        print('Initial vaues: ', pars)

        for i in range(3):
            f[0] = -self.dC1da(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[1] = -self.dC1db(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[2] = -self.dC1dr(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[3] = 0
            f[4] = -self.dC1dl2(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[5] = -self.dC1dtheta(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            #print(f)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars1[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars1=pars
            
        for i in range(3):
            f[0] = -self.dC2da(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[1] = -self.dC2db(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[2] = -self.dC2dr(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[3] = 0
            f[4] = -self.dC2dl2(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[5] = -self.dC2dtheta(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars2[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars2=pars
               
        
        for i in range(3):
            f[0] = -self.dL1da(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[1] = -self.dL1db(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[2] = 0
            f[3] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[4] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[5] = -self.dL1dtheta(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars3[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars3=pars
        
        
        for i in range(3):
            f[0] = -self.dL2da(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[1] = -self.dL2db(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[2] = 0
            f[3] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[4] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[5] = -self.dL2dtheta(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars4[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars4=pars

        circle = tuple(pars)
        return circle
        
    def fitStep(self, nstep, alpha1, alpha2, pars1, pars2, pars3, pars4, points):
        pars = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        f = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        dataC1, dataC2, dataL1, dataL2 = [], [], [], []
        
        for i in range(nstep):
            f[0] = -self.dC1da(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[1] = -self.dC1db(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[2] = -self.dC1dr(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[3] = 0
            f[4] = -self.dC1dl2(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[5] = -self.dC1dtheta(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars1[k] + alpha2*f[k]
                entryC1 = pars[2]
            dataC1.append(entryC1)
            pars1=pars
            
        for i in range(nstep):
            f[0] = -self.dC2da(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[1] = -self.dC2db(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[2] = -self.dC2dr(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[3] = 0
            f[4] = -self.dC2dl2(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[5] = -self.dC2dtheta(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars2[k] + alpha2*f[k]
                entryC2 = pars[2]
            dataC2.append(entryC2)
            pars2=pars
        
        for i in range(nstep):
            f[0] = -self.dL1da(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[1] = -self.dL1db(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[2] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[3] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[4] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[5] = -self.dL1dtheta(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars3[k] + alpha2*f[k]
            pars3=pars
        
        
        for i in range(nstep):
            f[0] = -self.dL2da(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[1] = -self.dL2db(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[2] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[3] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[4] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[5] = -self.dL2dtheta(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars4[k] + alpha2*f[k]
            pars4=pars

        circle = tuple(pars)
        return pars, circle

    def findCircle2(self, points):
        figPrefix='JPFlex30_b_BR'
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
                
        #pars1 = [27.0, -27.0, 1.58, 1.02, 1.02, 3*math.pi/4]
        pars1 = [xpos, ypos, 1.58, 1.02, 1.02, 3*math.pi/4]
        print('Initial values: ', pars1)
        
        pars_1, circle_1 = self.fitStep(100, 0.01, 0.0001, pars1, pars1, pars1, pars1, points)
        pars, circle = self.fitStep(100, 0.001, 0.0001, pars_1, pars_1, pars_1, pars_1, points)
        #pars, circle = fitStep(10, 0.001, 0.0001, pars1, pars1, pars1, pars1, points)
        
        return circle

    def dC1da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
        sum3 = 0.0
        for p in points:
            sum3 += (a-p.x()+(l2*math.cos(theta)/2))/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = n*a - xsum + n*l2*math.cos(theta)/2- r*sum3
        return c

    def dC1db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            ysum += p.y()
        sum3 = 0.0
        for p in points:
            sum3 += (b-p.y()+(l2*math.sin(theta)/2))/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = n*b - ysum + n*l2*math.sin(theta)/2 - r*sum3
        return c

    def dC1dr(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        for p in points:
            sum1 += math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = n*r - sum1
        return c

    def dC1dl2(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += ((a-p.x())*math.cos(theta)+(b-p.y())*math.sin(theta)+l2/2)/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = -xsum*math.cos(theta) + n*a*math.cos(theta) - ysum*math.sin(theta) + n*b*math.sin(theta) + n*l2/2 - r*sum1
        return c

    def dC1dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += (-(a-p.x())*math.sin(theta)*l2+(b-p.y())*math.cos(theta)*l2)/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = -n*l2*a*math.sin(theta) + l2*math.sin(theta)*xsum + n*l2*b*math.cos(theta) - l2*math.cos(theta)*ysum - r*sum1
        return c

    def dC2da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
        sum3 = 0.0
        for p in points:
            sum3 += (a-p.x()+(-l2*math.cos(theta)/2))/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*a - xsum - n*l2*math.cos(theta)/2- r*sum3
        return c

    def dC2db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            ysum += p.y()
        sum3 = 0.0
        for p in points:
            sum3 += (b-p.y()+(-l2*math.sin(theta)/2))/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*b - ysum - n*l2*math.sin(theta)/2 - r*sum3
        return c

    def dC2dr(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        for p in points:
            sum1 += math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*r - sum1
        return c

    def dC2dl2(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += ((-a+p.x())*math.cos(theta)+(-b+p.y())*math.sin(theta)+l2/2)/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = xsum*math.cos(theta) - n*a*math.cos(theta) + ysum*math.sin(theta) - n*b*math.sin(theta) + n*l2/2 - r*sum1
        return c

    def dC2dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += ((a-p.x())*math.sin(theta)*l2-(b-p.y())*math.cos(theta)*l2)/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*l2*a*math.sin(theta) - l2*math.sin(theta)*xsum - n*l2*b*math.cos(theta) + l2*math.cos(theta)*ysum - r*sum1
        return c

    def dL1da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.sin(theta)*math.cos(theta)*ysum + math.sin(theta)*math.sin(theta)*xsum - n*a*math.sin(theta)*math.sin(theta) + n*b*math.sin(theta)*math.cos(theta) - n*l3/2*math.sin(theta)
        return c

    def dL1db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.cos(theta)*math.cos(theta)*ysum + math.sin(theta)*math.cos(theta)*xsum - n*a*math.cos(theta)*math.sin(theta) + n*b*math.cos(theta)*math.cos(theta) - n*l3/2*math.cos(theta)
        return c

    def dL1dl3(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = math.sin(theta)*xsum - math.cos(theta)*ysum - n*a*math.sin(theta) + n*b*math.cos(theta) - n*l3/2
        return c

    def dL1dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        for p in points:
            sum1 += (-math.cos(theta)*p.y()+math.sin(theta)*p.x()-a*math.sin(theta)+b*math.cos(theta)-l3/2)*(math.sin(theta)*p.y()+math.cos(theta)*p.x()-a*math.cos(theta)-b*math.sin(theta))
        c = sum1
        return c

    def dL2da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.sin(theta)*math.cos(theta)*ysum + math.sin(theta)*math.sin(theta)*xsum - n*a*math.sin(theta)*math.sin(theta) + n*b*math.sin(theta)*math.cos(theta) + n*l3/2*math.sin(theta)
        return c

    def dL2db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.cos(theta)*math.cos(theta)*ysum + math.sin(theta)*math.cos(theta)*xsum - n*a*math.cos(theta)*math.sin(theta) + n*b*math.cos(theta)*math.cos(theta) + n*l3/2*math.cos(theta)
        return c

    def dL2dl3(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.cos(theta)*ysum + math.sin(theta)*xsum - n*a*math.sin(theta) + n*b*math.cos(theta) + n*l3/2
        return c

    def dL2dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        for p in points:
            sum1 += (-math.cos(theta)*p.y()+math.sin(theta)*p.x()-a*math.sin(theta)+b*math.cos(theta)+l3/2)*(math.sin(theta)*p.y()+math.cos(theta)*p.x()-a*math.cos(theta)-b*math.sin(theta))
        c = sum1
        return c


    def distancePointToCircle(self, a, b, r, l1, l2, theta, point):
        data = []
        d = 0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        dC1 = abs(math.sqrt( (a+l2*math.cos(theta)/2-point.x())**2 + (b+l2*math.sin(theta)/2-point.y())**2) - r)
        dC2 = abs(math.sqrt( (a-l2*math.cos(theta)/2-point.x())**2 + (b-l2*math.sin(theta)/2-point.y())**2) - r)
        dL1 = abs((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) - l3/2))
        dL2 = abs((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) + l3/2))
        v1 = np.array([math.cos(theta), math.sin(theta)])
        X = np.array([point.x(), point.y()])
        C1 = np.array([a, b])+np.array([l2*math.cos(theta)/2, l2*math.sin(theta)/2])
        C2 = np.array([a, b])-np.array([l2*math.cos(theta)/2, l2*math.sin(theta)/2])
    
        if np.dot(v1, (X-C1))<=0:
            dC1 = 100
        if np.dot(v1, (X-C2))>=0:
            dC2 = 100
            
        if (min(dC1, dC2, dL1, dL2) == dC1):
            d =  (math.sqrt( (a+l2*math.cos(theta)/2-point.x())**2 + (b+l2*math.sin(theta)/2-point.y())**2) - r)
            pos = 'dC1'
        elif (min(dC1, dC2, dL1, dL2) == dC2):
            d =  (math.sqrt( (a-l2*math.cos(theta)/2-point.x())**2 + (b-l2*math.sin(theta)/2-point.y())**2) - r)
            pos = 'dC2'
        elif (min(dC1, dC2, dL1, dL2) == dL1):
            d = ((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) - l3/2))
            pos = 'dL1'
        else:
            d = - ((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) + l3/2))
            pos = 'dL2'
            
        entry = d, pos
        data.append(entry)
        return d, pos

    def run(self, images):        
        bigImage = None
        circle = None
        points = []
        imageFiles = []
        imageXY = {}

        moduleDir = getModel().config.moduleDir()
        d0 = os.getcwd()
        if not moduleDir.startswith('/'):
            moduleDir = os.path.join(d0, moduleDir)
        os.chdir(moduleDir)
        
        for i, image in enumerate(images):
            fpath = image.filePath
            x, y = image.xyOffset[0], image.xyOffset[1]
            pointsLocal = CircleFit().extractPoints(fpath, (x, y), wsum=200, tgap=12) #tgap 10-20
            print(f'local points size: {len(pointsLocal)}')
            frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
            for p in pointsLocal:
                points.append(frame.toGlobal(p))
            fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
            imageFiles.append(fpath2)
            imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')
        circle = self.findCircle(points)
        
        canvas = self.createCanvas(imageFiles, points, circle, imageXY)
        figname = f'bigSlot'
        bigImage = ImageNP(figname, os.path.join(os.getcwd(), figname+'.jpg'))
        os.chdir(d0)
        
        return (bigImage, circle, points)

