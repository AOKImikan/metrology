#!/usr/bin/env python3
import os
import json
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#db.json -> 
def LoadData(dn):
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/db.json', 'rb') as fin:
            appdata = json.load(fin)
    if appdata:
        results = appdata['results']
        passed = appdata['passed']
        print(appdata['component'])
    return results

def hist(dnames):
    mergedlist = []
    for dn in dnames:
        results = LoadData(dn)
        for i in [0,1,2,3]:
            mergedlist.append(results['AVERAGE_THICKNESS'][i])
    print(mergedlist)
    #define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)
    #fill thickness list 
    ax.hist(mergedlist, bins=10)

    ax.set_title('AVERAGE_THICKNESS')
    ax.set_xlabel('thickness')
    ax.set_ylabel('unmber')
    #show hist
    plt.show()

def plot(dnames):
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    TRlistX,TRlistY = [],[]
    BLlistX,BLlistY = [],[]
    for dn in dnames:
        results = LoadData(dn)
        TR=results['PCB_BAREMODULE_POSITION_TOP_RIGHT']
        BL=results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT']
        TRlistX.append(results['PCB_BAREMODULE_POSITION_TOP_RIGHT'][0])
        TRlistY.append(results['PCB_BAREMODULE_POSITION_TOP_RIGHT'][1])
        BLlistX.append(results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT'][0])
        BLlistY.append(results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT'][1])

        ##set plot point##    
        ax.scatter(BL[0],BL[1],color="#007fff")      
    ax.set_title('PCB_BAREMODULE_POSITION_BOTTOM_LEFT')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
   
    #draw plot
    plt.show()

    #hist(TRlistY)
        
if __name__ == '__main__':
    dnames = [
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601020/MODULE_ASSEMBLY/003',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601015/MODULE_ASSEMBLY/002',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601016/MODULE_ASSEMBLY/002',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22110427/MODULE_ASSEMBLY/004',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22101021/MODULE_ASSEMBLY/001',
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601021/MODULE_ASSEMBLY/003'
    ]   
    #plot(dnames)
    hist(dnames)

