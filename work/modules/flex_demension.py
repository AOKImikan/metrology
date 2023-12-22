#!/usr/bin/env python3
import os
import pickle
import time
import argparse
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging

import LinePointPlot
import makeImages

from scipy import linalg
from pmm.model import *

logger = logging.getLogger(__name__)

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('tag', help='FlexX or flexY')

    args = parser.parse_args()  # analyze arguments
    return args

def getDictFromDF(tag):  # tag example:FlexX
    with open(f'data/PCB_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    #group dataframe by tags
    grouped = analysisData.groupby(['analysis_tags'])

    #extract by specified tag
    try:
         extractData = grouped.get_group((tag))
    except KeyError as e:
        logger.warning(f'no data! {tag}')
        return None

    pair = zip(extractData['serial_number'], extractData['analysis_value'])
    dataDict = dict(pair)
    
    return dataDict

def run(args):
    data = getDictFromDF(args.tag)

    # hist(dataDict, require, binrange, minmax=None, unit='', filename = None)
    if args.tag=='FlexX':
        makeImages.graph(data, [39.5,39.7], [1015,1170],
                         'mm', 'Flex_X_DIMENSION')
        makeImages.hist(data, [39.5,39.7], 0.01, [39.4,39.9],
                        'mm', 'Flex_X_DIMENSION_hist')
    elif args.tag=='FlexY':
        makeImages.graph(data, [40.3,40.5], [1015,1170],
                         'mm', 'Flex_Y_DIMENSION')
        makeImages.hist(data, [40.3,40.5], 0.01, [40.2,40.7],
                        'mm', 'Flex_Y_DIMENSION_hist')

    
if __name__ == '__main__':
    t1 = time.time()

    args = parseArg()  # analyze arguments
    
    run(args)
    
    t2 = time.time()
    elapsed_time = t2-t1
    logger.info(f'run time : {elapsed_time}')
