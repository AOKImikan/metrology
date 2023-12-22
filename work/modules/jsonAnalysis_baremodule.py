#!/usr/bin/env python3
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ReadJson_BareModule
import datapath

# bare module db.json analysis 
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    resultsKeyList = [
        ['SENSOR_X',[39.50, 39.55], 0.001, 'mm'],
        ['SENSOR_Y',[41.10, 41.15], 0.001, 'mm'],
        ['FECHIPS_X',[42.187, 42.257], 0.001, 'mm'],
        ['FECHIPS_Y',[40.255, 40.322], 0.001, 'mm'],
        ['FECHIP_THICKNESS',[131, 181], 1, 'um'],
        ['BAREMODULE_THICKNESS', [294, 344], 1, 'um'],
        ['SENSOR_THICKNESS',[137, 187], 1, 'um']
    ]
    # assign read file path
    dnames = datapath.getFilelistBare()

    analyDF = pd.DataFrame()
    ngSNDF = pd.DataFrame()
    
    for k in resultsKeyList:
        ngSN = ReadJson_BareModule.hist(dnames, k[0], k[1], k[2], k[3])
        analyDF = pd.concat([analyDF, ngSN[0]], axis=1)
        ngSNDF = pd.concat([ngSNDF, ngSN[1]], axis=1, ignore_index=0)

    # save created data
    analyDF.to_pickle("analysisJson/baremodule_json_analysis.pkl")
    analyDF.to_csv("analysisJson/baremodule_json_analysis.csv")
    ngSNDF.to_pickle("analysisJson/baremodule_json_ngSNs.pkl")
    ngSNDF.to_csv("analysisJson/baremodule_json_ngSNs.csv")
    print('save as analysisJson/baremodule_json')
    #print(ngSNDF)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
