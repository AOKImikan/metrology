#!/usr/bin/env python3
import os
import json
import time
#import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import logging
logger = logging.getLogger(__name__)

def getBadSN(dataDict, dataList, require):
    summary = {}
    summary['std'] = np.std(dataList)    # get data value std deviation
    summary['mean'] = np.mean(dataList)  # get data value mean
    summary['min'] = np.amin(dataList)   # get data value min
    summary['max'] = np.amax(dataList)   # get data value max
    summary['quantity'] = len(dataList)
    summary['req_min'] = require[0]
    summary['req_max'] = require[1]
    
    ngnumber = 0
    df_badSN = pd.DataFrame(columns=['serial_number','data'])
    sns = []
    datas = []
        
    for k,v in dataDict.items():
        if isinstance(v, list):
            for val in v:
                if val < require[0] or val > require[1]:
                    sns.append(k)
                    datas.append(val)
                    ngnumber += 1
        else:
            if v < require[0] or v > require[1]:
                datas.append(v)
                sns.append(k)
                ngnumber += 1
                
    df_badSN['serial_number'] = sns
    df_badSN['data'] = datas
  
    summary['bad_ratio'] = ngnumber/summary['quantity']*100
    summaryDF = pd.DataFrame.from_dict(summary,orient = "index")
    summaryDF = summaryDF.round(3)
    print('badSN')
    print(df_badSN)
    print('summary')
    print(summaryDF)
    return df_badSN, summaryDF

# make hist
def hist(dataDict, require, binrange, minmax=None, unit='', filename = None):
       
    #df_badSN = getBadSN(dataDict, require[0], require[1])
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    if require[0]==0 and require[1]==0:
        pass
    else:
        ax.axvspan(require[0], require[1], color='yellow', alpha=0.5)

    # fill data
    datas = []
    for i in dataDict.values():
        if isinstance(i, list):
            for val in i:
                datas.append(val)
        else:
            datas.append(i)

    # set histgram range
    if minmax:
        bins = np.arange(minmax[0], minmax[1], binrange)
    else:
        bins = np.arange(np.amin(datas), np.amax(datas), binrange)
     
    n = ax.hist(datas, bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # show text of required area
    ax.text(require[0]-2*binrange, np.amax(n[0]),f'{require[0]}',
            color='#ff5d00',size=14)
    ax.text(require[1]-5*binrange, np.amax(n[0]),f'{require[1]}',
            color='#ff5d00',size=14)
  
    # set hist style
    plt.tick_params(labelsize=18)
    if filename:
        ax.set_title(f'{filename}',fontsize=20)
    else:
        pass
    ax.set_xlabel(f'{unit}',fontsize=18, loc='right') 
    ax.set_ylabel(f'events/{binrange}{unit}',fontsize=18, loc='top')

    # show hist
    if filename:
        #plt.savefig(f'zhist/{filename}.jpg')  #save as jpeg
        plt.savefig(f'resultsHist/{filename}.jpg')  #save as jpeg
        logger.info(f'save as resultsHist/{filename}.jpg')
    else:
        pass
    
    plt.show()

    return

def graph(dataDict, require, minmax=None, unit='', filename = None):
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    fig.subplots_adjust(left=0.15)
    fig.subplots_adjust(bottom=0.1)
    ax = fig.add_subplot(1,1,1)

    # paint required area
    ax.axhspan(require[0], require[1], color='yellow', alpha=0.3,zorder=1)
    if minmax:
        # show text of required area
        ax.text(minmax[1],require[0]-0.01,f'{require[0]}',
                color='#ff5d00',size=14)
        ax.text(minmax[1],require[1],f'{require[1]}',
                color='#ff5d00',size=14)

    # set axis limit
    if minmax:
        ax.set_xlim(minmax[0], minmax[1])
        #ax.set_ylim(require[0]-0.4, require[1]+0.3)

    # add data
    for k,v in dataDict.items():
        last_four_digits = k[-4:]
        number = int(last_four_digits)
        #if v==0:
        #    bad = require[0]
        #    ax.scatter(number, bad, c='#ff0000',marker='x',zorder=2)
        if isinstance(v, list):
            for val in v:
                #ax.scatter(number, v[0], c='#ff0000',marker='x',zorder=2)
                ax.scatter(number, val, c='#0055e0',marker='o',zorder=2)
        else:
            ax.scatter(number, v, c='#0055e0',marker='o',zorder=2)

    # set hist style
    plt.tick_params(labelsize=16)
    if filename:
        ax.set_title(f'{filename}',fontsize=20)
    else:
        pass
    
    ax.set_xlabel(f'serialNumber(last 4 digits)',fontsize=18, loc='right') 
    ax.set_ylabel(f'{unit}',fontsize=18, loc='top')
   
    # show hist
    if filename:
        plt.savefig(f'zhist/{filename}.jpg')  #save as jpeg
        #plt.savefig(f'resultsHist/{filename}.jpg')  #save as jpeg
        logger.info(f'save as resultsHist/{filename}.jpg')
    else:
        pass
    plt.show()
    return
