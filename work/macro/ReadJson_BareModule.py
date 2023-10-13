#!/usr/bin/env python3
import os
import json
import time
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import data_baremodule

# get key extract by values
def stdNGSN(dic, threshold):
    mean = np.mean(list(dic.values()))
    keys = [k for k,v in dic.items() if abs(v-mean) > threshold]
    if keys:
        return keys
    else:
        return None

def requiredNGSN(key, dic, reqmin, reqmax):
    std = np.std(list(dic.values()))  # get data value std deviation
    mean = np.mean(list(dic.values()))  # get data value mean
    minimum = np.amin(list(dic.values()))  # get data value min
    maximum = np.amax(list(dic.values()))  # get data value max
    quantity = len(dic)

    nglist = {}
    ngnumber = 0
    for k,v in dic.items():
        if v < reqmin or v > reqmax:
            nglist[k] = v
            ngnumber += 1

    values = [quantity, minimum, maximum, mean, std, reqmin, reqmax, ngnumber/len(dic)]
    rows = ['Qty', 'min', 'max', 'mean', 'std', 'requirement min', 'requirement max', 'NG ratio']
    summary = pd.DataFrame(values, index=rows, columns=[key])
    ngSN = pd.DataFrame(nglist.keys(), columns=[key])
    ngSN = pd.concat([ngSN,pd.DataFrame(nglist.values())],axis=1)
    
    return summary, ngSN

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

def hist(dnames, key, require, binrange, unit, arg = 'unspecified'):
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

    # data summary
    # save as dataframe
    ngSN = requiredNGSN(key, dataDict, require[0], require[1])
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    ax.axvspan(require[0], require[1],color='yellow',alpha=0.5)
    #ax.axvline(reqire[0],color='black')
    #ax.axvline(reqire[1],color='black')

    # fill thickness list
    bins = np.arange(np.amin(list(dataDict.values())),
                     np.amax(list(dataDict.values())), binrange)
    n = ax.hist(dataDict.values(), bins=bins, alpha=1,
                histtype="stepfilled",edgecolor='black')

    # show text of required area
    ax.text(require[0]-2*binrange, np.amax(n[0]),f'{require[0]}',
            color='#ff5d00',size=14)
    ax.text(require[1]-5*binrange, np.amax(n[0]),f'{require[1]}',
            color='#ff5d00',size=14)
    
    # set hist style
    plt.tick_params(labelsize=18)
    if arg is 'unspecified':
        ax.set_title(f'{key}',fontsize=20)
        ax.set_xlabel(f'{unit}',fontsize=18,loc='right')
    else:
        ax.set_title(f'{key}-{arg}',fontsize=20)
        ax.set_xlabel(f'{unit}',fontsize=18,loc='right')
    ax.set_ylabel(f'events/{binrange}{unit}',fontsize=18,loc='top')

    # show hist
    if arg is 'unspecified':
        plt.savefig(f'resultsHist/bare_{key}.jpg')  #save as jpeg
        print(f'save as resultsHist/bare_{key}.jpg')
    else:
        plt.savefig(f'resultsHist/bare_{key}-{arg}.jpg')  #save as jpeg
        print(f'save as resultsHist/bare_{key}-{arg}.jpg')
    plt.show()

    return ngSN     

def run(dnames, args):
    if args.sensor:
        if args.sensor =='X':
            hist(dnames, 'SENSOR', [39.50, 39.55], 0.001, 'mm',args.sensor)
        if args.sensor =='Y':
            hist(dnames, 'SENSOR', [41.10, 41.15], 0.001, 'mm',args.sensor)
    elif args.fechips:
        if args.fechips == 'X':
            hist(dnames, 'FECHIPS', [42.187, 42.257], 0.001, 'mm',args.fechips)
        if args.fechips == 'Y':
            hist(dnames, 'FECHIPS', [40.255, 40.322], 0.001, 'mm',args.fechips)
    elif args.fe:
        hist(dnames, 'FECHIP_THICKNESS', [131, 181], 1, 'um')
    elif args.bare:
        hist(dnames, 'BAREMODULE_THICKNESS', [294, 344], 1, 'um')
    elif args.sen:
        hist(dnames, 'SENSOR_THICKNESS', [137, 187], 1, 'um')
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

