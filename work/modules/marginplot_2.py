#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def extractSN(dn):
    words = dn.split('/')
    #print('SN = ',words[9])
    return words[9]

def plot2(df):
    fig = plt.figure(figsize=(10,5))
    axes = fig.subplots(1,2,sharey='all')
    pltdata=df.groupby(['tags'])
    data1=pltdata.get_group(('HVCapacitor'))
    data2=pltdata.get_group(('Connector'))
    axes[0].annotate(f'$\sigma={data1["z"].std():.5f}$',
                     xy=(0.05, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0].annotate(f'entries={data1["z"].count()}',
                     xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)

    axes[1].annotate(f'$\sigma={data2["z"].std():.5f}$',
                     xy=(0.55, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1].annotate(f'entries={data2["z"].count()}',
                     xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
  
    axes[0].set_title('HVCapacitor')
    axes[1].set_title('Connector')
    axes[0].hist(data1['z'])
    axes[1].hist(data2['z'])
    plt.show()

def plot4(df):
    fig = plt.figure(figsize=(10,9))
    axes = fig.subplots(2,2,sharex='col',sharey='row')
    pltdata=df.groupby(['tags'])
    data1=pltdata.get_group(('Pickup1'))
    data2=pltdata.get_group(('Pickup2'))
    data3=pltdata.get_group(('Pickup3'))
    data4=pltdata.get_group(('Pickup4'))
    axes[0,0].annotate(f'$\sigma={data1["z"].std():.5f}$',
                       xy=(0.01, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0,0].annotate(f'entries={data1["z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[1,0].annotate(f'$\sigma={data2["z"].std():.5f}$',
                       xy=(0.51, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1,0].annotate(f'entries={data2["z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[0,1].annotate(f'$\sigma={data3["z"].std():.5f}$',
                       xy=(0.01, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0,1].annotate(f'entries={data3["z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[1,1].annotate(f'$\sigma={data4["z"].std():.5f}$',
                       xy=(0.01, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1,1].annotate(f'entries={data4["z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[0,0].set_title('Pickup1')
    axes[1,0].set_title('Pickup2')
    axes[0,1].set_title('Pickup3')
    axes[1,1].set_title('Pickup4')

    axes[0,0].hist(data1['z'])
    axes[1,0].hist(data2['z'])
    axes[0,1].hist(data3['z'])
    axes[1,1].hist(data4['z'])
    plt.show()
    
def plotPoint(SN, Name, scandata, analydata):    
    TR = analydata[SN]['{}TR_0_point'.format(Name)]
    TL = analydata[SN]['{}TL_0_point'.format(Name)]
    BR = analydata[SN]['{}BR_0_point'.format(Name)]
    BL = analydata[SN]['{}BL_0_point'.format(Name)]
    #point = v['scanPoint']
    print(SN)

    pltdata=scandata.groupby(['tags','serial_number'])
    data1=pltdata.get_group(('{}TL'.format(Name),f'{SN}'))
    data2=pltdata.get_group(('{}BL'.format(Name),f'{SN}'))
    data3=pltdata.get_group(('{}TR'.format(Name),f'{SN}'))
    data4=pltdata.get_group(('{}BR'.format(Name),f'{SN}'))

    fig = plt.figure(figsize=(10,9)) 
    axes = fig.subplots(2,2)
    dx=0.57
    dy=0.38
    xmax1=data1['x'].iloc[-1]+dx
    xmin1=data1['x'].iloc[-1]-dx
    ymax1=data1['y'].iloc[-1]+dy
    ymin1=data1['y'].iloc[-1]-dy
    xmax2=data2['x'].iloc[-1]+dx
    xmin2=data2['x'].iloc[-1]-dx
    ymax2=data2['y'].iloc[-1]+dy
    ymin2=data2['y'].iloc[-1]-dy
    xmax3=data3['x'].iloc[-1]+dx
    xmin3=data3['x'].iloc[-1]-dx
    ymax3=data3['y'].iloc[-1]+dy
    ymin3=data3['y'].iloc[-1]-dy
    xmax4=data4['x'].iloc[-1]+dx
    xmin4=data4['x'].iloc[-1]-dx
    ymax4=data4['y'].iloc[-1]+dy
    ymin4=data4['y'].iloc[-1]-dy

    axes[0,0].set_xlim(xmin1,xmax1)
    axes[0,0].set_ylim(ymin1,ymax1)
    axes[1,0].set_xlim(xmin2,xmax2)
    axes[1,0].set_ylim(ymin2,ymax2)  
    axes[0,1].set_xlim(xmin3,xmax3)
    axes[0,1].set_ylim(ymin3,ymax3)
    axes[1,1].set_xlim(xmin4,xmax4)
    axes[1,1].set_ylim(ymin4,ymax4)
    fig.suptitle(f'{SN}')
    axes[0,0].set_title('{}TL'.format(Name))
    axes[1,0].set_title('{}BL'.format(Name))
    axes[0,1].set_title('{}TR'.format(Name))
    axes[1,1].set_title('{}BR'.format(Name))
    print(data1['z'])
    axes[0,0].scatter(data1['x'],data1['y'],color="#00a0ff")
    axes[0,0].scatter(TL.position[0],TL.position[1],color="#ff0000")
    axes[1,0].scatter(data2['x'],data2['y'],color="#00a0ff")
    axes[1,0].scatter(BL.position[0],BL.position[1],color="#ff0000")
    axes[0,1].scatter(data3['x'],data3['y'],color="#00a0ff")
    axes[0,1].scatter(TR.position[0],TR.position[1],color="#ff0000")
    axes[1,1].scatter(data4['x'],data4['y'],color="#00a0ff")
    axes[1,1].scatter(BR.position[0],BR.position[1],color="#ff0000")
    plt.show()
    
def run(scanData, analydata):
    serialnum=[]
    for k,v in analydata.items():
        serialnum.append(k)

    ###################
    SN=serialnum[1]
    pointName = 'Fmark'
    lineName = 'Flex'
    ###################
    
    plotPoint(SN, pointName, scanData, analydata)

    #for k,v in analysis.items():
        #print(f'{k}:{v}')
    #plot4(scanData)

if __name__ == '__main__':
    scanData = pd.read_csv('data/DataFrame.csv')
    with open(f'data/scanAnalysis.pkl', 'rb') as fin:
        analysis = pickle.load(fin)
    run(scanData, analysis)    
