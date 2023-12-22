#!/usr/bin/env python3
import os, sys
import argparse
import re
import math
import cv2
import numpy as np
import pickle
#import matplotlib.pyplot as plt
#import math
#import tkinter as tk
#from PIL import Image, ImageTk
import logging
from scipy import linalg

import datapath
import LinePointPlot
import makeImages

from pmm.model import *
from pmm.reader import *
from pmm.design import *
from pmm.prec import *
from pmm.workflow import *
from pmm.tools import *
import pmm

logger = logging.getLogger(__name__)
badfit = 0
def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', help='kind of module : FLEX, BARE, ASSEM')
    parser.add_argument('--sn', help='serialnumber 20UPGPQ260-')
    parser.add_argument('--tag', help='tag : T, B, L, R')
    parser.add_argument('--size', help='X or Y : dimension histgram and graph')
    #parser.add_argument('-f', '--FlexNnumber', dest='FlexNumber',
    #                    type=str, default='',
    #                    help='FlexNumber')
    return parser.parse_args()

def lineDiff(line1, line2, line_vh):
    if not (line1 and line2):
        logger.warning(f'Cannot calculate the distance between lines')
        #logger.warning(f'  Line[{tag1}]={line1}, Line[{tag2}]={line2}')
        return None
    x, y = 0.0, 0.0
    if line_vh == 'v':
        x, y = line1.xAtY(0.0), 0.0
        x1, y1 = line1.xAtY(20.0), 20.0
        x2, y2 = line1.xAtY(-20.0), -20.0
        dd = abs(x1 - x2)/2.0
    if line_vh == 'h':
        x, y = 0.0, line1.yAtX(0.0)
        x1, y1 = 20.0, line1.xAtY(20.0)
        x2, y2 = -20.0, line1.xAtY(-20.0)
        dd = abs(y1 - y2)/2.0
    p = Point([x, y])
    d = line2.distance(p)
    logger.debug(f' L-P distance ({line2}-{p.position}): {d}')
    dd = 0.0
    #self.outData[tag] = MeasuredValue(tag, d, dd)
    logger.info(f'line distance : {d}')
    return d
    
#data.pickle -> ScanProcessor
def LoadData(dn):
    appdata = None
    sp = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
            #print(appdata.scanNames())
            sp = appdata.getScanProcessor('ITkPixV1xFlex.Size')
    return sp

def fitLine0(points):
    line = None
    n = len(points)
    v1 = np.array([1]*n)
    vx = np.array(list(map(lambda x: x[0], points) ) )
    vy = np.array(list(map(lambda x: x[1], points) ) )
    # Line: p0+p1*x+p2*y = 0
    X = np.c_[ v1, vx, vy]
    M = np.dot(X.T, X)
    xx = M[1][1] - M[1][0]*M[0][1]
    yy = M[2][2] - M[2][0]*M[0][2]
    if xx > yy: # y=ax+b
        ifix = 2
    else: # x=ay+b
        ifix = 1
    M2 = [ [0, 0], [0, 0] ]
    b2 = [0, 0]
    i2, j2 = 0, 0
    for i in range(3):
        if i == ifix:
            continue
        j2 = 0
        for j in range(3):
            if j == ifix:
                b2[i2] = -M[i][j]
                continue
            M2[i2][j2] = M[i][j]
            j2 += 1
        i2 += 1
    pars2 = linalg.solve(M2, b2)
    pars = [0]*3
    i2 = 0
    for i in range(3):
        if i == ifix:
            pars[i] = 1.0
        else:
            pars[i] = pars2[i2]
            i2 += 1
    line = Line()
    #for p in points:
    #    print(p.position)
    #print(pars)
    line.setPars(pars)
    return line    

def fitLine(points):
    global badfit
    # fit line by all points
    line = fitLine0(points)

    points2 = []
    thr_dis = 0.05  # distance [mm]
    thr_res = 0.05  # residual error
    s = 0
    for ipoint in points:
        d = line.distance(ipoint)
        #print('point to line',d,'mm')
        s += np.square(d)
        if d < thr_dis:  # distance < threshold
            points2.append(ipoint)
    if len(points2)<2:
        logger.warning('Try again points detection')
        badfit = 1
        return line
    logger.debug(f'line1 error {np.sqrt(s)}')
    
    # fit line by exculuded points
    line2 = fitLine0(points2)
    
    # calculate residual error sum of squares
    s = 0
    for ipoint in points2:
        d = line2.distance(ipoint)
        s += np.square(d)
        #print('point to line',d,'mm')

    logger.debug(f'line2 error {np.sqrt(s)}')
    if np.sqrt(s) > thr_res:  # error > threshold
        badfit = 1
        logger.warning('Try again points detection')
        return line2
    else:
        return line2

def extractSN(dn):
    words = dn.split('/')
    sn = words[8]
    return sn

def makePlot(args,sizeDict):
    if args.kind=='FLEX':
        if args.size=='X':
            makeImages.graph(sizeDict, [39.5,39.7], [1015,1170],
                             'mm', 'Flex_X_DIMENSION_reFit')
            makeImages.hist(sizeDict, [39.5,39.7], 0.01, [39.4,39.9],
                            'mm', 'Flex_X_DIMENSION_reFit_hist')
        elif args.size=='Y':
            makeImages.graph(sizeDict, [40.3,40.5], [1015,1170],
                             'mm', 'Flex_Y_DIMENSION_reFit')
            makeImages.hist(sizeDict, [40.3,40.5], 0.01, [40.2,40.7],
                            'mm', 'Flex_Y_DIMENSION_reFit_hist')
    elif args.kind=='BARE':
        if args.size=='X':
            makeImages.graph(sizeDict, [39.5,39.7], [1015,1170],
                             'mm', 'Bare_X_DIMENSION_reFit')
            makeImages.hist(sizeDict, [39.5,39.7], 0.01, [39.4,39.9],
                            'mm', 'Bare_X_DIMENSION_reFit_hist')
        elif args.size=='Y':
            makeImages.graph(sizeDict, [40.3,40.5], [1015,1170],
                             'mm', 'Bare_Y_DIMENSION_reFit')
            makeImages.hist(sizeDict, [40.3,40.5], 0.01, [40.2,40.7],
                            'mm', 'Bare_Y_DIMENSION_reFit_hist')
            
def run(args):
    global badfit
    sizeDict = {}
    if args.size:
        dnames = datapath.getFilelistPCB('PCB_POPULATION')
    if args.sn:
        dnames=[f'/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/20UPGPQ260{args.sn}/PCB_POPULATION/001']
    for dn in dnames:
        badfit = 0
        sn = extractSN(dn)
        logger.info(f'serial number : {sn}')
        sp = LoadData(dn)
        if sp is None:
            continue
        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
        pointsL, pointsR, pointsT, pointsB = [],[],[],[]

        # pattern analysis result
        for k,v in patternAnalysis.outData.items():
            if v is None:
                logger.info(f'{k} is None')
                continue
            if '_point' in k:  # '*_point'
                if f'FlexL' in k:  # 'FlexL_*_point'
                    pointsL.append(v)
                    logger.debug(f'get point at left {v}')
                elif f'FlexR' in k:  # 'FlexR_*_point'
                    pointsR.append(v)
                    logger.debug(f'get point at right {v}')
                elif f'FlexT' in k:  # 'FlexT_*_point'
                    pointsT.append(v)
                    logger.debug(f'get point at top {v}')
                elif f'FlexB' in k:  # 'FlexB_*_point'
                    pointsB.append(v)
                    logger.debug(f'get point at bottom {v}')

        if args.size == 'X':
            lineL = fitLine(pointsL)
            lineR = fitLine(pointsR)
            dimension = lineDiff(lineL, lineR, 'v')
        elif args.size == 'Y':
            lineT = fitLine(pointsT)
            lineB = fitLine(pointsB)
            dimension = lineDiff(lineT, lineB, 'h')        

        if args.size:
            if badfit is 0:
                sizeDict[sn] = dimension
            else:
                sizeDict[sn] = [dimension, 'b']
    if args.sn:
        if args.tag == 'T':
            points = pointsT
        elif args.tag == 'B':
            points = pointsB
        elif args.tag == 'L':
            points = pointsL
        elif args.tag == 'R':
            points = pointsR
            
    # show and save plot (line, points, filename)
    if args.sn:
        line = fitLine(points)
        LinePointPlot.drawplot(line, points,f'20UPGPQ260{args.sn}_Flex{args.tag}_after')
    if args.size:
        makePlot(args,sizeDict)

if __name__ == '__main__':
    args = parseArgs()
    logging.basicConfig(level=logging.WARNING)
    run(args)
