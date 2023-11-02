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

def ngSN(key, df, reqmin, reqmax):
    std = np.std(df[key])  # get data value std deviation
    mean = np.mean(df[key])  # get data value mean
    minimum = np.amin(df[key])  # get data value min
    maximum = np.amax(df[key])  # get data value max
    quantity = 100
    #quantity = pd.count(df[key])

    nglist = {}
    ngnumber = 0
    for k,v in dic.items():
        if v < reqmin or v > reqmax:
            nglist[k] = v
            ngnumber += 1

    values = [quantity, minimum, maximum, mean, std, reqmin, reqmax, ngnumber/len(dic)]
    rows = ['Qty', 'min', 'max', 'mean', 'std', 'requirement min', 'requirement max', 'NG ratio']
    summary = pd.DataFrame(values, index=rows, columns=[key])
    ngSNDF = pd.DataFrame(nglist.keys(), columns=[key])
    ngSNDF = pd.concat([ngSNDF,pd.DataFrame(nglist.values())],axis=1)
    print(ngSNDF)
    print(summary)
    
    return summary, ngSNDF

def specialHist(scanData, name):
    #group scandata dataframe by tags
    grouptag = scanData.groupby(['tags'])
    exdf = grouptag.get_group('Connector')
    exdf.describe().to_csv('zhist/PCB_Connector_ScanSummary.csv')
    print(exdf.describe())
    fillteredDF = exdf[(exdf['scan_z']< 6.4)|(exdf['scan_z']> 6.6)]
    fillteredDF.to_csv('zhist/PCB_Connector_filltered.csv')
    print(fillteredDF['scan_z'])

    #define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    
#    bins = np.linspace(exdf['scan_z'].min(),exdf['scan_z'].max(), 100)
    bins = np.arange(np.amin(list(exdf['scan_z'])),
                     np.amax(list(exdf['scan_z'])), 0.01)
    #fill std list
    n = ax.hist(exdf['scan_z'], bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # show text of required area
    #ax.text(require[0]-2*binrange, np.amax(n[0]), f'{require[0]}',
     #       color='#ff5d00',size=14)
    #ax.text(require[1]-5*binrange, np.amax(n[0]), f'{require[1]}',
      #      color='#ff5d00',size=14)

    # set hist style
    plt.tick_params(labelsize=18)
    ax.set_title(f'Connector scan z',fontsize=20)
    ax.set_xlabel(f'mm',fontsize=18,loc='right') 
    ax.set_ylabel(f'events/0.01mm',fontsize=18,loc='top')

    # show hist
    #ax.legend(loc='upper left',fontsize=18)
    plt.savefig(f'zhist/pcb_population_Connector.jpg')  #save as jpeg
    print(f'save as zhist/pcb_population_Connector.jpg')
    plt.show()
    
    #define matplotlib figure
    fig2 = plt.figure(figsize=(10,9))
    ax2 = fig2.add_subplot(1,1,1)
    
#    bins = np.linspace(exdf['scan_z'].min(),exdf['scan_z'].max(), 100)
    bins2 = np.arange(6.4,6.6, 0.01)
    #fill std list
    n2 = ax2.hist(exdf['scan_z'], bins=bins2, alpha=1, histtype="stepfilled",edgecolor='black')

    # set hist style
    plt.tick_params(labelsize=18)
    ax2.set_title(f'Connector scan z (extract)',fontsize=20)
    ax2.set_xlabel(f'mm',fontsize=18,loc='right') 
    ax2.set_ylabel(f'events/0.01mm',fontsize=18,loc='top')

    # show hist
    #ax.legend(loc='upper left',fontsize=18)
    plt.savefig(f'zhist/pcb_population_Connector_ex.jpg')  #save as jpeg
    print(f'save as zhist/pcb_population_Connector_ex.jpg')
    plt.show()
    
    
    
def fmark(scanData, anaData, tag):
    #define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    #allZ = np.concatenate(scanData['z'])
    exScanData = scanData[scanData['tags'].str.contains('\AFmark')]
    bins = np.linspace(exScanData['scan_z'].min(),exScanData['scan_z'].max(), 100)
    #group scandata dataframe by tags
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
    with open(f'data/PCB_ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/PCB_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    #get arguments
    arg = sys.argv
    #Differentiate the cases by arguments
    if len(arg)==2:
        fmark(scanData, analysisData, arg[1])
    if len(arg)==1:
        specialHist(scanData, 'Connector')
