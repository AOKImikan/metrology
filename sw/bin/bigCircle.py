#!/usr/bin/env python3
import os, sys
import argparse
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import linalg
from mpl_toolkits.mplot3d import axes3d
import statistics
from scipy.stats import norm
import tkinter as tk
from PIL import Image, ImageTk

import pmm


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--scanDir', dest='scanDir',
                        type=str, default='.',
                        help='Name of the directory with scan results')
    parser.add_argument('-i', '--imageFiles', dest='imageFiles',
                        type=str, default='',
                        help='List of image files (CSV format)')
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

    fitter = pmm.CircleFit()

    imageXY = fitter.readLog(logname)
    print(imageXY)

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

    print('centre of the cirle :')
    print(circle)

        
    pass

if __name__ == '__main__':
    args = parseArgs()
    run(args)
    
    
