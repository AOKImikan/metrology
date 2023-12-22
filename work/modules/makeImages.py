#!/usr/bin/env python3
import os
import json
import time
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import logging
logger = logging.getLogger(__name__)

def getBadSN(dic, reqmin, reqmax):
    summary = {}
    summary['std'] = np.std(list(dic.values()))  # get data value std deviation
    summary['mean'] = np.mean(list(dic.values()))  # get data value mean
    summary['min'] = np.amin(list(dic.values()))  # get data value min
    summary['max'] = np.amax(list(dic.values()))  # get data value max
    summary['quantity'] = len(dic)
    summary['req_min'] = reqmin
    summary['req_max'] = reqmax
    
    ngnumber = 0
    ngDict = {}
    for k,v in dic.items():
        if v < reqmin or v > reqmax:
            ngDict[k] = v
            ngnumber += 1
            
    summary['bad_ratio'] = ngnumber/summary['quantity']
    summaryDF = pd.DataFrame.from_dict(summary,orient = "index")
    df_badSN = pd.DataFrame(ngDict.keys())
    df_badSN = pd.concat([df_badSN, pd.DataFrame(ngDict.values())],axis=1)
    print(df_badSN)
    print(summaryDF)
    return df_badSN, summary

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

    # set histgram range
    if minmax:
        bins = np.arange(minmax[0], minmax[1], binrange)
    else:
        bins = np.arange(np.amin(list(dataDict.values())),
                         np.amax(list(dataDict.values())), binrange)

    # fill data
    datas = []
    for i in dataDict.values():
        if isinstance(i, list):
            pass
        else:
            datas.append(i)
     
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
        ax.set_ylim(require[0]-0.01, require[1]+0.06)

    # add data
    for k,v in dataDict.items():
        last_four_digits = k[-4:]
        number = int(last_four_digits)
        #if v==0:
        #    bad = require[0]
        #    ax.scatter(number, bad, c='#ff0000',marker='x',zorder=2)
        if isinstance(v, list):
            ax.scatter(number, v[0], c='#ff0000',marker='x',zorder=2)
        else:
            ax.scatter(number, v, c='#0055e0',marker='o',zorder=2)

    # set hist style
    plt.tick_params(labelsize=16)
    if filename:
        ax.set_title(f'{filename}',fontsize=20)
    else:
        pass
    ax.set_xlabel(f'serialNumber(20UPGPQ260-)',fontsize=18, loc='right') 
    ax.set_ylabel(f'{unit}',fontsize=18, loc='top')
   
    # show hist
    if filename:
        plt.savefig(f'resultsHist/{filename}.jpg')  #save as jpeg
        logger.info(f'save as resultsHist/{filename}.jpg')
    else:
        pass
    plt.show()
    return
