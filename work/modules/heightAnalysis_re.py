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


#get serial number from directory path
def extractSN(dn):
    words = dn.split('/')
    sn = words[8]
    #print('SN = ',sn)
    return sn

def correctHeight(points, refPlane):
    fmt = '5.4f'
    points2 = []
    for p in points:
        z = roundF(refPlane.distance(p),fmt)
        points2.append(Point([p[0], p[1], z]) )
    return points2

def run(dn):   
    sp = LoadData(dn)
    scanData = sp.scanData
    ConPoints = scanData.pointsWithTag('Connector')
    CapPoints = scanData.pointsWithTag('HVCapacitor')
    JigPoints = scanData.pointsWithTag('Jig')
    JigPlane = fitPlane(JigPoints)
    ConPoints = correctHeight(ConPoints, JigPlane[0])
    CapPoints = correctHeight(CapPoints, JigPlane[0])
    zs = []
    for p in ConPoints:
        z = p.position[2]
        print(z)
        if z < 10:
            zs.append(z)
    print(zs)
    print(np.mean(zs))
    
if __name__ == '__main__':
    t1 = time.time()

    dnames = datapath.getFilelistPCB('PCB_POPULATION')
    for dn in dnames:
         sn = extractSN(dn)
         if sn == '20UPGPQ2601144':
             run(dn)    
    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
    
 
