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
    results = {}
    if os.path.exists(f'{dn}/db.json'):
        with open(f'{dn}/db.json', 'rb') as fin:
            appdata = json.load(fin)
        results = appdata['results']
        passed = appdata['passed']
    return results

def hist(dnames, key, arg = 'unspecified'):
    mergedlist = []
    if arg is 'unspecified':    # multiple values and individual
        for dn in dnames:
            results = LoadData(dn)
            if len(results)>0:
                mergedlist.append(results[key])
    else:
        for dn in dnames:
            results = LoadData(dn)
            if len(results)>0:
                key2 = f'{key}_{arg}'
                mergedlist.append(results[key2])
                
                
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # fill thickness list 
    ax.hist(mergedlist, bins=50)
    
    # set hist style
    if arg is 'unspecified':
        ax.set_title(f'{key}')
        ax.set_xlabel(f'{key}')
    else:
        ax.set_title(f'{key}-{arg}')
        ax.set_xlabel(f'{key}-{arg}')
    ax.set_ylabel('number')

    # show hist
    if arg is 'unspecified':
        plt.savefig(f'resultsHist/{key}.jpg')  #save as jpeg
        print(f'save as resultsHist/{key}.jpg')
    else:
        plt.savefig(f'resultsHist/{key}-{arg}.jpg')  #save as jpeg
        print(f'save as resultsHist/{key}-{arg}.jpg')
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
        if args.std == 'sensor':
            hist(dnames, 'SENSOR_THICKNESS_STD_DEVIATION')
        if args.std == 'fe':
            hist(dnames, 'FECHIP_THICKNESS_STD_DEVIATION')
        if args.std == 'bare':
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
    parser.add_argument('--std', help='THICKNESS_STD_DEVIATION',choices=['fe','bare','sensor'])
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

