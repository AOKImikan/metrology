#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def readData(dn):
    appdata = None
    data = {}
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
        for k,v in patternAnalysis.outData.items():
            data[k] = v
        for k,v in sizeAnalysis.outData.items():
            data[k] = v
    return data

def scanPointCnvDataframe(SN,dn):
    appdata = None
    sn=[]
    scanList_x ,scanList_y, scanList_z, scanList_tags,scanList_imPath = [],[],[],[],[]
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
        i = 0
        while i < len(sp.scanData.points):
            point = sp.scanData.points[i]
            sn.append(SN)
            scanList_x.append(point.get('x'))
            scanList_y.append(point.get('y'))
            scanList_z.append(point.get('z'))
            scanList_tags.append(point.get('tags')[0])
            scanList_imPath.append(point.get('imagePath'))
            i += 1
    df=pd.DataFrame({'serial_number':sn})
    df['x']=scanList_x
    df['y']=scanList_y
    df['z']=scanList_z
    df['tags']=scanList_tags
    df['imagePath']=scanList_imPath
    #print(df.head(20))
    return df

def scanPointDict(dn):
    appdata = None
    scanDict = {}
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
        i = 0
        while i < len(sp.scanData.points):
            point = sp.scanData.points[i].data
            #print(point['index'],':',point['x'],'  ',point['y'],'  ',  point['z'])
            scanDict[i]={'x':point['x'],'y':point['y'],'z':point['z']}
            i += 1
    return scanDict

def extractSN(dn):
    words = dn.split('/')
    print('SN = ',words[9])
    return words[9]

def extractQcNum(dn):
    words = dn.split('/')
    qcnum=words[10]+"/"+words[11]
    print("qcnum=",qcnum)
    return qcnum

    
def run(dnames):
    data = {}
    df = pd.DataFrame()
    for dn in dnames:
        sn = extractSN(dn)
        qcnum = extractQcNum(dn)
        x = readData(dn)
        x['scanpoint']=scanPointDict(dn)
        data[sn] = x
        y = scanPointCnvDataframe(sn,dn)
        df = df.append(y, ignore_index=False)
    with open("scanAnalysis.pkl","wb") as tf:
        pickle.dump(data,tf)
    print(data)
    df.to_pickle("data/ScanAndAnalysis.pkl")
    df.to_csv("data/DataFrame.csv")
    print("save file to scanAnalysis.pkl and DataFrame.csv")

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
