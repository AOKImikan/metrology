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

import pmm
import data_pcb
import LinePointPlot
from scipy import linalg
from pmm.model import *

logger = logging.getLogger(__name__)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('sn', help='serialnumber 20UPGPQ-')
    parser.add_argument('tag', help='tag : T, B, L, R')
    #parser.add_argument('-f', '--FlexNnumber', dest='FlexNumber',
    #                    type=str, default='',
    #                    help='FlexNumber')
    return parser.parse_args()

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
    # fit line by all points
    line = fitLine0(points)

    points2 = []
    thr_dis = 0.05  # distance [mm]
    thr_res = 0.005  # residual error
    s = 0
    print('initial')
    for ipoint in points:
        d = line.distance(ipoint)
        print(d,'mm')
        s += np.square(line.distance(ipoint))
        if d < thr_dis:  # distance < threshold
            points2.append(ipoint)
    if len(points2)<2:
        print('try again points detection')
        return line
    print(s)
    # fit line by exculuded points
    line2 = fitLine0(points2)
    
    # calculate residual error sum of squares
    
    print('exclude')
    for ipoint in points2:
        d = line2.distance(ipoint)
        s += np.square(line2.distance(ipoint))
        print(d,'mm')

    print(s)

    if s > thr_res:
        print('try again points detection')
        return line
    else:
        return line2
                    
def run(args):
    #dnames = data_pcb.getFilelist('PCB_POPULATION')
    dns=[f'/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/20UPGPQ260{args.sn}/PCB_POPULATION/001']  # test
    for dn in dns:
        sp = LoadData(dn)

        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
        points = []

        # pattern analysis result
        for k,v in patternAnalysis.outData.items():
            if v is None:
                pass
    
            elif f'Flex{args.tag}' in k:
                if '_point' in k:
                    points.append(v)

        line = fitLine(points)
        # show and save plot (line, points, filename)
        LinePointPlot.drawplot(line, points,f'20UPGPQ260{args.sn}_Flex{args.tag}_after')
        

if __name__ == '__main__':
    args = parseArgs()
    logging.basicConfig(level=logging.INFO)
    run(args)
