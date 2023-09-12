#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------
import logging

logger = logging.getLogger(__name__)

class ModuleAnalysis:
    def __init__(self, data):
        self.data = data
        self.logFileHeight = ''
        self.logFilePickup = ''
        self.logFileSize = ''
        self.logFileFlatness = ''
        self.logFileFlatness = ''
        pass
    def processPickupHeight(self):
        self.updateHeightScanResults()
        self.updatePickupScanResults()

    def processSize(self):
        logger.debug('Executing ModuleAnalysis.processSize')
        scanConfigData = self.data.sizeScanConfig
        scanResultsData = self.data.scanResults.size()
        nConfig = scanConfigData.nPoints()
        nResults = scanResultsData.nPoints()
        tagParametersMap = {}
        if nConfig == nResults or nResults < nConfig:
            tags = scanConfigData.allTags()
            logger.info('processSize() %d points, tags=%s' % (nResults, str(tags)) )
            for tag in tags:
                indexList = scanConfigData.indicesWithTag(tag)
                parameters = self.patternRec(tag, indexList)
                tagParametersMap[tag] = parameters
            pass
        else:
            logger.warning('Number of results differs from the config (%d vs %d)' % \
                           (nResults, nConfig))
        self.updateSizeTable(tagParametersMap)
        pass
    
    # Internal operations
    def patternRec(self, tag, indexList):
        scanConfigData = self.data.sizeScanConfig
        scanResultsData = self.data.scanResults.size()
        fnames = []
        x, y, r, l1, l2, theta = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        if tag == 'HoleTL':
            for i in indexList:
                fnames.append(scanResultsData.imagePath(i))
            logger.info('Fit alignemnt circle with photos: %s' % (str(fnames)) )
            return (x, y, r)
        elif tag == 'HoleBR':
            logger.warning('Pattern rec for tag %s not implemented yet' % tag)
            return (x, y, r, l1, l2, theta)
            pass
        elif tag == 'FiducialMark': # '+' + 'o'
            logger.warning('Pattern rec for tag %s not implemented yet' % tag)
            pass
        elif tag == 'FiducialF':
            logger.warning('Pattern rec for tag %s not implemented yet' % tag)
            pass
        else:
            logger.warning('Pattern rec for tag %s not implemented yet' % tag)
            return (x, y)
            pass
        return ()

    def updateSizeTable(tagParametersMap):
        pass
        
    def updateHeightScanResults(self):
        pass

    def updatePickupScanResults(self):
        pass

    def updateSizeScanTable(self):
        pass


