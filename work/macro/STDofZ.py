#!/usr/bin/env python3
import os
import pickle
import sys
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def extractLargeZ(scanData,tag):
    #group scandata dataframe by tags
    pltdata = scanData.groupby(['tags'])
    #extract by specified tag
    extractData = pltdata.get_group((tag[1]))

    #get standard deviation
    std = extractData['scan_z'].std()
    mean = extractData['scan_z'].mean()
    print('std = ',std)

    #define return list
    NGSN = []
    
    #extractData 1 row roop
    i = 0
    while i<len(extractData):
        #extract 1 row (dataframe -> series)
        rowi = extractData.iloc[i]
        # z > standard deviation?
        if abs(rowi['scan_z']-mean) > 0.03:
            #print NG serial number
            print('NG SN ', rowi['image_path'])
            NGSN.append(rowi['serial_number'])
        i += 1
    return NGSN

def plotPoint(scanData, anaData, tagName):    
    #group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
   
    #extract by specified tag
    extractData = grouptag.get_group((tagName[1]))
    #print(extractData)

    #group analysis data by tags
    grouptag_ana = anaData.groupby(['tags'])
    #extract by specified tag
    extractData_ana = grouptag_ana.get_group((tagName[1]))
    
    #define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)

    ax.set_title(tagName[1])
   
    #set plot area
    #set image edge
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
    
    #add point at center of photo
    ax.scatter(extractData['scan_x'].iloc[1],extractData['scan_y'].iloc[1],
               color="#10f000", marker="x")

    #large difference between scan z and average z
    #NG serial number
    NGsn = extractLargeZ(scanData,tagName)
    
    ##set plot point##
    for sn in extractData_ana['serial_number']:
        name = 'serial_number==\"{}\"'.format(sn)
        x = extractData_ana.loc[extractData_ana.query(name).index[0], 'detect_x']
        y = extractData_ana.loc[extractData_ana.query(name).index[0], 'detect_y']

        if len(NGsn)>0:
            ##if serial number = NG serial number 
            if sn in NGsn:
                #add detected point as red
                ax.scatter(x,y,color="#ff0000", label='large deviation of z')
            else:
                #add detected point as green
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
    #group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
    #get std x,y,z
    stdDF = grouptag.std()
    #get std z
    stdlist = stdDF['scan_z']

    #define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    #fill std list 
    ax.hist(stdlist, bins=50)

    ax.set_title('scan data z standard deviation')
    ax.set_xlabel('std')
    ax.set_ylabel('number of tags')
    #show hist
    plt.show()

def extractStd(scanData, threshold):
    #group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
    #get std x,y,z
    stdDF = grouptag.std()

    largeStd = stdDF[stdDF.scan_z > threshold]
    print(largeStd)  
        
def run(scanData, anaData, args):
    #####extractMargin(scanData, anaData)
    #command argment is true
    if len(args)==3:
        com = args[2]
        if com=='exStd':
            #show tag and scan xyz if large std
            extractStd(scanData, 0.03)
        if com=='histStd':
            #std histgram
            HistStd(scanData)
    #none command
    if len(args)==2:
        #plot scan point with image center
        plotPoint(scanData, anaData, args)
    
if __name__ == '__main__':
    #get argument
    args = sys.argv
    #open data as dataframe
    with open(f'data/ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)
        
    run(scanData, analysisData, args)    
