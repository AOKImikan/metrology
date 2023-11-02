#!/usr/bin/env python3
import os
import pickle
import sys
import time
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt

def extractLargeZ(scanData,tag):
    # group scandata dataframe by tags
    pltdata = scanData.groupby(['tags'])
    # extract by specified tag
    extractData = pltdata.get_group((tag))

    # get standard deviation
    std = extractData['scan_z'].std()
    mean = extractData['scan_z'].mean()
    print('std = ',std)

    # define return list
    NGSN = []
    
    # extractData 1 row roop
    i = 0
    while i<len(extractData):
        # extract 1 row (dataframe -> series)
        rowi = extractData.iloc[i]
        # z > standard deviation?
        if abs(rowi['scan_z']-mean) > 0.03:
            # print NG serial number
            print('NG SN ', rowi['image_path'])
            NGSN.append(rowi['serial_number'])
        i += 1
    return NGSN

def plotPoint(scanData, anaData, tagName):    
    # group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
   
    # extract by specified tag
    extractData = grouptag.get_group((tagName))
    
    # group analysis data by tags
    grouptag_ana = anaData.groupby(['tags'])
    # extract by specified tag
    extractData_ana = grouptag_ana.get_group((tagName))
    
    # define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)

    ax.set_title(tagName)
   
    # set plot area
    # set image edge
    dx=0.57
    dy=0.38
    right = extractData['scan_x'].iloc[1]+dx
    left = extractData['scan_x'].iloc[1]-dx
    top = extractData['scan_y'].iloc[1]+dy
    botom = extractData['scan_y'].iloc[1]-dy
    ax.axvline(right, color="#10f000",lw=1)
    ax.axvline(left, color="#10f000",lw=1)
    ax.axhline(top, color="#10f000",lw=1)
    ax.axhline(botom, color="#10f000",lw=1)
    
    # add point at center of photo
    ax.scatter(extractData['scan_x'].iloc[1],extractData['scan_y'].iloc[1],
               color="#10f000", marker="x")

    # large difference between scan z and average z
    # NG serial number 
    NGsn = extractLargeZ(scanData,tagName)

    # set point
    for sn in extractData_ana['serial_number']:
        name = 'serial_number==\"{}\"'.format(sn)
        x = extractData_ana.loc[extractData_ana.query(name).index[0], 'detect_x']
        y = extractData_ana.loc[extractData_ana.query(name).index[0], 'detect_y']

        if len(NGsn)>0:
            if sn in NGsn:  # if serial number = NG serial number 
                # add detected point as red
                ax.scatter(x,y,color="#ff0000", label='large deviation of z')
            else:  # normal z
                # add detected point as green
                ax.scatter(x,y,color="#007fff")
        else:
            #add detected point as green
            ax.scatter(x,y,color="#007fff")
            
    #set legend
    plt.legend(loc="upper right")
    
    #draw plot
    plt.show()
    
def extractMargin(scandata, analydata):
    serialnum=[]
    for k,v in analydata.items():
        serialnum.append(k)

    ###################
    SN=serialnum[0]
    pointName = 'AsicFmark'
    lineName = 'Flex'
    ###################
    
    plotPoint(SN, pointName, scandata, analydata)

#show all tags std hist
def HistStd(scanData):
    # group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
    # get std x,y,z
    stdDF = grouptag.std()
    # save
    stdDF.to_csv('data/scandataSTD.csv')
    # get std z
    stdlist = stdDF['scan_z']

    # define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    # fill std list 
    ax.hist(stdlist, bins=50)

    ax.set_title('scan data z standard deviation')
    ax.set_xlabel('std')
    ax.set_ylabel('number of tags')

    # show hist
    plt.show()

def extractStd(scanData, threshold):
    # group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
    # get std x,y,z
    stdDF = grouptag.std()

    largeStd = stdDF[stdDF.scan_z > threshold]
    print(largeStd)  
        
def run(scanData, anaData, args):
    #####extractMargin(scanData, anaData)
    if args.asic:
        # plot scan point with image center
        if args.asic=='TL':
            plotPoint(scanData, anaData, 'AsicFmarkTL')
        if args.asic=='TR':
            plotPoint(scanData, anaData, 'AsicFmarkTR')
        if args.asic=='BL':
            plotPoint(scanData, anaData, 'AsicFmarkBL')
        if args.asic=='BR':
            plotPoint(scanData, anaData, 'AsicFmarkBR')

    if args.flex:
        # plot scan point with image center
        if args.flex=='TL':
            plotPoint(scanData, anaData, 'FmarkTL')
        if args.flex=='TR':
            plotPoint(scanData, anaData, 'FmarkTR')
        if args.flex=='BL':
            plotPoint(scanData, anaData, 'FmarkBL')
        if args.flex=='BR':
            plotPoint(scanData, anaData, 'FmarkBR')

    if args.extract:
        # show tag and scan xyz if large std
        extractStd(scanData, 0.03)
        
    if args.hist:
        # std histgram
        HistStd(scanData)
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp

    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('-a','--asic', help='Asic fiducial mark',
                        choices=['TL','TR','BL','BR'])
    parser.add_argument('-f','--flex', help='Flex fiducial mark',
                        choices=['TL','TR','BL','BR'])
    parser.add_argument('-e','--extract', help='extract', action='store_true')
    parser.add_argument('--hist', help='show all tags std of z histgram', action='store_true')

    args = parser.parse_args()  # analyze arguments
    
    # assign read file path 
    with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    # run main
    run(scanData, analysisData, args)    

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
