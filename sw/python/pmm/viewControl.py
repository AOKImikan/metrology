#------------------------------------------------------------------------
# pmm: viewControl.py
#---------------------
# View control
#------------------------------------------------------------------------
import copy
import logging
logger = logging.getLogger(__name__)

from functools import partial

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .acommon import setAppCommon
from .amodel import *
from .handlers import *
from .flowlayout import FlowLayout

#class ViewController(QObject):
class ViewModel(QObject):
    
    sigClearGallery = pyqtSignal()
    
    sigPhotoReady = pyqtSignal(str)
    
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view
        #self.gui = None
        #self.controller = None
        self.galleryMainLayout = None
        self.galleryEntries = []
        self.galleryTagLayoutMap = {}

        pass

    def initialize(self):
        setAppCommon(view=self.view, model=self.model, viewModel=self)
        self.selectComponentType(self.model.config.defaultComponentType())
        self.sigPhotoReady.connect(self.handlePhoto)

    def selectComponentType(self, ctype):
        logger.info('Selected component type %s' % ctype)
        #
        stypes = self.model.scanTypes(ctype)
        scanInputs = []
        logger.debug('scan types: %s' % str(stypes))
        for stype in stypes:
            y = self.model.scanInput(ctype, stype)
            if y:
                scanInputs.append(y)
                self.model.setComponentType(ctype)
                self.model.updateScanInputs(scanInputs)
                #
        self.updateScansFrame(scanInputs)
        
    def createScanInput(self, scan):
        box = QGroupBox(scan.scanName)
        layout0 = QVBoxLayout()
        box.setLayout(layout0)
        #
        frame1 = QFrame()
        layout0.addWidget(frame1)
        configLabel = QLabel('Scan config:')
        configList = QComboBox()
        zoomLabel = QLabel('Zoom:')
        zoomList = QComboBox()
        zoomValues = self.model.config.zoomValues()
        logger.debug('%s Default zoom: %d' % (scan.scanName, scan.defaultZoom))
        for i, zoom in enumerate(zoomValues):
            zoomList.addItem(str(zoom))
            if zoom == scan.defaultZoom:
                zoomList.setCurrentIndex(i)
        for i, config in enumerate(scan.configs):
            configList.addItem(config)
            if i == 0:
                configList.setCurrentIndex(i)
        fn = partial(self.view.handlers.useScanConfig, scanName=scan.scanName)
        print(fn, scan.scanName)
        configList.currentTextChanged.connect(fn)
        #
        layout1 = QHBoxLayout()
        frame1.setLayout(layout1)
        layout1.setContentsMargins(2, 2, 2, 2)
        layout1.addWidget(configLabel)
        layout1.addWidget(configList)
        layout1.addWidget(zoomLabel)
        layout1.addWidget(zoomList)
        #
        logger.debug('%s buttons: %d' % (scan.scanName, len(scan.selectButtonTexts)))
        for ilog, logText in enumerate(scan.selectButtonTexts):
            logger.debug('Button Text : %s' % logText)
            logFileEntry = QLineEdit()
            button = QPushButton(logText)
            #
            layout2 = QHBoxLayout()
            layout2.setContentsMargins(2, 2, 2, 2)
            layout2.addWidget(logFileEntry)
            layout2.addWidget(button)
            frame2 = QFrame()
            frame2.setLayout(layout2)
            layout0.addWidget(frame2)
            button.clicked.connect(partial(self.view.handlers.selectLogFile, scan.scanName, logFileEntry, ilog))
        #
        return box

    def updateScansFrame(self, scanInputs):
        logger.info('Update scan sets (x%d)' % len(scanInputs))
        frame = self.view.frameScans
        layout = frame.layout()
        layout.children().clear()
        while layout.count()>0:
            layout.itemAt(0).widget().setParent(None)
        for scanInput in scanInputs:
            box = self.createScanInput(scanInput)
            layout.addWidget(box)
        pass

    def updateTable(self, tableName, data, columnHeaders=None, rowTags=[]):
        logger.debug('Try to update %s table (entries=%d)' %(tableName, len(data)))
        table = self.view.getTable(tableName)
        if table == None:
            return False
        nrows = table.rowCount()
        ncols = table.columnCount()
        table.clear()#removeRows(0, nrows-1)
        #n1 = len(columnHeaders)
        #if n1>0 and n1 != ncols:
        #    pass
        logging.debug(f'Update table {len(data)} rows')
        nTags = len(rowTags)
        for i in range(len(data)):
            for j in range(len(data[i])):
                logger.debug('Table item[%d,%d]: %s' % (i, j, str(data[i][j])) )
                cdata = data[i][j]
                if j > 0:
                    #cdata = '%5.3f' % data[i][j]
                    cdata = '%6.4f' % data[i][j]
                item = QTableWidgetItem(cdata)
                bgcolor = Qt.white;
                fgcolor = Qt.black
                if nTags>=(i+1):
                    if rowTags[i] == '':
                        bgcolor = Qt.white;
                        fgcolor = Qt.black
                    elif rowTags[i] == 'Good':
                        bgcolor = Qt.white;
                        fgcolor = Qt.black
                    elif rowTags[i] == 'Bad':
                        bgcolor = Qt.white;
                        fgcolor = Qt.black
                item.setBackground(bgcolor)
                item.setForeground(fgcolor)
                table.setItem(i, j, item)
        return True

    def addTag(self, tag):
        pass
    
    def addImageForTag(self, tag, imagePath):
        pass
    
    @Slot()
    def clearGallery(self):
        logger.info(f'Clear gallery')
        panel = self.view.getComponent('PhotoPanel')
        
        self.galleryEntries = []
        self.galleryTagLayoutMap = {}
        pass
    
    @Slot(str)
    def handlePhoto(self, imageTagName):
        logger.info(f'Handle photo for {imageTagName}')
        tag, name = tuple(imageTagName.split('/'))
        logger.info(f'Handle photo {tag} - {name}')

        if imageTagName in self.galleryEntries:
            logger.warning(f'Image {imageTagName} already in the gallery')
            return

        if self.galleryMainLayout == None:
            panel = self.view.getComponent('PhotoPanel')
            layout1 = QVBoxLayout()
            panel.setLayout(layout1)
            #
            msg = QTextEdit('If there is a problem with the detected points on the image, set the correct location of the pattern by double clicking on the image')
            msg.setObjectName('photoMessage')
            msg.setEnabled(False)
            layout1.addWidget(msg)
            self.galleryMainLayout = layout1
            logger.info('Created the main layout of the photo panel')

        logger.debug(f'  gallery tags: {self.galleryTagLayoutMap.keys()}')
        if not tag in self.galleryTagLayoutMap.keys():
            self.galleryMainLayout.addWidget(QLabel(tag))
            frame = QFrame()
            self.galleryMainLayout.addWidget(frame)
            layout2 = FlowLayout()
            frame.setLayout(layout2)
            self.galleryTagLayoutMap[tag] = layout2

        layout2 = self.galleryTagLayoutMap[tag]
        imageNP = self.model.findImageNP(imageTagName)
        logger.debug(f'  image path: {imageNP.filePath}, {imageNP.imageQ}')
        # Check if the image is already read from file
        if imageNP == None:
            logger.warning(f'Cannot find image data for {imageTagName}')
            return
        if imageNP.imageQResized:
            logger.debug('  Resized image is already available')
            pass
        elif imageNP.imageQ:
            logger.debug('  Create scaled image for display')
            w, h = 180, 120
            imageScaled = imageNP.imageQ.scaled(w, h, Qt.KeepAspectRatio)
            imageNP.imageQResized = imageScaled
        elif os.path.exists(imageNP.filePath):
            logger.debug('  Read image and create a scaled one for display')
            w, h = 180, 120
            imageQ = QPixmap(imageNP.filePath)
            imageScaled = imageQ.scaled(w, h, Qt.KeepAspectRatio)
            imageNP.imageQ = imageQ
            imageNP.imageQResied = imageScaled
        #
        logger.debug('    Display resized image for %s' % (imageTagName))
        if imageNP.imageQResized:
            imgLabel = QLabel('Empty')
            imgLabel.setPixmap(imageNP.imageQResized)
            layout2.addWidget(imgLabel)
            # Add event handler
            sp = self.model.currentScanProcessor()
            analysis = None
            if sp:
                analysis = sp.findImageOwner(imageTagName) # Analysis
            if not sp:
                analysis = self.model.findImageOwnerAnalysis(imageTagName)
            args = (imageTagName, imageNP, analysis, imgLabel)
            imgLabel.mouseDoubleClickEvent = \
                partial(self.setPointOnImage2, args)

        pass
    
    def updatePhotoDetail(self, panel, tagPatternsMap):
        tags = tagPatternsMap.keys()
        logger.debug('tags = %s', str(tags))

        layout1 = QVBoxLayout()
        panel.setLayout(layout1)

        self.photoLayouts = {
        }

        logger.debug('Update photo detail')
        msg = QTextEdit('If there is a problem with the detected points on the image, set the correct location of the pattern by double clicking on the image')
        msg.setObjectName('photoMessage')
        msg.setEnabled(False)
        layout1.addWidget(msg)

        #n = len(scanConfig.pointConfigList)
        for tag in tags:
            layout1.addWidget(QLabel(tag))
            frame = QFrame()
            layout1.addWidget(frame)
            layout2 = FlowLayout()
            frame.setLayout(layout2)
            self.photoLayouts[tag] = layout2

            patterns = tagPatternsMap[tag]
            logger.debug('Number of details for tag %s is %d' %\
                         (tag, len(patterns) ) )
            for details in patterns:
                thumbnailPath = details.thumbnailPath
                if os.path.exists(thumbnailPath):
                    logger.debug('Read thumbnail: %s' % thumbnailPath)
                    w, h = 180, 120
                    image = QPixmap(thumbnailPath)
                    imageScaled = image.scaled(w, h, Qt.KeepAspectRatio)
                    imgLabel = QLabel('Empty')
                    imgLabel.setPixmap(imageScaled)
                    layout2.addWidget(imgLabel)
                    imgLabel.mouseDoubleClickEvent = \
                        partial(self.setPointOnImage, (details, imgLabel) )
        pass
    
    def setPointOnImage(self, detailsAndLabel, event):
        patternDetails = detailsAndLabel[0]
        label = detailsAndLabel[1]
        w0, h0 = 600, 400
        w1, h1 = 180, 120
        scale = w0/w1
        x0, y0 = patternDetails.offsetXY
        fpath2b = patternDetails.thumbnailPath0
        pos = event.localPos()
        c, r = int(pos.x()*scale), int(pos.y()*scale)

        print('in setPointOnImage')
        logger.debug('Double-clicked on %s' % str( (c, r) ) )
        logger.debug('  add the point to %s' % fpath2b)
        logger.debug('  photo at %6.3f, %6.3f' % (x0, y0) )
        offset = CvPoint(x0, y0)
        zoom1 = patternDetails.zoom/scale
        frame = ImageFrame(offset, patternDetails.zoom/scale, w0, h0)
        frame.setSize(w0, h0, dx20*6000, dx20*4000)
        logger.debug('  pixel size: %6.4f, w=%d zoom(small)=%6.3f' %\
                     (frame.pixelSize, frame.width, zoom1))
        p = frame.toGlobal( (c, r) )
        logger.debug('  New position = %6.3f, %6.3f' % (p.x(), p.y()))
        patternDetails.addManualPoint( (p.x(), p.y()), (c, r) )
        #
        image = QPixmap(patternDetails.thumbnailPath)
        imageScaled = image.scaled(w1, h1, Qt.KeepAspectRatio)
        label.setPixmap(imageScaled)
        #

    def setPointOnImage2(self, args, event):
        #patternDetails = detailsAndLabel[0]
        #label = detailsAndLabel[1]
        tagName = args[0]
        imageNP = args[1]
        analysis = args[2]
        label = args[3]
        tag, name = tuple(tagName.split('/'))
        name = name.replace('_p1', '').replace('_p2', '')
        w0, h0 = 600, 400
        w1, h1 = 180, 120
        scale = w0/w1
        x0 = imageNP.xyOffset[0]
        y0 = imageNP.xyOffset[1]
        fpath2b = imageNP.filePath ### update file name (for now overwrite)
        pos = event.localPos()
        c, r = int(pos.x()*scale), int(pos.y()*scale)

        logger.debug(f'in setPointOnImage {tag}/{name}')
        logger.debug('Double-clicked on %s' % str( (c, r) ) )
        logger.debug('  add the point to %s' % fpath2b)
        logger.debug('  photo at %6.3f, %6.3f' % (x0, y0) )
        offset = CvPoint(x0, y0)
        zoom1 = imageNP.zoom/scale
        frame = ImageFrame(offset, imageNP.zoom/scale, w0, h0)
        frame.setSize(w0, h0, dx20*6000, dx20*4000)
        logger.debug('  pixel size: %6.4f, w=%d zoom(small)=%6.3f' %\
                     (frame.pixelSize, frame.width, zoom1))
        p = frame.toGlobal( (c, r) )
        logger.debug('  New position = %6.3f, %6.3f' % (p.x(), p.y()))
        suffix = '_p1'
        key = name
        if key.endswith(suffix): key = key[0:-len(suffix)]
        pp2 = Point([p[0], p[1]])
        key1 = f'{key}_point'
        keyx = f'{key}_x'
        keyy = f'{key}_y'
        if key1 in analysis.outData.keys():
            pp1 = analysis.outData[key1]
            logger.info(f'  Overwrite point {pp1} to {pp2}')
        else:
            logger.info(f'  Overwrite point to {pp2}')
        analysis.outData[key1] = pp2
        analysis.outData[keyx] = MeasuredValue(keyx, p.x(), 0.0)
        analysis.outData[keyy] = MeasuredValue(keyy, p.y(), 0.0)
        #
        rec = None
        if tag in analysis.tagImagePatterns.keys() and \
           name in analysis.tagImagePatterns[tag].keys():
            rec = analysis.tagImagePatterns[tag][name]
        if rec:
            rec.addManualPoint( (p.x(), p.y()), [c, r])
            if os.path.exists(rec.imageP2Path):
                logger.debug(f'  Read image (2b) {rec.imageP2Path}')
                image = QPixmap(rec.imageP2Path)
                imageScaled = image.scaled(w1, h1, Qt.KeepAspectRatio)
                label.setPixmap(imageScaled)
                analysis.propagateChanges()
                scanp = analysis.scanProcessor
                #
                if scanp:
                    stype, tdata = scanp.tableData()
                    if len(tdata)>0:
                        logger.info('Update table %s for %s' % (stype, scanp.name))
                        self.updateTable('Table:%s' % stype, tdata)
            else:
                logger.warning(f'  Image {rec.imageP2Path} does not exist')
        else:
            logger.warning(f'  PatternRecImage for {tag}/{name} does not exist')
        #

    def addPointOnImage(self, imageNP, xy, cr):
        fpath1b = imageNP.filePath.replace('_p1.jpg', '_p1b.jpg')
        radius=10
        color_point = (0, 255, 0)
        img = cv2.imread(imageNP.filePath)
        cv2.circle(img, cr, radius, color_point, thickness=-2)
        cv2.imwrite(fpath1b, img)
        imageNPb = copy.copy(imageNP)
        imageNPb.filePath = fpath1b
        return imageNPb

    def updateRawData(self, scan):
        pass
    
    def updateModuleModel(self, scan):
        pass


