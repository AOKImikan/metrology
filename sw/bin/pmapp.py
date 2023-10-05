#!/usr/bin/env python3
#--------------------------------------------------------------------
# Pixel Module Metrology Analysis
# 
#--------------------------------------------------------------------

import os, sys
import argparse
import logging
import json
import time
import re

from PyQt5.QtWidgets import QApplication

import pmm
#from pmm import *

logger = logging.getLogger(__name__)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--batchMode', dest='batchMode', 
                        action='store_true', default=False, 
                        help='Run in batch mode (no GUI)')
    parser.add_argument('-c', '--componentType', dest='componentType',
                        type=str, default='',
                        help='Component type to preset or batch')
    parser.add_argument('-n', '--componentName', dest='componentName',
                        type=str, default='SOME_COMPONENT',
                        help='Component name to preset or batch')
    parser.add_argument('--settings', dest='settings', 
                        type=str, default='', 
                        help='Semicolon-separated list of settings (dict) for batch mode')
    parser.add_argument('-l', '--logLevel', dest='logLevel', 
                        type=str, default='INFO', 
                        help='Logger level (DEBUG|INFO|WARNING|ERROR)')
    parser.add_argument('-e', '--showExamples', dest='showExamples', 
                        action='store_true', default=False, 
                        help='Show examples to run this program')
    return parser.parse_args()

def setLogLevel(logLevel):
    if logLevel == 'DEBUG': logger.setLevel(logging.DEBUG)
    elif logLevel == 'INFO': logger.setLevel(logging.INFO)
    elif logLevel == 'WARNING': logger.setLevel(logging.WARNING)
    elif logLevel == 'ERROR': logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)
        logger.warning('Logger level is set to INFO')

if __name__ == '__main__':
    app = QApplication([])

    args = parseArgs()

    logLevel = getattr(logging, args.logLevel)
    print('logLevel %s -> %d' % (args.logLevel, logLevel) )
    logging.basicConfig(stream=sys.stdout, 
                        #format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        format='%(name)-12s %(levelname)-8s %(message)s',
                        level=logLevel)

    pmmConfig = os.getenv('PMMCONFIG')
    
    cfgFile = os.path.join(os.getenv('PMMDIR'), 'share/setups.cfg')
    appModel = pmm.AppModel()
    appModel.readSetups(cfgFile)
    appModel.readSiteConfig(pmmConfig)
    
    if not args.batchMode:
        cssFile = os.path.join(os.getenv('PMMDIR'), 'share/pmappStyles.css')
        if os.path.exists(cssFile):
            with open(cssFile) as f:
                app.setStyleSheet(f.read())

        logger.info('Starting the main window')

        window = pmm.PmmWindow(pmmConfig, appModel)
        vmodel = pmm.ViewModel(view=window, model=appModel)
        handlers = pmm.Handlers(model=appModel, viewModel=vmodel)
        
        window.setHandlers(handlers)
        window.setup()
        
        window.show()
        app.exec()
        time.sleep(0.01)
    else:
        logger.info('Running in batch mode')
        job = pmm.BatchJob(appModel)
        if args.componentType != '':
            job.setComponentType(args.componentType)
        if args.componentName != '':
            job.setComponentName(args.componentName)
            
        data = {}
        for kv in args.settings.split(';'):
            k, v = tuple(map(lambda x: x.strip(), kv.split(':')) )
            data[k] = v
        job.setSettings(data)
        job.run()
        appModel.save()
        
