#!/usr/bin/env python3
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ReadJson_module
import datapath
import ReadJson_module

# module db.json analysis 
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    resultsKeyList = [
        ['PCB_BAREMODULE_POSITION_TOP_RIGHT', [2.112, 2.312], 0.004, 'mm',0],
        ['PCB_BAREMODULE_POSITION_TOP_RIGHT', [0.65, 0.85],0.004, 'mm', 1],
        ['PCB_BAREMODULE_POSITION_BOTTOM_LEFT', [2.112, 2.312], 0.004, 'mm', 0],
        ['PCB_BAREMODULE_POSITION_BOTTOM_LEFT', [0.65, 0.85], 0.004, 'mm', 1],
        ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 0],
        ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 1],
        ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 2],
        ['AVERAGE_THICKNESS', [0.52,0.62], 0.002, 'mm', 3],
        ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 0],
        ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 1],
        ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 2],
        ['STD_DEVIATION_THICKNESS', [0, 0.01], 0.001, '', 3],
        ['ANGLE_PCB_BM', [0.0, 0.01], 0.001, '', 8],  # angle all 0 ?
        ['THICKNESS_VARIATION_PICKUP_AREA', [0, 0.05], 0.002, '', 8],
        ['THICKNESS_INCLUDING_POWER_CONNECTOR', [1.891, 2.131], 0.01, 'mm', 8],
        ['HV_CAPACITOR_THICKNESS', [2.071, 2.481], 0.01, 'mm', 8]      
    ]
    # assign read file path
    dnames = datapath.getFilelistModule()
    #dnames = ReadJson_module.getFilelist()

    analyDF = pd.DataFrame()
    ngSNDF = pd.DataFrame()
    
    for k in resultsKeyList:
        ngSN = ReadJson_module.hist(dnames, k[0], k[1], k[2], k[3],k[4])
        analyDF = pd.concat([analyDF, ngSN[0]], axis=1)
        ngSNDF = pd.concat([ngSNDF, ngSN[1]], axis=1, ignore_index=0)
        
    #save the created data
    analyDF.to_pickle("analysisJson/module_json_analysis.pkl")
    analyDF.to_csv("analysisJson/module_json_analysis.csv")
    ngSNDF.to_pickle("analysisJson/module_json_ngSNs.pkl")
    ngSNDF.to_csv("analysisJson/module_json_ngSNs.csv")
    print('analysis data save as analysisJson/module_json_analysis')
    #print(ngSNDF)
    
    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
