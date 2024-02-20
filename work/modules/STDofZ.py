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
import FmarkMarginPlot

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('-e','--extract', help='extract', action='store_true')
    parser.add_argument('-s', '--std', help='show all tags std of z histgram', action='store_true')
    parser.add_argument('-t', '--tag', help='show z hist of that tag')

    # tag list
    # 'Jig' 'Pickup1' 'Pickup2' 'Pickup3' 'Pickup4' 'FmarkTR' 'FmarkBR'
    # 'FmarkBL' 'FmarkTL' 'AsicFmarkTR' 'AsicFmarkBR' 'AsicFmarkBL'
    # 'AsicFmarkTL' 'HVCapacitor' 'Connector' 'AsicR' 'SensorB' 'AsicL'
    # 'SensorT' 'FlexL' 'FlexT' 'FlexR' 'FlexB'

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
    
    FmarkMarginPlot.plotPoint(SN, pointName, scandata, analydata)

def HistTag(scanData, tag):
    # group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
 
    
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
    print(scanData['tags'].unique())
    #####extractMargin(scanData, anaData)
    if args.extract:
        # show tag and scan xyz if large std
        extractStd(scanData, 0.03)
        
    if args.hist:
        # std histgram
        HistStd(scanData)
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp

    args = parseArg()
    
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
