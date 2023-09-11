#------------------------------------------------------------------------
# pmm: data2.py
#---------------
# Internal data used for scans
#------------------------------------------------------------------------
import cv2
import logging
logger = logging.getLogger(__name__)

from .reader import *
from .data1 import *
from .prec import CvPoint, pixelSizeForZoom

class ImageNP:
    def __init__(self, name, filePath, image=None):
        self.name = name
        self.filePath = filePath
        self.image = image
        self.xyOffset = [0.0, 0.0]
        self.width = 6000
        self.height = 4000
        self.zoom = 20
        self.pixelSize = pixelSizeForZoom(20)
        self.imageCV = None
        self.imageQ = None
        self.imageQResized = None

    def persKeys(self):
        return ['name','filePath', 'xyOffset', 'width', 'height', 'zoom',
                'pixelSize' ]
    
    def imageReady(self):
        t = type(image)
        tn = type(None)
        s = False
        if t != tn:
            s = True
        return s

    def readImageBW(self, fn=''):
        if fn != '':
            self.filePath = fn
        self.image = cv2.imread(self.filePath, cv2.IMREAD_GRAYSCALE)
        return self.image

    
    def toGlobal(self, col, row):
        x = self.xyOffset[0] + col*self.pixelSize
        y = self.xyOffset[1] + (self.height/2 - row) * self.pixelSize
        return CvPoint(x, y)
        

class ScanData:
    def __init__(self, configPath, zoom, logPath):
        self.configPath = configPath
        self.zoom = zoom
        self.logPath = logPath
        #
        self.points = []
        self.results = None
        pass

    def persKeys(self):
        return ['configPath', 'zoom', 'logPath', 'points', 'results']
    
    def setLogFile(self, fname):
        self.logPath = fname
        self.logDir = os.path.dirname(fname)

    def setConfigFile(self, fname):
        self.configPath = fname

    def nPoints(self):
        return len(self.points)
    
    def listImages(self):
        v = []
        dn = os.path.dirname(self.logPath)
        files = os.listdir(dn)
        for fn in files:
            if fn.endswith('.jpg'):
                v.append(os.path.join(dn, fn))
        return v

    def pointsWithTag(self, tag):
        points = []
        for p in self.points:
            if tag in p.get('tags'):
                points.append(p)
        return points
    
    def read(self):
        logger.debug('Reading input data from %s (%s) (zoom=%d)' %\
                     (self.logPath, self.configPath, self.zoom))
        log_ok = os.path.exists(self.logPath)
        config_ok = os.path.exists(self.configPath)
        if not log_ok:
            logger.warning('No scan log file %s' % self.logPath)
        if not config_ok:
            logger.warning('No scan config file %s' % self.configPath)
        if not (log_ok and config_ok):
            return False
        print('log/config ', log_ok, config_ok)
        #
        self.points.clear()
        reader = ReaderB4v1()
        configPoints = readScanConfig(self.configPath)
        dataPoints = []
        logType = reader.checkFormat(self.logPath)
        if logType == 0 or logType == 1:
            dataPoints = reader.readPoints(self.logPath)
        elif logType == 2:
            v = reader.readPointsSize(self.logPath)
            #print(v)
            dname = os.path.dirname(self.logPath)
            dataPoints = []
            for x in v:
                fname = x[3]
                if fname != '':
                    i1 = fname.rfind('\\')
                    if i1>=0: fname = fname[i1+1:]
                    fname = os.path.join(dname, fname)
                y = [x[0], x[1], 0.0, fname, True]
                dataPoints.append(y)
            #logger.debug(f'{dataPoints}')
        imageList = self.listImages()
        #
        n1, n2, n3 = len(configPoints), len(dataPoints), len(imageList)
        logger.info(f'Number of points in config,log,images={n1},{n2},{n3}')
        if n1 == n2 or n2 == (n1+1):
            self.points = []
            for i in range(n1):
                cp = configPoints[i]
                dp = dataPoints[i]
                #print(dp)
                ipath = imageList[i]
                point = ScanPoint()
                point.setIndex(i)
                point.setXYZ(dp[0], dp[1], dp[2])
                point.setError(not dp[3])
                point.setZoom(self.zoom)
                point.setImagePath(ipath)
                point.setTags(cp.tags)
                self.points.append(point)
            logger.info('Read %d scan points from %s' %\
                     (len(self.points), self.logPath))
            for i, p in enumerate(self.points):
                logger.debug(f"  point[{i}] {p.get('x'):5.3f}, {p.get('y'):5.3f}: {cp.tags}")
        else:
            logger.warning('Number of points mismatch (config/log): %d vs. %d' %\
                        (n1, n2))
        return True
    def allTags(self):
        tags = []
        for p in self.points:
            ptags = p.value('tags')
            for tag in ptags:
                if not tag in tags:
                    tags.append(tag)
        return tags
    pass

