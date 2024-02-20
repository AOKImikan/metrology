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
import glob

# get key extract by values
def getNGSN(dic, threshold):
    mean = np.mean(list(dic.values()))
    keys = [k for k,v in dic.items() if abs(v-mean) > threshold]
    if keys:
        return keys
    else:
        return None

def requiredNGSN(key, dic, reqmin, reqmax):
    #print(key,dic)
    std = np.std(list(dic.values()))  # get data value std deviation
    mean = np.mean(list(dic.values()))  # get data value mean
    minimum = np.amin(list(dic.values()))  # get data value min
    maximum = np.amax(list(dic.values()))  # get data value max
    quantity = len(dic)
    
    ngnumber = 0
    nglist = {}
    for k,v in dic.items():
        if v < reqmin or v > reqmax:
            nglist[k] = v
            ngnumber += 1
    
    values = [quantity, minimum, maximum, mean, std, reqmin, reqmax, ngnumber/len(dic)]
    rows = ['Qty','min', 'max', 'mean', 'std', 'requirement min', 'requirement max', 'NG ratio']
    summary = pd.DataFrame(values, index=rows, columns=[key])
    ngSN = pd.DataFrame(nglist.keys(), columns=[key])
    ngSN = pd.concat([ngSN,pd.DataFrame(nglist.values())],axis=1)
   
    return summary, ngSN

# db.json -> results and somponent serial number
def LoadData(dn):
    #print(dn)
    appdata = None
    results = {}
    sn = 'serial number'
    if os.path.exists(dn):
        path0 = f'{dn}/db_fmarkUpdate.json'
        path1 = f'{dn}/db_v2.json'
        path2 = f'{dn}/db.json'
        # if os.path.exists(path0):
        #     with open(path0, 'rb') as fin:
        #         appdata = json.load(fin)
        #         results = appdata['results']
        #         sn = appdata['component']
        if os.path.exists(path1):
            with open(path1, 'rb') as fin:
                appdata = json.load(fin)
                results = appdata['results']
                sn = appdata['component']
        elif os.path.exists(path2):
            with open(path2, 'rb') as fin:
                appdata = json.load(fin)
                results = appdata['results']
                sn = appdata['component']

    return results, sn

# make hist
def hist(dnames, key, require, binrange, unit, arg = 8):
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

    # data summary
    # save as dataframe
    print(len(dataDict))
    ngSN = requiredNGSN(key, dataDict, require[0], require[1])
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    ax.axvspan(require[0], require[1], color='yellow', alpha=0.5)

    # exclude 0
    ex0data = [v for v in dataDict.values() if v !=0]
    bins = np.arange(np.amin(ex0data), np.amax(ex0data), binrange)
    n = ax.hist(ex0data, bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')
    
    # fill thickness list
    # bins = np.arange(np.amin(list(dataDict.values())),
    #                  np.amax(list(dataDict.values())), binrange)
    # n = ax.hist(dataDict.values(), bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # show text of required area
    ax.text(require[0]-2*binrange, np.amax(n[0]),f'{require[0]}',
            color='#ff5d00',size=14)
    ax.text(require[1]-5*binrange, np.amax(n[0]),f'{require[1]}',
            color='#ff5d00',size=14)
  
    # set hist style
    plt.tick_params(labelsize=18)
    if arg < 8:
        ax.set_title(f'{key}_{arg}',fontsize=20)
        ax.set_xlabel(f'{unit}',fontsize=18, loc='right')
    else:
        ax.set_title(f'{key}',fontsize=20)
        ax.set_xlabel(f'{unit}',fontsize=18, loc='right') 
    ax.set_ylabel(f'events/{binrange}{unit}',fontsize=18, loc='top')

    # show hist
    if arg < 8:
        plt.savefig(f'resultsHist/module_asem_{key}_{arg}.jpg')  #save as jpeg
        print(f'save as resultsHist/module_assem_{key}_{arg}.jpg')
    else:
        plt.savefig(f'resultsHist/module_assem_{key}.jpg')  #save as jpeg
        print(f'save as resultsHist/module_assem_{key}.jpg')
    plt.show()

    return ngSN
    
def run(dnames, args):
    
    if args.TR:
        if args.TR == '0':
            hist(dnames, 'PCB_BAREMODULE_POSITION_TOP_RIGHT',
                 [2.112, 2.312], 0.004, 'mm', 0)
        if args.TR == '1':
            hist(dnames, 'PCB_BAREMODULE_POSITION_TOP_RIGHT',
                 [0.65, 0.85],0.004, 'mm', 1)
    elif args.BL:
        if args.BL == '0':
            hist(dnames, 'PCB_BAREMODULE_POSITION_BOTTOM_LEFT',
                 [2.112, 2.312], 0.004, 'mm', 0)
        if args.BL == '1':
            hist(dnames, 'PCB_BAREMODULE_POSITION_BOTTOM_LEFT',
                 [0.65, 0.85], 0.004, 'mm', 1)
    elif args.aveThick:
        hist(dnames, 'AVERAGE_THICKNESS',
             [0.52,0.62], 0.002, 'mm', int(args.aveThick))
    elif args.stdThick:
        hist(dnames, 'STD_DEVIATION_THICKNESS',
             [0, 0.01], 0.001, '', int(args.stdThick))
    elif args.angle:
        hist(dnames, 'ANGLE_PCB_BM',
             [0.0, 0.01], 0.001,  '')
    elif args.pickup:
        hist(dnames, 'THICKNESS_VARIATION_PICKUP_AREA',
             [0, 0.02], 0.002, '')
    elif args.power:
        hist(dnames, 'THICKNESS_INCLUDING_POWER_CONNECTOR',
             [1.891, 2.131], 0.01, 'mm')
    elif args.HVcapa:
        hist(dnames, 'HV_CAPACITOR_THICKNESS',
             [2.071, 2.481], 0.01, 'mm')
    else:
        print('Error: No such Command. type option -h or --help')  

def getFilelist():
    dnames = []  # define path list
    #files = glob.glob("/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM*")
    files = glob.glob("/nfs/space3/aoki/Metrology/HR/FmarkUpdate_MODULE/20UPGM*")
    for fn in files:
        sn = fn.split('/')[7]        
        filepath = fn + '/MODULE_ASSEMBLY'  # stage
        if os.path.exists(filepath):  
            scanNumList = glob.glob(filepath+'/*')
            scanNumList.sort()
            count = len(scanNumList)
            dnames.append(scanNumList[count-1])
    return dnames
    
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
    dnames = datapath.getFilelistModule()
    #dnames = getFilelist()
           
    print(f'counts of module : {len(dnames)}')

    # run main
    run(dnames,args)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
