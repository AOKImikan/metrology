#-----------------------------------------------------------------------
# pmm/componentView.py
#-----------------------------------------------------------------------

import os
import configparser
import logging

logger = logging.getLogger(__name__)

class ScanView:
    def __init__(self, name):
        self.name = name
        self.scanTypes = []
        self.scanConfigs = []
        self.properties = []
        self.auxProperties = []
        self.buttonTexts = []

    def setTypes(self, scanTypes):
        # set scan types
        if type(scanTypes) == type(''):
            words = scanTypes.split(',')
            for w in words:
                self.scanTypes.append(w)
        elif type(scanTypes) == type([]):
            for w in scanTypes:
                self.scanTypes.append(w)

    def setConfigs(self, scanConfigs):
        # set scan configs
        if type(scanConfigs) == type(''):
            words = scanConfigs.split(',')
            for w in words:
                self.scanConfigs.append(w)
        elif type(scanConfigs) == type([]):
            for w in scanConfigs:
                self.scanConfigs.append(w)
    def setButtonTexts(self, v):
        self.buttonTexts = v

    def setProperties(self, v):
        self.properties = v

    def setAuxProperties(self, v):
        self.auxProperties = v

    def dump(self, prefix=''):
        logger.info('%sScan[%s]' % (prefix, self.name))
        logger.info('%s  types: %s' % (prefix, str(self.scanTypes)) )
        logger.info('%s  configs: %s' % (prefix, str(self.scanConfigs)) )
        logger.info('%s  properties: %s' % (prefix, str(self.properties)) )
        logger.info('%s  aux. properties: %s' % (prefix, str(self.auxProperties)) )
        logger.info('%s  button texts: %s' % (prefix, str(self.buttonTexts)) )

class ComponentView:
    def __init__(self, name):
        self.name = name
        self.scans = []

    def addScan(self, scan):
        self.scans.append(scan)

    def dump(self, prefix=''):
        logger.info('%sComponent[%s]' % (prefix, self.name))
        for s in self.scans:
            s.dump(prefix+'  ')    

class ComponentViewConfig:
    def __init__(self):
        self.componentViewMap = {}

    def componentView(self, cname):
        x = None
        if cname in self.componentViewMap.keys():
            x =  self.componentViewMap[cname]
        else:
            x = ComponentView(cname)
            self.componentViewMap[cname] = x
        return x

    def addScanView(self, cname, scan):
        c = self.componentView(cname)
        if c:
            c.addScan(scan)
        
    def read(self, fname):
        p = configparser.ConfigParser()
        if not os.path.exists(fname):
            logger.warning('File %s does not exist' % fname)
            return -1
        x = p.read(fname)
        if len(x) != 1:
            return -2
        component = None
        scan = None
        for s in p.sections():
            logger.info('Section: %s' % s)
            words = s.split('.')
            logger.info(words)
            if len(words) == 3:
                cname, pname, sname = words
                component = self.componentView(cname)
                if pname == 'Scans':
                    scan = ScanView(sname)
                    self.addScanView(cname, scan)
                section = p[s]
                if 'Types' in section.keys():
                    scan.setTypes(section['Types'])
                if 'ScanConfigs' in section.keys():
                    scan.scanConfigs = section['ScanConfigs'].split(',')
                v = self.readProperties(section)
                scan.setProperties(v)

                v = self.readAuxProperties(section)
                scan.setAuxProperties(v)

                v = self.readButtonTexts(section)
                scan.setButtonTexts(v)

    def readArray(self, section, key):
        v = []
        if key in section.keys():
            v = section[key].split(',')
        else:
            i = 0
            while True:
                key2 = '%s[%d]' % (key, i)
                logger.debug('check key: %s' % key2)
                if key2 in section.keys():
                    v.extend(section[key2].split(','))
                    i += 1
                else:
                    break
                if i >= 100:
                    logger.warning('Key for an array is split to more than 100 lines, too many.')
                    break
        return v
            
    def readProperties(self, section):
        return self.readArray(section, 'Properties')
        # v = []
        # if 'Properties' in section.keys():
        #     v = section['Properties'].split(',')
        # else:
        #     i = 0
        #     while True:
        #         key = 'Properties[%d]' % i
        #         logger.debug('check key: %s' % key)
        #         if key in section.keys():
        #             v.extend(section[key].split(','))
        #             i += 1
        #         else:
        #             break
        #         if i >= 100: break
        # return v

    def readAuxProperties(self, section):
        return self.readArray(section, 'AuxProperties')
        # v = []
        # if 'AuxProperties' in section.keys():
        #     v = section['AuxProperties'].split(',')
        # else:
        #     i = 0
        #     while True:
        #         key = 'AuxProperties[%d]' % i
        #         logger.debug('check key: %s' % key)
        #         if key in section.keys():
        #             v.extend(section[key].split(','))
        #             i += 1
        #         else:
        #             break
        #         if i >= 100: break
        # return v

    def readButtonTexts(self, section):
        return self.readArray(section, 'ButtonTexts')
        # v = []
        # if 'ButtonTexts' in section.keys():
        #     v = section['ButtonTexts'].split(',')
        # else:
        #     i = 0
        #     while True:
        #         key = 'ButtonTexts[%d]' % i
        #         logger.debug('check key: %s' % key)
        #         if key in section.keys():
        #             v.extend(section[key].split(','))
        #             i += 1
        #         else:
        #             break
        #         if i >= 100: break
        # return v

    def dump(self, prefix=''):
        logger.info('ComponentViews:')
        for k, c in self.componentViewMap.items():
            c.dump('  ')
        
