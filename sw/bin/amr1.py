#!/usr/bin/env python3
#-----------------------------------------------------------------------
# Analyze metrology results 1
#-----------------------------------------------------------------------
import os, sys
import argparse
import json

import numpy as np
import matplotlib.pyplot as plt

from pmm.reader import *
from pmm.tools import *

dataPoints_height = '../data/dataPoints_height.txt'
dataPoints_height2 = '../data/dataPoints_height2.txt'
dataPoints_pickup = '../data/dataPoints_pickup.txt'
dataPoints_iwashita = './mp_iwashita_points.txt'

def removeLocalOutliers(points, thr=0.05):
    n1 = 4
    n2 = 4
    n = points.shape[0]
    xmin = min(points[:, 0])
    xmax = min(points[:, 0])

def amr_flatness(args):
    reader = ReaderB4v1()
    pointsVacOn = readPoints(args.flatnessVacOnFile, reader)
    pointsVacOff = readPoints(args.flatnessVacOffFile, reader)
    n1 = len(pointsVacOn)
    n2 = len(pointsVacOff)
    print(n1, n2)
    if n1 > 0 and n2 > 0 and n1 == n2:
        zdiff = pointsVacOff[:,2]- pointsVacOn[:,2]
        pointsDiff = pointsVacOff
        pointsDiff = np.c_[pointsVacOff[:,0], pointsVacOff[:,1], zdiff]
        plane = fitPlane(pointsDiff, 0.06)
        plane = plane[0]
        #print(str(plane), plane.zsigma)
        print('Flatness %6.3f +- %6.3f' % (plane.c, plane.zsigma) )
        fig = plt.figure()
        ax1 = fig.add_subplot('111', projection='3d')
        ax1.scatter(pointsDiff[:,0], pointsDiff[:,1], pointsDiff[:,2])
        plt.show()

def amr_jig(args):
    reader = ReaderB4v1()
    points = readPoints(args.jigFile, reader)
    n = len(points)
    z = sum(points[:,2])/len(points)
    print('Jig average height = %6.3f' % z)
    return z

def readPointsConfig(fname):
    pointIndices = {}
    f = open(fname, 'r')
    for i, line in enumerate(f.readlines()):
        line = line.strip()
        words = line.split()
        if len(words)>=4:
            if words[-1] in pointIndices.keys():
                pointIndices[words[3]].append(i)
            else:
                pointIndices[words[3]] = [i]
    f.close()
    return pointIndices

def readPointsConfig2(fname):
    pointIndices = {}
    f = open(fname, 'r')
    for i, line in enumerate(f.readlines()):
        line = line.strip()
        words = line.split()
        if len(words)>=4:
            tag = words[-1]
            if words[-1] in pointIndices.keys():
                pointIndices[words[3]].append(i)
            else:
                pointIndices[words[3]] = [i]
    f.close()
    return pointIndices

def calcAverage(points, indices):
    print(indices)
    n = len(indices)
    x = 0.0
    x2 = 0.0
    for i in indices:
        x += points[i][2]
        x2 += points[i][2]*points[i][2]
    x /= n
    x2 /= n
    x = float(x)
    dx = x2 - x*x
    #print('%6.3f +- %6.6f' % (x, dx) )
    return x

def amr_pickup(args, jigHeight, offset, jsonData=None):
    reader = ReaderB4v1()
    points = readPoints(args.pickupFile, reader)
    #
    pointIndices = readPointsConfig(dataPoints_pickup)
    z_pickup = [0]*4
    dz = -jigHeight + offset
    dz = -4.670 + 0.600
    z_pickup[0] = calcAverage(points, pointIndices['Pickup1']) + dz
    z_pickup[1] = calcAverage(points, pointIndices['Pickup2']) + dz
    z_pickup[2] = calcAverage(points, pointIndices['Pickup3']) + dz
    z_pickup[3] = calcAverage(points, pointIndices['Pickup4']) + dz

    print('Jig : %6.3f' % jigHeight)
    print('Pickup1 : %6.3f' % (z_pickup[0]) )
    print('Pickup2 : %6.3f' % (z_pickup[1]) )
    print('Pickup3 : %6.3f' % (z_pickup[2]) )
    print('Pickup4 : %6.3f' % (z_pickup[3]) )
    if jsonData!=None:
        jsonData['Thickness pickup area chip1~4'] = z_pickup
        
def amr_height(args, jigHeight, jsonData=None):
    reader = ReaderB4v1()
    points = readPoints(args.heightFile, reader)
    #
    pointIndices = readPointsConfig(dataPoints_height)
    z_asic = [0]*4
    z_flex = [0]*4
    z_asic[0] = calcAverage(points, pointIndices['Asic1']) - jigHeight
    z_asic[1] = calcAverage(points, pointIndices['Asic2']) - jigHeight
    z_asic[2] = calcAverage(points, pointIndices['Asic3']) - jigHeight
    z_asic[3] = calcAverage(points, pointIndices['Asic4']) - jigHeight

    print('Jig : %6.3f' % jigHeight)
    asic_ave = sum(z_asic)/4
    offset = 0.200 - asic_ave
    dz = -jigHeight + offset
    for i in range(len(z_asic)):
        z_asic[i] += offset
        
    z_flex[0] = calcAverage(points, pointIndices['Flex1']) + dz
    z_flex[1] = calcAverage(points, pointIndices['Flex2']) + dz
    z_flex[2] = calcAverage(points, pointIndices['Flex3']) + dz
    z_flex[3] = calcAverage(points, pointIndices['Flex4']) + dz
    hvcap = calcAverage(points, pointIndices['Hv1']) + dz
    conn = calcAverage(points, pointIndices['Connector1']) + dz
    
    print('Asic1 : %6.3f' % (z_asic[0]) )
    print('Asic2 : %6.3f' % (z_asic[1]) )
    print('Asic3 : %6.3f' % (z_asic[2]) )
    print('Asic4 : %6.3f' % (z_asic[3]) )
    print('Flex1 : %6.3f' % (z_flex[0]) )
    print('Flex2 : %6.3f' % (z_flex[1]) )
    print('Flex3 : %6.3f' % (z_flex[2]) )
    print('Flex4 : %6.3f' % (z_flex[3]) )
    print('HV capacitor : %6.3f' % (hvcap) )
    print('Connector : %6.3f' % (conn) )

    if jsonData:
        jsonData['Thickness edge chip1~4'] = z_flex
        jsonData['Thickness HV capacitor'] = hvcap
        jsonData['Thickness data connector'] = conn
    return offset
        
def amr_height2(args, jigHeight, jsonData=None):
    reader = ReaderB4v1()
    points = readPoints(args.height2File, reader)
    #
    pointIndices = readPointsConfig(dataPoints_height2)
    z_asic = [0]*4
    z_asic[0] = calcAverage(points, pointIndices['Asic_TL']) - jigHeight
    z_asic[1] = calcAverage(points, pointIndices['Asic_BL']) - jigHeight
    z_asic[2] = calcAverage(points, pointIndices['Asic_BR']) - jigHeight
    z_asic[3] = calcAverage(points, pointIndices['Asic_TR']) - jigHeight
    asic_ave = sum(z_asic)/4
    offset = 0.200 - asic_ave
    print('Asic1 : %6.3f' % z_asic[0])
    print('Asic2 : %6.3f' % z_asic[1])
    print('Asic3 : %6.3f' % z_asic[2])
    print('Asic4 : %6.3f' % z_asic[3])
    print('Jig : %6.3f' % jigHeight)
    for p in points:
        print('Point (%s) : %6.3f' % ('?', p[2]) )
    return offset

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sizeFile', dest='sizeFile', 
                        type=str, default='',
                        help='Result file of the size measurement')
    parser.add_argument('--flatnessVacOnFile', dest='flatnessVacOnFile', 
                        type=str, default='',
                        help='Result file of the flatness with vacuum on.')
    parser.add_argument('--flatnessVacOffFile', dest='flatnessVacOffFile', 
                        type=str, default='',
                        help='Result file of the flatness with vacuum off.')
    parser.add_argument('--jigFile', dest='jigFile', 
                        type=str, default='',
                        help='Result file of the jig height')
    parser.add_argument('--pickupFile', dest='pickupFile', 
                        type=str, default='',
                        help='Result file of the pickup heigt')
    parser.add_argument('--heightFile', dest='heightFile', 
                        type=str, default='',
                        help='Result file of the height')
    parser.add_argument('--height2File', dest='height2File', 
                        type=str, default='',
                        help='Result file of the height (2)')
    parser.add_argument('--outputJsonFile', dest='outputJsonFile', 
                        type=str, default='',
                        help='Output JSON file')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parseArgs()
    jigHeight = 0.0
    offset = 0.0

    print(args)
    jsonData = None
    if args.outputJsonFile!='':
        if os.path.exists(args.outputJsonFile):
            f = open(args.outputJsonFile, 'r')
            jsonData = json.load(f)
            f.close()
        else:
            jsonData = {}

    if args.jigFile!='':
        jigHeight = amr_jig(args)
    if args.heightFile!='':
        offset = amr_height(args, jigHeight, jsonData)
    if args.height2File!='':
        offset = amr_height2(args, jigHeight, jsonData)
    if args.pickupFile!='':
        amr_pickup(args, jigHeight, offset, jsonData)
    if args.flatnessVacOnFile!='' and args.flatnessVacOffFile!='':
        amr_flatness(args)

    print('jsonData=', jsonData)
    if jsonData:
        files = ''
        if args.jigFile!='': files += '%s/log.txt,' % args.jigFile
        if args.sizeFile!='': files += '%s/log.txt,' % args.sizeFile
        if args.heightFile!='': files += '%s/log.txt,' % args.heightFile
        if args.pickupFile!='': files += '%s/log.txt,' % args.pickupFile
        if args.flatnessVacOnFile!='': files += '%s/log.txt' % args.flatnessVacOnFile
        if args.flatnessVacOffFile!='': files += '%s/log.txt' % args.flatnessVacOffFile
        files = files.strip(',')
        files = files.replace('../data/', '')
        jsonData['Raw data (file)'] = files
        print('Dump JSON data')
        for item in jsonData.items():
            print(item)

        f = open(args.outputJsonFile, 'w')
        json.dump(jsonData, f, indent=4)
        f.close()
        
    
