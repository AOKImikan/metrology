#!/usr/bin/env python3
import os
import pickle
import time
import glob
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datapath

# data.pickle -> ScanProcessor
def LoadData(dn):
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
    return sp

def commonAppend(commonslist,tags,commons,tag):
    commonslist[0].append(commons[0])    # serial number
    commonslist[1].append(commons[1])    # qc stage
    commonslist[2].append(commons[2])  # scan number
    tags.append(tag)     # tag

      
def heightDataCnvDataFrame(SN,qc,num,dn):
    # define list dor dataframe
    snlist, qclist, numlist = [],[],[]
    values, tags = [],[]
   
    # open pickle
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Height')
    if sp:
        pass
    else:
        return None
    heightAnalysis = sp.analysisList[0]
    
    # pattern analysis result
    for k,v in heightAnalysis.outData.items():
        snlist.append(SN)
        qclist.append(qc)
        numlist.append(num)
        tags.append(k)
        values.append(v.get('value'))

    # make dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['tags']=tags
    df['values']=values
   
    return df
    
# analysis -> dataframe
def analyDataCnvDataFrame(SN,qc,num,dn):
    # define list dor dataframe
    snlist, qclist, numlist = [],[],[]
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
        #print(k)
        if('point'in k):
            # get tag (match for scan tag)
            key = k.split('_')
            tag = key[0]
            # add data to list
            if v is None:
                pass
            else:
                values.append(v.position[0])  # Fill detect x
                vType.append('detect_x')
                commonAppend(commonslist,tags,commons, tag)
                values.append(v.position[1])  # Fill detect y
                vType.append('detect_y')
                commonAppend(commonslist,tags,commons, tag)
                
        if('line'in k):
            # get tag (match for scan tag)
            key = k.split('_')
            tag = key[0]
            # add data to list
            if v is None:
                pass
            else:
                values.append(v.p[0])  # Fill line parameter0
                vType.append('line_p0')
                commonAppend(commonslist,tags,commons, tag)
                values.append(v.p[1])  # Fill line parameter1
                vType.append('line_p1')
                commonAppend(commonslist,tags,commons, tag)
                values.append(v.p[2])  # Fill line parameter2
                vType.append('line_p2')
                commonAppend(commonslist,tags,commons, tag)
                
    # make dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['tags']=tags
    df['valueType']=vType
    df['values']=values
    
    return df

# scanData -> dataframe
def scanPointCnvDataframe(SN,qc,num,dn):
    # define list for dataframe
    snlist, qclist, numlist = [],[],[]
    scanList_x ,scanList_y, scanList_z, scanList_tags,scanList_imPath = [],[],[],[],[]

    # open pickle
    sp = LoadData(dn)
    i = 0
    while i < len(sp.scanData.points):
        # add data to list
        snlist.append(SN)    # serial number
        qclist.append(qc)    # qc stage
        numlist.append(num)  # scan number
        
        # get scan point (center of image)
        point = sp.scanData.points[i]
        # add data to list
        scanList_x.append(point.get('x'))  # x 
        scanList_y.append(point.get('y'))  # y
        scanList_z.append(point.get('z'))  # z
        scanList_tags.append(point.get('tags')[0])      # tag
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

# get serial number from directory path
def extractSN(dn):
    words = dn.split('/')
    #print('SN = ',words[7])
    return words[7]

# get QC stage from directory path
def extractQcStage(dn):
    words = dn.split('/')
    qcstage = words[8]
    #print("qcStage=",qcstage)
    return qcstage

# get Metrology number from directory path
def extractMetrologyNum(dn):
    words = dn.split('/')
    num = words[9]
    return num

def run(dnames):
    # define the aimed dataframe
    scanDFs = pd.DataFrame()
    analyDFs = pd.DataFrame()
    heightDFs = pd.DataFrame()
    
    i = 0
    # repeat for each serial number
    for dn in dnames:
        # get serial number and qc stage
        sn = extractSN(dn)
        qcstage = extractQcStage(dn)
        number = extractMetrologyNum(dn)

        # convert from pickle to dataframe
        analydf = analyDataCnvDataFrame(sn,qcstage,number,dn)
        heightdf = heightDataCnvDataFrame(sn,qcstage,number,dn)        
        scandf = scanPointCnvDataframe(sn,qcstage,number,dn)

        # concat each serial numbers
        analyDFs = pd.concat([analyDFs,analydf],ignore_index=True)
        heightDFs = pd.concat([heightDFs,heightdf],ignore_index=True)
        scanDFs = pd.concat([scanDFs,scandf],ignore_index=True)
        #i += 1
        #if i > 3:
         #   break

    print(scanDFs)
    print(analyDFs)
    print(heightDFs)
    # save the created data
    analyDFs.to_pickle("data/MODULE_AnalysisData.pkl")
    scanDFs.to_pickle("data/MODULE_ScanData.pkl")
    heightDFs.to_pickle("data/MODULE_HeightData.pkl")
    analyDFs.to_csv("data/MODULE_AnalysisData.csv")
    scanDFs.to_csv("data/MODULE_ScanData.csv")
    heightDFs.to_csv("data/MODULE_HeightData.csv")

    print("save as data/MODULE_****Data")

if __name__ == '__main__':
    t1 = time.time()

    dnames = datapath.getFilelistModule()
    
    print(f'counts of module : {len(dnames)}')    
    run(dnames)

    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
    
