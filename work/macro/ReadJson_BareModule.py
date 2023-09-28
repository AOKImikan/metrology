#!/usr/bin/env python3
import os
import json
import time
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from myModules import data_baremodule

# get key extract by values
def getNGSN(dic, threshold):
    mean = np.mean(list(dic.values()))
    keys = [k for k,v in dic.items() if abs(v-mean) > threshold]
    if keys:
        return keys
    else:
        return None
    
def calculateSTD(dic):
    std = np.std(list(dic.values()))
    print(np.std(list(dic.values())))
    return std
    
# db.json -> results and serial number
def LoadData(dn):
    appdata = None
    results = {}
    sn = 'serial_number'
    if os.path.exists(f'{dn}/db.json'):
        with open(f'{dn}/db.json', 'rb') as fin:
            appdata = json.load(fin)
        results = appdata['results']
        sn = appdata['component']
    return results, sn

def hist(dnames, key, requiremin, requiremax, arg = 'unspecified'):
    dataDict = {}
    exception = ['20UPGB42399001','20UPGB42399002','20UPGB42399003']
    
    if arg is 'unspecified':    # multiple values and individual
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                if sn in exception and key.endswith('THICKNESS'):
                    dataDict[sn]=results[key]*1000
                else:
                    dataDict[sn]=results[key]
    else:
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                key2 = f'{key}_{arg}'

                dataDict[sn]=results[key2]

    # print NG data            
    std = np.std(list(dataDict.values()))  # get data value std deviation
    SNlist = getNGSN(dataDict,std*2)  # get bad serial number list
    for k in  SNlist:
        print(k,'  ',dataDict[k])  # print serial number and data value   
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    ax.axvspan(requiremin, requiremax,color='yellow',alpha=0.5)
    #ax.axvline(requiremin,color='black')
    #ax.axvline(requiremax,color='black')
 
    # fill thickness list 
    ax.hist(dataDict.values(), bins=50, alpha=1, histtype="stepfilled",edgecolor='black')

    # set hist style
    plt.tick_params(labelsize=18)
    if arg is 'unspecified':
        ax.set_title(f'{key}',fontsize=20)
        #ax.set_xlabel(f'{key}',fontsize=18)
    else:
        ax.set_title(f'{key}-{arg}',fontsize=20)
        #ax.set_xlabel(f'{key}-{arg}',fontsize=18)
    ax.set_ylabel('events',fontsize=18)

    # show hist
    if arg is 'unspecified':
        plt.savefig(f'resultsHist/bare_{key}.jpg')  #save as jpeg
        print(f'save as resultsHist/bare_{key}.jpg')
    else:
        plt.savefig(f'resultsHist/bare_{key}-{arg}.jpg')  #save as jpeg
        print(f'save as resultsHist/bare_{key}-{arg}.jpg')
    plt.show()
    

def run(dnames, args):
    if args.sensor:
        if args.sensor =='X':
            hist(dnames, 'SENSOR', 39.5, 39.55, args.sensor)
        if args.sensor =='Y':
            hist(dnames, 'SENSOR', 41.1, 41.15, args.sensor)
    elif args.fechips:
        if args.fechips == 'X':
            hist(dnames, 'FECHIPS', 42.187, 42.257, args.fechips)
        if args.fechips == 'Y':
            hist(dnames, 'FECHIPS', 40.255, 40.322, args.fechips)
    elif args.fe:
        hist(dnames, 'FECHIP_THICKNESS', 153, 159)
    elif args.bare:
        hist(dnames, 'BAREMODULE_THICKNESS', 310, 330)
    elif args.sen:
        hist(dnames, 'SENSOR_THICKNESS', 146, 178)
    elif args.std:
        if args.std == 's':
            hist(dnames, 'SENSOR_THICKNESS_STD_DEVIATION',0,10)
        if args.std == 'f':
            hist(dnames, 'FECHIP_THICKNESS_STD_DEVIATION',0,10)
        if args.std == 'b':
            hist(dnames, 'BAREMODULE_THICKNESS_STD_DEVIATION',0,10)
    else:
        print('Error: No such Command. type option -h or --help')  
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp

    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('-s','--sensor', help='SENSOR',choices=['X','Y'])
    parser.add_argument('-f','--fechips', help='FECHIPS',choices=['X','Y'])
    parser.add_argument('--fe', help='FECHIPS_THICKNESS',action='store_true')
    parser.add_argument('--bare', help='BAREMODULE_THICKNESS',action='store_true')
    parser.add_argument('--sen', help='SENSOR_THICKNESS', action='store_true')
    parser.add_argument('--std', help='THICKNESS_STD_DEVIATION FeChip, Bare, Sensor',choices=['f','b','s'])
    args = parser.parse_args()  # analyze arguments

    # assign read file path
    dnames = data_baremodule.getFilelist()
    # run
    run(dnames,args)
    
    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  

