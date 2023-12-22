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
import hist_rec
from scipy import linalg
from pmm.model import *

logger = logging.getLogger(__name__)

# analysis -> dataframe
def getFmarkPoint(sn, tag):  # tag example:AsicFmarkTL, FmarkBR
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    #group dataframe by tags
    grouped = analysisData.groupby(['serial_number', 'tags'])
    #extract by specified tag
    try:
         extractData = grouped.get_group((sn, tag))
    except KeyError as e:
        logger.warning(f'no data! {sn}, {tag}')
        return None
    #extractData = grouped.get_group((sn, tag))

    xindexs = list(extractData.query('valueType == "detect_x"').index)
    
    for xi in xindexs:
        detectX = extractData.loc[xi]['values']
        detectY = extractData.loc[xi+1]['values']
        point = [detectX, detectY]
    logger.info(point)

    return point

def oppositeAngle(tan1, tan2):
    tanDelta = (tan1-tan2)/(1+tan1*tan2)
    angle = np.arctan(tanDelta)  #radian
    angle = np.degrees(angle)  #degree
    logger.info(angle)
    return angle

def calcdist(p1, p2):
    dx = p1[0]-p2[0]
    dy = p1[1]-p2[1]
    d = np.sqrt(dx**2+ dy**2)
    return d, dx, dy

def run(args):
    #define the aimed dataframe
    analyDFs = pd.DataFrame()
    serialnum = '20UPGM' + args.sn
    # get serial number and qc stage
    if args.tag == 'TL':
        asic = getFmarkPoint(serialnum, 'AsicFmarkTL')
        flex = getFmarkPoint(serialnum, 'FmarkTL')
    if args.tag == 'TR':
        asic = getFmarkPoint(serialnum, 'AsicFmarkTR')
        flex = getFmarkPoint(serialnum, 'FmarkTR')
    if args.tag == 'BL':
        asic = getFmarkPoint(serialnum, 'AsicFmarkBL')
        flex = getFmarkPoint(serialnum, 'FmarkBL')
    if args.tag == 'BR':
        asic = getFmarkPoint(serialnum, 'AsicFmarkBR')
        flex = getFmarkPoint(serialnum, 'FmarkBR')
    print(calcdist(asic, flex))
      
if __name__ == '__main__':
    t1 = time.time()
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('sn', help='serialnumber 20UPGM-')
    parser.add_argument('tag', help='tag : TL, BL, TR, BR')
    args = parser.parse_args()  # analyze arguments
    
    run(args)
    
    t2 = time.time()
    elapsed_time = t2-t1
    logger.info(f'run time : {elapsed_time}')
