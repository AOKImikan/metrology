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

import Flex_Bare_relation
import makeImages
from scipy import linalg
from pmm.model import *

logger = logging.getLogger(__name__)
def parseArg():
    # make parser
    parser = argparse.ArgumentParser()

    # add argument
    parser.add_argument('-m','--mark', help='Fmark distance',
                        choices=['TL','TR','BL','BR'])
    parser.add_argument('-l','--line', help='line angle',
                        choices=['T','B','L','R'])
    parser.add_argument('-t','--table',help='make table of Fmark points',
                        action='store_true')
    parser.add_argument('-r','--ran',help='Fmark range',
                        choices=['AT','AB','AL','AR','FT','FB','FL','FR'])
    parser.add_argument('-a','--ang',help='Fmark angle',
                        choices=['ATL','ATR','ABL','ABR','FTL','FTR','FBL','FBR'])
    
    args = parser.parse_args()  # analyze arguments
    return args

def hist(vlist, name, binrange = 0.02): 
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # fill value list
    bins = np.arange(np.nanmin(vlist),np.nanmax(vlist), binrange)
    n = ax.hist(vlist, bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # set hist style
    plt.tick_params(labelsize=18)    
    ax.set_title(name,fontsize=20)
    ax.set_xlabel(f'mm',fontsize=18,loc='right') 
    ax.set_ylabel(f'number of modules',fontsize=18,loc='top')

    # show hist
    plt.savefig(f'lineFit/{name}.jpg')  #save as jpeg
    logger.info(f'save as lineFit/{name}.jpg')
    plt.show()

def run(args):
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)
    SNs = analysisData['serial_number'].unique()
    angleDict = {}
    dxDict, dyDict = {},{}
    dataDict = {}
    snlist,taglist,xlist,ylist = [],[],[],[]
    df = pd.DataFrame()
    seriesList = []
    
    for sn in SNs:
        logger.info(f'load {sn}')
        if args.mark:
            if args.mark == 'TL':
                asic = Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkTL')
                flex = Flex_Bare_relation.getFmarkPoint(sn, 'FmarkTL')
                if asic is None or flex is None:
                    continue
            
            if args.mark == 'TR':
                asic = Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkTR')
                flex = Flex_Bare_relation.getFmarkPoint(sn, 'FmarkTR')
                if asic is None or flex is None:
                    continue

            if args.mark == 'BL':
                asic = Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkBL')
                flex = Flex_Bare_relation.getFmarkPoint(sn, 'FmarkBL')
                if asic is None or flex is None:
                    continue
            
            if args.mark == 'BR':
                asic = Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkBR')
                flex = Flex_Bare_relation.getFmarkPoint(sn, 'FmarkBR')
                if asic is None or flex is None:
                    continue
            
            dist = Flex_Bare_relation.calcdist(asic, flex)  # d, dx, dy 
            dxDict[sn] = dist[1]  # dx(abs)
            dyDict[sn] = dist[2]  # dy(abs)

        elif args.line:
            if args.line == 'T':
                edge1 = Flex_Bare_relation.edgeInfo(sn, 'SensorT')
                edge2 = Flex_Bare_relation.edgeInfo(sn, 'FlexT')
                if edge1 is None or edge2 is None:
                    continue
                angle = Flex_Bare_relation.oppositeAngle(edge1[1][1], edge2[1][1])    
            elif args.line == 'B':
                edge1 = Flex_Bare_relation.edgeInfo(sn, 'SensorB')
                edge2 = Flex_Bare_relation.edgeInfo(sn, 'FlexB')
                if edge1 is None or edge2 is None:
                    continue
                angle = Flex_Bare_relation.oppositeAngle(edge1[1][1], edge2[1][1])
            elif args.line == 'L':
                edge1 = Flex_Bare_relation.edgeInfo(sn, 'AsicL')
                edge2 = Flex_Bare_relation.edgeInfo(sn, 'FlexL')
                if edge1 is None or edge2 is None:
                    continue
                angle = Flex_Bare_relation.oppositeAngle(edge1[1][2], edge2[1][2])
            elif args.line == 'R':
                edge1 = Flex_Bare_relation.edgeInfo(sn, 'AsicR')
                edge2 = Flex_Bare_relation.edgeInfo(sn, 'FlexR')
                if edge1 is None or edge2 is None:
                    continue
                angle = Flex_Bare_relation.oppositeAngle(edge1[1][2], edge2[1][2])
            angleDict[sn] = angle

        elif args.table:
            tags = ['AsicFmarkTL','AsicFmarkTR','AsicFmarkBL','AsicFmarkBR',
                   'FmarkTL','FmarkTR','FmarkBL','FmarkBR']
            data = {}
            for tag in tags:
                point = Flex_Bare_relation.getFmarkPoint(sn, tag)
                snlist.append(sn)
                taglist.append(tag)
                if point is None:
                    data[tag] = [0,0]
                    xlist.append(None)
                    ylist.append(None)
                else:
                    data[tag] = point
                    xlist.append(point[0])
                    ylist.append(point[1])
            series = pd.Series({
                'serial_number' : sn,
                'AsicFmarkTL_x': data['AsicFmarkTL'][0],
                'AsicFmarkTL_y': data['AsicFmarkTL'][1],
                'AsicFmarkTR_x': data['AsicFmarkTR'][0],
                'AsicFmarkTR_y': data['AsicFmarkTR'][1],
                'AsicFmarkBL_x': data['AsicFmarkBL'][0],
                'AsicFmarkBL_y': data['AsicFmarkBL'][1],
                'AsicFmarkBR_x': data['AsicFmarkBR'][0],
                'AsicFmarkBR_y': data['AsicFmarkBR'][1],
                'FlexFmarkTL_x': data['FmarkTL'][0],
                'FlexFmarkTL_y': data['FmarkTL'][1],
                'FlexFmarkTR_x': data['FmarkTR'][0],
                'FlexFmarkTR_y': data['FmarkTR'][1],
                'FlexFmarkBL_x': data['FmarkBL'][0],
                'FlexFmarkBL_y': data['FmarkBL'][1],
                'FlexFmarkBR_x': data['FmarkBR'][0],
                'FlexFmarkBR_y': data['FmarkBR'][1]
            })
            seriesList.append(series)

        elif args.ran:
            points = []
            if args.ran == 'AT':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkTL'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkTR'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'AB':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkBL'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkBR'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'AL':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkTL'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkBL'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'AR':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkTR'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'AsicFmarkBR'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'FT':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkTL'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkTR'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'FB':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkBL'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkBR'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'FL':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkTL'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkBL'))
                if points[0] is None or points[1] is None:
                    continue
            elif args.ran == 'FR':
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkTR'))
                points.append(Flex_Bare_relation.getFmarkPoint(sn, 'FmarkBR'))
                if points[0] is None or points[1] is None:
                    continue
            dist = Flex_Bare_relation.calcdist(points[0], points[1])  # d, dx, dy 
            dataDict[sn] = dist[0]  # d (abs)

            
        else:
            'no argument! type -h or --help'

    ####
    # serial number for roop
    ####################################
    # make hist and plot (sn VS data)
    ####
    
    if args.mark:
        # (dataDict, requirement, binrange, minmax, unit, filename=None)
        logger.info(f'{args.mark} dx')
        makeImages.hist(dxDict, [2.112, 2.312], 0.005, [2.0,2.5], 'mm',
                      f'flexBarePosition_{args.mark}_dx')
        makeImages.getBadSN(dxDict, 2.112, 2.312)
        logger.info(f'{args.mark} dy')
        makeImages.hist(dyDict, [0.65, 0.85], 0.005, [0.5, 1.0], 'mm',
                      f'flexBarePosition_{args.mark}_dy')
        makeImages.getBadSN(dyDict, 0.65, 0.85)
      
    elif args.line:
        makeImages.hist(angleDict, f'angle_between_2lines_{args.line}', 0.01)

    elif args.table:
        # make dataframe with serial number
        df = pd.concat(seriesList, axis=1)
        
        if args.table=='a':
            df=pd.DataFrame({'serial_number':snlist})    
            # add data to dataframe
            df['tag']=taglist
            df['x']=xlist
            df['y'] = ylist
            
        print(df)
        #df.to_csv('Fmark_XY_table_new.csv')
        #print('save Fmark xy table to Fmark_XY_table_new.csv')
    elif args.ran:
        if args.ran == 'AT':
            makeImages.hist(dataDict, [0,0], 0.005, [41.9,42.1], 'mm',
                            f'ASIC_Top_Fmark_range')
        elif args.ran == 'AB':
            makeImages.hist(dataDict, [0,0], 0.005, [41.9,42.1], 'mm',
                            f'ASIC_Bottom_Fmark_range')
        elif args.ran == 'AL':
            makeImages.hist(dataDict, [0,0], 0.005, [40.0,40.2], 'mm',
                            f'ASIC_Left_Fmark_range')
        elif args.ran == 'AR':
            makeImages.hist(dataDict, [0,0], 0.005, [40.0,40.2], 'mm',
                            f'ASIC_Right_Fmark_range')
            
        elif args.ran == 'FT':
            makeImages.hist(dataDict, [37.5,37.7], 0.005, [37.5,37.7], 'mm',
                            f'FLEX_Top_Fmark_range')
            makeImages.getBadSN(dataDict, 37.5, 37.7)
        elif args.ran == 'FB':
            makeImages.hist(dataDict, [37.5,37.7], 0.005, [37.5,37.7], 'mm',
                            f'FLEX_Bottom_Fmark_range')
            makeImages.getBadSN(dataDict, 37.5, 37.7)
        elif args.ran == 'FL':
            makeImages.hist(dataDict, [38.5,38.7], 0.005, [38.5,38.7], 'mm',
                            f'FLEX_Left_Fmark_range')
            makeImages.getBadSN(dataDict, 38.5,38.7)
        elif args.ran == 'FR':
            makeImages.hist(dataDict, [38.5,38.7], 0.005, [38.5,38.7], 'mm',
                            f'FLEX_Right_Fmark_range')
            makeImages.getBadSN(dataDict, 38.5,38.7)

      
        
        
if __name__ == '__main__':
    t1 = time.time()
#    logging.basicConfig(level=logging.INFO)
    args = parseArg()
    run(args)
    t2 = time.time()
    elapsed_time = t2-t1
    logger.info(f'run time : {elapsed_time}')
