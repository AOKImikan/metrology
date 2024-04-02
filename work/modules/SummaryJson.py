#!/usr/bin/env python3
import os
import json
import time
#import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import datapath
import makeImages

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()

    # add argument
    parser.add_argument('module',
                        help='component type [PCB, BAREMODULE, MODULE]')
    parser.add_argument('-k','--key',
                        help='specify result key',action='store_true')
    parser.add_argument('-a',
                        help='all result key analysis',action='store_true')
    parser.add_argument('--hist',
                        help='draw histgram',action='store_true')
    
    parser.add_argument('-X', help='X_DIMENSION',action='store_true')
    parser.add_argument('-Y', help='Y_DIMENSION',action='store_true')
    parser.add_argument('--thick', help='AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS',action='store_true')
    parser.add_argument('--dmt', help='DIAMETER_DOWEL_HOLE_A', action='store_true')
    parser.add_argument('--width', help='WIDTH_DOWEL_SLOT_B', action='store_true')
    parser.add_argument('--power', help='AVERAGE_THICKNESS_POWER_CONNECTOR',
                        action='store_true')
    parser.add_argument('--HVcapa', help='HV_CAPACITOR_THICKNESS',
                        action='store_true')

    # analyze arguments
    args = parser.parse_args()
    return args

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
        results, sn = LoadData(dn)
        if len(results)>0:
            dataDict[sn]=results[key]

    #print(dataDict)
    makeImages.hist(dataDict, require, binrange, minmax, unit, f'PCB_POPULATION_{key}')

    # # data summary
    # # save as dataframe
    # df = requiredNGSN(key, dataDict, require[0], require[1])
  
    # # define matplotlib figure
    # fig = plt.figure(figsize=(8,7))
    # ax = fig.add_subplot(1,1,1)

    # # paint required area
    # ax.axvspan(require[0], require[1], color='yellow', alpha=0.5)

    # # set histgram range
    # if minmax:
    #     bins = np.arange(minmax[0], minmax[1], binrange)
    # else:
    #     nonZeroValues = [value for value in dataDict.values() if value != 0]
    #     bins = np.arange(np.nanmin(nonZeroValues),
    #                      np.nanmax(nonZeroValues), binrange)
    #     #bins = np.arange(np.amin(list(dataDict.values())),
    #     #                 np.amax(list(dataDict.values())), binrange)

    # # fill thickness list
    # n = ax.hist(dataDict.values(), bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # # show text of required area
    # ax.text(require[0]-2*binrange, np.amax(n[0]), f'{require[0]}',
    #         color='#ff5d00',size=14)
    # ax.text(require[1]-5*binrange, np.amax(n[0]), f'{require[1]}',
    #         color='#ff5d00',size=14)

    # # set hist style
    # plt.tick_params(labelsize=18)
    # ax.set_title(f'{key}',fontsize=20)
    # ax.set_xlabel(f'{unit}',fontsize=18,loc='right') 
    # ax.set_ylabel(f'events/{binrange}{unit}',fontsize=18,loc='top')

    # # show hist
    # plt.savefig(f'resultsHist/pcb_population_{key}.jpg')  #save as jpeg
    # print(f'save as resultsHist/pcb_population_{key}.jpg')
    # plt.show()

    # return df

def run(dnames, args):
    if args.a:
        if args.module=='PCB':
             # key, require, binrange, minmax=None, unit=''
            keyList = [
                ['X_DIMENSION', [39.5, 39.7], 0.005, [39.45,39.85], 'mm'],
                ['Y_DIMENSION', [40.3, 40.5], 0.005, [40.30,40.70] ,'mm'],
                ['AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS',[0.15, 0.25], 0.004, [0.15,0.25] ,'mm'],
                ['STD_DEVIATION_THICKNESS_FECHIP_PICKUP_AREAS',[0,0.05], 0.001, [0,0.1],''],
                ['HV_CAPACITOR_THICKNESS', [1.701, 2.111], 0.004, [1.7,2.115], 'mm'],
                ['AVERAGE_THICKNESS_POWER_CONNECTOR', [1.521, 1.761], 0.004, [1.5,1.761], 'mm'],
                ['DIAMETER_DOWEL_HOLE_A',[3.0,3.1], 0.005, [2.9,3.2], 'mm'],
                ['WIDTH_DOWEL_SLOT_B',[3.0,3.1], 0.005, [2.9,3.2], 'mm'],
            ]
        elif args.module=='BAREMODULE':
            keyList = [
                ['SENSOR_X',[39.50, 39.55], 0.001, [39,40], 'mm'],
                ['SENSOR_Y',[41.10, 41.15], 0.001, [40.5,41.5], 'mm'],
                ['FECHIPS_X',[42.187, 42.257], 0.001, [42,43], 'mm'],
                ['FECHIPS_Y',[40.255, 40.322], 0.001, [40,41], 'mm'],
                ['FECHIP_THICKNESS',[131, 181], 1, [120,200], 'um'],
                ['FECHIP_THICKNESS_STD_DEVIATION',[0, 0.05], 0.001, [0,0.1], ''],
                ['BAREMODULE_THICKNESS', [294, 344], 1, [280,360], 'um'],
                ['BAREMODULE_THICKNESS_STD_DEVIATION',[0, 0.05], 0.001, [0,0.1], ''],
                ['SENSOR_THICKNESS',[137, 187], 1, [120,200], 'um'],
                ['SENSOR_THICKNESS_STD_DEVIATION',[0, 0.05], 0.001, [0,0.1], ''],
            ]
        elif args.module=='MODULE':
            keyList = [
                # ['PCB_BAREMODULE_POSITION_TOP_RIGHT', [2.112, 2.312], 0.004, 'mm',0],
                # ['PCB_BAREMODULE_POSITION_TOP_RIGHT', [0.65, 0.85],0.004, 'mm', 1],
                # ['PCB_BAREMODULE_POSITION_BOTTOM_LEFT', [2.112, 2.312], 0.004, 'mm', 0],
                # ['PCB_BAREMODULE_POSITION_BOTTOM_LEFT', [0.65, 0.85], 0.004, 'mm', 1],
                # ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 0],
                # ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 1],
                # ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 2],
                # ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 3],
                # ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 0],
                # ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 1],
                # ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 2],
                # ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 3],
                # ['ANGLE_PCB_BM', [0.0, 0.01], 0.001, None, ''],  # angle all 0 ?
                ['THICKNESS_VARIATION_PICKUP_AREA', [0, 0.05], 0.002, None, ''],
                ['THICKNESS_INCLUDING_POWER_CONNECTOR', [1.891, 2.131], 0.01, None, 'mm'],
                ['HV_CAPACITOR_THICKNESS', [2.071, 2.481], 0.01, None,'mm']      
            ]
        for k in keyList:
            print(k[0])
            hist(dnames, k[0], k[1], k[2], k[3], k[4])

    elif args.key:
        hist(dnames, args.key, [0.0, 0.4], 0.02)

    else:
        print('Error: No such Command. type option -h or --help')  
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    args = parseArg()
    
    # assign read file path 
    if args.module == 'PCB':
        dnames = datapath.getFilelistPCB('PCB_POPULATION')
        # PCB_POPULATION
        # PCB_RECEPTION
        # PCB_RECEPTION_MODULE_SITE
    elif args.module=='BAREMODULE':
        dnames = datapath.getFilelistBare() 
    elif args.module=='MODULE':
        dnames = datapath.getFilelistModule()
   
    
    print(f'counts of module : {len(dnames)}')

    # run main
    run(dnames,args)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
