#!/usr/bin/env python3
import os
import pickle
import time
import argparse
import tkinter as tk
from tkinter import ttk
import pmm
from pmm.model import *
from pmm.tools import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging

import LinePointPlot
from scipy import linalg

logger = logging.getLogger(__name__)

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('sn', help='serialnumber 20UPGM-')

    parser.add_argument('-m','--mark', help='Fmark distance',
                        choices=['TL','TR','BL','BR'])
    parser.add_argument('-l','--line', help='line angle',
                        choices=['T','B','L','R'])

    args = parser.parse_args()  # analyze arguments
    return args

def getFmarkPoint(sn, tag):  # tag example:AsicFmarkTL, FmarkBR
    fmt = '5.3f'
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
        point = [roundF(detectX,fmt), roundF(detectY,fmt)]
    logger.info(point)
    
    return point

def oppositeAngle(tan1, tan2):
    tanDelta = (tan1-tan2)/(1+tan1*tan2)
    angle = np.arctan(tanDelta)  #radian
    angle = np.degrees(angle)  #degree
    logger.info(angle)
    return angle

def calcdist(p1, p2):
    dx = abs(p1[0]-p2[0])
    dy = abs(p1[1]-p2[1])
    d = np.sqrt(dx**2+ dy**2)
    return d, dx, dy

def edgeInfo(sn, tag):  # tag example:FlexL, SensorT
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    #serialnum = '20UPGM'+sn
    points = []
    linePars = []

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
    p0index = list(extractData.query('valueType == "line_p0"').index)[0]
    
    for xi in xindexs:
        detectX = extractData.loc[xi]['values']
        detectY = extractData.loc[xi+1]['values']
        points.append([detectX, detectY])
    logger.info(points)
    for pi in range(p0index, p0index+3):
        parameter = extractData.loc[pi]['values']
        linePars.append(parameter)
    logger.info(linePars)

    return points, linePars

def run(args):
    #define the aimed dataframe
    analyDFs = pd.DataFrame()
    serialnum = '20UPGM' + args.sn
    # get serial number and qc stage
    if args.mark:
        if args.mark == 'TL':
            asic = getFmarkPoint(serialnum, 'AsicFmarkTL')
            flex = getFmarkPoint(serialnum, 'FmarkTL')
        if args.mark == 'TR':
            asic = getFmarkPoint(serialnum, 'AsicFmarkTR')
            flex = getFmarkPoint(serialnum, 'FmarkTR')
        if args.mark == 'BL':
            asic = getFmarkPoint(serialnum, 'AsicFmarkBL')
            flex = getFmarkPoint(serialnum, 'FmarkBL')
        if args.mark == 'BR':
            asic = getFmarkPoint(serialnum, 'AsicFmarkBR')
            flex = getFmarkPoint(serialnum, 'FmarkBR')
        print(calcdist(asic, flex))

    elif args.line:
        if args.line == 'T':
            edge1 = edgeInfo(serialnum, 'SensorT')
            edge2 = edgeInfo(serialnum, 'FlexT')
            angle = oppositeAngle(edge1[1][1], edge2[1][1])
        if args.line == 'B':
            edge1 = edgeInfo(serialnum, 'SensorB')
            edge2 = edgeInfo(serialnum, 'FlexB')
            angle = oppositeAngle(edge1[1][1], edge2[1][1])
        if args.line == 'L':
            edge1 = edgeInfo(serialnum, 'AsicL')
            edge2 = edgeInfo(serialnum, 'FlexL')
            angle = oppositeAngle(edge1[1][2], edge2[1][2])
        if args.line == 'R':
            edge1 = edgeInfo(serialnum, 'AsicR')
            edge2 = edgeInfo(serialnum, 'FlexR')
            angle = oppositeAngle(edge1[1][2], edge2[1][2])
        print(angle)

if __name__ == '__main__':
    t1 = time.time()

    args = parseArg()  # analyze arguments
    
    run(args)
    
    t2 = time.time()
    elapsed_time = t2-t1
    logger.info(f'run time : {elapsed_time}')
