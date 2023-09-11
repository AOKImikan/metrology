#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# 
# Unit: mm
# Module coordinate system: origin at the middle
#                           x (towards right) and y (towards top)
#--------------------------------------------------------------------

import os
import re
import math
import logging

import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

from .model import *
from .reader import *
from .view import *
from .gui import *

logger = logging.getLogger(__name__)

def fitLine0(points):
    line = None
    n = len(points)
    v1 = np.array([1]*n)
    vx = np.array(list(map(lambda x: x[0], points) ) )
    vy = np.array(list(map(lambda x: x[1], points) ) )
    # Line: p0+p1*x+p2*y = 0
    X = np.c_[ v1, vx, vy]
    M = np.dot(X.T, X)
    xx = M[1][1] - M[1][0]*M[0][1]
    yy = M[2][2] - M[2][0]*M[0][2]
    if xx > yy: # y=ax+b
        ifix = 2
    else: # x=ay+b
        ifix = 1
    M2 = [ [0, 0], [0, 0] ]
    b2 = [0, 0]
    i2, j2 = 0, 0
    for i in range(3):
        if i == ifix:
            continue
        j2 = 0
        for j in range(3):
            if j == ifix:
                b2[i2] = -M[i][j]
                continue
            M2[i2][j2] = M[i][j]
            j2 += 1
        i2 += 1
    pars2 = linalg.solve(M2, b2)
    pars = [0]*3
    i2 = 0
    for i in range(3):
        if i == ifix:
            pars[i] = 1.0
        else:
            pars[i] = pars2[i2]
            i2 += 1
    line = Line()
    for p in points:
        print(p.position)
    print(pars)
    line.setPars(pars)
    return line

def fitLine(points):
    line = fitLine0(points)
    return line

def fitPlane0(points):
    # z = f(x, y; pars)
    plane = None
    logger.debug('Fit plane with %d points' % len(points))
    # Input data
    vx = np.array(list(map(lambda x: x[0], points) ) )
    vy = np.array(list(map(lambda x: x[1], points) ) )
    vz = np.array(list(map(lambda x: x[2], points) ) )
    n = len(vx)
    #print('fitPlane0 n=%d' % n)
    #print(points)
    #print(vx, vy, vz)
    # M = (X_k X_l), b=X_k*z
    X = np.c_[ [1]*n, vx, vy]
    M = np.dot(X.T, X)
    b = np.dot(X.T, vz)
    #print(M)
    pars = linalg.solve(M, b)
    plane = Plane()
    plane.setPars(pars)
    return plane

def fitPlane(points, outlierThr=-1.0):
    plane1 = fitPlane0(points)
    outliers = []
    points2 = []
    for i, p in enumerate(points):
        d = plane1.distance(p)
        #print(d)
        if outlierThr>0.0 and abs(d) > outlierThr:
            outliers.append(i)
        else:
            points2.append(points[i])
    #print('Second fit n=%d out=%d' % (len(points2), len(outliers) ) )
    plane2 = fitPlane0(points2)
    plist = []
    for i, p in enumerate(points):
        if i not in outliers:
            plist.append(p)
    plane2.calculateErrors(plist)
    return (plane2, outliers)
            

def summaryPointsOnPlane(points, plane, outliers=[], title='', figPrefix=''):
    vx1, vy1, vz1 = [], [], []
    for i, p in enumerate(points):
        if i in outliers: continue
        vx1.append(p[0])
        vy1.append(p[1])
        vz1.append(p[2])
    vx = np.array(vx1)
    vy = np.array(vy1)
    vz = np.array(vz1)
    #
    n = len(points)
    dz = list(map(lambda p: plane.distance(p), points) )
    zmax = max(dz)
    zmin = min(dz)
    zmean = sum(dz)/n
    z2 = sum(list(map(lambda x: x*x, dz) ) )
    zsigma = math.sqrt( (z2 - zmean*zmean)/n)
    nv = plane.normalVector
    print('Summary of plane fit (%s)' % title)
    print('  %s' % plane)
    print('  N points: %d' % len(vx))
    print('  N outliers: %d' % len(outliers))
    print('  Normal vector: (%6.4f, %6.4f, %6.4f)' % (nv[0], nv[1], nv[2]))
    print('  <z> +- sigma : %7.5f += %7.5f' % (zmean, zsigma) )
    print('  z(max-min): %7.5f' % (zmax - zmin) )
    #
    fig = plt.figure()
    ax = fig.add_subplot(111,projection='3d')
    p = ax.scatter(vx, vy, vz, s=5,c=vz,cmap=plt.cm.jet)
    plt.colorbar(p)
    #p=ax.plot_wireframe(xmesh,ymesh,zmesh,color='b')
    p=ax.set_xlabel("x [mm]")
    p=ax.set_ylabel("y [mm]")
    p=ax.set_zlabel("z [mm]")
    fig.savefig('%s_3d.png' % figPrefix)
    #
    fig = plt.figure()
    plt.hist(dz, bins=100, range=(-0.5, 0.5))
    plt.xlabel('Delta Z [mm]')
    plt.ylabel('Entries')
    fig.savefig('%s_deltaZ.png' % figPrefix)

def checkHeight(fname, reader):
    print('Check height')
    points = reader.readPoints(fname)
    if points == None:
        return -1
    print('N points in %s: %d' % (fname, len(points) ) )
    n1 = 12
    #pointsOnJig = points[0:4]
    pointsOnAsic = points[0:4]
    pointsOnSensor = points[4:8]
    pointsOnFlex = points[8:12] # [12:16]
    pointsOnDataConnector = points[12:15] #[16:19]
    pointsOnHvCapacitor = points[15:17] #[19:21]
    pointsOnLeftCapacitors = points[17:23] #[21:27]
    #
    #planeJig = fitPlane(pointsOnJig)
    #summaryPointsOnPlane(pointsOnJig, planeJig)
    #
    planeAsic, out1 = fitPlane(pointsOnAsic)
    summaryPointsOnPlane(pointsOnAsic, planeAsic, out1, 'Height (ASIC)', 'height_asic')
    z_asic = planeAsic.c
    #
    planeSensor, out2 = fitPlane(pointsOnSensor)
    summaryPointsOnPlane(pointsOnSensor, planeSensor, out2, 'Height (sensor)', 'height_sensor')
    z_sensor = planeAsic.c
    #
    planeFlex, out3 = fitPlane(pointsOnFlex)
    summaryPointsOnPlane(pointsOnFlex, planeFlex, out3, 'Height (Flex)', 'height_flex')
    z_flex = planeFlex.c
    #
    print('  Average height (ASIC): %7.5f [mm]' % z_asic)
    print('  Average height (Sensor): %7.5f [mm]' % z_sensor)
    print('  Average height (Flex): %7.5f [mm]' % z_flex)
    print('  Estimated glue thickness (flex-sensor): %7.5f [mm]' % (z_flex - z_sensor) )

def checkPickup(fname, reader):
    points = reader.readPoints(fname)
    if points == None:
        return -1
    print('N points in %s: %d' % (fname, len(points) ) )

def checkPhoto(fname, reader, results, configFile=''):
    points = reader.readPoints(fname)
    dname = os.path.dirname(fname)
    flist = os.listdir(dname)
    imglist = list(filter(lambda x: x.startswith('Img'), flist))
    imglist = list(map(lambda x: os.path.join(dname, x), imglist))
    imglist.sort()
    print('%d points and %d photos' % (len(points), len(imglist)))
    #
    pointNames = []
    if configFile!='' and os.path.exists(configFile):
        fp = open(configFile, 'r')
        for line in fp.readlines():
            if len(line)==0 or line[0] == '#': continue
            line = line.strip()
            if len(line)>0: pointNames.append(line)
    print('%d point names from %s' % (len(pointNames), configFile))
    for i, p in enumerate(points):
        imgfile = ''
        if i < len(imglist): imgfile = imglist[i]
        xxx = 'xxx'
        if i < len(pointNames): xxx = pointNames[i]
        data = [ xxx, p[0], p[1], p[2], imgfile]
        results.addMeasurement(data)

def checkSize(fname, reader, results, suffix=''):
    points = reader.readPointsSize(fname)
    #
    opts1 = {
        'r': 0.12, 
        'stroke': 'blue', 
        'stroke-width': 0.1, 
        'fill': 'blue', 
    }
    opts2 = {
        'r': 0.12, 
        'stroke': 'red', 
        'stroke-width': 0.1, 
        'fill': 'none', 
    }
    vopts = []
    for p in points:
        if len(p)>4:
            vopts.append(opts1)
        else:
            vopts.append(opts2)
    if points == None:
        return -1
    print('N points in %s: %d' % (fname, len(points) ) )
    
    for p in points:
        if suffix != '': p[0] = '%s%s' % (p[0], suffix)
        results.addMeasurement(p)
    for e in SizeResults.edgeLocationTypes:
        v = results.pointsOnEdge(e)
        print('Points on edge %s => %d' % (e, len(v)))
        if len(v)>=2:
            line = fitLine(v)
            #print('Line at edge %s => normal=(%7.5f, %7.5f)' % (e, line.p[1], line.p[2]) )
            results.setLine(e, line)
    # Module View
    mv = ModuleView()
    for i, p in enumerate(points):
        opts2 = dict(vopts[i])
        opts2['fill'] = 'none'
        mv.addPoint(p[1:3], opts2)
        if len(p)>=6:
            mv.addPoint(p[5:7], vopts[i])
    fimg = open('size1.svg', 'w')
    fimg.write(mv.toSvg())
    #

def inspectSizeResults(results, datadir):
    #datadir = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/20210706/tray-1size_12'
    for m in results.measurements:
        if len(m)<6: continue
        xc = m[1:3]
        zoom = m[3]
        imageFile = m[4]
        x = m[5:7]
        print('Point %s %s in an image centered at %s' % (m[0], str(x), str(xc)))
        cr = globalToLocal(x, xc)
        imageFile
        i = imageFile.find('Img')
        if i>=0:
            imageFile = '%s/%s' % (datadir, imageFile[i:])
        if os.path.exists(imageFile):
            print('pass circle ', cr)
            w = CvWindow(imageFile, [cr])
            cr = w.point
            cv2.destroyAllWindows()
            if len(cr)== 2:
                p = results.getPoint(m[0])
                xy = localToGlobal(cr, xc)
                p.update(xy)

def inspectRecPoints(fname, datadir):
    # File consists of a set of lines:
    # Full: [ name, x0, y0, zoom, photo, x, y, dx, dy ] or
    #       [ name, x0, y0, zoom, photo ]
    if not os.path.exists(fname):
        print('File %s doesnot exist' % fname)
        return -1
    f = open(fname, 'r')
    re1 = re.compile('([\w]+)_size_(\d+)\.txt')
    mg1 = re1.search(fname)
    fout = None
    if mg1:
        prefix = mg1.group(1)
        i = int(mg1.group(2))
        foutName = '%s_size_%d.txt' % (prefix, i+1)
        ntry = 0
        abc = ('', 'a', 'b', 'c', 'd', 'e')
        while ntry <5:
            foutName = '%s_size_%d%s.txt' % (prefix, i+1, abc[ntry])
            if not os.path.exists(foutName):
                break
            ntry += 1
        if ntry >= 5:
            print('Remove the output file %s_size_%d.txt first' % (prefix, i+1))
            return
        fout = open(foutName, 'w')
    for line in f.readlines():
        if len(line) == 0 or line[0] == '#': continue
        line = line.strip()
        words = line.split()
        n = len(words)
        name = ''
        x0, x, dx = [], [], []
        zoom = 1
        photo = ''
        #print(n)
        #print(line)
        if n >= 5:
            x0 = [0.0, 0.0]
            name = words[0]
            x0[0] = float(words[1])
            x0[1] = float(words[2])
            zoom = int(float(words[3]))
            photoFile = words[4]
        if n >= 9:
            x, dx = [0.0, 0.0], [0.0, 0.0]
            x[0] = float(words[5])
            x[1] = float(words[6])
            dx[0] = float(words[7])
            dx[1] = float(words[8])
        #
        #print('name=%s' % name)
        #print('x0, y0 = %7.5f, %7.5f' % (x0[0], x0[1]))
        #print('zoom=%d, file=%s' % (zoom, photoFile))
        #if n >= 9:
        #    #print('x, y = %7.5f, %7.5f', x[0], x[1])
        #    #print('dx, dy = %7.5f, %7.5f', dx[0], dx[1])
        if os.path.exists(photoFile):
            print('Open photo %s' % photoFile)
            clist = []
            if len(x)== 2:
                print('x=', x, 'x0=', x0)
                cr = globalToLocal(x, x0)
                clist.append(cr)
            print('Reconstruct point at %s' % name)
            w = CvWindow(photoFile, clist)
            cr = w.point
            cv2.destroyAllWindows()
            data = [ name, x0[0], x0[1], zoom, photoFile]
            if n == 9:
                data.append(x[0])
                data.append(x[1])
                data.append(dx[0])
                data.append(dx[1])
            if len(cr) == 2:
                xy = localToGlobal(cr, x0)
                print('Update reconstructed position to (%7.5f, %7.5f)' % (xy[0], xy[1]))
                if n == 5:
                    data.extend([xy[0], xy[1], 0.0, 0.0])
                elif n == 9:
                    data[5] = xy[0] 
                    data[6] = xy[1]
            if fout:
                if len(data)==9:
                    fout.write('%s %10.5f %10.5f %d %s %10.5f %10.5f %10.5f %10.5f\n' % tuple(data))
                elif len(data)==7:
                    fout.write('%s %10.5f %10.5f %d %s %10.5f %10.5f\n' % tuple(data))
        else:
            print('Cannot open photo %s' % photoFile)
    if fout:
        fout.close()

def analyzeHeightFromPoints(fname):
    print('Height analysis from file %s' % fname)
    points = readHeight2(fname)
    results = PhotoResults()
    for p in points:
        results.addMeasurement(p)
    pointsOnJig = results.pointsOn('Jig')
    pointsOnAsic = results.pointsOn('Asic')
    pointsOnSensor = results.pointsOn('Sensor')
    pointsOnFlex = results.pointsOn('Flex')

    thr = 0.1
    planeJig, outliersJig = fitPlane(pointsOnJig, thr)
    summaryPointsOnPlane(pointsOnJig, planeJig, outliersJig, 'Jig')

    planeAsic, outliersAsic = fitPlane(pointsOnAsic, thr)
    summaryPointsOnPlane(pointsOnAsic, planeAsic, outliersAsic, 'Asic')

    planeSensor, outliersSensor = fitPlane(pointsOnSensor, thr)
    summaryPointsOnPlane(pointsOnSensor, planeSensor, outliersSensor, 'Sensor')

    planeFlex, outliersFlex = fitPlane(pointsOnFlex, thr)
    summaryPointsOnPlane(pointsOnFlex, planeFlex, outliersFlex, 'Flex')

    dz1, dz2 = planeAsic.zsigma, planeJig.zsigma
    print('Asic thickness: %5.3f +- %5.3f [mm]' %\
          (planeAsic.c - planeJig.c, math.sqrt(dz1*dz1 + dz2*dz2)) )

    dz1, dz2 = planeSensor.zsigma, planeAsic.zsigma
    print('Sensor thickness: %5.3f +- %5.3f [mm]' %\
          (planeSensor.c - planeAsic.c, math.sqrt(dz1*dz1 + dz2*dz2)) )

    dz1, dz2 = planeSensor.zsigma, planeFlex.zsigma
    print('Flex+glue thickness: %5.3f +- %5.3f [mm]' %\
          (planeFlex.c - planeSensor.c, math.sqrt(dz1*dz1 + dz2*dz2)) )

def analyzeSizeFromPoints(fname):
    # File consists of a set of lines:
    # Full: [ name, x0, y0, zoom, photo, x, y, dx, dy ] or
    print('Open file: %s' % fname)
    points = readSize3(fname)
    results = analyzeSize(points)
    results.calculateLengths()
    # Asic size
    print('ASIC width(T): %5.3f [mm]' % results.getLength('AsicWidthT'))
    print('ASIC width(B): %5.3f [mm]' % results.getLength('AsicWidthB'))
    print('ASIC height(R): %5.3f [mm]' % results.getLength('AsicHeightR'))
    print('ASIC height(L): %5.3f [mm]' % results.getLength('AsicHeightL'))
    # Sensor size
    print('Sensor width(T): %5.3f [mm]' % results.getLength('SensorWidthT'))
    print('Sensor width(B): %5.3f [mm]' % results.getLength('SensorWidthB'))
    print('Sensor height(R): %5.3f [mm]' % results.getLength('SensorHeightR'))
    print('Sensor height(L): %5.3f [mm]' % results.getLength('SensorHeightL'))
    # Flex size
    print('Flex width(T): %5.3f [mm]' % results.getLength('FlexWidthT'))
    print('Flex width(B): %5.3f [mm]' % results.getLength('FlexWidthB'))
    print('Flex height(R): %5.3f [mm]' % results.getLength('FlexHeightR'))
    print('Flex height(L): %5.3f [mm]' % results.getLength('FlexHeightL'))
    # Flex to Asic
    print('FlexToAsic (TR): %5.3f [mm]' % results.getLength('FlexToAsicTR'))
    print('FlexToAsic (TL): %5.3f [mm]' % results.getLength('FlexToAsicTL'))
    print('FlexToAsic (BR): %5.3f [mm]' % results.getLength('FlexToAsicBR'))
    print('FlexToAsic (BL): %5.3f [mm]' % results.getLength('FlexToAsicBL'))
    print('FlexToAsic (RT): %5.3f [mm]' % results.getLength('FlexToAsicRT'))
    print('FlexToAsic (RB): %5.3f [mm]' % results.getLength('FlexToAsicRB'))
    print('FlexToAsic (LT): %5.3f [mm]' % results.getLength('FlexToAsicLT'))
    print('FlexToAsic (LB): %5.3f [mm]' % results.getLength('FlexToAsicLB'))
    # Flex to Sensor
    print('FlexToSensor (TR): %5.3f [mm]' % results.getLength('FlexToSensorTR'))
    print('FlexToSensor (TL): %5.3f [mm]' % results.getLength('FlexToSensorTL'))
    print('FlexToSensor (BR): %5.3f [mm]' % results.getLength('FlexToSensorBR'))
    print('FlexToSensor (BL): %5.3f [mm]' % results.getLength('FlexToSensorBL'))
    print('FlexToSensor (RT): %5.3f [mm]' % results.getLength('FlexToSensorRT'))
    print('FlexToSensor (RB): %5.3f [mm]' % results.getLength('FlexToSensorRB'))
    print('FlexToSensor (LT): %5.3f [mm]' % results.getLength('FlexToSensorLT'))
    print('FlexToSensor (LB): %5.3f [mm]' % results.getLength('FlexToSensorLB'))
    # Asic to sensor
    print('AsicToSensor (TR): %5.3f [mm]' % results.getLength('AsicToSensorTR'))
    print('AsicToSensor (TL): %5.3f [mm]' % results.getLength('AsicToSensorTL'))
    print('AsicToSensor (BR): %5.3f [mm]' % results.getLength('AsicToSensorBR'))
    print('AsicToSensor (BL): %5.3f [mm]' % results.getLength('AsicToSensorBL'))
    print('AsicToSensor (RT): %5.3f [mm]' % results.getLength('AsicToSensorRT'))
    print('AsicToSensor (RB): %5.3f [mm]' % results.getLength('AsicToSensorRB'))
    print('AsicToSensor (LT): %5.3f [mm]' % results.getLength('AsicToSensorLT'))
    print('AsicToSensor (LB): %5.3f [mm]' % results.getLength('AsicToSensorLB'))

    print('#----- Summary -----')
    print('#  Size')
    print('ASIC width: %5.3f +- %5.3f [mm]' % \
          (results.par('AsicWidthMean'), results.par('AsicWidthError')) )
    print('ASIC height: %5.3f +- %5.3f [mm]' % \
          (results.par('AsicHeightMean'), results.par('AsicHeightError')) )
    print('Sensor width: %5.3f +- %5.3f [mm]' % \
          (results.par('SensorWidthMean'), results.par('SensorWidthError')))
    print('Sensor height: %5.3f +- %5.3f [mm]' % \
          (results.par('SensorHeightMean'), results.par('SensorHeightError')) )
    print('Flex width: %5.3f +- %5.3f [mm]' % \
          (results.par('FlexWidthMean'), results.par('FlexWidthError')))
    print('Flex height: %5.3f +- %5.3f [mm]' % \
          (results.par('FlexHeightMean'), results.par('FlexHeightError')) )
    print('#  Flex to ASIC')
    print('FlexToAsic (T): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToAsicTMean'), results.par('FlexToAsicTError')) )
    print('FlexToAsic (B): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToAsicBMean'), results.par('FlexToAsicBError')) )
    print('FlexToAsic (L): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToAsicLMean'), results.par('FlexToAsicLError')) )
    print('FlexToAsic (R): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToAsicRMean'), results.par('FlexToAsicRError')) )
    print('#  Flex to Sensor')
    print('FlexToSensor (T): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToSensorTMean'), results.par('FlexToSensorTError')) )
    print('FlexToSensor (B): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToSensorBMean'), results.par('FlexToSensorBError')) )
    print('FlexToSensor (L): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToSensorLMean'), results.par('FlexToSensorLError')) )
    print('FlexToSensor (R): %5.3f +- %5.3f [mm]' % \
          (results.par('FlexToSensorRMean'), results.par('FlexToSensorRError')) )
    print('#  ASIC to Sensor')
    print('AsicToSensor (T): %5.3f +- %5.3f [mm]' % \
          (results.par('AsicToSensorTMean'), results.par('AsicToSensorTError')) )
    print('AsicToSensor (B): %5.3f +- %5.3f [mm]' % \
          (results.par('AsicToSensorBMean'), results.par('AsicToSensorBError')) )
    print('AsicToSensor (L): %5.3f +- %5.3f [mm]' % \
          (results.par('AsicToSensorLMean'), results.par('AsicToSensorLError')) )
    print('AsicToSensor (R): %5.3f +- %5.3f [mm]' % \
          (results.par('AsicToSensorRMean'), results.par('AsicToSensorRError')) )
    print('AngleFlexSensorTL: %5.3f (deg)' % results.par('AngleFlexSensorTL') )
    print('AngleFlexSensorTR: %5.3f (deg)' % results.par('AngleFlexSensorTR') )
    print('AngleFlexSensorBL: %5.3f (deg)' % results.par('AngleFlexSensorBL') )
    print('AngleFlexSensorBR: %5.3f (deg)' % results.par('AngleFlexSensorBR') )

def checkPlanarity(fnameVacOff, fnameVacOn, reader):
    print('Check planarity')
    pointsOff = reader.readPoints(fnameVacOff)
    pointsOn = reader.readPoints(fnameVacOn)
    if pointsOff == None or pointsOn == None:
        return -1
    print('N points in %s: %d' % (fnameVacOff, len(pointsOff) ) )
    print('N points in %s: %d' % (fnameVacOn, len(pointsOn) ) )
    #
    othr = 0.3 # 0.5 um for outlier threshold
    # Vacuum off
    planeOff, outliers1 = fitPlane(pointsOff, othr)
    summaryPointsOnPlane(pointsOff, planeOff, outliers1, 'Planarity vac. Off', 'planarity_vacOff')
    # Vacuum off
    planeOn, outliers2 = fitPlane(pointsOn, othr)
    summaryPointsOnPlane(pointsOn, planeOn, outliers2, 'Planarity vac. On', 'planarity_vacOn')
    # Difference between vacuum on/off
    dxyz = []
    for i in range(len(pointsOn)):
        if i in outliers1 or i in outliers2: continue
        x = pointsOff[i][0]
        y = pointsOff[i][1]
        dz = pointsOff[i][2] - pointsOn[i][2]
        dxyz.append([x, y, dz])
    planeDiff, outliers3 = fitPlane(dxyz, othr)
    summaryPointsOnPlane(dxyz, planeDiff, [], 'Planarity vac. diff', 'planarity_vacDiff')

def analyzeSize(points):
    results = SizeResults()
    for p in points:
        results.addPoint(p)
        print('Point %s %7.5f %7.5f' % (p.name, p.position[0], p.position[1]))
    for e in SizeResults.edgeLocationTypes:
        v = results.pointsOnEdge(e)
        print('Points on edge %s => %d' % (e, len(v)))
        if len(v)>=2:
            line = fitLine(v)
            print('Line at edge %s => normal=(%7.5f, %7.5f)' % (e, line.p[1], line.p[2]) )
            results.setLine(e, line)
    results.calculateLengths()
    return results

def createSvg(results, figname):
    points = results.allPoints()
    #
    s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-25 -25 50 50">\n'
    #
    objectTypes = ('Asic', 'Sensor', 'Flex')
    edgeTypes = ('T', 'R', 'B', 'L')
    hTypes = ('T', 'B')
    vTypes = ('R', 'L')
    colors = {
        'Asic': 'blue', 
        'Sensor': 'black', 
        'Flex': 'green', 
    }
    widths = {
        'T': 10, 
        'R': 15, 
        'B': 20, 
        'L': 25, 
    }
    # Lines
    for obj in objectTypes:
        c = colors[obj]
        for t in hTypes:
            w = 10
            n1 = '%s_%s' % (obj, t)
            line = results.getLine(n1)
            if not line:
                print('Cannot get line %s from SizeResults' % n1)
                continue
            x1, x2 = -20, 20
            y1= line.yAtX(x1)
            y2= line.yAtX(x2)
            s += '<line x1="%7.5f" y1="%7.5f" x2="%7.5f" y2="%7.5f" stroke="%s"></line>' %\
                 (x1, y1, x2, y2, c)
    # Points
    print('N points %d' % len(points))
    for obj in objectTypes:
        for edge in edgeTypes:
            n1 = '%s_%s' % (obj, edge)
            print('Check %s' % n1)
            v = list(filter(lambda x: x.name.upper().find(n1.upper()), points))
            print('Points on %s => %d' % (n1, len(v)))
    s += '</svg>\n'

