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

def testDict(module):
    if module == "Flex":
        kind_of_module = ["Flex"]
        kind_of_test = ["Size", "Height"]
        d = {"analysisLog":{"qcstage":{None:None},
                            "analysisnum":{None:None}},
             "Size":{
                 "FlexL":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction"]
                 },
                 "FlexR":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction"]
                 },
                 "FlexT":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction"]
                 },
                 "FlexB":{
                     "points":["0","1", "2", "3"],
                     "line":["point", "direction"]
                 },
                 "HoleTL":{
                     "point":["center"],
                     "hole":["r","x","y"]
                     },
                 "SlotBR":{
                     "point":["center"],
                     "hole":["r", "x", "y",  "l", "alpha"],
                 }
             },
             # "Height":{
             #     "Jig":{
             #         "plane":["point","direction"]},
             #     "pickupPoint":{
             #         "points":["p1","p2","p3","p4"]},
             #     "Connector":{
             #         "points":["p1","p2","p3","p4"]},
             #     "Capacitor":{
             #         "points":["p1","p2","p3","p4"]}
             # },
             "Height":{
                 "Jig":{
                     "plane":["point","direction"]},
                 "PickupZ":{
                     "averaged":''},
                 "ConnectorZ":{
                     "averaged":''},
                 "HVCapacitorZ":{
                     "averaged":''}
             },
             "results":{
                 "Flex":{
                     "X":"dimension",
                     "Y":"dimension",
                     "L":"Line",
                     "R":"Line",
                     "T":"Line",
                     "B":"Line",},
                 "HoleTL":{
                     "circle":"diameter"},
                 "SlotBR":{
                     "bigCircle":"width"}
                 # "Asic":{
                 #     "X":"dimension"},
                 # "Sensor":{
                 #     "Y":"dimension"}
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

def getData(k1,k2,k3,v1,v2,v3,SP):
    if k3 == 'points': #[[x1, y1],[x2,y2],...]
        i = 0
        pList = []
        while i < len(v3):
            name = k2+f'_{i}_point'
            p = SP.outData[name].position
            p[0] = round(p[0],3)
            p[1] = round(p[1],3)
            pList.append(p)
            i += 1
        return pList
            
    elif k3 == 'point': # [x,y]
        #print('point',v3)
        namex = k2 + '_x'
        namey = k2 + '_y'
        x = round(SP.outData[namex].get('value'),3)
        y = round(SP.outData[namey].get('value'),3)
        center = [x,y]
        return center
    
    elif k3 == 'line': #[point,direction,d]
        name = k2 + '_line'
        line = SP.outData[name]
        p = line.center()
        p[0] = round(p[0],3)
        p[1] = round(p[1],3)
        direction = line.direction()
        direction[0] = round(direction[0] , 3)
        direction[1] = round(direction[1] , 3)
        # print(dir(line))
        # print(type(line))
        return p, direction
    
    elif k3 == 'hole': #['r','l', 'std']
        #print('hole',v3)
        i = 0
        returnlist = []
        while i < len(v3):
            name = k2 + '_'+ v3[i]
            #print(name, SP.outData[name].get('value'))
            r = SP.outData[name].get('value')
            returnlist.append(round(r,3))
            # if v3[i] == 'r':
            #     name = k2 + '_r'
            #     print(name, SP.outData[name].get('value'))
            #     r = SP.outData[name].get('value')
            # elif v3[i] == 'l':
            #     name = k2 + '_l'
            #     print(name, SP.outData[name].get('value'))
            #     l = SP.outData[name].get('value')
            i += 1
        return returnlist
    
    elif k3 == 'plane': #
        #print('plane', v3)
        return 'point', 'direction'

    elif k3 == 'averaged':
        name = k2
        value = round(SP.outData[name].get('value'),3) 
        return value

    elif k3 == 'X' or k3 == 'Y':
        name = k2 + k3
        dimension = SP.outData[name]
        dimension = dimension.get('value')
        return round(dimension, 3)
    
    elif k3 == 'L' or k3 == 'R' or k3 == 'T' or k3 == 'B':
        name = k2 + k3 +'_line'
        line = SP.outData[name]
        return line
    elif k3 =='circle':
        name1 = k2 +'_diameter'
        r = SP.outData[name1].get('value')
        return round(r,3)
    elif k3 =='bigCircle':
        name1 = k2 +'_width'
        r = SP.outData[name1].get('value')
        return round(r,3)
    
    else:
        #print('more',k3)
        return 0
    
def pickupAnalysisDataFlex(dn):
    qcstage = extractQcStage(dn)
    number = extractMetrologyNum(dn)
    DATA = [qcstage, number]
    # open pickle
    spSize =LoadData(dn,'ITkPixV1xFlex.Size')
    spHeight =LoadData(dn,'ITkPixV1xFlex.Height')
    if spSize:
        PatternAnalysis = spSize.analysisList[0]
        SizeAnalysis = spSize.analysisList[1]
    else:
        return None
    if spHeight:
        HeightAnalysis = spHeight.analysisList[0]
     #    for k,v in HeightAnalysis.outData.items():
    #         print(k,v)
    # print('patternanalysis')
    # for k,v in PatternAnalysis.outData.items():
    #     print(k,v)
    # print('sizeanalysis')
    # for k,v in SizeAnalysis.outData.items():
    #     print(k,v)
  
    data = ['POPULATION','001',
            1,2,3,4,[3,3,3],[1,0],'d',
            1,2,3,4,[3,3,3],[0,1],'d',
            1,2,3,4,['x','y','z'],[1,0,0],'d',
            1,2,3,4,['x','y','z'],['x','y','z'],'d',
            10,3,0.1,
            10,3,0.1,1,
            'p','d',
            1,2,3,4,5,6,7
    ]
    d = testDict('Flex')
    for k1, v1 in d.items():
        for k2, v2 in v1.items():
            for k3, v3 in v2.items():
                if k1 == 'Size':
                    #print(k1,k2,k3)
                    Data = getData(k1,k2,k3,v1,v2,v3,PatternAnalysis)
                    #print(Data)
                    if k3 =='points' or k3 =='line' or k3 == 'plane' or k3 =='hole':
                        for pp in Data:
                            DATA.append(pp)
                    else:
                        DATA.append(Data)
                elif k1 == 'Height':
                    #print(k1,k2,k3)
                    Data = getData(k1,k2,k3,v1,v2,v3,HeightAnalysis)
                    #print(Data)
                    if k3 =='points' or k3 =='hole' or k3 == 'plane':
                        for pp in Data:
                            DATA.append(pp)
                    else:
                        DATA.append(Data)
                elif k1 == 'results':
                    #print(k1,k2,k3)
                    Data = getData(k1,k2,k3,v1,v2,v3,SizeAnalysis)
                    DATA.append(Data)
                else:
                    pass
                
                
    # pattern analysis result
        # elif '_alpha' in k:
        #     print(v.get('value'))
               
#    for k,v in sizeAnalysis.outData.items():
        #print(k,v)
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
   
    return DATA

def run(dnames):
    # define the dataframe
    df_index = indexDF("Flex")
    mindex = pd.MultiIndex.from_frame(df_index)
    dfs = pd.DataFrame(index=mindex)
    # datalists = []
    # snlist = []
    dflist = []
    i = 0
    
    #repeat for each serial number
    for dn in dnames:
        df = pd.DataFrame(index=mindex)
        number = extractMetrologyNum(dn)
        if number == 'n':
            continue
        i += 1
        sn = extractSN(dn)
        print(sn)
        # convert from pickle to dataframe
        datalist = pickupAnalysisDataFlex(dn)        

        #datalists.append(datalist)
        #snlist.append(sn)
        df[sn] =datalist
        dflist.append(df)
        
    #
    dfs = pd.concat(dflist,axis=1)
    print(dfs)
    # for sn, datalist in zip(snlist, datalists):
    #     df[sn]=datalist
    # print(df)
    # save the created data
    dfs.to_pickle("PCB_analysisDataFrame.pickle")
  
if __name__ == '__main__':
    t1 = time.time()

    dnames = datapath.getFilelistPCB('PCB_POPULATION')
    
    run(dnames)
    print(f'counts of module : {len(dnames)}')
    
    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
