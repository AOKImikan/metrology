#------------------------------------------------------------------------
# pmm: data1.py
#---------------
# Input data for scans
#------------------------------------------------------------------------
import os
import re
import json
import logging
logger = logging.getLogger(__name__)

import configparser

class KeyValueData:
    def __init__(self):
        self.data = {}

    def setValue(self, key, value):
        keys = self.allowedKeys()
        if key in keys:
            self.data[key] = value

    def value(self, key):
        x = None
        keys = self.allowedKeys()
        if key in keys:
            x = self.data[key]
        return x
    
    def get(self, key):
        return self.value(key)

    def hasKey(self, key):
        #return key in self.allowedKeys()
        return key in self.data.keys()
    
    def allowedKeys(self):
        return []

    def persKeys(self):
        return ['data']
    
    def persData(self):
        pdata = {}
        for k, v in self.data.items():
            if type(v) == type([]):
                y = []
                for a in v:
                    if hasattr(a, 'persData'):
                        y.append(a.persData())
                pdata[k] = y
            elif hasattr(v, 'persData'):
                pdata[k] = v.persData()
            else:
                pdata[k] = v
        return pdata
    
class ScanInput:
    def __init__(self, scanName, scanType, configs,
                 zoom=20, buttonTexts=['Select log file']):
        self.scanName = scanName
        self.scanType = scanType
        self.configs = configs
        if type(configs) != type([]):
            self.configs = [configs]
        self.defaultZoom = zoom
        self.selectButtonTexts = buttonTexts
        self.analysisList = []

    def defaultConfig(self):
        c = ''
        if len(self.configs)>0:
            c = self.configs[0]
        return c
    
    def setAnalysisList(self, v):
        self.analysisList = v

    def persKeys(self):
        return [ 'scanName', 'scanType', 'configs', 'defaultZoom',
                 'selectButtonTexts', 'analysisList' ]
    
class SetupsConfig:
    def __init__(self):
        self.configFile = ''
        self.parser = configparser.ConfigParser()
        self.data = {}
        self.baseWorkDir = os.getcwd()

    def persKeys(self):
        return ['configFile', 'data']
    
    def read(self, fn):
        with open(fn, 'r') as f:
            self.parser.optionxform = str
            x = self.parser.read(fn)
            f.close()
            for s in self.parser.sections():
                self.data[s] = self.sectionToDict(self.parser[s])

    def pmmDir(self):
        return os.getenv('PMMDIR')

    def configDir(self):
        return os.path.join(self.pmmDir(), 'share')
    
    def moduleDir(self):
        mdir = self.data['Basic']['ModuleDir']
        if not mdir.startswith('/'):
            mdir = os.path.join(self.baseWorkDir, mdir)
        return mdir
    
    def componentTypes(self):
        v = self.data['Basic']['ComponentTypes']
        return v
    
    def testSteps(self):
        v = self.data['Basic']['TestSteps']
        return v
    
    def zoomValues(self):
        v = list(map(lambda x: int(x), self.data['Basic']['ZoomValues']))
        return v

    def defaultComponentType(self):
        return self.data['Basic']['DefaultComponentType']
    
    def scanTypes(self, moduleType):
        keys = self.parser.sections()
        s = 'Scans.%s.' % moduleType
        n1 = len(s)
        keys1 = filter(lambda x: x.startswith(s), keys)
        v = list(map(lambda x: x[n1:], keys1))
        return v
    
    def scanInput(self, moduleType, scanType):
        s = 'Scans.%s.%s' % (moduleType, scanType)
        #section = self.parser[s]
        #x = self.sectionToDict(section)
        x = self.data[s]
        keys = x.keys()
        #
        scanName, sType, zoom = '', '', 20
        configs, analyses = [], []
        texts = []
        if 'Name' in keys: scanName = x['Name']
        if 'Type' in keys: sType = x['Type']
        if 'Zoom' in keys: zoom = int(x['Zoom'])
        if 'ScanConfigs' in keys:
            configs = x['ScanConfigs']
            if type(configs) != type([]):
                configs = [configs]
        if 'Analyses' in keys:
            analyses = x['Analyses']
            if type(analyses) != type([]):
                analyses = [analyses]
        if 'ButtonTexts' in keys:
            texts = x['ButtonTexts']
            if type(texts) != type([]):
                texts = [texts]
        if scanName == '':
            scanName = '%s.%s' % (moduleType, scanType)
        y = ScanInput(scanName, scanType, configs,
                      zoom=zoom, buttonTexts=texts)
        y.setAnalysisList(analyses)
        return y
    
    def sectionToDict(self, section):
        x = {}
        keys = section.keys()
        re1 = re.compile('([\w._+-]+)\[(\d+)\]')
        for key in keys:
            value = section[key]
            mg = re1.search(key)
            if mg:
                k1 = mg.group(1)
                if k1 in x.keys():
                    x[k1].extend(value.split(','))
                else:
                    x[k1] = value.split(',')
            elif value.find(',')>=0:
                x[key] = value.split(',')
            else:
                x[key] = value
        return x

def readSiteConfig(fn):
    data = {}
    if os.path.exists(fn):
        with open(fn, 'r') as fin:
            data = json.load(fin)
    return data

class ScanPoint(KeyValueData):
    sAllowedKeys = [
        'index', 'x', 'y', 'z', 'error', 'zoom', 'imagePath', 'tags'
        ]
    def __init__(self):
        self.data = {}
        self.setValue('index', -1)
        self.setValue('x', 0.0)
        self.setValue('y', 0.0)
        self.setValue('z', 0.0)
        self.setValue('error', False)
        self.setValue('zoom', 1)
        self.setValue('imagePath', '')
        self.setValue('tags', [])
    def allowedKeys(self):
        return ScanPoint.sAllowedKeys
    
    def setIndex(self, i):
        self.setValue('index', i)
    def setXYZ(self, x, y, z):
        self.setValue('x', float(x))
        self.setValue('y', float(y))
        self.setValue('z', float(z))
    def setError(self, e):
        self.setValue('error', e)
    def setZoom(self, x):
        self.setValue('zoom', x)
    def setImagePath(self, x):
        self.setValue('imagePath', x)
    def setTags(self, x):
        self.setValue('tags', x)
    def __getitem__(self, i):
        x = 99999.9
        if i == 0:
            x = self.get('x')
        elif i == 1:
            x = self.get('y')
        elif i == 2:
            x = self.get('z')
        return x
    pass

