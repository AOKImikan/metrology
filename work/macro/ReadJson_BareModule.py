#!/usr/bin/env python3
import os
import json
import time
import glob
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

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

def hist(dnames, key, arg = 'unspecified'):
    dataDict = {}
    mergedlist = []
    if arg is 'unspecified':    # multiple values and individual
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                #mergedlist.append(results[key])
                dataDict[sn]=results[key]
    else:
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                key2 = f'{key}_{arg}'
                #mergedlist.append(results[key2])
                dataDict[sn]=results[key2]

    # print NG data            
    std = np.std(list(dataDict.values()))  # get data value std deviation
    SNlist = getNGSN(dataDict,std*2)  # get bad serial number list
    for k in  SNlist:
        print(k,'  ',dataDict[k])  # print serial number and data value   
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)
 
    # fill thickness list 
    ax.hist(dataDict.values(), bins=50, alpha=1, histtype="stepfilled",edgecolor='black')

    # set hist style
    plt.tick_params(labelsize=18)
    if arg is 'unspecified':
        #ax.set_title(f'{key}',fontsize=18)
        ax.set_xlabel(f'{key}',fontsize=18)
    else:
        #ax.set_title(f'{key}-{arg}',fontsize=18)
        ax.set_xlabel(f'{key}-{arg}',fontsize=18)
    ax.set_ylabel('events',fontsize=18)

    # show hist
    #if arg is 'unspecified':
        #plt.savefig(f'resultsHist/{key}.jpg')  #save as jpeg
        #print(f'save as resultsHist/{key}.jpg')
    #else:
        #plt.savefig(f'resultsHist/{key}-{arg}.jpg')  #save as jpeg
        #print(f'save as resultsHist/{key}-{arg}.jpg')
    #plt.show()

def run(dnames, args):
    if args.sensor:
        hist(dnames, 'SENSOR', args.sensor)
    elif args.fechips:
        hist(dnames, 'FECHIPS', args.fechips)
    elif args.fethick:
        hist(dnames, 'FECHIP_THICKNESS')
    elif args.barethick:
        hist(dnames, 'BAREMODULE_THICKNESS')
    elif args.senthick:
        hist(dnames, 'SENSOR_THICKNESS')
    elif args.std:
        if args.std == 's':
            hist(dnames, 'SENSOR_THICKNESS_STD_DEVIATION')
        if args.std == 'f':
            hist(dnames, 'FECHIP_THICKNESS_STD_DEVIATION')
        if args.std == 'b':
            hist(dnames, 'BAREMODULE_THICKNESS_STD_DEVIATION')
    else:
        print('Error: No such Command. type option -h or --help')  
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp

    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('-s','--sensor', help='SENSOR',choices=['X','Y'])
    parser.add_argument('-f','--fechips', help='FECHIPS',choices=['X','Y'])
    parser.add_argument('--fethick', help='FECHIPS_THICKNESS',action='store_true')
    parser.add_argument('--barethick', help='BAREMODULE_THICKNESS',action='store_true')
    parser.add_argument('--senthick', help='SENSOR_THICKNESS', action='store_true')
    parser.add_argument('--std', help='THICKNESS_STD_DEVIATION FeChip, Bare, Sensor',choices=['f','b','s'])
    args = parser.parse_args()  # analyze arguments

    # assign read file path
    files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/20UPG*")
    dnames = []  # define path list
    for fn in files:
        filepath = fn + '/BAREMODULERECEPTION'  # stage
        if os.path.exists(filepath) :  
            scanNumList = glob.glob(filepath+'/*')
            scanNumList.sort()
            count = len(scanNumList)
            dnames.append(scanNumList[count-1])
    print(f'counts of module : {len(dnames)}')

    # run
    run(dnames,args)
    
    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  

