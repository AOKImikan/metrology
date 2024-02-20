#!/usr/bin/env python3
import os
import pickle
import time
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datapath
from pmm.model import *
from pmm.reader import *
from pmm.design import *
from pmm.prec import *
from pmm.workflow import *
from pmm.tools import *

#data.pickle -> ScanProcessor
def LoadData(dn,spname):
    appdata = None
    sp = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
            #print(appdata.scanNames())
            sp = appdata.getScanProcessor(spname)
    return sp
#get serial number from directory path
def extractSN(dn):
    words = dn.split('/')
    sn = words[8]
    #print('SN = ',sn)
    return sn

#get QC stage from directory path
def extractQcStage(dn):
    words = dn.split('/')
    qcstage = words[9]
    #print("qcStage=",qcstage)
    return qcstage

#get Metrology number from directory path
def extractMetrologyNum(dn):
    words = dn.split('/')
    num = words[10]
    #print("Number=",num)
    return num

def indexDF(data):
    
    return df

def testDict(module):
    if module == "Flex":
        kind_of_module = ["Flex"]
        kind_of_test = ["Size", "Height"]
        d = {"analysisLog":{"qcstage":{None:None},
                            "analysisnum":{None:None}},
             "Size":{
                 "FlexL":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction","d"]
                 },
                 "FlexR":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction","d"]
                 },
                 "FlexT":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction","d"]
                 },
                 "FlexB":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction","d"]
                 },
                 "HoleTL":{
                     "point":["center"],
                     "hole":["r","std"]
                     },
                 "SlotBR":{
                     "point":["center"],
                     "hole":["r","l"]
                 }
             },
             "Height":{
                 "Jig":{
                     "plane":["point","direction"]},
                 "pickupPoint":{
                     "points":["p1","p2","p3","p4"]},
                 "Connector":{
                     "points":["p1","p2","p3","p4"]},
                 "Capacitor":{
                     "points":["p1","p2","p3","p4"]}
             }
        }   
    elif module == "Module":
        kind_of_module = ["Asic", "Sensor", "Flex"]

    return d

def indexDF(module):
    d = testDict(module)
    data = []
    def unpack(d, path=None):
        if path is None:
            path = []

        for k, v in d.items():
            current_path = path + [k]
            if isinstance(v, dict):
                unpack(v, current_path)
            elif isinstance(v, list):
                for item in v:
                    data.append(current_path + [item])
            else:
                data.append(current_path + [v])

    unpack(d)
    df = pd.DataFrame(
        data, columns=['Level{}'.format(i+1) for i in range(len(data[0]))])
    return df

def getData(k1,k2,k3,v1,v2,v3,PAsize):
    if k3 == 'points': #[[x1, y1],[x2,y2],...]
        print('points',v3)
        i = 0
        while i < len(v3):
            name = k2+f'_{i}_point'
            print(i, PAsize.outData[name].position)
            i += 1
    elif k3 == 'point': # [x,y]
        print('point',v3)
        namex = k2 + '_x'
        namey = k2 + '_y'
        x = PAsize.outData[namex].get('value')
        y = PAsize.outData[namey].get('value')
        center = [x,y]
        print(center)
    elif k3 == 'line': #[point,direction,d]
        print('line', v3)
        name = k2 + '_line'
        print('dirrection',PAsize.outData[name].direction())
        # print('par',PAsize.outData[name].p[1])
        # print('par',PAsize.outData[name].p[2])
        print('center',PAsize.outData[name].center())
    elif k3 == 'hole': #['r','l', 'std']
        print('hole',v3)
        i = 0
        while i < len(v3):
            if v3[i] == 'r':
                name = k2 + '_r'
                print(name, PAsize.outData[name].get('value'))
            if v3[i] == 'l':
                name = k2 + '_l'
                print(name, PAsize.outData[name].get('value'))
            i += 1
    elif k3 == 'plane': #
        print('plane', v3)
    else:
        print('more',k3)
    
def pickupAnalysisDataFlex(dn):
    qcstage = extractQcStage(dn)
    number = extractMetrologyNum(dn)
        
    # open pickle
    spSize =LoadData(dn,'ITkPixV1xFlex.Size')
    spHeight =LoadData(dn,'ITkPixV1xFlex.Height')
    if spSize:
        PAsize = spSize.analysisList[0]
        SAsize = spSize.analysisList[1]
    else:
        return None
    if spHeight:
        PAhigh = spHeight.analysisList[0]
        
    data = ['POPULATION','001',
            1,2,3,4,'p','d','d',
            1,2,3,4,'p','d','d',
            1,2,3,4,'p','d','d',
            1,2,3,4,'p','d','d',
            10,3,0.1,
            10,3,0.1,
            'p','d',
            1,2,3,4,
            1,2,3,4,
            1,2,3,4
    ]
    d = testDict('Flex')
    for k1, v1 in d.items():
        for k2, v2 in v1.items():
            for k3, v3 in v2.items():
                if k1 == 'Size':
                    print(k1,k2,k3)
                    getData(k1,k2,k3,v1,v2,v3,PAsize)
                #elif k1 == 'Height':
    # pattern analysis result
    for k,v in PAsize.outData.items():
        print(k,v)
    for k,v in PAhigh.inData.items():
        print(k,v)
        # elif '_alpha' in k:
        #     print(v.get('value'))
               
    # for k,v in sizeAnalysis.outData.items():
    #     #print(k,v)
    #     if 'line' in k:
    #         commonAppend(commonslist, tags, commons, tag)
    #         valuelist.append(v.p[0])
    #         analyTags.append(k)
    #     else:
    #         commonAppend(commonslist, tags, commons, tag)
    #         valuelist.append(v.get('value'))
    #         analyTags.append(k)
            
    # # make dataframe with serial number
    # df=pd.DataFrame({'serial_number':snlist})

    # # add data to dataframe
    # df['qc_stage']=qclist
    # df['scan_num']=numlist
    # df['scan_tags']=tags
    # df['analysis_tags']=analyTags
    # df['analysis_value'] = valuelist
   
    return data

def run(dnames):
    # define the dataframe
    df_index = indexDF("Flex")
    mindex = pd.MultiIndex.from_frame(df_index)
    df = pd.DataFrame(index=mindex)

    i = 0
    #repeat for each serial number
    for dn in dnames:
        i += 1
        # convert from pickle to dataframe
        datalist = pickupAnalysisDataFlex(dn)        
        sn = extractSN(dn)

        df[sn] =datalist
        print(df)
        # concat each serial numbers
        #analyDFs = pd.concat([analyDFs,analydf],ignore_index=True)
        if i > 0:
            return
   
    # save the created data
    #analyDFs.to_pickle("data/PCB_AnalysisData.pkl")
    #analyDFs.to_csv("data/PCB_AnalysisData.csv")
  
if __name__ == '__main__':
    t1 = time.time()

    dnames = datapath.getFilelistPCB('PCB_POPULATION')
    
    run(dnames)
    print(f'counts of module : {len(dnames)}')
    
    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
