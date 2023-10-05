#!/usr/bin/env python3
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ReadJson_PCB
from myModules import data_pcb

# pcb db.json analysis 
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    resultsKeyList = [
        ['X_DIMENSION', [39.5, 39.6], 0.005, 'mm'],
        ['Y_DIMENSION', [40.2, 40.4], 0.005, 'mm'],
        ['AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS',[0.15, 0.25], 0.001, 'mm'],
        ['AVERAGE_THICKNESS_POWER_CONNECTOR', [1.521, 1.761], 0.002, 'mm'],
        ['HV_CAPACITOR_THICKNESS', [1.701, 2.111], 0.004, 'mm'],
        ['DIAMETER_DOWEL_HOLE_A',[3.0,3.1], 0.005, 'mm'],
        ['WIDTH_DOWEL_SLOT_B',[3.0,3.1], 0.005, 'mm']
    ]
    # assign read file path
    dnames = data_pcb.getFilelist('PCB_POPULATION')
    # PCB_POPULATION
    # PCB_RECEPTION
    # PCB_RECEPTION_MODULE_SITE

    analyDF = pd.DataFrame()
    ngSNDF = pd.DataFrame()
    
    for k in resultsKeyList:
        ngSN = ReadJson_PCB.hist(dnames, k[0], k[1], k[2], k[3])
        analyDF = pd.concat([analyDF, ngSN[0]], axis=1)
        ngSNDF = pd.concat([ngSNDF, ngSN[1]], axis=1, ignore_index=0)
        
    #save the created data
    analyDF.to_pickle("analysisJson/pcb_json_analysis.pkl")
    analyDF.to_csv("analysisJson/pcb_json_analysis.csv")
    ngSNDF.to_pickle("analysisJson/pcb_json_ngSNs.pkl")
    ngSNDF.to_csv("analysisJson/pcb_json_ngSNs.csv")
    print('analysis data save as analysisJson/pcb_json')
    #print(ngSNDF)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
