#!/usr/bin/env python3
import os
import json
import time
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import datapath

# get key extract by values
def getNGSN(dic, threshold):
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
def hist(dnames, key, require, binrange, minmax=None, unit=''):
    dataDict = {}
    for dn in dnames:
        results = LoadData(dn)[0]
        sn = LoadData(dn)[1]
        if len(results)>0:
            dataDict[sn]=results[key]

    # data summary
    # save as dataframe
    df = requiredNGSN(key, dataDict, require[0], require[1])
  
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    ax.axvspan(require[0], require[1], color='yellow', alpha=0.5)

    # set histgram range
    if minmax:
        bins = np.arange(minmax[0], minmax[1], binrange)
    else:
        nonZeroValues = [value for value in dataDict.values() if value != 0]
        bins = np.arange(np.nanmin(nonZeroValues),
                         np.nanmax(nonZeroValues), binrange)
        #bins = np.arange(np.amin(list(dataDict.values())),
        #                 np.amax(list(dataDict.values())), binrange)

    # fill thickness list
    n = ax.hist(dataDict.values(), bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # show text of required area
    ax.text(require[0]-2*binrange, np.amax(n[0]), f'{require[0]}',
            color='#ff5d00',size=14)
    ax.text(require[1]-5*binrange, np.amax(n[0]), f'{require[1]}',
            color='#ff5d00',size=14)

    # set hist style
    plt.tick_params(labelsize=18)
    ax.set_title(f'{key}',fontsize=20)
    ax.set_xlabel(f'{unit}',fontsize=18,loc='right') 
    ax.set_ylabel(f'events/{binrange}{unit}',fontsize=18,loc='top')

    # show hist
    plt.savefig(f'resultsHist/pcb_population_{key}.jpg')  #save as jpeg
    print(f'save as resultsHist/pcb_population_{key}.jpg')
    plt.show()

    return df

def run(dnames, args):
    if args.X:
        hist(dnames, 'X_DIMENSION', [39.5, 39.7], 0.005, 'mm')
    elif args.Y:
        hist(dnames, 'Y_DIMENSION', [40.3, 40.5], 0.005, 'mm')
    elif args.thick:
        hist(dnames, 'AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS',
             [0.2, 0.25], 0.001, 'mm')
    elif args.dmt:
        hist(dnames, 'DIAMETER_DOWEL_HOLE_A',[3.0,3.1], 0.005, 'mm')
    elif args.width:
        hist(dnames, 'WIDTH_DOWEL_SLOT_B',[3.0,3.1], 0.005, 'mm')
    elif args.power:
        hist(dnames, 'AVERAGE_THICKNESS_POWER_CONNECTOR',
             [1.521, 1.761], 0.002, 'mm')
    elif args.HVcapa:
        hist(dnames, 'HV_CAPACITOR_THICKNESS', [1.701, 2.111], 0.004, 'mm')
    else:
        print('Error: No such Command. type option -h or --help')  
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp

    # make parser

    parser = argparse.ArgumentParser()

    # add argument
    parser.add_argument('-X', help='X_DIMENSION',action='store_true')
    parser.add_argument('-Y', help='Y_DIMENSION',action='store_true')
    parser.add_argument('--thick', help='AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS',action='store_true')
    parser.add_argument('--dmt', help='DIAMETER_DOWEL_HOLE_A', action='store_true')
    parser.add_argument('--width', help='WIDTH_DOWEL_SLOT_B', action='store_true')
    parser.add_argument('--power', help='AVERAGE_THICKNESS_POWER_CONNECTOR',
                        action='store_true')
    parser.add_argument('--HVcapa', help='HV_CAPACITOR_THICKNESS',
                        action='store_true')
    
    args = parser.parse_args()  # analyze arguments
    
    # assign read file path 
    dnames = datapath.getFilelistPCB('PCB_POPULATION')
    # PCB_POPULATION
    # PCB_RECEPTION
    # PCB_RECEPTION_MODULE_SITE
    
    print(f'counts of module : {len(dnames)}')

    # run main
    run(dnames,args)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
