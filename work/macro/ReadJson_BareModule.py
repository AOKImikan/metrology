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

# db.json -> 
def LoadData(dn):
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/db.json', 'rb') as fin:
            appdata = json.load(fin)
    if appdata:
        results = appdata['results']
        passed = appdata['passed']
        print(appdata['component'])
    return results

def hist(dnames, key, arg = 8):
    mergedlist = []
    if arg < 8:    # multiple values and individual
        for dn in dnames:
            results = LoadData(dn)
            mergedlist.append(results[key][arg])
    elif arg > 8:  # multiple values and all
        for dn in dnames:
            results = LoadData(dn)
            for val in results[key]:
                mergedlist.append(val)
    else:          # one value (arg=8)
        for dn in dnames:
            results = LoadData(dn)
            mergedlist.append(results[key])
        
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # fill thickness list 
    ax.hist(mergedlist, bins=10)
    
    # set hist style
    if arg < 8:
        ax.set_title(f'{key}-{arg}')
    else:
        ax.set_title(f'{key}')
    ax.set_xlabel('must be change')
    ax.set_ylabel('number')

    # show hist
    if arg < 8:
        plt.savefig(f'resultsHist/{key}-{arg}.jpg')  #save as jpeg
    else:
        plt.savefig(f'resultsHist/{key}.jpg')  #save as jpeg
    #plt.show()

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
        hist(dnames, 'PCB_BAREMODULE_POSITION_TOP_RIGHT', int(args.TR))
    elif args.BL:
        hist(dnames, 'PCB_BAREMODULE_POSITION_BOTTOM_LEFT', int(args.BL))
    elif args.aveThick:
        hist(dnames, 'AVERAGE_THICKNESS', int(args.aveThick))
    elif args.stdThick:
        hist(dnames, 'STD_DEVIATION_THICKNESS', int(args.stdThick))
    elif args.angle:
        hist(dnames, 'ANGLE_PCB_BM')
    elif args.pickup:
        hist(dnames, 'THICKNESS_VARIATION_PICKUP_AREA')
    elif args.power:
        hist(dnames, 'THICKNESS_INCLUDING_POWER_CONNECTOR')
    elif args.HVcapa:
        hist(dnames, 'HV_CAPACITOR_THICKNESS')
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

