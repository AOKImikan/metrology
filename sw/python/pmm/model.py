#--------------------------------------------------------------------
# Pixel Module Metrology Analysis (Data model)
# 
# Unit: mm
# Module coordinate system: origin at the middle
#                           x (towards right) and y (towards top)
#--------------------------------------------------------------------
import os
import pickle
import math
import logging
import json

from pmm.design import *
from pmm.componentView import *
from pmm.ScanConfigList import *

logger = logging.getLogger()

# Zoom=20
dx20 = (0.39E-3)/2.0
def globalToLocal(p, xc, zoom=20):
    dx = dx20
    if zoom > 0 and zoom != 20:
        dx = dx20 * 20.0/zoom
    c = (p[0] - xc[0])/dx + 3000.0
    r = -(p[1] - xc[1])/dx + 2000.0
    return [ int(c), int(r) ]

def localToGlobal(cr, xc, zoom=20):
    dx = dx20
    if zoom > 0 and zoom != 20:
        dx = dx20 * 20.0/zoom
    x = (cr[0] - 3000)*dx + xc[0]
    y = -(cr[1] - 2000)*dx + xc[1]
    return [x, y]

class Point:
    def __init__(self, pos=[], name=''):
        self.set(pos, name)
        self.oldData = []
    def set(self, pos, name=''):
        self.name = name
        if len(pos) < 2:
            self.valid = False
        else:
            self.valid = True
        self.position = pos
    def update(self, pos):
        p = Point(self.position, self.name)
        self.oldData.append(p)
        self.set(pos, self.name)
    def isValid(self):
        return self.valid
    def __str__(self):
        return f'Point({self.position[0]:6.3f},{self.position[1]:6.3f})'
    def __getitem__(self, i):
        return self.position[i]

class LineMeasurement:
    def __init__(self, data=[]):
        self.data = data
        # Failed to take photo: [name, xc, yc] (only camera position)
        # Failed to find a line: [name, xc, yc, zoom, photo]
        # successful measurement: [name, xc, yc, zoom, photo, x, y, dx, dy]
    def isValid(self):
        s = False
        if len(self.data) > 4:
            s = True
        return s

class CircleMeasurement:
    def __init__(self, data=[]):
        self.data = data
        # Failed to take photo: [xc, yc] (only camera position)
        # Failed to find a circle: [xc, yc, zoom, photo]
        # successful measurement: [xc, yc, zoom, photo, cx, cy, r]
    def isValid(self):
        s = False
        if len(self.data) > 4:
            s = True
        return s

# Line parameterization
class Line:
    def __init__(self):
        # Line: p0 + p1*x + p2*y = 0
        self.p = [0]*3
        self.d = 0.0
        self.theta = 0.0
    def setPars(self, pars):
        for i in range(3):
            self.p[i] = pars[i]
        self.d = pars[0]
        self.theta = pars[1]
    def setParsFromCenterDirection(self, center, direction):
        nx = -direction.y
        ny = direction.x
        n = math.sqrt(nx**2 + ny**2)
        nx /= n
        ny /= n
        cx = center.x()
        cy = center.y()
        pars = [ -(nx*cx + ny*cy), nx, ny ]
        self.setPars(pars)
        
    def distance(self, point):
        d = math.sqrt(self.p[1]**2 + self.p[2]**2)
        x = 0.0
        if d > 0.0:
            x = abs(self.p[0] + self.p[1]*point[0] + self.p[2]*point[1])/d
        return x
    def xAtY(self, y):
        x = 0.0
        num = -(self.p[2]*y + self.p[0])
        den = self.p[1]
        if abs(den)<1.0E-10:
            x = 0.0
        else:
            x = num/den
        return x
    def yAtX(self, x):
        y = 0.0
        num = -(self.p[1]*x + self.p[0])
        den = self.p[2]
        if abs(den)<1.0E-10:
            y = 0.0
        else:
            y = num/den
        return y
    def direction(self):
        n = [ self.p[2], -self.p[1] ]
        if abs(n[0]) > abs(n[1]):
            if n[0] < 0.0:
                n[0] *= -1.0
                n[1] *= -1.0
        else:
            if n[1] < 0.0:
                n[0] *= -1.0
                n[1] *= -1.0
        a = math.sqrt(n[0]**2 + n[1]**2)
        n[0] /= a
        n[1] /= a
        return n
    def angle(self, line2):
        dir1 = self.direction()
        dir2 = line2.direction()
        iprod = dir1[0]*dir2[0] + dir1[1]*dir2[1]
        a1 = math.sqrt(dir1[0]*dir1[0] + dir1[1]*dir1[1])
        a2 = math.sqrt(dir2[0]*dir2[0] + dir2[1]*dir2[1])
        iprod /= (a1*a2)
        angle = math.acos(abs(iprod))
        return angle
    def __str__(self):
        s = 'Line p=(%5.3f, %5.3f, %5.3f)' % (self.p[0], self.p[1], self.p[2])
        return s
    pass

# Plane parameterization
class Plane:
    def __init__(self):
        # Plane: z = dx*x + dy*y + c
        self.c = 0
        self.dx = 0
        self.dy = 0
        self.normalVector = (0.0, 0.0, 0.0)
        self.refPoint = (0.0, 0.0, 0.0)
        self.zmin = 0.0
        self.zmax = 0.0
        self.zmean = 0.0
        self.zsigma = 0.0
    def setPars(self, pars):
        self.c = pars[0]
        self.dx = pars[1]
        self.dy = pars[2]
        nz = 1.0/(1.0 + self.dx**2 + self.dy**2)
        nx = -nz*self.dx
        ny = -nz*self.dy
        self.normalVector = (nx, ny, nz)
        self.refPoint = (0.0, 0.0, self.c)
    def distance(self, point):
        cnz = self.c * self.normalVector[2]
        d = 0.0
        for i in range(3):
            d += self.normalVector[i]*point[i]
        d -= cnz
        return d
    def calculateErrors(self, points):
        dz = list(map(lambda p: self.distance(p), points) )
        n = len(dz)
        self.zmax = max(dz)
        self.zmin = min(dz)
        self.zmean = sum(dz)/n
        z2 = sum(list(map(lambda x: x*x, dz) ) )
        self.zsigma = math.sqrt( (z2 - self.zmean*self.zmean)/n)
    def __str__(self):
        s = 'Plane p=(%5.3f, %5.3f, %5.3f) [z=ax+by+c]' % \
            (self.dx, self.dy, self.c)
        return s
    pass

class SizeResults:
    edgeLocationTypes = (
        'Asic_T', 'Asic_R', 'Asic_B', 'Asic_L', 
        'Sensor_T', 'Sensor_R', 'Sensor_B', 'Sensor_L', 
        'Flex_T', 'Flex_R', 'Flex_B', 'Flex_L', 
    )
    lengthTypes = (
        # Length of various objects
        'AsicWidthT', 'AsicWidthB', 'AsicHeightR', 'AsicHeightL', 
        'SensorWidthT', 'SensorWidthB', 'SensorHeightR', 'SensorHeightL', 
        'FlexWidthT', 'FlexWidthB', 'FlexHeightR', 'FlexHeightL', 
        # Relative positions
        'FlexToAsicTR', 'FlexToAsicTL', 'FlexToAsicBR', 'FlexToAsicBL', 
        'FlexToAsicRT', 'FlexToAsicRB', 'FlexToAsicLT', 'FlexToAsicLB', 
        'FlexToSensorTR', 'FlexToSensorTL', 'FlexToSensorBR', 'FlexToSensorBL', 
        'FlexToSensorRT', 'FlexToSensorRB', 'FlexToSensorLT', 'FlexToSensorLB', 
        'AsicToSensorTR', 'AsicToSensorTL', 'AsicToSensorBR', 'AsicToSensorBL', 
        'AsicToSensorRT', 'AsicToSensorRB', 'AsicToSensorLT', 'AsicToSensorLB', 
        )
    parameterTypes = (
        'AsicWidthMean', 'AsicWidthError', 'AsicHeightMean', 'AsicHeightError', 
        'SensorWidthMean', 'SensorWidthError', 'SensorHeightMean', 'SensorHeightError', 
        'FlexWidthMean', 'FlexWidthError', 'FlexHeightMean', 'FlexHeightError', 
        'FlexToAsicTMean', 'FlexToAsicTError', 'FlexToAsicBMean', 'FlexToAsicBError', 
        'FlexToAsicLMean', 'FlexToAsicLError', 'FlexToAsicRMean', 'FlexToAsicRError', 
        'FlexToSensorTMean', 'FlexToSensorTError', 'FlexToSensorBMean', 'FlexToSensorBError', 
        'FlexToSensorLMean', 'FlexToSensorLError', 'FlexToSensorRMean', 'FlexToSensorRError', 
        'AsicToSensorTMean', 'AsicToSensorTError', 'AsicToSensorBMean', 'AsicToSensorBError', 
        'AsicToSensorLMean', 'AsicToSensorLError', 'AsicToSensorRMean', 'AsicToSensorRError',
        'AngleFlexSensorTL', 'AngleFlexSensorTR', 
        'AngleFlexSensorBL', 'AngleFlexSensorBR', 
    )

    def __init__(self):
        self.measurements = []
        self.pointsAsic = []
        self.pointsSensor = []
        self.pointsFlex = []
        self.pointsOther = []
        # Analysis results
        self.lines = {}
        self.lengthList = {}
        self.parameters = {}
        # Summary info
        
    def addMeasurement(self, data):
        n = len(data)
        allNames = list(map(lambda x: x[0], self.measurements))
        # if len(data)>0 and data[0] not in allNames:
        #     #print('add measurment %s' % data[0], allNames)
        #     if n < 6:
        #         self.measurements.append(data)
        #     else:
        #         a = (data[5], data[6])
        #         dup = False
        #         for m in self.measurements:
        #             if len(m) < 6: continue
        #             p = (m[5], m[6])
        #             dd = math.sqrt( (a[0] - p[0])**2 + (a[1] - p[1])**2)
        #             #print(data[0], dd)
        #             if dd < 1.0E-3:
        #                 dup = True
        #                 break
        #         if not dup:
        #             self.measurements.append(data)
        self.measurements.append(data)
        #print('add measurement %d %s' % (len(data), data[0]) )
        # else:
        #     print('Measurement with name %s already exists' % data[0])
        #     return -1
        p = None
        if n < 4: # [name, x1, y1]
            pass
        elif n < 6: # [name, x1, y1, zoom, photo]
            pass
        else: # [name, x1, y1, zoom, photo, x, y, dx, dy]
            name = data[0]
            x = data[5]
            y = data[6]
            p = Point([x, y, 0.0], name)
        if p:
            upname = p.name.upper()
            if upname.find('ASIC')>=0:
                self.pointsAsic.append(p)
            elif upname.find('SENSOR')>=0:
                self.pointsSensor.append(p)
            elif upname.find('FLEX')>=0:
                self.pointsFlex.append(p)
            else:
                self.pointsOther.append(p)

    def addPoint(self, p):
        name2 = p.name.upper()
        if name2.find('ASIC')>=0:
            self.pointsAsic.append(p)
        elif name2.find('SENSOR')>=0:
            self.pointsSensor.append(p)
        elif name2.find('FLEX')>=0:
            self.pointsFlex.append(p)
        else:
            self.pointsOther.append(p)

    def allPoints(self):
        v = []
        v += self.pointsAsic
        v += self.pointsSensor
        v += self.pointsFlex
        v += self.pointsOther
        return v

    def getPoint(self, name):
        p = None
        for x in self.pointsAsic+self.pointsSensor+self.pointsFlex+self.pointsOther:
            if x.name == name:
                p = x
                break
        return p

    def pointsOnEdge(self, location):
        v = []
        if location in SizeResults.edgeLocationTypes:
            def genfunc(loc):
                def f(x):
                    s = False
                    #print('Compare %s and %s' % (x.name.upper(), loc.upper()))
                    if x.name.upper().find(loc.upper())>=0: s = True
                    return s
                return f
            #
            if location.find('Asic')>=0:
                v = list(filter(genfunc(location), self.pointsAsic))
            elif location.find('Sensor')>=0:
                v = list(filter(genfunc(location), self.pointsSensor))
            elif location.find('Flex')>=0:
                v = list(filter(genfunc(location), self.pointsFlex))
        return v
    def setLine(self, location, line):
        if location in SizeResults.edgeLocationTypes:
            self.lines[location] = line
        pass

    def getLine(self, location):
        line = None
        if location in SizeResults.edgeLocationTypes:
            if location in self.lines.keys():
                line = self.lines[location]
        return line

    def calculateLengths(self):
        lpos, rpos = -20.0, 20.0
        bpos, tpos = -20.0, 20.0
        # Size
        self.setLength('AsicHeightR', self.getLine('Asic_T').yAtX(lpos) - self.getLine('Asic_B').yAtX(lpos))
        self.setLength('AsicHeightL', self.getLine('Asic_T').yAtX(rpos) - self.getLine('Asic_B').yAtX(rpos))
        self.setLength('AsicWidthT', self.getLine('Asic_R').xAtY(tpos) - self.getLine('Asic_L').xAtY(tpos))
        self.setLength('AsicWidthB', self.getLine('Asic_R').xAtY(bpos) - self.getLine('Asic_L').xAtY(bpos))
        #
        self.setLength('SensorHeightR', self.getLine('Sensor_T').yAtX(lpos) - self.getLine('Sensor_B').yAtX(lpos))
        self.setLength('SensorHeightL', self.getLine('Sensor_T').yAtX(rpos) - self.getLine('Sensor_B').yAtX(rpos))
        self.setLength('SensorWidthT', self.getLine('Sensor_R').xAtY(tpos) - self.getLine('Sensor_L').xAtY(tpos))
        self.setLength('SensorWidthB', self.getLine('Sensor_R').xAtY(bpos) - self.getLine('Sensor_L').xAtY(bpos))
        #
        self.setLength('FlexHeightR', self.getLine('Flex_T').yAtX(lpos) - self.getLine('Flex_B').yAtX(lpos))
        self.setLength('FlexHeightL', self.getLine('Flex_T').yAtX(rpos) - self.getLine('Flex_B').yAtX(rpos))
        self.setLength('FlexWidthT', self.getLine('Flex_R').xAtY(tpos) - self.getLine('Flex_L').xAtY(tpos))
        self.setLength('FlexWidthB', self.getLine('Flex_R').xAtY(bpos) - self.getLine('Flex_L').xAtY(bpos))
        # Relative positions
        self.setLength('FlexToAsicTR', self.getLine('Flex_T').yAtX(rpos) - self.getLine('Asic_T').yAtX(rpos))
        self.setLength('FlexToAsicTL', self.getLine('Flex_T').yAtX(lpos) - self.getLine('Asic_T').yAtX(lpos))
        self.setLength('FlexToAsicBR', self.getLine('Flex_B').yAtX(rpos) - self.getLine('Asic_B').yAtX(rpos))
        self.setLength('FlexToAsicBL', self.getLine('Flex_B').yAtX(lpos) - self.getLine('Asic_B').yAtX(lpos))
        self.setLength('FlexToAsicLT', self.getLine('Flex_L').xAtY(tpos) - self.getLine('Asic_L').xAtY(tpos))
        self.setLength('FlexToAsicLB', self.getLine('Flex_L').xAtY(bpos) - self.getLine('Asic_L').xAtY(bpos))
        self.setLength('FlexToAsicRT', self.getLine('Flex_R').xAtY(tpos) - self.getLine('Asic_R').xAtY(tpos))
        self.setLength('FlexToAsicRB', self.getLine('Flex_R').xAtY(bpos) - self.getLine('Asic_R').xAtY(bpos))
        #
        self.setLength('FlexToSensorTR', self.getLine('Flex_T').yAtX(rpos) - self.getLine('Sensor_T').yAtX(rpos))
        self.setLength('FlexToSensorTL', self.getLine('Flex_T').yAtX(lpos) - self.getLine('Sensor_T').yAtX(lpos))
        self.setLength('FlexToSensorBR', self.getLine('Flex_B').yAtX(rpos) - self.getLine('Sensor_B').yAtX(rpos))
        self.setLength('FlexToSensorBL', self.getLine('Flex_B').yAtX(lpos) - self.getLine('Sensor_B').yAtX(lpos))
        self.setLength('FlexToSensorLT', self.getLine('Flex_L').xAtY(tpos) - self.getLine('Sensor_L').xAtY(tpos))
        self.setLength('FlexToSensorLB', self.getLine('Flex_L').xAtY(bpos) - self.getLine('Sensor_L').xAtY(bpos))
        self.setLength('FlexToSensorRT', self.getLine('Flex_R').xAtY(tpos) - self.getLine('Sensor_R').xAtY(tpos))
        self.setLength('FlexToSensorRB', self.getLine('Flex_R').xAtY(bpos) - self.getLine('Sensor_R').xAtY(bpos))
        #
        self.setLength('AsicToSensorTR', self.getLine('Asic_T').yAtX(rpos) - self.getLine('Sensor_T').yAtX(rpos))
        self.setLength('AsicToSensorTL', self.getLine('Asic_T').yAtX(lpos) - self.getLine('Sensor_T').yAtX(lpos))
        self.setLength('AsicToSensorBR', self.getLine('Asic_B').yAtX(rpos) - self.getLine('Sensor_B').yAtX(rpos))
        self.setLength('AsicToSensorBL', self.getLine('Asic_B').yAtX(lpos) - self.getLine('Sensor_B').yAtX(lpos))
        self.setLength('AsicToSensorLT', self.getLine('Asic_L').xAtY(tpos) - self.getLine('Sensor_L').xAtY(tpos))
        self.setLength('AsicToSensorLB', self.getLine('Asic_L').xAtY(bpos) - self.getLine('Sensor_L').xAtY(bpos))
        self.setLength('AsicToSensorRT', self.getLine('Asic_R').xAtY(tpos) - self.getLine('Sensor_R').xAtY(tpos))
        self.setLength('AsicToSensorRB', self.getLine('Asic_R').xAtY(bpos) - self.getLine('Sensor_R').xAtY(bpos))
        #
        self.calculateParameters()

    def setLength(self, key, x):
        if key in SizeResults.lengthTypes:
            self.lengthList[key] = x
        
    def getLength(self, key):
        x = None
        if key in SizeResults.lengthTypes:
            if key in self.lengthList.keys():
                x = self.lengthList[key]
        return x

    def calculateParameters(self):
        def calcMean(key1, key2):
            x1, x2 = self.getLength(key1), self.getLength(key2)
            return (x1 + x2)/2.0
        def calcError(key1, key2):
            x1, x2 = self.getLength(key1), self.getLength(key2)
            return abs(x1 - x2)/2.0
        self.parameters['AsicWidthMean'] = calcMean('AsicWidthT', 'AsicWidthB')
        self.parameters['AsicWidthError'] = calcError('AsicWidthT', 'AsicWidthB')
        self.parameters['AsicHeightMean'] = calcMean('AsicHeightR','AsicHeightL')
        self.parameters['AsicHeightError'] = calcError('AsicHeightR', 'AsicHeightL')
        self.parameters['SensorWidthMean'] = calcMean('SensorWidthT','SensorWidthB')
        self.parameters['SensorWidthError'] = calcError('SensorWidthT', 'SensorWidthB')
        self.parameters['SensorHeightMean'] = calcMean('SensorHeightR','SensorHeightL')
        self.parameters['SensorHeightError'] = calcError('SensorHeightR', 'SensorHeightL')
        self.parameters['FlexWidthMean'] = calcMean('FlexWidthT','FlexWidthB')
        self.parameters['FlexWidthError'] = calcError('FlexWidthT', 'FlexWidthB')
        self.parameters['FlexHeightMean'] = calcMean('FlexHeightR','FlexHeightL')
        self.parameters['FlexHeightError'] = calcError('FlexHeightR', 'FlexHeightL')
        #
        self.parameters['FlexToAsicTMean'] = calcMean('FlexToAsicTR', 'FlexToAsicTL')
        self.parameters['FlexToAsicTError'] = calcError('FlexToAsicTR', 'FlexToAsicTL')
        self.parameters['FlexToAsicBMean'] = calcMean('FlexToAsicBR', 'FlexToAsicBL')
        self.parameters['FlexToAsicBError'] = calcError('FlexToAsicBR', 'FlexToAsicBL')
        self.parameters['FlexToAsicLMean'] = calcMean('FlexToAsicLT', 'FlexToAsicLB')
        self.parameters['FlexToAsicLError'] = calcError('FlexToAsicLT', 'FlexToAsicLB')
        self.parameters['FlexToAsicRMean'] = calcMean('FlexToAsicRT', 'FlexToAsicRB')
        self.parameters['FlexToAsicRError'] = calcError('FlexToAsicRT', 'FlexToAsicRB')
        #
        self.parameters['FlexToSensorTMean'] = calcMean('FlexToSensorTR', 'FlexToSensorTL')
        self.parameters['FlexToSensorTError'] = calcError('FlexToSensorTR', 'FlexToSensorTL')
        self.parameters['FlexToSensorBMean'] = calcMean('FlexToSensorBR', 'FlexToSensorBL')
        self.parameters['FlexToSensorBError'] = calcError('FlexToSensorBR', 'FlexToSensorBL')
        self.parameters['FlexToSensorLMean'] = calcMean('FlexToSensorLT', 'FlexToSensorLB')
        self.parameters['FlexToSensorLError'] = calcError('FlexToSensorLT', 'FlexToSensorLB')
        self.parameters['FlexToSensorRMean'] = calcMean('FlexToSensorRT', 'FlexToSensorRB')
        self.parameters['FlexToSensorRError'] = calcError('FlexToSensorRT', 'FlexToSensorRB')
        #
        self.parameters['AsicToSensorTMean'] = calcMean('AsicToSensorTR', 'AsicToSensorTL')
        self.parameters['AsicToSensorTError'] = calcError('AsicToSensorTR', 'AsicToSensorTL')
        self.parameters['AsicToSensorBMean'] = calcMean('AsicToSensorBR', 'AsicToSensorBL')
        self.parameters['AsicToSensorBError'] = calcError('AsicToSensorBR', 'AsicToSensorBL')
        self.parameters['AsicToSensorLMean'] = calcMean('AsicToSensorLT', 'AsicToSensorLB')
        self.parameters['AsicToSensorLError'] = calcError('AsicToSensorLT', 'AsicToSensorLB')
        self.parameters['AsicToSensorRMean'] = calcMean('AsicToSensorRT', 'AsicToSensorRB')
        self.parameters['AsicToSensorRError'] = calcError('AsicToSensorRT', 'AsicToSensorRB')

        # Angles
        def calcAngle(dir1, dir2):
            iprod = dir1[0]*dir2[0] + dir1[1]*dir2[1]
            return math.acos(iprod)*180.0/math.pi
        dirFlexL = self.getLine('Flex_L').direction()
        dirFlexR = self.getLine('Flex_R').direction()
        dirSensorT = self.getLine('Sensor_T').direction()
        dirSensorB = self.getLine('Sensor_B').direction()
        print('Dir flex L = ', dirFlexL[0], dirFlexL[1])
        print('Dir sensor T = ', dirSensorT[0], dirSensorT[1])
        angleTL = calcAngle(dirFlexL, dirSensorT)
        angleTR = calcAngle(dirFlexR, dirSensorT)
        angleBL = calcAngle(dirFlexL, dirSensorB)
        angleBR = calcAngle(dirFlexR, dirSensorB)
        self.parameters['AngleFlexSensorTL'] = angleTL
        self.parameters['AngleFlexSensorTR'] = angleTR
        self.parameters['AngleFlexSensorBL'] = angleBL
        self.parameters['AngleFlexSensorBR'] = angleBR
        
    def par(self, key):
        x = None
        if key in SizeResults.parameterTypes:
            if key in self.parameters.keys():
                x = self.parameters[key]
        return x

    def showSummary(self):
        print('%d measurements' % len(self.measurements))
        for m in self.measurements:
            print('name=%s file=%s' % (m[0], m[4]) )
            
    def dump(self, fname):
        f = open(fname, 'w')
        print('Dump %d measurements' % len(self.measurements))
        for m in self.measurements:
            n = len(m)
            s = ''
            if n >= 3:
                s += '%-20s %7.5f %7.5f' % (m[0], m[1], m[2])
            if n >= 5:
                s += ' %2d %s' % (m[3], m[4])
            if n >= 9:
                s += ' %7.5f %7.5f %7.5f %7.5f' % (m[5], m[6], m[7], m[8])
            s += '\n'
            f.write(s)
        f.close()

class HeightResults:
    def __init__(self):
        self.pointsJig = []
        self.pointsAsic = []
        self.pointsSensor = []
        self.pointsFlex = []

class PhotoResults:
    def __init__(self):
        self.measurements = [] # [ x, y, z, photo ]

    def addMeasurement(self, data):
        self.measurements.append(data)

    def pointsOn(self, tag):
        v = []
        for p in self.measurements:
            tag = tag.upper()
            name = p[0].upper()
            xyz = p[1:4]
            if name.find(tag)>=0:
                v.append(xyz)
        return v
            
    def dump(self, fname):
        f = open(fname, 'w')
        for m in self.measurements:
            s = '%-20s %7.5f %7.5f %7.5f %s\n' % (m[0], m[1], m[2], m[3], m[4])
            f.write(s)
        f.close()

class MetrologyResults1:
    def __init__(self):
        self.sizeResults = SizeResults()
        self.pickupResults = {}
        self.heightResults = HeightResults()
        self.planarityResults = {}
        self.photoResults = PhotoResults()

    def load(self, fileName):
        print('Load MetrologyResults from %s' % fileName)
        if os.path.exists(fileName):
            f = open(fileName, 'rb')
            v = pickle.load(f)
            if len(v)== 4:
                self.sizeResults = v[0]
                self.pickupResults = v[1]
                self.heightResults = v[2]
                self.planarityResults = v[3]
                self.photoResults = v[4]
            f.close()

    def save(self, fileName):
        f = open(fileName, 'wb')
        v = (
            self.sizeResults, 
            self.pickupResults, 
            self.heightResults, 
            self.planarityResults,
            self.photoResults,
        )
        pickle.dump(v, f)
        f.close()

class ScanPoint1:
    def __init__(self, x, y, z, photo=None, tags=None):
        self.x = x
        self.y = y
        self.z = z
        self.imgFile = photo
        self.tags = tags
        self.targetXY = None

class MetrologyResults2:
    def __init__(self):
        self.heightResults = []
        self.sizeResults = []
        self.flatnessResultsVacOn = []
        self.flatnessResultsVacOff = []
    def setSizeResults(self, points, config):
        n = len(config)
        if len(points) != n: #(n+1):
            print('Number of points does not match the number in configuration %d ... %d' % (len(points), n))
            return -1
        self.sizeResults = []
        for i in range(n):
            c = config[i]
            p = points[i]
            if len(p)>3:
                data = ScanPoint1(p[0], p[1], p[2], photo=p[3], tags=c.tags)
            elif len(p)>2:
                data = ScanPoint1(p[0], p[1], p[2], photo='-', tags=c.tags)
            self.sizeResults.append(data)

class MetrologySummary:
    def __init__(self):
        self.heightMap = {}
        self.pickupMap = {}
        self.sizeMap = {}
        self.flatnessMap = {}
        #
    def createKeys(self):
        self.heightKeys = [
            'Jig', 'Asic', 'Sensor', 'Flex',
        ]
        self.pickupKeys = [
            'Pickup1', 'Pickup2', 'Pickup3', 'Pickup4', 
            'FlexL', 'FlexR', 'HVCapacitor', 'Connector', 
        ]
        self.sizeKeys = [
            'AsicT', 'AsicB', 'AsicL', 'AsicR', 
            'SensorT', 'SensorB', 'SensorL', 'SensorR', 
            'FlexT', 'FlexB', 'FlexL', 'FlexR', 
            'AsicX', 'AsicY', 
            'SensorX', 'SensorY', 
            'FlexX', 'FlexY', 
            'FlexToAsicL', 'FlexToAsicR', 
            'FlexToSensorT', 'FlexToSensorB', 
            'Angle', 
        ]
        self.flatnessKeys = [
            'zmax', 'zmin', 'zDiffMax', 'zMean', 
            'AngleA', 'AngleB', 
        ]


class MetrologyData:
    def __init__(self):
        self.dbData = {
            'distanceTop': 0.0, 
            'distanceBottom': 0.0, 
            'distanceLeft': 0.0, 
            'distanceRight': 0.0,
            'angleTopLeft': 0.0, 
            'angleTopRight': 0.0, 
            'angleBottomLeft': 0.0, 
            'angleBottomRight': 0.0,
            'thicknessPickupAreas': [ 0.0, 0.0, 0.0, 0.0], 
            'thicknessEdges': [ 0.0, 0.0, 0.0, 0.0],
            'thicknessHvCap': 0.0, 
            'thicknessDataConnector': 0.0, 
            'planarityVacOn': 0.0, 
            'planarityVacOff': 0.0, 
            'planarityVacDiff': 0.0, 
            'planarityVacDiffStdDev': 0.0,
            'rawData': None
        }
        self.auxData = {
        }
        self.operator = 'Unknown'
        self.date = None

class ModuleShape:
    def __init__(self):
        self.name = ''
        self.heights = {
            'Jig': 0.0, 
            'Asic': 0.0, 
            'Sensor': 0.0, 
            'Flex': 0.0, 
            'FlexEdgeL': 0.0, 
            'FlexEdgeR': 0.0, 
            'FlexPickup1': 0.0, 
            'FlexPickup2': 0.0, 
            'FlexPickup3': 0.0, 
            'FlexPickup4': 0.0, 
            'FlexHVCapacitor': 0.0, 
            'FlexConnector': 0.0, 
            'FlexResistor1': 0.0, 
            'FlexResistor2': 0.0, 
            'FlexResistor3': 0.0, 
            'FlexResistor4': 0.0, 
            'FlexResistor5': 0.0, 
            'FlexResistor6': 0.0, 
        }
        self.edges = {
            'AsicT': 0.0, 
            'AsicB': 0.0, 
            'AsicL': 0.0, 
            'AsicR': 0.0, 
            'SensorT': 0.0, 
            'SensorB': 0.0, 
            'SensorL': 0.0, 
            'SensorR': 0.0, 
            'FlexT': 0.0, 
            'FlexB': 0.0, 
            'FlexL': 0.0, 
            'FlexR': 0.0, 
        }
        self.flatness = 0.0

class ModuleView:
    def __init__(self, components=()):
        self.design = Rd53aModule()
        self.shape = ModuleShape()

class ScanPointConfig:
    def __init__(self, x, y, tags, uses):
        self.x = x
        self.y = y
        self.tags = tags
        self.uses = uses
        
class ScanPointResult:
    def __init__(self, x, y, z, valid, photo='', zoom=0):
        self.x = x
        self.y = y
        self.z = z
        self.isValid = valid
        self.photo = photo
        self.zoom = zoom

class PatternRecResults:
    def __init__(self, tag, pointData, imagePath):
        self.tag = tag
        self.pointData = pointData
        self.imagePath = imagePath
        self.offsetXY = [ pointData.x, pointData.y ]
        self.regionXY = [0.0]*4 # [x1, y1, x2, y2]
        self.regionCR = [0.0]*4 # [c1, r1, c2, r2]
        self.recXY = [ 0.0, 0.0 ]

    def recXY(self):
        xy = self.recXY
        return xy
    def regionXY(self):
        return self.regionXY
    def regionCR(self):
        return self.regionCR

class ScanConfig:
    def __init__(self, scanConfigFile):
        self.scanConfigFile = scanConfigFile
        self.pointConfigList = []
        self.readConfig(self.scanConfigFile)
    def readConfig(self, fname):
        if not os.path.exists(fname):
            logger.warn('ScanConfig file does not exist: %s' % fname)
            return
        points = []
        f = open(fname, 'r')
        for line in f.readlines():
            if len(line)==0 or line[0]=='#' or \
               line.startswith('ScanConfig'): continue
            words = line.split()
            x, y, tags = 0, 0, []
            uses = []
            if len(words)>0: x = float(words[0])
            if len(words)>1: y = float(words[1])
            if len(words)>2: tags = words[2].split(',')
            if len(words)>3: uses = words[3].split(',')
            c = ScanPointConfig(x, y, tags, uses)
            self.pointConfigList.append(c)
        logger.info('Successfully read %d points from %s' % \
                    (len(self.pointConfigList), fname) )
        f.close()
    def nPoints(self):
        return len(self.pointConfigList)

    def allTags(self):
        tags = []
        for p in self.pointConfigList:
            for t in p.tags:
                if t == '1mm_step': continue
                if t not in tags:
                    tags.append(t)
        return tags
    def indicesWithTag(self, tag):
        v = []
        for i, c in enumerate(self.pointConfigList):
            if tag in c.tags:
                v.append(i)
        return v
    def add(self, pointConfig):
        self.pointConfigList(pointConfig)
    def pointConfig(self, i):
        if i < len(self.pointConfigList):
            return self.pointConfigList[i]
        else:
            return None

class ScanResults:
    def __init__(self, logFile):
        self.logFile = logFile
        self.scanDir = os.path.dirname(logFile)
        self.pointDataList = []
        self.recPointList = []
        pass
    def add(self, p):
        self.pointDataList.append(p)
    def nPoints(self):
        return len(self.pointDataList)
    def pointResult(self, i):
        p = None
        if i < len(self.pointDataList):
            p = self.pointDataList[i]
        return p
    def hasPhotos(self):
        yes = False
        for p in self.pointDataList:
            if p.photo != '':
                yes = True
                break
        return yes
    def imageFile(self, i):
        fname = ''
        if i < len(self.pointDataList):
            p = self.pointDataList[i]
            fname = ''
            if len(p.photo)>0:
                fname = p.photo
        return fname
    def imagePath(self, i):
        fname = self.imageFile(i)
        if fname != '':
            fname = os.path.join(self.scanDir, fname)
        return fname

class MetrologyScanResults:
    def __init__(self):
        self.heightResults = None
        self.pickupResults = None
        self.sizeResults = None
        self.flatnessVacOnResults = None
        self.flatnessVacOffResults = None

    def height(self):
        return self.heightResults
    def pickup(self):
        return self.pickupResults
    def size(self):
        return self.sizeResults
    def flatnessVacOn(self):
        return self.flatnessVacOnResults
    def flatnessVacOff(self):
        return self.flatnessVacOffResults

class ConfigStore:
    def __init__(self, configFile=None):
        self.myconfig = ''

        logger.info('Read initial configuration from %s' % configFile)
        if configFile!=None and os.path.exists(configFile):
            self.myconfig = configFile
            self.readConfig()

        self.swDir = os.getenv('PMMDIR')
        if self.swDir == None: self.swDir = '.'
        self.shareDir = os.path.join(self.swDir, 'share')
        self.scanDir = ''
        self.workDir = '.'
        self.modulesDir = './modules'
        self.componentViewConfig = ComponentViewConfig()
        cvConfig = os.path.join(self.swDir, 'share/pmmview.cfg')
        self.componentViewConfig.read(cvConfig)
        
        self.scanConfigList = ScanConfigList()

        #self.checkScanConfigs()
        self.pickupScanConfig = ''
        self.heightScanConfig = ''
        self.sizeScanConfig = ''
        self.flatnessScanConfig = ''
        self.readConfig()

        if os.path.exists(self.workDir):
            self.modulesDir = os.path.join(self.workDir, 'modules')
            dirs = [
                self.modulesDir, 
                os.path.join(self.workDir, 'summary'), 
                os.path.join(self.workDir, 'AppData'),
                ]
            for dname in dirs:
                if not os.path.exists(dname):
                    os.mkdir(dname)
                
    def checkScanConfigs(self):
        files = os.listdir(self.shareDir)
        for f in files:
            if f.startswith('ScanConfig'):
                scName = f.replace('.txt', '')
                scName = scName.replace('ScanConfig_', '')
                if scName.find('pickup'):
                    self.extendPickupList([scName])
                elif scName.find('height'):
                    self.extendHeightList([scName])
                elif scName.find('size'):
                    self.extendSizeList([scName])
                elif scName.find('flatness'):
                    self.extendFlatnessList([scName])
                #
                self.scanConfigNames.append(scName)
        n = len(self.scanConfigNames)
        logger.info('ConfigStore read %d scan configurations' % n)

    def readConfig(self):
        if os.path.exists(self.myconfig):
            with open(self.myconfig, 'r') as f:
                data = json.load(f)
                keys = data.keys()
                if 'scanDir' in keys:
                    self.scanDir = data['scanDir']
                if 'workDir' in keys:
                    self.workDir = data['workDir']
                if 'pickupScanConfig' in keys:
                    self.pickupScanConfig = data['pickupScanConfig']
                if 'heightScanConfig' in keys:
                    self.heightScanConfig = data['heightScanConfig']
                if 'sizeScanConfig' in keys:
                    self.sizeScanConfig = data['sizeScanConfig']
                if 'flatnessScanConfig' in keys:
                    self.flatnessScanConfig = data['flatnessScanConfig']
    def getScanConfig(self, name):
        sc = None
        if name in self.scanConfigNames:
            fname = os.path.join(self.shareDir, 
                                 'ScanConfig_{%s}.txt'.format(name))
            sc = self.readScanConfig(fname)
        return sc
    def readScanConfig(self, fname):
        sc = None
        if os.path.exists(fname):
            sc = ScanConfig(fname)
            with open(fname, 'r') as f:
                for line in f.readlines():
                    if len(line)==0 or line[0]=='#': continue
                    if line.startswith('ScanConfig')>=0: continue
                    words = line.split()
                    x = float(words[0])
                    y = float(words[1])
                    tags, uses = [], []
                    if len(words)>2: tags = words[2].split(',')
                    if len(words)>3: uses = words[3].split(',')
                    scp = ScanPointConfig(x, y, tags, uses)
                    sc.add(scp)
        return sc
    def getScanConfigs(self, ctag):
        ctag = ctag.lower()
        if ctag == 'pickup':
            return self.scanConfigList.pickupList
        elif ctag == 'height':
            return self.scanConfigList.heightList
        elif ctag == 'size':
            return self.scanConfigList.sizeList
        elif ctag == 'flatness':
            return self.scanConfigList.flatnessList
        return []

    # def configsWithString(self, s):
    #     v = []
    #     for c in self.scanConfigNames:
    #         if c.find(s)>=0: v.append(c)
    #     return v
    # def getHeightConfigs(self):
    #     return self.configsWithString('height')
    # def getSizeConfigs(self):
    #     return self.configsWithString('size')
    # def getFlatnessConfigs(self):
    #     return self.configsWithString('flatness')
