#-----------------------------------------------------------------------
# pmm: batchjob.py
#-----------------------------------------------------------------------
import os
import logging
logger = logging.getLogger(__name__)

from .handlers import Handlers

class BatchJob:
    def __init__(self, model):
        self.model = model
        self.handlers = Handlers(self.model, None)
        self.componentType = ''
        self.componentName = ''
        self.settings = {}
        
    def setComponentType(self, ctype):
        self.componentType = ctype

    def setComponentName(self, cname):
        self.componentName = cname

    def setSettings(self, settings):
        self.settings = settings
        
    def run(self):
        logger.info(f'Running ITkPixV1xFlex analysis for {self.componentName}')
        self.handlers.selectComponentType(self.componentType)
        self.model.setComponentName(self.componentName)

        for SType in ('Size', 'Height'):
            stype = SType.lower()
            configkey = f'{stype}Config'
            logkey = f'{stype}Log'
            scanName = f'{self.componentType}.{SType}'
            #
            config = ''
            log = ''
            if not logkey in self.settings.keys():
                continue
            else:
                log = self.settings[logkey]
                if configkey in self.settings.keys():
                    config = self.settings[configkey]
            logger.debug(f'scanName = {scanName}')
            proc = self.model.getScanProcessor(scanName)
            if config != '':
                configPath = '%s/ScanConfig_%s.txt' %\
                    (self.model.config.configDir(), config)
                self.handlers.useScanConfig(config, scanName)
                proc.scanData.setConfigFile(configPath)
            proc.setLogFile(log)
            
            logger.debug(f'Run {proc} config={proc.scanData.configPath}')
            proc.run()
            proc.tableData()
