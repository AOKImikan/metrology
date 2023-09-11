#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def LoadData(dn):
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
    return sp

def analyDataCvtDict(dn):
    data={}
    sp =LoadData(dn)
    patternAnalysis = sp.analysisList[0]
    sizeAnalysis = sp.analysisList[1]
    for k,v in patternAnalysis.outData.items():
        data[k] = v
    for k,v in sizeAnalysis.outData.items():
        data[k] = v
    df=pd.DataFrame([data])
    print(df.T)
    return data

def analyDataCnvDataFrame(SN,dn):
    sp =LoadData(dn)
    patternAnalysis = sp.analysisList[0]
    sizeAnalysis = sp.analysisList[1]
    lstx, lsty = [],[]
    for k,v in patternAnalysis.outData.items():
        if k == 'FmarkTL_0_x':
            lstx.append(['FmarkTL',v.get('value')])
            #dic={'FmarkTL':v.get('value')}
        elif k == 'FmarkTR_0_x':
            lstx.append(['FmarkTR',v.get('value')])
        elif k == 'FmarkBL_0_x':
            lstx.append(['FmarkBL',v.get('value')])
        elif k == 'FmarkBR_0_x':
            lstx.append(['FmarkBR',v.get('value')])
        elif k == 'AsicFmarkTL_0_x':
            lstx.append(['AsicFmarkTL',v.get('value')])
        elif k == 'AsicFmarkTR_0_x':
            lstx.append(['AsicFmarkTR',v.get('value')])
        elif k == 'AsicFmarkBL_0_x':
            lstx.append(['AsicFmarkBL',v.get('value')])
        elif k == 'AsicFmarkBR_0_x':
            lstx.append(['AsicFmarkBR',v.get('value')])
        if k == 'FmarkTL_0_y':
            lsty.append(['FmarkTL',v.get('value')])
        elif k == 'FmarkTR_0_y':
            lsty.append(['FmarkTR',v.get('value')])
        elif k == 'FmarkBL_0_y':
            lsty.append(['FmarkBL',v.get('value')])
        elif k == 'FmarkBR_0_y':
            lsty.append(['FmarkBR',v.get('value')])
        elif k == 'AsicFmarkTL_0_y':
            lsty.append(['AsicFmarkTL',v.get('value')])
        elif k == 'AsicFmarkTR_0_y':
            lsty.append(['AsicFmarkTR',v.get('value')])
        elif k == 'AsicFmarkBL_0_y':
            lsty.append(['AsicFmarkBL',v.get('value')])
        elif k == 'AsicFmarkBR_0_y':
            lsty.append(['AsicFmarkBR',v.get('value')])
            
    #for k,v in sizeAnalysis.outData.items():
    
    dfx = pd.DataFrame(lstx,columns=['tags','detect_x'])
    dfy = pd.DataFrame(lsty,columns=['tags','detect_y'])
    df = pd.merge(dfx, dfy, on='tags')
    return df

def scanPointCnvDataframe(SN,qcnum,dn):
    sn=[]
    qc=[]
    scanList_x ,scanList_y, scanList_z, scanList_tags,scanList_imPath = [],[],[],[],[]
    sp = LoadData(dn)
    i = 0
    while i < len(sp.scanData.points):
        point = sp.scanData.points[i]
        sn.append(SN)
        qc.append(qcnum)
        scanList_x.append(point.get('x'))
        scanList_y.append(point.get('y'))
        scanList_z.append(point.get('z'))
        scanList_tags.append(point.get('tags')[0])
        scanList_imPath.append(point.get('imagePath'))
        i += 1

    df=pd.DataFrame({'serial_number':sn})
    df['qcnum']=qc
    df['x']=scanList_x
    df['y']=scanList_y
    df['z']=scanList_z
    df['tags']=scanList_tags
    df['imagePath']=scanList_imPath
    
    return df

def scanPointCvtDict(dn):
    scanDict = {}
    sp = LoadData(dn)
    i = 0
    while i < len(sp.scanData.points):
        point = sp.scanData.points[i].data
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
    scanAnalyDFs = pd.DataFrame()
    scanDFs = pd.DataFrame()
    analyDFs = pd.DataFrame()
    for dn in dnames:
        sn = extractSN(dn)
        qcnum = extractQcNum(dn)
        analydf = analyDataCnvDataFrame(sn,dn)        
        analyDataCvtDict(dn)
        #x['scanpoint']=scanPointDict(dn)
        #data[sn] = x
        scandf = scanPointCnvDataframe(sn,qcnum,dn)
        df = pd.merge(scandf, analydf, on='tags', how='left')
        scanAnalyDFs = pd.concat([scanAnalyDFs,df])
        scanDFs = pd.concat([scanDFs,scandf])
        analyDFs = pd.concat([analyDFs,analydf])

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
