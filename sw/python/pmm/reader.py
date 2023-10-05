#--------------------------------------------------------------------
# Pixel Module Metrology Analysis (Readers)
# 
#--------------------------------------------------------------------

import os, sys
import re
import numpy as np
from .model import ScanPointConfig

z_umPerPulse = 0.156 # um/pulse (AF)
NEAREND = 334791*z_umPerPulse # [um]

def kekB4FileToUser(p):
    r = 1.0E-3
    return (p[0]*r, -p[1]*r, (NEAREND - p[2])*r)

def userToKekB4File(p):
    r = 1.0E+3
    return (p[0]*r, -p[1]*r, NEAREND - p[2]*r)

def kekB4bFileToUser(p):
    r = 1.0E-3
    return (-p[0]*r, -p[1]*r, (NEAREND - p[2])*r)

def userToKekB4bFile(p):
    r = 1.0E+3
    return (-p[0]*r, -p[1]*r, NEAREND - p[2]*r)

def kekB4GuiToUser(p):
    return (-p[0], -p[1], 0.001*(NEAREND - p[2]))

def userToKekB4Gui(p):
    return (-p[0], -p[1], NEAREND - p[2]*1.0E+3)

class Reader:
    def __init__(self):
        pass
    def readPoints(self, fname):
        v = []
        return v
    def readPointsSize(self, fname):
        v = []
        return v

class ReaderB4v1(Reader):
    def __init__(self):
        super().__init__()
        
    def checkFormat(self,fname):
        logType = 0
        if os.path.exists(fname):
            f = open(fname, 'r')
            fmt2 = 'Photo at'
            logType = 1
            for line in f.readlines()[:10]:
                if line.find(fmt2)>=0:
                    logType = 2
                    break
            f.close()
        return logType
    
    def createScanResults(self, fname, zoom=20, requirePhoto=False):
        scanDir = os.path.dirname(fname)
        logType = self.checkFormat(fname)
        logger.debug('Scan results format %d' % logType)
        results = None
        if logType == 0:
            results = ScanResults(fname)
        elif logType == 1:
            results = self.createScanResults1(fname, zoom)
        elif logType == 2:
            results = self.createScanResults2(fname)
        #
        if requirePhoto and not results.hasPhotos():
            files = os.listdir(scanDir)
            photos = []
            for fn in files:
                if fn.endswith('.jpg'):
                    photos.append(fn)
            photos.sort()
            if results.nPoints() == len(photos):
                logger.info('Assign photos to the measurements in order')
            else:
                logger.warning('Number of measurements (%d) does not match the number of photos (%d)' % (results.nPoints(), len(photos)) )
                logger.warning('  Nevertheless assign photos to the measurements in order, likely to have inconsistency')
            for i, p in enumerate(results.pointDataList):
                if i < len(photos):
                    p.photo = photos[i]
                else:
                    break
        return results

    def createScanResults1(self, fname, zoom=20):
        # Format:
        # x y z
        results = ScanResults(fname)
        v = self.readPoints(fname)
        for p in v:
            x = p[0]
            y = p[1]
            z = p[2]
            photo = ''
            #
            if len(p)>4:
                photo = os.path.basename(p[4])
            valid = p[3]
            scanPoint = ScanPointResult(x, y, z, valid, photo, zoom)
            results.add(scanPoint)
        return results

    def createScanResults2(self, fname):
        # Photo at ...:
        # 
        # Retrieve: x y zoom, z, zoom, photo
        results = ScanResults(fname)
        re1 = re.compile('Photo at \(([\d+-.eE]+), ([\d+-.eE]+)\).*zoom:([\d]+), height:([\d+-.eE]+) , file=(.+)')
        if os.path.exists(fname):
            f = open(fname, 'r')
            iline = 0
            for line in f.readlines():
                if len(line)==0 or line[0] == '#':
                    iline += 1
                    continue
                mg = re1.search(line)
                logger.debug('line=%s' % line)
                logger.debug('match=%s' % str(mg))
                if mg:
                    mm = 1.0E-3
                    x = float(mg.group(1)) * mm
                    y = float(mg.group(2)) * mm
                    zoom = int(mg.group(3))
                    h = float(mg.group(4))
                    photo = mg.group(5)
                    z = (NEAREND - h) * mm
                    photo = os.path.basename(photo.replace('\\', os.sep))
                    valid = True
                    scanPoint = ScanPointResult(x, y, z, valid, photo, zoom)
                    results.add(scanPoint)
                iline += 1
        return results
        
    def readPoints(self, fname):
        v = []
        if not os.path.exists(fname):
            print('File %s does not exist!' % fname)
            return None
        scanDir = os.path.dirname(fname)
        f = open(fname, 'r')
        for line in f.readlines():
            if len(line) == 0: continue
            words = line.split()
            if len(words)>=3:
                p0 = tuple(map(lambda x: float(x), words[0:3]) )
                p = list(kekB4FileToUser(p0))
                #
                if len(words)>=4:
                    photo = os.path.join(scanDir, words[3])
                    p = list(p)
                    p.append(photo)
                #print('%5.4f, %5.4f, %5.4f' % (p[0], p[1], p[2]) )
                if words[2] == '0':
                    p.append(False)
                else:
                    p.append(True)
                v.append(p)
        return v

    def readPointsSize(self, fname):
        v, vopts = [], []
        if not os.path.exists(fname):
            print('File %s does not exist!' % fname)
            return None
        # Expected lines
        # (1) Normal case
        # Photo at
        # Line ref=
        # (2) Failed to take photo
        # # Cannot find photo
        # (3) Photo taken but failed to extract line
        # Photo at
        # Failed to find
        f = open(fname, 'r')
        #
        re1 = re.compile('Photo at \(([\d+-.]+), ([\d+-.]+)\)')
        re2 = re.compile('zoom:(\d+)')
        re2b = re.compile('file=([^\s]+)')
        re3 = re.compile('Line ref=\(([\d+-.]+), ([\d+-.]+)\) dir=\(([\d+-.]+), ([\d+-.]+)\)')
        re3b = re.compile('name=([^\s]+)')
        re4 = re.compile('# Cannot find photo at \(([\d+-.]+), ([\d+-.]+)\)')
        points = []
        pdata = []
        ip = 0
        for line in f.readlines():
            if len(line) == 0: continue
            line = line.strip()
            #
            addPoint = False
            mg1 = re1.search(line)
            if mg1:
                x = float(mg1.group(1))*1.0E-3
                y =float(mg1.group(2))*1.0E-3
                #pdata.append('xxx')
                pdata.append(x)
                pdata.append(y)
                mg2 = re2.search(line)
                mg2b = re2b.search(line)
                if mg2 and mg2b:
                    pdata.append(int(mg2.group(1)))
                    pdata.append(mg2b.group(1))
            mg3 = re3.search(line)
            if mg3:
                x = float(mg3.group(1))*1.0E-3
                y =float(mg3.group(2))*1.0E-3
                vx = float(mg3.group(3))
                vy =float(mg3.group(4))
                pdata.append(x)
                pdata.append(y)
                pdata.append(vx)
                pdata.append(vy)
                mg3b = re3b.search(line)
                if mg3b:
                    name =mg3b.group(1)
                    #print('Find name %s' % name)
                    pdata[0] = name
                addPoint = True
            elif line.find('Failed to find a line') >= 0:
                addPoint = True
            #
            mg4 = re4.search(line)
            if mg4:
                x, y = float(mg4.group(1)), float(mg4.group(2))
                pdata = [ x, y, 0, '', 0.0, 0.0, 0.0, 0.0]
                addPoint = True
                logger.debug(f'add failed point {pdata}')
            if addPoint:
                logger.debug('add point %s' % str(pdata))
                points.append(pdata)
                pdata = []
                addPoint = False
                ip += 1
        return points
    def nameSizeScan(self, i):
        names = [
            # ASIC
            'ASIC_L0', 'ASIC_L1', 'ASIC_L2', 'ASIC_L3', 
            'ASIC_B0', 'ASIC_B1', 
            'ASIC_T0', 'ASIC_T1', 
            'ASIC_R0', 'ASIC_R1', 'ASIC_R2', 'ASIC_R3', 
            # Sensor
            'SENSOR_L0', 'SENSOR_L1', 
            'SENSOR_B0', 'SENSOR_B1', 'SENSOR_B2', 'SENSOR_B3', 
            'SENSOR_T0', 'SENSOR_T1', 'SENSOR_T2', 'SENSOR_T3', 
            'SENSOR_R0', 'SENSOR_R1', 
            # Flex
            'FLEX_L0', 'FLEX_L1', 'FLEX_L2', 'FLEX_L3', 
            'FLEX_B0', 'FLEX_B1', 'FLEX_B2', 'FLEX_B3', 
            'FLEX_T0', 'FLEX_T1', 'FLEX_T2', 'FLEX_T3', 
            'FLEX_R0', 'FLEX_R1', 'FLEX_R2', 'FLEX_R3', 
        ]
        if i>=0 and i<len(names):
            return names[i]
        else:
            return ''

def readSize3(fname):
    if not os.path.exists(fname):
        print('File %s does not exist' % fname)
        exit(-1)
    f = open(fname, 'r')
    points = []
    for line in f.readlines():
        if len(line)==0 or line[0] == '#': continue
        line = line.strip()
        words = line.split()
        n = len(words)
        name, x, y = '', 0.0, 0.0
        if n >= 7:
            name = words[0]
            x = float(words[5])
            y = float(words[6])
            points.append(Point([x,y], name))
    return points

def readHeight2(fname):
    if not os.path.exists(fname):
        print('File %s does not exist' % fname)
        sys.exit(-1)
    f = open(fname, 'r')
    points = []
    for line in f.readlines():
        if len(line)==0 or line[0] == '#': continue
        line = line.strip()
        words = line.split()
        n = len(words)
        if n >= 4:
            name = words[0]
            x = float(words[1])
            y = float(words[2])
            z = float(words[3])
            imgFile = ''
            if n >= 5: 
                imgFile = words[4]
            points.append([name, x, y, z, imgFile])
        else:
            continue
    return points

def readPoints(fname, reader):
    points = []
    if fname != None:
        if os.path.exists(fname):
            print('Read points from ', fname)
            points = reader.readPoints(fname)
        else:
            print('File does not exist: %s' % fname)
    else:
        print('File is not specified:', fname)
    return np.array(points)
    
def readScanConfig(fname):
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
        points.append(c)
    f.close()
    return points
