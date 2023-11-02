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

# make array
def array(dnames, key, require, binrange, unit):
    dataDict = {}
    # define dataframe / column = key
    #df1 = pd.DataFrame(columns=['serial_num',key])
    
    for dn in dnames:
        results = LoadData(dn)[0]  # dictionary
        sn = LoadData(dn)[1]  # string
        if len(results)>0:  # results is exist?
            dataDict[sn]=results[key]
            
    df1=pd.DataFrame.from_dict(dataDict,orient="index", columns=[key])

    # data summary
    # save as dataframe
    df = requiredNGSN(key, dataDict, require[0], require[1])  
    
    return df1

def run(dnames):
    
    df = array(dnames, 'SENSOR_X', [39.50, 39.55], 0.001, 'mm')
    
    df = df.merge(array(dnames, 'SENSOR_Y',  [41.10, 41.15], 0.001, 'mm'),
             left_index=True,right_index=True,how='outer')    

    df = df.merge(array(dnames, 'FECHIPS_X',
                         [42.187, 42.257], 0.001, 'mm'),
                  left_index=True,right_index=True,how='outer')

    df = df.merge(array(dnames, 'FECHIPS_Y',
                        [40.255, 40.322], 0.001, 'mm'),
                  left_index=True,right_index=True,how='outer')
    
    df= df.merge(array(dnames, 'FECHIP_THICKNESS',
                       [131, 181], 1, 'um'),
                 left_index=True,right_index=True,how='outer')
    
    df = df.merge(array(dnames, 'FECHIP_THICKNESS_STD_DEVIATION',
                        [0, 1], 0.001, ''),
                  left_index=True,right_index=True,how='outer')

    df = df.merge(array(dnames, 'BAREMODULE_THICKNESS',
                         [294, 344], 1, 'um'),
                  left_index=True,right_index=True,how='outer')
    
    df = df.merge(array(dnames, 'BAREMODULE_THICKNESS_STD_DEVIATION',
                        [0,1], 0.001, ''),
                  left_index=True,right_index=True,how='outer')

    df = df.merge(array(dnames, 'SENSOR_THICKNESS',
                        [137, 187], 1, 'um'),
                  left_index=True,right_index=True,how='outer')
    
    df = df.merge(array(dnames, 'SENSOR_THICKNESS_STD_DEVIATION',
                        [0,1], 0.001, ''),
                  left_index=True,right_index=True,how='outer')
       

    df = df.sort_index(axis='index')
    df.to_csv("analysisJson/BAREMODULE_all_results.csv")
    df.describe().to_csv("analysisJson/BAREMODULE_all_results_summary.csv")
    print(df.describe())
    print(df)
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    
    # assign read file path 
    dnames = data_baremodule.getFilelist()
    
    print(f'counts of module : {len(dnames)}')

    # run main
    run(dnames)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
