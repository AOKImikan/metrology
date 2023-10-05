#!/usr/bin/env python3
import os, sys
import argparse
import re
import math
import cv2
import numpy as np
#import matplotlib.pyplot as plt
#import math
#import tkinter as tk
#from PIL import Image, ImageTk
import logging

import pmm

logger = logging.getLogger(__name__)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--scanDir', dest='scanDir',
                        type=str, default='.',
                        help='Name of the directory with scan results')
    parser.add_argument('-i', '--imageFiles', dest='imageFiles',
                        type=str, default='',
                        help='List of image files (CSV format)')
    parser.add_argument('--shape', dest='shape',
                        type=str, default='Circle',
                        help='Shape to fit the edges')
    parser.add_argument('-s', '--subRegion', dest='subRegion',
                        type=str, default='',
                        help='Sub-region to draw image patches')
    parser.add_argument('-f', '--FlexNnumber', dest='FlexNumber',
                        type=str, default='',
                        help='FlexNumber')
    return parser.parse_args()

    
def run(args):
    scanDir = args.scanDir
    print('scanDir => %s' % scanDir)
    logname = os.path.join(args.scanDir, 'log.txt')

    fitter = pmm.ShapeFit()
    shape = None
    if args.shape == 'Circle':
        shape = pmm.Circle1(parameters=[0.0, 0.0, 1.0E-3])
    elif args.shape == 'LongCircle':
        logger.info(f'Use {args.shape} to fit')
        alpha = -math.pi/4.0
        #shape = pmm.LongCircle(parameters=[0.0, 0.0, 1.0E-3, 1.0, alpha])
        shape = pmm.LongCircle(parameters=[26.89, -26.74, 1.53, 0.9, alpha])
    fitter.setInitialShape(shape)

    imageXY = fitter.readLog(logname)

    files = args.imageFiles.split(',')

    images = []
    for i, fname in enumerate(files):
        fpath = os.path.join(args.scanDir, fname)
        x, y = imageXY[fname]
        name = f'img_{i}'
        image = pmm.ImageNP(name, fpath)
        image.xyOffset = pmm.CvPoint(x, y)
        images.append(image)

    bigImage, circle, pointsGlobal = fitter.run(images)
    cv2.imwrite('combined.jpg', bigImage)
    cx = pmm.roundF(circle.cx, '5.3f')
    cy = pmm.roundF(circle.cy, '5.3f')
    r = pmm.roundF(circle.r, '5.3f')
    logger.info(f'Circle ({cx}, {cy}) r={r}')

    outliers=[]
    vx1, vy1 = [], []
    for i, p in enumerate(pointsGlobal):
        if i in outliers: continue
        vx1.append(p[0])
        vy1.append(p[1])
    vx = np.array(vx1)
    vy = np.array(vy1)
    #dz = np.array(d)
    #print(vx)

    print(circle)

        
    pass

if __name__ == '__main__':
    args = parseArgs()
    logging.basicConfig(level=logging.DEBUG)
    run(args)
    
    
