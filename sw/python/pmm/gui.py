#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# 
#--------------------------------------------------------------------

import os
import logging
logger = logging.getLogger(__name__)

from functools import partial
import threading
import pickle
import json

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .flowlayout import FlowLayout

# Need to be removed
from .model import *
from .reader import *
from .design import *
from .prec import *
from .workflow import *
from .AppData import *


moduleTypes = (
    'Rd53aBareModule', 
    'Rd53aFlex',
    'Rd53aModule',
    'Rd53aModuleBack', 
    'ITkPixV1xBareModule',
    'ITkPixV1xBareModuleBack',
    'ITkPixV1xFlex',
    'ITkPixV1xModule', 
    'ITkPixV1xModuleBack', 
    )
testSteps = (
    'Step1 - Reception test', 
    'Step2 - After assembly', 
    'Step3 - After wirebonding', 
    'Step4 - After parylene coating', 
    'Step5 - After wirebond protection', 
    'Step6 - After burn-in',
    'StepA - Before population', 
    'StepB - After population', 
    )
    
class PmmWindow(QMainWindow):
    signalProcessPhoto = pyqtSignal(str, str, int)
    signalDecoratePhoto = pyqtSignal(str, str, int)

    def __init__(self, configFile=None):
        super().__init__()
        self.title = 'Pixel module metrology analysis'
        self.width = 1300
        self.height = 800

        # Get rid of all the following
        self.configStore = ConfigStore(configFile)
        self.data = AppData(os.path.join(self.configStore.workDir, 'AppData'))

    def setHandlers(self, handlers):
        self.handlers = handlers
        
    def setup(self):
        #
        #self.handlers = GuiHandlers(self, self.data, self.configStore)
        
        self.data.moduleType = 'Rd53aModule'
        self.data.moduleName = 'KEKQ000'
        self.moduleDesign = createModule(self.data.moduleType)

        #cvConfig = self.configStore.componentViewConfig
        #self.componentView = cvConfig.componentView(self.data.moduleType)

        self.data.heightZoom = 20
        self.data.sizeZoom = 20
        self.data.flatnessZoom = 20

        #
        self.componentMap = {}
        self.buildGui()

    def getComponent(self, cName):
        x = None
        if cName in self.componentMap.keys():
            x = self.componentMap[cName]
        return x
    
    def getTable(self, tableName):
        table = None
        if tableName in self.componentMap.keys():
            table = self.componentMap[tableName]
        return table
    
    def buildGui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, self.width, self.height)
        self.statusBar().showMessage('Started')

        menuBar = self.menuBar()
        self.buildMenu(menuBar)
        self.componentMap['MenuBar'] = menuBar

        main = QSplitter(Qt.Horizontal)
        main.setObjectName('main')
        self.setCentralWidget(main)
        frame1 = QSplitter(Qt.Vertical)
        self.frameDetail = QFrame()
        self.frameDetail.setObjectName('frameDetail')
        main.addWidget(frame1)
        main.addWidget(self.frameDetail)
        main.setSizes([2, 1])
        self.componentMap['Frame:Detail'] = self.frameDetail

        frame2 = QSplitter(Qt.Horizontal)
        self.frameLog = QTextEdit()
        self.frameLog.setObjectName('frameLog')
        self.frameLog.resize(800, 300)
        frame1.addWidget(frame2)
        frame1.addWidget(self.frameLog)
        frame1.setSizes([300, 100])
        self.componentMap['Frame:Log'] = self.frameLog

        self.frameConfig = QFrame()
        self.frameSummary = QFrame()
        self.frameConfig.setObjectName('frameConfig')
        self.frameSummary.setObjectName('frameSummary')
        frame2.addWidget(self.frameConfig)
        frame2.addWidget(self.frameSummary)
        frame2.setSizes([1, 1])
        self.componentMap['Frame:Config'] = self.frameConfig
        self.componentMap['Frame:Summary'] = self.frameSummary

        # Input panel
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.frameConfig.setLayout(layout)
        layout.addWidget(self.buildModulePanel())
        self.frameScans = QFrame()
        self.frameScans.setObjectName('frameScans')
        layout.addWidget(self.frameScans)
        self.componentMap['Frame:Scans'] = self.frameScans

        layout1 = QVBoxLayout()
        layout1.setContentsMargins(5, 5, 5, 5)
        self.frameScans.setLayout(layout1)
        #self.buildInputBoxes(layout1)
        
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.buildControlFrame())

        # Summary panel
        layout = QHBoxLayout()
        self.frameSummary.setLayout(layout)
        self.summaryTab = QTabWidget()
        layout.addWidget(self.summaryTab)
        self.summaryTab.addTab(QFrame(), 'Summary')
        self.summaryTab.addTab(QFrame(), 'Height')
        self.summaryTab.addTab(QFrame(), 'Size')
        self.summaryTab.addTab(QFrame(), 'Flatness')
        self.componentMap['Frame:OverallSummary'] = self.summaryTab.widget(0)
        self.componentMap['Frame:HeightSummary'] = self.summaryTab.widget(1)
        self.componentMap['Frame:SizeSummary'] = self.summaryTab.widget(2)
        self.componentMap['Frame:FlatnessSummary'] = self.summaryTab.widget(3)

        self.buildSummary(self.summaryTab.widget(0))
        self.buildHeightSummary(self.summaryTab.widget(1))
        self.buildSizeSummary(self.summaryTab.widget(2))
        self.buildFlatnessSummary(self.summaryTab.widget(3))

        # Details panel
        layout = QHBoxLayout()
        self.frameDetail.setLayout(layout)
        self.detailTab = QTabWidget()
        layout.addWidget(self.detailTab)
        self.detailTab.addTab(QFrame(), 'Raw data')
        self.detailTab.addTab(QFrame(), 'Module')
        self.detailTab.addTab(QFrame(), 'Height')
        self.detailTab.addTab(QFrame(), 'Size')
        self.detailTab.addTab(QFrame(), 'Flatness')
        self.detailTab.addTab(QFrame(), 'Photo')
        self.componentMap['Frame:Raw'] = self.detailTab.widget(0)
        self.componentMap['Frame:Module'] = self.detailTab.widget(1)
        self.componentMap['Frame:HeightDetails'] = self.detailTab.widget(2)
        self.componentMap['Frame:SizeDetails'] = self.detailTab.widget(3)
        self.componentMap['Frame:FlatnessDetails'] = self.detailTab.widget(4)
        self.componentMap['Frame:Photo'] = self.detailTab.widget(5)

        self.buildDataDetail(self.detailTab.widget(0))
        self.buildModuleDetail(self.detailTab.widget(1))
        self.buildHeightDetail(self.detailTab.widget(2))
        self.buildSizeDetail(self.detailTab.widget(3))
        self.buildFlatnessDetail(self.detailTab.widget(4))
        self.buildPhotoDetail(self.detailTab.widget(5))

        #self.btnExit.clicked.connect(self.close)

    def buildMenu(self, menuBar):
        menuFile = menuBar.addMenu('&File')
        menuOption = menuBar.addMenu('&Options')
        menuHelp = menuBar.addMenu('&Help')

        actionOpen = QAction('&Open', self)
        actionOpen.setShortcut('Ctrl-O')
        actionOpen.triggered.connect(self.openModuleFile)
        menuFile.addAction(actionOpen)

    def openModuleFile(self):
        files = QFileDialog.getOpenFileName(self, 'Open module file',
                                            self.configStore.workDir, 
                                            'Pickle files (*.pickle)')
        fname = files[0]
        data = loadAppData(fname)
        if data!=None:
            logger.info('Opened module file %s' % fname)
            self.data = data
            self.data.scanResults = MetrologyScanResults()
        else:
            logger.warning('Cannot load module file %s' % fname)
        self.processPickupHeight()
        self.updateSizeScanTable()
        self.updateFlatnessScanTable()

    def relfectAppDataToGui(self):
        print(data)
        
    def closeEvent(self, event):
        logger.info('Closing the main window')
        #self.data.save()

    def buildModulePanel(self):
        panel = QFrame()
        layout1 = QVBoxLayout()
        layout1.setContentsMargins(2, 2, 2, 2)
        panel.setLayout(layout1)
        frame1 = QFrame()
        frame2 = QFrame()
        frame3 = QFrame()
        layout1.addWidget(frame1)
        layout1.addWidget(frame2)
        layout1.addWidget(frame3)

        # Module type
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        frame1.setLayout(layout)
        layout.addWidget(QLabel(text='Module type: '))
        typeBox = QComboBox()
        #typeBox = QLineEdit(self.data.moduleType)
        for c in moduleTypes:
            typeBox.addItem(c)
        #typeBox.currentTextChanged.connect(self.handlers.selectComponentType)
        typeBox.currentTextChanged.connect(self.handlers.selectComponentType)
        layout.addWidget(typeBox)

        # Test step
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        frame2.setLayout(layout)
        layout.addWidget(QLabel(text='Test step: '))
        stepBox = QComboBox()
        for c in testSteps:
            stepBox.addItem(c)
        stepBox.currentTextChanged.connect(self.setTestStep)
        layout.addWidget(stepBox)
        
        # Module name
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        frame3.setLayout(layout)
        nameBox = QLineEdit(self.data.moduleName)
        layout.addWidget(QLabel('Module name: '))
        layout.addWidget(nameBox)
        nameBox.textChanged.connect(self.setModuleName)
        return panel

    def buildControlFrame(self):
        frame = QFrame()
        frame.setObjectName('controlFrame')
        layout1 = QVBoxLayout()
        layout1.setContentsMargins(2, 2, 2, 2)
        frame.setLayout(layout1)

        buttons = []
        #texts = ('Pickup, Height', 'All', 'Flatness', 'Done')
        texts = ('All','Done')
        for x in texts:
            text = 'Process %s' % x
            if x == 'Done': text = 'Done (create JSON file)'
            frame2 = QFrame()
            layout1.addWidget(frame2)
            layout2 = QHBoxLayout()
            layout2.setContentsMargins(2, 2, 2, 2)
            frame2.setLayout(layout2)
            button = QPushButton(text)
            layout2.addWidget(button)
            layout2.addStretch()
            if x == texts[0]:
                button.clicked.connect(self.handlers.processAllScans)
            elif x == texts[1]:
                button.clicked.connect(self.saveJsonFile)
            buttons.append(button)
        return frame

    def buildSummary(self, panel):
        pass
    def buildHeightSummary(self, panel):
        cols = ['Tag', 'z [mm]', 'dz [mm]', 'z (ref)', 'Tolerance']
        data = [
            ['Jig', 0.0, 0.0, 0.0, 0.0], 
            ['Asic', 0.0, 0.0, 0.0, 0.0], 
            ['Sensor', 0.0, 0.0, 0.0, 0.0], 
            ['Flex', 0.0, 0.0, 0.0, 0.0], 
            ['Pickup1', 0.0, 0.0, 0.0, 0.0], 
            ['Pickup2', 0.0, 0.0, 0.0, 0.0], 
            ['Pickup3', 0.0, 0.0, 0.0, 0.0], 
            ['Pickup4', 0.0, 0.0, 0.0, 0.0], 
            ['FlexLSide', 0.0, 0.0, 0.0, 0.0], 
            ['FlexRSide', 0.0, 0.0, 0.0, 0.0], 
            ['Connector', 0.0, 0.0, 0.0, 0.0], 
            ['HVCapacitor', 0.0, 0.0, 0.0, 0.0], 
            ]
        for i, entry in enumerate(data):
            key = entry[0]
            if self.moduleDesign and \
               key in self.moduleDesign.valueToleranceData.keys():
                dv, dt = self.moduleDesign.valueToleranceData[key]
                if dv: entry[3] = dv
                if dt: entry[4] = dt
        self.heightEntryMap = {}
        for i, x in enumerate(data):
            k = x[0]
            self.heightEntryMap[k] = i
        self.heightSummaryTable = QTableWidget(len(data), len(cols))
        self.heightSummaryTable.setHorizontalHeaderLabels(cols)
        for i, entry in enumerate(data):
            for col, value in enumerate(entry):
                itemValue = QTableWidgetItem(value)
                if col>0:
                    itemValue = QTableWidgetItem('%6.3f' % value)
                self.heightSummaryTable.setItem(i, col, itemValue)
        self.heightSummaryTable.resizeRowsToContents()
        self.heightSummaryTable.resizeColumnsToContents()
        self.componentMap['Table:Height'] = self.heightSummaryTable
        layout = QVBoxLayout()
        #layout.addWidget(QLabel('Test'))
        layout.addWidget(self.heightSummaryTable)
        panel.setLayout(layout)
        pass
    def buildSizeSummary(self, panel):
        cols = ['Tag', 'Value [mm]', 'Error [mm]', 'Ref.', 'Tolerance' ]
        data = [
            ['AsicT', 0.0, 0.0, 0.0, 0.0], 
            ['AsicB', 0.0, 0.0, 0.0, 0.0], 
            ['AsicL', 0.0, 0.0, 0.0, 0.0], 
            ['AsicR', 0.0, 0.0, 0.0, 0.0], 
            ['SensorT', 0.0, 0.0, 0.0, 0.0], 
            ['SensorB', 0.0, 0.0, 0.0, 0.0], 
            ['SensorL', 0.0, 0.0, 0.0, 0.0], 
            ['SensorR', 0.0, 0.0, 0.0, 0.0], 
            ['FlexT', 0.0, 0.0, 0.0, 0.0], 
            ['FlexB', 0.0, 0.0, 0.0, 0.0], 
            ['FlexL', 0.0, 0.0, 0.0, 0.0], 
            ['FlexR', 0.0, 0.0, 0.0, 0.0], 
            ['AsicToFlexL', 0.0, 0.0, 0.0, 0.050], 
            ['AsicToFlexR', 0.0, 0.0, 0.0, 0.050], 
            ['SensorToFlexT', 0.0, 0.0, 0.0, 0.050], 
            ['SensorToFlexB', 0.0, 0.0, 0.0, 0.050], 
            ['Angle', 0.0, 0.0, 0.0, 0.050], 
            ['AsicX', 0.0, 0.0, 0.0, 0.0], 
            ['AsicY', 0.0, 0.0, 0.0, 0.0], 
            ['SensorX', 0.0, 0.0, 0.0, 0.0], 
            ['SensorY', 0.0, 0.0, 0.0, 0.0], 
            ['FlexX', 0.0, 0.0, 0.0, 0.0], 
            ['FlexY', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ['', 0.0, 0.0, 0.0, 0.0], 
            ]
        for i, entry in enumerate(data):
            key = entry[0]
            if self.moduleDesign and \
               key in self.moduleDesign.valueToleranceData.keys():
                dv, dt = self.moduleDesign.valueToleranceData[key]
                if dv: entry[3] = dv
                if dt: entry[4] = dt
        self.sizeEntryMap = {}
        for i, x in enumerate(data):
            k = x[0]
            self.sizeEntryMap[k] = i
        self.sizeSummaryTable = QTableWidget(len(data), len(cols))
        self.sizeSummaryTable.setHorizontalHeaderLabels(cols)
        for i, entry in enumerate(data):
            for col, value in enumerate(entry):
                itemValue = QTableWidgetItem(value)
                if col>0:
                    itemValue = QTableWidgetItem('%6.3f' % value)
                item = QTableWidgetItem(itemValue)
                self.sizeSummaryTable.setItem(i, col, item)
        self.sizeSummaryTable.resizeRowsToContents()
        self.sizeSummaryTable.resizeColumnsToContents()
        self.componentMap['Table:Size'] = self.sizeSummaryTable
        layout = QVBoxLayout()
        #layout.addWidget(QLabel('Test'))
        layout.addWidget(self.sizeSummaryTable)
        panel.setLayout(layout)
        pass
    def buildFlatnessSummary(self, panel):
        cols = ['Key', 'Value', 'Ref.', 'Tolerance' ]
        data = [
            ('p0', 0.0, 0.0, 0.0), 
            ('p1', 0.0, 0.0, 0.0), 
            ('p2', 0.0, 0.0, 0.0), 
            ('dz(max)', 0.0, 0.0, 0.0), 
            ('dz(min)', 0.0, 0.0, 0.0), 
            ('dz(max-min)', 0.0, 0.0, 0.0), 
            ('z(average)', 0.0, 0.0, 0.0), 
            ]
        self.flatnessSummaryTable = QTableWidget(len(data), len(cols))
        self.flatnessSummaryTable.setHorizontalHeaderLabels(cols)
        for i, entry in enumerate(data):
            for col, value in enumerate(entry):
                itemValue = QTableWidgetItem(value)
                if col > 0:
                    itemValue = QTableWidgetItem('%6.3f' % value)
                item = QTableWidgetItem(itemValue)
                self.flatnessSummaryTable.setItem(i, col, item)
        #self.flatnessSummaryTable.resizeRowsToContents()
        self.flatnessSummaryTable.resizeColumnsToContents()
        self.componentMap['Table:Flatness'] = self.flatnessSummaryTable
        layout = QVBoxLayout()
        layout.addWidget(self.flatnessSummaryTable)
        panel.setLayout(layout)
        pass
    def buildDataDetail(self, panel):
        layout1 = QVBoxLayout()
        frame1 = QGroupBox()
        frame2 = QFrame()
        layout1.addWidget(frame1)
        layout1.addWidget(frame2)
        panel.setLayout(layout1)

        rbutton1 = QRadioButton('Height')
        rbutton2 = QRadioButton('Size')
        rbutton3 = QRadioButton('Flatness (Vac. On)')
        rbutton4 = QRadioButton('Flatness (Vac. Off)')
        rbutton1.toggled.connect(partial(self.updateRawDataTable, 'Height'))
        rbutton2.toggled.connect(partial(self.updateRawDataTable, 'Size'))
        rbutton3.toggled.connect(partial(self.updateRawDataTable, 'FlatnessVacOn'))
        rbutton4.toggled.connect(partial(self.updateRawDataTable, 'FlatnessVacOff'))
        layout2 = QHBoxLayout()
        layout2.addWidget(rbutton1)
        layout2.addWidget(rbutton2)
        layout2.addWidget(rbutton3)
        layout2.addWidget(rbutton4)
        frame1.setLayout(layout2)

        cols = [ 'Tag', 'x [mm]', 'y [mm]', 'z [mm]', 'Photo', 'Zoom' ]
        data = [
            ('', 0.0, 0.0, 0.0, '-', 0)
        ]
        table = QTableWidget(len(data), len(cols))
        layout3 = QVBoxLayout()
        layout3.addWidget(table)
        frame2.setLayout(layout3)
        table.setHorizontalHeaderLabels(cols)
        for i, x in enumerate(data):
            for j, value in enumerate(x):
                logger.debug('row=%d, col=%d -> value=%s' %\
                             (i, j+1, str(value)) )
                item = QTableWidgetItem(str(value))
                table.setItem(i, j, item)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        self.rawDataTable = table
        pass

    def buildModuleDetail(self, panel):
        layout1 = QVBoxLayout()
        frame1 = QGroupBox()
        frame2 = QFrame()
        layout1.addWidget(frame1)
        layout1.addWidget(frame2)
        panel.setLayout(layout1)

        rbutton1 = QRadioButton('Height')
        rbutton2 = QRadioButton('Size')
        rbutton3 = QRadioButton('Flatness (Vac. On)')
        rbutton4 = QRadioButton('Flatness (Vac. Off)')
        rbutton1.toggled.connect(partial(self.updateRawDataTable, 'Height'))
        rbutton2.toggled.connect(partial(self.updateRawDataTable, 'Size'))
        rbutton3.toggled.connect(partial(self.updateRawDataTable, 'FlatnessVacOn'))
        rbutton4.toggled.connect(partial(self.updateRawDataTable, 'FlatnessVacOff'))
        layout2 = QHBoxLayout()
        layout2.addWidget(rbutton1)
        layout2.addWidget(rbutton2)
        layout2.addWidget(rbutton3)
        layout2.addWidget(rbutton4)
        frame1.setLayout(layout2)

        scene = QGraphicsScene(QRectF(0, 0, 400, 400))
        view = QGraphicsView(scene)
        layout3 = QVBoxLayout()
        layout3.addWidget(view)
        frame2.setLayout(layout3)
        self.moduleView = ModuleView()
        self.modulePainter = ModulePainter(scene)
        logger.debug('scene w/h = {0}/{1}'.format(scene.width(), scene.height()))
        components = [
            'Axis', 'Design', 'Asic', 'Sensor', 'Flex', 
        ]
        self.modulePainter.drawModule(self.moduleView, components)

        pass
    def buildHeightDetail(self, panel):
        pass
    def buildSizeDetail(self, panel):
        pass
    def buildFlatnessDetail(self, panel):
        pass

    def buildPhotoDetail(self, panel):
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        layout1 = QVBoxLayout()
        layout1.addWidget(scrollArea)
        panel.setLayout(layout1)

        frame = QFrame()
        frame.setObjectName('PhotoPanel')
        scrollArea.setWidget(frame)

        self.componentMap['PhotoPanel'] = frame
        self.photoPanel = frame
        pass

    def processLogFile(self, ctag):
        logFile = ''
        if ctag == 'Height':
            logFile = self.data.heightLogFile
        elif ctag == 'Size':
            logFile = self.data.sizeLogFile
        elif ctag == 'FlatnessVacOn':
            logFile = self.data.flatnessVacOnLogFile
        elif ctag == 'FlatnessVacOff':
            logFile = self.data.flatnessVacOffLogFile
        logger.debug('Process log file for %s log=%s' % (ctag, logFile))

        if ctag == 'Height':
            self.updateHeightScanResults()
        elif ctag == 'Size':
            self.updateSizeScanResults()
        elif ctag == 'Flatness':
            self.updateFlatnessScanResults()
        else:
            logger.warning('Process log file request for unknown tag %s' % ctag)

    def processPickupHeight(self):
        #reader = ReaderB4v1()
        #logFile = self.data.heightLogFile
        #zoom = 20
        #self.data.scanResults.heightResults = reader.createScanResults(logFile, zoom)
        #logFile = self.data.pickupLogFile
        #zoom = 10
        #self.data.scanResults.heightResults = reader.createScanResults(logFile, zoom)
        #
        self.updateHeightScanResults()
        self.updatePickupScanResults()

    def fullName(self):
        return self.data.fullName()
        
    def saveJsonFile(self):
        #dir = self.moduleDir()
        #fname = os.path.join(dir, 'metrologyResults_%s.json' % self.moduleName)
        fname = os.path.join(self.configStore.workDir,
                             'summary/metrologyResults_%s.json' % self.fullName())
        logger.info('Save metrology results in a JSON file %s' % fname)
        fout = open(fname, 'w')
        json.dump(self.data.summaryJson(), fout, indent=2)
        fout.close()
        logger.info('Saving application data')
        self.data.save()
        
    def updateDataDetail(self, ctag):
        pass

    def openShowPhotos(self, tags, scanConfig, scanResults):
        n = len(scanConfig.pointConfigList)
        for tag in tags:
            logger.info('Read photo in tag %s' % tag)
            for i in range(n):
                config = scanConfig.pointConfig(i)
                if tag=='All' or (config!=None and tag in config.tags):
                    imgFile = scanResults.imagePath(i)
                    data = scanResults.pointResult(i)
                    logger.info('Reading photo %s' % imgFile)
                    self.signalProcessPhoto.emit(tag, imgFile, i)
                    #self.addNewPhoto(tag, imgFile, data)
            break
        logger.debug('Finished opening all photos')
        pass

    def updatePhotoDetail(self, panel, patternDetailsMap):
        tags = patternDetailsMap.keys()
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

            detailsList = patternDetailsMap[tag]
            logger.debug('Number of details for tag %s is %d' %\
                         (tag, len(detailsList) ) )
            for details in detailsList:
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
        self.updateSizeScanTable()

    def recPointInPhoto(self, tag, imageFile, ipoint):
        pointResult = self.data.scanResults.size().pointResult(ipoint)

        targetData = None
        module = Rd53aModule()
        if tag in module.targetData.keys():
            targetData = module.targetData[tag]

        logger.debug('Process image: %s' % imageFile)
        patterns = None
        if targetData != None and tag.find('Jig')<0:
            offset = CvPoint(pointResult.x, pointResult.y)
            frame = ImageFrame(offset, pointResult.zoom)
            dx = 0.3 # mm
            x0 = targetData.x
            y0 = targetData.y
            vedges = [ a+b for a in ('Asic', 'Sensor', 'Flex') for b in ('L', 'R')]
            hedges = [ a+b for a in ('Asic', 'Sensor', 'Flex') for b in ('T', 'B')]
            p1 = CvPoint(x0 - dx, y0 + dx)
            p2 = CvPoint(x0 + dx, y0 - dx)
            cr1 = frame.trimCR(frame.toCR(p1))
            cr2 = frame.trimCR(frame.toCR(p2))
            if tag in vedges:
                h2 = frame.height/2.0
                cr1[1], cr2[1] = int(h2 - h2/2.0), int(h2 + h2/2.0)
            elif tag in hedges:
                w2 = frame.width/2.0
                cr1[0], cr2[0] = int(w2 - w2/2.0), int(w2 + w2/2.0)
                
            wsum, tgap = 30, 30.0
            img = cv2.imread(imageFile)
            patterns = patternRec1(img, targetData.ptype, rect=(cr1, cr2), 
                                   wsum=wsum, tgap=tgap)
        return patterns

    def processPhoto(self, tag, imageFile, ipoint):
        pointResult = self.data.scanResults.size().pointResult(ipoint)
        p = ProcessPhoto(tag, imageFile, pointResult)
        p.start()
            
            
    # Event handlers
    def setZoom(self, ctag, text):
        zoom = 0
        if text != '':
            zoom = int(text)
        if ctag == 'Height':
            self.data.heightZoom = zoom
            logger.info('Height zoom -> %d' % zoom)
        elif ctag == 'Size':
            self.data.sizeZoom = zoom
            logger.info('Size zoom -> %d' % zoom)
        elif ctag == 'Flatness':
            self.data.flatnessZoom = zoom
            logger.info('Flatness zoom -> %d' % zoom)
            
    def setModuleType(self, x):
        logger.info('Module type is %s' % x)
        self.data.moduleType = x
        self.moduleDesign = createModule(self.data.moduleType)
        cvConfig = self.configStore.componentViewConfig
        self.componentView = cvConfig.componentView(self.data.moduleType)
        self.buildInputBoxes(self.frameScans.layout())

    def setTestStep(self, x):
        logger.info('Test step is "%s"' % x)
        self.data.testStep = x
        
    def setModuleName(self, name):
        self.data.moduleName = name

    def selectLogFile(self, ctag, ltext):
        dir = self.configStore.scanDir
        files = QFileDialog.getOpenFileName(self, 'Open scan log', dir)
        logFile = files[0]
        ft = files[1]

        if logFile!=None and logFile!='':
            ltext.setText(logFile)
            dname = os.path.dirname(logFile)
            bname = os.path.basename(logFile)
            self.configStore.scanDir = dname
            reader = ReaderB4v1()
            if ctag == 'Height':
                zoom = self.data.heightZoom
                self.data.heightLogFile = logFile
                self.data.scanResults.heightResults = reader.createScanResults(logFile, zoom)
                #self.updateHeightScanResults()
            elif ctag == 'Pickup':
                zoom = self.data.pickupZoom
                self.data.pickupLogFile = logFile
                self.data.scanResults.pickupResults = reader.createScanResults(logFile, zoom)
                #self.updateHeightScanResults()
            elif ctag == 'Size':
                zoom = self.data.sizeZoom
                self.data.sizeLogFile = logFile
                self.data.scanResults.sizeResults = reader.createScanResults(logFile, zoom, requirePhoto=True)
                #logger.debug('size %d points' % \
                #             self.data.scanResults.sizeResults.nPoints())
                #self.updateSizeScanResults()
            elif ctag == 'FlatnessVacOn':
                zoom = self.data.flatnessZoom
                self.data.flatnessVacOnLogFile = logFile
                self.data.scanResults.flatnessVacOnResults = reader.createScanResults(logFile, zoom)
                logger.info('Reading Flatness VacOn results')
                #self.updateFlatnessScanResults()
            elif ctag == 'FlatnessVacOff':
                zoom = self.data.flatnessZoom
                self.data.flatnessVacOffLogFile = logFile
                self.data.scanResults.flatnessVacOffResults = reader.createScanResults(logFile, zoom)
                logger.info('Reading Flatness VacOff results')
                #self.updateFlatnessScanResults()
    def selectScanConfig(self, ctag, configName):
        logger.debug('Select ScanConfig {0} -> {1}'.format(ctag, configName))
        fname = os.path.join(self.configStore.shareDir, 
                             'ScanConfig_%s.txt' % configName)
        if os.path.exists(fname):
            if ctag == 'Height':
                self.data.heightScanConfig = ScanConfig(fname)
            elif ctag == 'Pickup':
                self.data.pickupScanConfig = ScanConfig(fname)
            elif ctag == 'Size':
                self.data.sizeScanConfig = ScanConfig(fname)
            elif ctag == 'Flatness':
                self.data.flatnessScanConfig = ScanConfig(fname)
        else:
            logger.warn('ScanConfig file %s does not exist' % fname)
    def updateHeightScanResults(self):
        s = self.data.processHeightResults()
        if s != 0:
            return
        nrows = self.heightSummaryTable.rowCount()
        ncols = self.heightSummaryTable.columnCount()
        keys = []
        for i in range(nrows):
            item = self.heightSummaryTable.item(i, 0)
            k = str(item.text())
            keys.append(k)
            logger.debug('Update height data for %s' % k)
            if k in self.data.summary.heightMap.keys():
                x = self.data.summary.heightMap[k]
                z, dz, n = x
                item1 = QTableWidgetItem('%6.3f' % z)
                item2 = QTableWidgetItem('%6.3f' % dz)
                self.heightSummaryTable.setItem(i, 1, item1)
                self.heightSummaryTable.setItem(i, 2, item2)
                tolcheck = self.moduleDesign.isInTolerance(k, z)
                self.cellColors(self.heightSummaryTable, i, 5, tolcheck)
            else:
                # This is not for reporting
                pass
        self.summaryTab.setCurrentIndex(1)
        pass
    
    def cellColors(self, table, irow, ncols, tolcheck):
        bgcolor = Qt.white
        fgcolor = Qt.black
        if tolcheck == 'Pass':
            bgcolor = Qt.green
        elif tolcheck == 'Fail':
            bgcolor = Qt.white
            fgcolor = Qt.red
        else:
            bgcolor = Qt.yellow
        for j in range(ncols):
            c = table.item(irow, j)
            if c:
                c.setBackground(bgcolor)
                c.setForeground(fgcolor)
            else:
                pass
                
    def updatePickupScanResults(self):
        s = self.data.processPickupResults()
        if s != 0:
            return
        nrows = self.heightSummaryTable.rowCount()
        ncols = self.heightSummaryTable.columnCount()
        keys = []
        for i in range(nrows):
            item = self.heightSummaryTable.item(i, 0)
            k = str(item.text())
            keys.append(k)
            if k in self.data.summary.pickupMap.keys():
                x = self.data.summary.pickupMap[k]
                z, dz, n = x
                item1 = QTableWidgetItem('%6.3f' % z)
                item2 = QTableWidgetItem('%6.3f' % dz)
                self.heightSummaryTable.setItem(i, 1, item1)
                self.heightSummaryTable.setItem(i, 2, item2)
                tolcheck = self.moduleDesign.isInTolerance(k, z)
                self.cellColors(self.heightSummaryTable, i, 5, tolcheck)
        self.summaryTab.setCurrentIndex(1)
        pass
    def updateSizeScanResults(self):
        logger.debug('Update size scan results')
        self.data.patternResultsMap = {}
        worker = PatternRecScan(self.data.moduleType, 
                                self.data.moduleDir(self.configStore.workDir), 
                                self.data.scanResults.size(), 
                                self.data.sizeScanConfig, 
                                self.data.patternResultsMap,
                                configStore=self.configStore)
        t1 = threading.Thread(target=worker.run)
        t1.start()
        logger.debug('Try to join')
        t1.join()
        logger.debug('Joined thread')
        #logger.debug(str(self.patternResultsMap))
        self.updatePhotoDetail(self.photoPanel, self.data.patternResultsMap)
        self.updateSizeScanTable()

    def updateSizeScanTable(self):
        self.data.postProcessSizeResults()

        # Update the summary table
        nr = self.sizeSummaryTable.rowCount()
        nc = self.sizeSummaryTable.columnCount()
        tagToRowMap = {}
        logger.debug('N size entries: %d' % len(self.sizeEntryMap))
        for k, i in self.sizeEntryMap.items():
            logger.debug('Size entry %s => index %d' % (k, i) )
            if k in self.data.sizeValueMap.keys():
                z = self.data.sizeValueMap[k]
                entry1 = '%6.3f' % self.data.sizeValueMap[k]
                entry2 = '%6.3f' % self.data.sizeSigmaMap[k]
                self.sizeSummaryTable.item(i, 1).setText(entry1)
                self.sizeSummaryTable.item(i, 2).setText(entry2)
                tolcheck = self.moduleDesign.isInTolerance(k, z)
                self.cellColors(self.sizeSummaryTable, i, 5, tolcheck)
            elif k in self.data.summary.sizeMap.keys():
                z = self.data.summary.sizeMap[k][0]
                entry = '%6.3f' % self.data.summary.sizeMap[k][0]
                self.sizeSummaryTable.item(i, 1).setText(entry)
                tolcheck = self.moduleDesign.isInTolerance(k, z)
                self.cellColors(self.sizeSummaryTable, i, 5, tolcheck)

        logger.debug('Finished updateSizeScanResults(...)')
        self.summaryTab.setCurrentIndex(2)
        self.detailTab.setCurrentIndex(5)
        pass
    def updateFlatnessScanResults(self):
        s = self.data.postProcessFlatnessResults()
        self.updateFlatnessScanTable()

    def updateFlatnessScanTable(self):
        #if s != 0:
        #    return
        nrows = self.flatnessSummaryTable.rowCount()
        ncols = self.flatnessSummaryTable.columnCount()
        keys = []
        logger.debug('flatness rows: %d' % nrows)
        for i in range(nrows):
            item = self.flatnessSummaryTable.item(i, 0)
            k = str(item.text())
            keys.append(k)
            logger.debug('flatness table key: %s' % k)
            if k in self.data.summary.flatnessMap.keys():
                x = self.data.summary.flatnessMap[k]
                logger.debug(str(x))
                #z, dz, n = x
                z = x
                item1 = QTableWidgetItem('%6.3f' % z)
                self.flatnessSummaryTable.setItem(i, 1, item1)
                #item2 = QTableWidgetItem('%6.3f' % dz)
                #self.flatnessSummaryTable.setItem(i, 2, item2)
        self.summaryTab.setCurrentIndex(3)
        pass
    def updateFlatnessVacOnScanResults(self):
        pass
    def updateFlatnessVacOffScanResults(self):
        pass

    def updateRawDataTable(self, ctag):
        object = self.sender()
        if object.isChecked():
            logger.debug('Radio button %s -> is checked' % ctag)
            config = None
            results = None
            if ctag == 'Height':
                config = self.data.heightScanConfig
                results = self.data.scanResults.height()
            elif ctag == 'Size':
                config = self.data.sizeScanConfig
                results = self.data.scanResults.size()
            if results!=None:
                ncols = 5
                n = len(results.pointDataList)
                self.rawDataTable.setRowCount(n)
                for i in range(n):
                    p = results.pointResult(i)
                    if p==None: continue
                    if config!=None:
                        pc = config.pointConfig(i)
                        if pc != None:
                            tags = ','.join(pc.tags)
                            self.rawDataTable.setItem(i,0,QTableWidgetItem(tags))
                    self.rawDataTable.setItem(i, 1, QTableWidgetItem('%6.3f' % p.x))
                    self.rawDataTable.setItem(i, 2, QTableWidgetItem('%6.3f' % p.y))
                    self.rawDataTable.setItem(i, 3, QTableWidgetItem('%6.3f' % p.z))
                    self.rawDataTable.setItem(i, 4,QTableWidgetItem(str(p.photo)))
                    self.rawDataTable.setItem(i, 5, QTableWidgetItem('%d' % p.zoom))
                self.rawDataTable.resizeRowsToContents()
                self.rawDataTable.resizeColumnsToContents()
            else:
                self.rawDataTable.setRowCount(0)
            pass
        else:
            logger.debug('Radio button %s -> is not checked' % ctag)
            pass

class ModulePainter:
    def __init__(self, scene):
        self.scene = scene
        self.width = self.scene.width()
        self.height = self.scene.height()
    def scale(self):
        l = min(self.width, self.height)
        s = l/(2*60.0)
        return s
    def drawModule(self, module, components):
        self.module = module
        if 'Axis' in components:
            self.drawAxis()
        if 'Design' in components:
            self.drawDesign()
        if 'Asic' in components:
            self.drawAsic()
        if 'Sensor' in components:
            self.drawSensor()
        if 'Flex' in components:
            self.drawFlex()
        pass
    def xyToCr(self, xy):
        s = self.scale()
        x = xy[0]*s
        y = xy[1]*s
        cr = [x + self.width/2, self.height/2 - y]
        return cr
    def drawLineXY(self, xy1, xy2):
        cr1 = self.xyToCr(xy1)
        cr2 = self.xyToCr(xy2)
        self.scene.addLine(QLineF(*cr1, *cr2))
        pass
    def drawRectXY(self, xy1, xy2):
        cr1 = self.xyToCr(xy1)
        cr2 = self.xyToCr(xy2)
        cr2[0] -= cr1[0]
        cr2[1] -= cr1[1]
        self.scene.addRect(QRectF(*cr1, *cr2))
        pass
    def drawCircleXY(self, xy1, r):
        cr = self.xyToCr(xy1)
        cr1[0] = cr[0] - r
        cr1[1] = cr[1] - r
        cr2[0] = 2*r
        cr2[1] = 2*r
        self.scene.addEllipse(QRectF(*cr1, *cr2))
        pass
    def drawAxis(self):
        # x-axis
        mx = 58
        my = 58
        x1, y1 = -mx, 0
        x2, y2 = mx, 0
        self.drawLineXY( (x1, y1), (x2, y2) )
        # y-axis
        x1, y1 = 0, -my
        x2, y2 = 0, my
        self.drawLineXY( (x1, y1), (x2, y2) )
    def drawDesign(self):
        logger.info('Draw module design')
        self.drawRectXY( (-40, -40), (40, 40))
        pass
    def drawAsic(self):
        pass
    def drawSensor(self):
        pass
    def drawFlex(self):
        pass


#-----------------------------------------------------------------------
# Obsolete classes
#-----------------------------------------------------------------------
class PhotoData:
    def __init__(self, tag, pointResult, imageFile):
        self.tag = tag
        self.pointResult = pointResult
        self.imageFile = imageFile
        self.image0 = None
        self.processedImage = None
        self.module = Rd53aModule()

    def open(self):
        width, height = 200, 300
        if os.path.exists(self.imageFile):
            self.image0 = QPixmap(self.imageFile)
            self.processedImage = QImage(self.imageFile)
            self.image0 = self.image0.scaled(width, height, Qt.KeepAspectRatio)
            
    def process(self):
        targetData = None
        width, height = 200, 300
        if self.tag in self.module.targetData.keys():
            targetData = self.module.targetData[self.tag]

        logger.debug('Process image')
        if targetData != None and self.tag.find('Jig')<0:
            offset = CvPoint(self.pointResult.x, self.pointResult.y)
            frame = ImageFrame(offset, self.pointResult.zoom)
            dx = 0.3 # mm
            x0 = targetData.x
            y0 = targetData.y
            vedges = [ a+b for a in ('Asic', 'Sensor', 'Flex') for b in ('L', 'R')]
            hedges = [ a+b for a in ('Asic', 'Sensor', 'Flex') for b in ('T', 'B')]
            p1 = CvPoint(x0 - dx, y0 + dx)
            p2 = CvPoint(x0 + dx, y0 - dx)
            cr1 = frame.trimCR(frame.toCR(p1))
            cr2 = frame.trimCR(frame.toCR(p2))
            if self.tag in vedges:
                cr1 = (cr1[0], frame.height/2-700)
                cr2 = (cr2[0], frame.height/2+700)
            if self.tag in hedges:
                x0 = frame.width/2
            w = abs(cr2[0] - cr1[0])
            h = abs(cr2[1] - cr1[1])
            logger.debug('Paint on the image')
            painter = QPainter()
            painter.begin(self.processedImage)
            painter.setPen(QPen(Qt.red, 20))
            #painter.setFont(QFont('Times', 500))
            #painter.drawText(self.processedImage.rect(), Qt.AlignCenter, 'Symfoware')
            logger.debug('x,y=%6.3f, %6.3f' % (p1[0], p1[1]))
            logger.debug('cr1, cr2 = %s, %s' % (str(cr1), str(cr2)) )
            painter.drawRect(QRectF(*cr1, w, h))
            #painter.drawRect(QRectF(1000, 2000, 500, 800))
            painter.end()
            self.processedImage = QPixmap.fromImage(self.processedImage)
            self.processedImage = self.processedImage.scaled(width, height, Qt.KeepAspectRatio)

class PhotoWorker(QObject):
    def __init__(self, tags, scanConfig, scanResults):
        super().__init__()
        self.tags = tags
        self.scanConfig = scanConfig
        self.scanResults = scanResults
        
    def run(self, tag, imageFile):
        n = len(self.scanConfig.pointConfigList)
        for tag in self.tags:
            for i in range(n):
                config = self.scanConfig.pointConfig(i)
                if tag=='All' or (config!=None and tag in config.tags):
                    imgFile = self.scanResults.imageFile(i)
                    self.newPhoto.emit(tag, imgFile)
