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

#data.pickle -> ScanProcessor
def LoadData(dn):
    appdata = None
    sp = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
            #print(appdata.scanNames())
            sp = appdata.getScanProcessor('ITkPixV1xFlex.Size')
    return sp

def commonAppend(commonslist,tags,commons,tag):
      commonslist[0].append(commons[0])    # serial number
      commonslist[1].append(commons[1])    # qc stage
      commonslist[2].append(commons[2])  # scan number
      tags.append(tag)     # tag

# analysis -> dataframe
def analyDataCnvDataFrame(SN,qc,num,dn):
    # define list dor dataframe
    snlist, qclist, numlist = [],[],[]
    valuelist = []
    analyTags = []
    values, tags, vType = [],[],[]
    commons = [SN, qc, num]
    commonslist = [snlist, qclist, numlist]
    
    # open pickle
    sp =LoadData(dn)
    if sp:
        pass
    else:
        return None

    patternAnalysis = sp.analysisList[0]
    sizeAnalysis = sp.analysisList[1]

    ##repeat##
    # pattern analysis result
    for k,v in patternAnalysis.outData.items():
        #print(k,v)
        if v is None:
            valuelist.append(None)  # Fill NaN
            analyTags.append(None)  # Fill NaN  
        elif '_alpha' in k:
            valuelist.append(v.get('value'))
            analyTags.append(k)
        elif '_x' in k :
            valuelist.append(v.get('value'))
            analyTags.append(k)
        elif '_y' in k:
            valuelist.append(v.get('value'))
            analyTags.append(k)
        elif '_r' in k:
            valuelist.append(v.get('value'))
            analyTags.append(k)
        else:
            continue
        # get tag (match for scan tag)
        key = k.split('_')
        tag = key[0]
        commonAppend(commonslist, tags, commons, tag)
        #tags.append(tag)     # tag
        #snlist.append(SN)    # serial number
        #qclist.append(qc)    # qc stage
        #numlist.append(num)  # scan number
        
    for k,v in sizeAnalysis.outData.items():
        #print(k,v)
        if 'line' in k:
            commonAppend(commonslist, tags, commons, tag)
            valuelist.append(v.p[0])
            analyTags.append(k)
        else:
            commonAppend(commonslist, tags, commons, tag)
            valuelist.append(v.get('value'))
            analyTags.append(k)
            
    # make dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})

    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['scan_tags']=tags
    df['analysis_tags']=analyTags
    df['analysis_value'] = valuelist
   
    return df

# scanData -> dataframe
def scanPointCnvDataframe(SN,qc,num,dn):
    # define list for dataframe
    snlist, qclist, numlist = [],[],[]
    scanList_x ,scanList_y, scanList_z, scanList_tags,scanList_imPath = [],[],[],[],[]

    # open pickle
    sp = LoadData(dn)
    if sp:
        pass
    else:
        return None
    
    i = 0    
    while i < len(sp.scanData.points):
        # add data to list
        snlist.append(SN)    # serial number
        qclist.append(qc)    # qc stage
        numlist.append(num)  # scan number
        
        # get scan point (center of image)
        point = sp.scanData.points[i]
        # add data to list
        scanList_x.append(point.get('x')) # x
        scanList_y.append(point.get('y')) # y
        scanList_z.append(point.get('z')) # z
        if point.get('tags'):
            scanList_tags.append(point.get('tags')[0])  # tag
        else:
            scanList_tags.append('')  # tag
            
        scanList_imPath.append(point.get('imagePath'))  # image path
        i += 1  # repeat parameter
        
    # define dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['scan_x']=scanList_x
    df['scan_y']=scanList_y
    df['scan_z']=scanList_z
    df['tags']=scanList_tags
    df['image_path']=scanList_imPath

    return df

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

def run(dnames):
    #define the aimed dataframe
    scanDFs = pd.DataFrame()
    analyDFs = pd.DataFrame()
    i = 0
    #repeat for each serial number
    for dn in dnames:
        i += 1
        # get serial number and qc stage
        sn = extractSN(dn)
        qcstage = extractQcStage(dn)
        number = extractMetrologyNum(dn)
    
        # convert from pickle to dataframe
        analydf = analyDataCnvDataFrame(sn,qcstage,number,dn)        
        scandf = scanPointCnvDataframe(sn,qcstage,number,dn)

        # concat each serial numbers
        analyDFs = pd.concat([analyDFs,analydf],ignore_index=True)
        scanDFs = pd.concat([scanDFs,scandf],ignore_index=True)
          
    # save the created data
    analyDFs.to_pickle("data/PCB_AnalysisData.pkl")
    scanDFs.to_pickle("data/PCB_ScanData.pkl")
    analyDFs.to_csv("data/PCB_AnalysisData.csv")
    scanDFs.to_csv("data/PCB_ScanData.csv")
    print(analyDFs)
    print("save as data/PCB_AnalysisData")

if __name__ == '__main__':
    t1 = time.time()

    dnames = datapath.getFilelistPCB('PCB_POPULATION')
    print(f'counts of module : {len(dnames)}')
    run(dnames)
    print(f'counts of module : {len(dnames)}')
    
    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
    
 
