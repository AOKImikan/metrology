#!/usr/bin/env python3
import os
import pickle
import sys
import re
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse


def parseArg():
    parser = argparse.ArgumentParser()

    # add argument
    parser.add_argument('--tag', help='scan tag')
    
    args = parser.parse_args()  # analyze arguments
    return args

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

#show hist
def hist(listlist, tag): 
    #define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    #fill std list 
    ax.hist(listlist, bins=50)

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

    largeStd = stdDF[stdDF.z > threshold]
    print(largeStd)  
    
def extractLargeZ(scanData,tag):
    #group scandata dataframe by tags
    pltdata = scanData.groupby(['tags'])
    #extract by specified tag
    extractData = pltdata.get_group((tag[1]))

    #get standard deviation
    std = extractData['z'].std()
    mean = extractData['z'].mean()
    print('std = ',std)

    #define return list
    NGSN = []
    
    #extractData 1 row roop
    i = 0
    while i<len(extractData):
        #extract 1 row (dataframe -> series)
        rowi = extractData.iloc[i]
        # z > standard deviation?
        if abs(rowi['z']-mean) > 0.03:
            #print NG serial number
            print('NG SN ', rowi['serialnumber'])
            NGSN.append(rowi['serialnumber'])
        i += 1
    return NGSN

def general(scanData, anaData):
    print('h')
    
def fmark(scanData, anaData, tag):
    #define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    #allZ = np.concatenate(scanData['z'])
    exScanData = scanData[scanData['tags'].str.contains('\AFmark')]
    bins = np.linspace(exScanData['scan_z'].min(),exScanData['scan_z'].max(), 100)
    # group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
    #pattern = re.compile('{}Fmark\w'.format(tag))
    pattern = re.compile('\AFmark\w')
    listlist = []
    namelist = []
    for name in scanData['tags'].unique():
        if pattern.search(name):
            #extract by specified tag
            extractData = grouptag.get_group(name)
            
            #fill std list
            #histtype='step'
            ax.hist(extractData['scan_z'], bins, alpha=0.5, edgecolor='gray', label=name)
            #listlist.append(extractData[['scan_z','tags']])
    #hist(listlist, tag)
    plt.tick_params(labelsize=18)
    ax.set_title('scan data z',fontsize=18)
    ax.set_xlabel('z',fontsize=18)
    ax.set_ylabel('events',fontsize=18)
    #show hist
    ax.legend(loc='upper left',fontsize=18)
    plt.show()

    
if __name__ == '__main__':
        
    with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    #get arguments
    args = parseArg()
    
    fmark(scanData, analysisData, args.tag)
    #general(scanData, analysisData)
        
