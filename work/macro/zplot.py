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
    pltdata = df.groupby(['tags'])
    data1 = pltdata.get_group(('HVCapacitor'))
    data2 = pltdata.get_group(('Connector'))
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
    axes = fig.subplots(2,2,sharex='all',sharey='all')
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
    
def run(scanData, analysis):
    plot2(scanData)

if __name__ == '__main__':
    scanData = pd.read_csv('data/DataFrame.csv')
    with open(f'data/scanAnalysis.pkl', 'rb') as fin:
        analysis = pickle.load(fin)
    run(scanData, analysis)    
