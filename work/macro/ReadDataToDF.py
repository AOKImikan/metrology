#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#data.pickle -> ScanProcessor
def LoadData(dn):
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
    return sp

#analysis -> dataframe
def analyDataCnvDataFrame(SN,qc,num,dn):
    #define list dor dataframe
    snlist, qclist, numlist = [],[],[]
    xlist, ylist,tags = [],[],[]

    #open pickle
    sp =LoadData(dn)
    patternAnalysis = sp.analysisList[0]
    sizeAnalysis = sp.analysisList[1]

    ##repeat##
    #pattern analysis result
    for k,v in patternAnalysis.outData.items():
        if('point'in k):
            #get tag (match for scan tag)
            key = k.split('_')
            tag = key[0]
            #add data to list
            snlist.append(SN)   #serial number
            qclist.append(qc)   #qc stage
            numlist.append(num) #scan number
            tags.append(tag)    #tag
            xlist.append(v.position[0]) #detect x
            ylist.append(v.position[1]) #detect y
    
    #make dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    #add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['tags']=tags
    df['detect_x']=xlist
    df['detect_y']=ylist
    
    return df

#scanData -> dataframe
def scanPointCnvDataframe(SN,qc,num,dn):
    #define list for dataframe
    snlist, qclist, numlist = [],[],[]
    scanList_x ,scanList_y, scanList_z, scanList_tags,scanList_imPath = [],[],[],[],[]

    #open pickle
    sp = LoadData(dn)
    i = 0
    while i < len(sp.scanData.points):
        #add data to list
        snlist.append(SN)   #serial number
        qclist.append(qc)   #qc stage
        numlist.append(num) #scan number
        
        #get scan point (center of image)
        point = sp.scanData.points[i]
        #add data to list
        scanList_x.append(point.get('x')) #x
        scanList_y.append(point.get('y')) #y
        scanList_z.append(point.get('z')) #z
        scanList_tags.append(point.get('tags')[0])     #tag
        scanList_imPath.append(point.get('imagePath')) #image path
        i += 1  #repeat parameter
        
    #define dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    #add data to dataframe
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
    print('SN = ',words[9])
    return words[9]

#get Metrology number from directory path
def extractMetrologyNum(dn):
    words = dn.split('/')
    num = words[11]
    print("Number=",num)
    return num

#get QC stage from directory path
def extractQcStage(dn):
    words = dn.split('/')
    qcstage = words[10]
    print("qcStage=",qcstage)
    return qcstage

def run(dnames):
    #define the aimed dataframe
    scanDFs = pd.DataFrame()
    analyDFs = pd.DataFrame()

    #repeat for each serial number
    for dn in dnames:
        #get serial number and qc stage
        sn = extractSN(dn)
        qcstage = extractQcStage(dn)
        number = extractMetrologyNum(dn)

        #convert from pickle to dataframe
        analydf = analyDataCnvDataFrame(sn,qcstage,number,dn)        
        scandf = scanPointCnvDataframe(sn,qcstage,number,dn)

        #concat each serial numbers
        analyDFs = pd.concat([analyDFs,analydf],ignore_index=True)
        scanDFs = pd.concat([scanDFs,scandf],ignore_index=True)

    #save the created data
    analyDFs.to_pickle("data/AnalysisData.pkl")
    scanDFs.to_pickle("data/ScanData.pkl")
    analyDFs.to_csv("data/AnalysisData.csv")
    scanDFs.to_csv("data/ScanData.csv")

    print("save data file")

if __name__ == '__main__':
    dnames = [
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601020/MODULE_ASSEMBLY/003',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601015/MODULE_ASSEMBLY/002',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601016/MODULE_ASSEMBLY/002',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22110427/MODULE_ASSEMBLY/004',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22101021/MODULE_ASSEMBLY/001',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601021/MODULE_ASSEMBLY/003'
    ]   
    run(dnames)
