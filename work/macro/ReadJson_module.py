#!/usr/bin/env python3
import os
import json
import time
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from myModules import data_module

# get key extract by values
def getNGSN(dic, threshold):
    mean = np.mean(list(dic.values()))
    keys = [k for k,v in dic.items() if abs(v-mean) > threshold]
    if keys:
        return keys
    else:
        return None

# db.json -> results and somponent serial number
def LoadData(dn):
    appdata = None
    results = {}
    sn = 'serial number'
    if os.path.exists(dn):
        with open(f'{dn}/db.json', 'rb') as fin:
            appdata = json.load(fin)
            results = appdata['results']
            sn = appdata['component']
    return results, sn

# make hist
def hist(dnames, key,requiremin, requiremax, arg = 8):
    dataDict = {}
    if arg < 8:    # multiple values and individual
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                dataDict[sn]=results[key][arg]

    elif arg > 8:  # multiple values and all
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                for val in results[key]:
                    dataDict[sn]=val

    else:          # one value (arg=8)
        for dn in dnames:
            results = LoadData(dn)[0]
            sn = LoadData(dn)[1]
            if len(results)>0:
                dataDict[sn]=results[key]

    # print NG data            
    std = np.std(list(dataDict.values()))  # get data value std deviation
    SNlist = getNGSN(dataDict,std*2)  # get bad serial number list
    if SNlist:  # NGSN is exist or not
        for k in SNlist:
            print(k,'  ',dataDict[k])  # print serial number and data value   
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    ax.axvspan(requiremin, requiremax, color='yellow', alpha=0.5)
    
    # fill thickness list 
    ax.hist(dataDict.values(), bins=50, alpha=1, histtype="stepfilled",edgecolor='black')
    
    # set hist style
    plt.tick_params(labelsize=18)
    if arg < 8:
        ax.set_title(f'{key}_{arg}',fontsize=20)
        #ax.set_xlabel(f'{key}_{arg}',fontsize=18)
    else:
        ax.set_title(f'{key}',fontsize=20)
        #ax.set_xlabel(f'{key}',fontsize=18) 
    ax.set_ylabel('events',fontsize=18)

    # show hist
    if arg < 8:
        plt.savefig(f'resultsHist/module_asem_{key}_{arg}.jpg')  #save as jpeg
        print(f'save as resultsHist/module_assem_{key}_{arg}.jpg')
    else:
        plt.savefig(f'resultsHist/module_assem_{key}.jpg')  #save as jpeg
        print(f'save as resultsHist/module_assem_{key}.jpg')
    plt.show()

def plot(dnames):
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    TRlistX,TRlistY = [],[]
    BLlistX,BLlistY = [],[]
    for dn in dnames:
        results = LoadData(dn)
        TR=results['PCB_BAREMODULE_POSITION_TOP_RIGHT']
        BL=results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT']
        TRlistX.append(results['PCB_BAREMODULE_POSITION_TOP_RIGHT'][0])
        TRlistY.append(results['PCB_BAREMODULE_POSITION_TOP_RIGHT'][1])
        BLlistX.append(results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT'][0])
        BLlistY.append(results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT'][1])

        # set plot point    
        ax.scatter(BL[0],BL[1],color="#007fff")      
    ax.set_title('PCB_BAREMODULE_POSITION_BOTTOM_LEFT')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
   
    # draw plot
    plt.show()

def run(dnames, args):
    
    if args.TR:
        if args.TR == '0':
            hist(dnames, 'PCB_BAREMODULE_POSITION_TOP_RIGHT', 2.162, 2.262, 0)
        if args.TR == '1':
            hist(dnames, 'PCB_BAREMODULE_POSITION_TOP_RIGHT', 0.7, 0.8, 1)
    elif args.BL:
        if args.BL == '0':
            hist(dnames, 'PCB_BAREMODULE_POSITION_BOTTOM_LEFT', 2.162, 2.262, 0)
        if args.BL == '1':
            hist(dnames, 'PCB_BAREMODULE_POSITION_BOTTOM_LEFT', 0.7, 0.8, 1)
    elif args.aveThick:
        hist(dnames, 'AVERAGE_THICKNESS',0.56,0.58, int(args.aveThick))
    elif args.stdThick:
        hist(dnames, 'STD_DEVIATION_THICKNESS', int(args.stdThick))
    elif args.angle:
        hist(dnames, 'ANGLE_PCB_BM', -0.01, 0.01)
    elif args.pickup:
        hist(dnames, 'THICKNESS_VARIATION_PICKUP_AREA')
    elif args.power:
        hist(dnames, 'THICKNESS_INCLUDING_POWER_CONNECTOR', 1.521, 1.761)
    elif args.HVcapa:
        hist(dnames, 'HV_CAPACITOR_THICKNESS', 1.701, 2.111)
    else:
        print('Error: No such Command. type option -h or --help')  
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp

    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('--TR', help='PCB_BAREMODULE_POSITION_TOP_RIGHT',choices=['0','1','10'])
    parser.add_argument('--BL', help='PCB_BAREMODULE_POSITION_BOTTOM_LEFT',choices=['0','1','10'])
    parser.add_argument('--aveThick', help='AVERAGE_THICKNESS',choices=['0','1','2','3','10'])
    parser.add_argument('--stdThick', help='STD_DEVIATION_THICKNESS',choices=['0','1','2','3','10'])
    parser.add_argument('--angle', help='ANGLE_PCB_BM', action='store_true')
    parser.add_argument('--pickup', help='THICKNESS_VARIATION_PICKUP_AREA',
                        action='store_true')
    parser.add_argument('--power', help='THICKNESS_INCLUDING_POWER_CONNECTOR',
                        action='store_true')
    parser.add_argument('--HVcapa', help='HV_CAPACITOR_THICKNESS',
                        action='store_true')
    args = parser.parse_args()  # analyze arguments
    
    # assign read file path 
    dnames = data_module.getFilelist()
           
    print(f'counts of module : {len(dnames)}')

    # run main
    run(dnames,args)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
