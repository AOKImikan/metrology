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
import fitline_without
from scipy import linalg
from pmm.model import *

logger = logging.getLogger(__name__)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('sn', help='serialnumber 20UPGPQ260-')
    parser.add_argument('tag', help='tag : X, Y')
    #parser.add_argument('-f', '--FlexNnumber', dest='FlexNumber',
    #                    type=str, default='',
    #                    help='FlexNumber')
    return parser.parse_args()

def lineDiff(line1, line2, line_vh):
    if not (line1 and line2):
        logger.warning(f'Cannot calculate the distance between lines')
        return

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
    self.outData[tag] = MeasuredValue(tag, d, dd)

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

def run(args):
    #dnames = data_pcb.getFilelist('PCB_POPULATION')
    dns=[f'/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/20UPGPQ260{args.sn}/PCB_POPULATION/001']  # test
    for dn in dns:
        sp = LoadData(dn)

        patternAnalysis = sp.analysisList[0]

        # pattern analysis result
       
        if args.tag=='X':
            for k,v in patternAnalysis.outData.items():
                points1, points2 = [],[]
                if v is None:
                    pass
                
                elif f'FlexL' in k:
                    if '_point' in k:  # 'FlexL_*_point'
                        points1.append(v)
                elif f'FlexR' in k:
                    if '_point' in k:  # 'FlexR_*_point'
                        points2.append(v)
        elif args.tag=='Y':
             for k,v in patternAnalysis.outData.items():
                points1, points2 = [],[]
                if v is None:
                    pass
                
                elif f'FlexT' in k:
                    if '_point' in k:  # 'FlexT_*_point'
                        points1.append(v)
                elif f'FlexB' in k:
                    if '_point' in k:  # 'FlexB_*_point'
                        points2.append(v)

        line1 = fitline_without.fitLine(points1)
        line2 = fitline_without.fitLine(points2)
        
        if args.tag=='X':
            d = lineDiff(line1,line2,h)
        elif args.tag=='Y':
            d = lineDiff(line1,line2,v)
        print(d)
    
if __name__ == '__main__':
    args = parseArgs()
    logging.basicConfig(level=logging.INFO)
    run(args)
