#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# 
# Unit: mm
# Module coordinate system: origin at the middle
#                           x (towards right) and y (towards top)
#--------------------------------------------------------------------

import os
import re
import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

def kekB4FileToUser(p):
    return (p[0], -p[1], p[2])

def userToKekB4File(p):
    return (p[0], -p[1], p[2])

def kekB4GuiToUser(p):
    return (-p[0], -p[1], p[2])

def userToKekB4Gui(p):
    return (-p[0], -p[1], p[2])

# Plane parameterization
class Plane:
    def __init__(self):
        # Plane: z = dx*x + dy*y + c
        self.c = 0
        self.dx = 0
        self.dy = 0
        self.normalVector = (0.0, 0.0, 0.0)
        self.refPoint = (0.0, 0.0, 0.0)
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
    pass

def readPoints(fname):
    v = []
    if not os.path.exists(fname):
        print('File %s does not exist!' % fname)
        return None
    f = open(fname, 'r')
    for line in f.readlines():
        if len(line) == 0: continue
        words = line.split()
        if len(words)>=3:
            p = tuple(map(lambda x: float(x)*0.001, words[0:3]) )
            p = kekB4FileToUser(p)
            print('%5.4f, %5.4f, %5.4f' % (p[0], p[1], p[2]) )
            v.append(p)
    return v

def readPointsPhoto(fname):
    v = []
    if not os.path.exists(fname):
        print('File %s does not exist!' % fname)
        return None
    #
    re_photoAt = re.compile('Photo at \(([\d+-.]+), ([\d+-.]+)\)')
    re_zoom = re.compile('zoom:(\d+)')
    re_file = re.compile('file=([\w._:\\\/]+)')
    re_point = re.compile('ref=\(([\d+-.]+), ([\d+-.]+)\)')
    re_dir = re.compile('dir=\(([\d+-.]+), ([\d+-.]+)\)')
    re_name = re.compile('name=([\w_.]+)')
    # 
    p, p2, dline = [], [], []
    zoom = 1
    name = ''
    photoFile = ''
    f = open(fname, 'r')
    for line in f.readlines():
        if len(line) == 0: continue
        ok1, ok2 = False, False
        if line.find('Photo at')>=0:
            mg1 = re_photoAt.search(line)
            mg2 = re_zoom.search(line)
            mg3 = re_file.search(line)
            if mg1 and mg2 and mg3:
                p0 = list(map(lambda x: float(x)*0.001, mg1.groups()) )
                zoom = int(mg2.group(1))
                photoFile = mg3.group(1)
                ok1 = True
        elif line.find('Line ref')>=0:
            mg1 = re_point.search(line)
            mg2 = re_dir.search(line)
            mg3 = re_name.search(line)
            if mg1 and mg2 and mg3:
                p = list(map(lambda x: float(x)*0.001, mg1.groups()) )
                dline = list(map(lambda x: float(x), mg2.groups()) )
                name = mg3.group(1)
                ok2 = True
        elif line.find('Failed to find a line')>=0:
            pass
        else:
            print('Unrecognized line: %s' % line)
        if ok2:
            print('p=(%5.2f, %5.2f), dir=(%7.5f, %7.5f) file=%s %s' % \
                  (p[0], p[1], dline[0], dline[1], photoFile, name) )
            # Reset parameters
            p, p2, dline = [], [], []
            zoom = 1
            name = ''
            file = ''
    return v

def fitPlane(points):
    # z = f(x, y; pars)
    plane = None
    # Input data
    vx = np.array(list(map(lambda x: x[0], points) ) )
    vy = np.array(list(map(lambda x: x[1], points) ) )
    vz = np.array(list(map(lambda x: x[2], points) ) )
    n = len(vx)
    #print(points)
    #print(vx, vy, vz)
    # M = (X_k X_l), b=X_k*z
    X = np.c_[ [1]*n, vx, vy]
    M = np.dot(X.T, X)
    b = np.dot(X.T, vz)
    pars = linalg.solve(M, b)
    plane = Plane()
    plane.setPars(pars)
    return plane

def summaryPointsOnPlane(points, plane):
    vx = np.array(list(map(lambda x: x[0], points) ) )
    vy = np.array(list(map(lambda x: x[1], points) ) )
    vz = np.array(list(map(lambda x: x[2], points) ) )
    #
    fig = plt.figure()
    ax = fig.add_subplot(111,projection='3d')
    p = ax.scatter(vx, vy, vz, s=5,c=vz,cmap=plt.cm.jet)
    plt.colorbar(p)
    #p=ax.plot_wireframe(xmesh,ymesh,zmesh,color='b')
    p=ax.set_xlabel("x [mm]")
    p=ax.set_ylabel("y [mm]")
    p=ax.set_zlabel("z [mm]")
    plt.show()
    #
    n = len(points)
    dz = list(map(lambda p: plane.distance(p), points) )
    print(dz)

def checkHeight(fname):
    print('Check height')
    points = readPoints(fname)
    if points == None:
        return -1
    print('N points in %s: %d' % (fname, len(points) ) )
    n1 = 12
    pointsOnJig = points[0:4]
    pointsOnAsic = points[4:8]
    #pointsOnSensor = points[8:12]
    pointsOnFlex = points[8:12] # [12:16]
    pointsOnDataConnector = points[12:15] #[16:19]
    pointsOnHvCapacitor = points[15:17] #[19:21]
    pointsOnLeftCapacitors = points[17:23] #[21:27]
    #
    planeJig = fitPlane(pointsOnJig)
    summaryPointsOnPlane(pointsOnJig, planeJig)
    #planeSensor = fitPlane(pointsOnSensor)
    #planeAsic = fitPlane(pointsOnAsic)
    #planeFlex = fitPlane(pointsOnFlex)

def checkPickup(fname):
    points = readPoints(fname)
    if points == None:
        return -1
    print('N points in %s: %d' % (fname, len(points) ) )

def checkSize(fname):
    points = readPointsPhoto(fname)
    if points == None:
        return -1
    print('N points in %s: %d' % (fname, len(points) ) )

def checkPlanarity(fnameVacOff, fnameVacOn):
    print('Check planarity')
    pointsOff = readPoints(fnameVacOff)
    pointsOn = readPoints(fnameVacOn)
    if pointsOff == None or pointsOn == None:
        return -1
    print('N points in %s: %d' % (fnameVacOff, len(pointsOff) ) )
    print('N points in %s: %d' % (fnameVacOn, len(pointsOn) ) )
    planeOff = fitPlane(pointsOff)
    summaryPointsOnPlane(pointsOff, planeOff)
    
