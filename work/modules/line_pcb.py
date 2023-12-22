#!/usr/bin/env python3
import os
import pickle
import time
import argparse
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

# analysis -> dataframe
def drawplot(dn, sn, tag):
    serialnum = '20UPGPQ'+sn
    tagnames = ['Flex'+tag+'_0','Flex'+tag+'_1','Flex'+tag+'_2','Flex'+tag+'_3']
    pointListX, pointListY =[], []
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(1,1,1)
    fig.tight_layout(rect=[0.12, 0.06, 1, 0.94])

    # open pickle
    sp =LoadData(dn)
    if sp:
        pass
    else:
        return None

    patternAnalysis = sp.analysisList[0]
    sizeAnalysis = sp.analysisList[1]
    for k,v in sizeAnalysis.outData.items():
        if 'Flex'+tag+'_line' in k:
            fitPars = v.p
            
    # pattern analysis result
    for tagname in tagnames:
        for k,v in patternAnalysis.outData.items():
            if v is None:
                continue
            if tagname+'_x' in k:
                pointListX.append(v.get('value'))
            elif tagname+'_y' in k:
                pointListY.append(v.get('value'))

    # add points
    ax.scatter(pointListX,pointListY,marker="o")
    
    # add line
    if tag == 'L':
        y = np.linspace(-20,20,10)
        x = (-fitPars[0] - fitPars[2]*y)/fitPars[1]
        plt.text(-fitPars[0],0,f'{-fitPars[0]}')
    elif tag=='R':
        y = np.linspace(-20,20,10)
        x = (-fitPars[0] - fitPars[2]*y)/fitPars[1]
        plt.text(-fitPars[0],0,f'{-fitPars[0]}')
    elif tag=='T':  
        x = np.linspace(-20,20,10)
        y = (-fitPars[0] - fitPars[1]*x)/fitPars[2]
        plt.text(0,-fitPars[0],f'{-fitPars[0]}')
    elif tag=='B':  
        x = np.linspace(-20,20,10)
        y = (-fitPars[0] - fitPars[1]*x)/fitPars[2]
        plt.text(0,-fitPars[0],f'{-fitPars[0]}')
    ax.plot(x,y)
    
    # set style
    plt.tick_params(labelsize=18)
    #ax.set_xlim(-22,22)
    #ax.set_ylim(-22,22)
    ax.set_title(f'20UPGPQ{sn}_Flex{tag}',fontsize=20)
    ax.set_xlabel(f'x [mm]',fontsize=18,loc='right') 
    ax.set_ylabel(f'y [mm]',fontsize=18,loc='top')

    # show hist
    plt.savefig(f'lineFit/20UPGPQ{sn}_Flex{tag}_zoom.jpg')  #save as jpeg
    plt.show()
    
    return 0

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
    print("Number=",num)
    return num

def run(dnames, args):
    #define the aimed dataframe
    analyDFs = pd.DataFrame()
    serialnum = '20UPGPQ' + args.sn
    #repeat for each serial number
    for dn in dnames:
        # get serial number and qc stage
        sn = extractSN(dn)
        if sn==serialnum:
            print(dn)
            drawplot(dn, args.sn, args.tag)

if __name__ == '__main__':
    t1 = time.time()
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('sn', help='serialnumber 20UPGPQ-')
    parser.add_argument('tag', help='tag : T, B, L, R')
    args = parser.parse_args()  # analyze arguments

    dnames = datapath.getFilelistPCB('PCB_POPULATION')
    
    run(dnames,args)
    print(f'counts of module : {len(dnames)}')
    
    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
    
 
