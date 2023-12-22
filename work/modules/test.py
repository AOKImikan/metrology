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
import makeImages

with open(f'data/MODULE_HeightData.pkl', 'rb') as fin:
    data = pickle.load(fin)
    
#group dataframe by tags
grouped = data.groupby(['tags'])

taglist = data['tags'].unique()

for tag in taglist:
    #extract by specified tag
    try:
        exData = grouped.get_group((tag))
    except KeyError as e:
        continue

    dataDict = exData.set_index('serial_number')['values'].to_dict()
    datamin = min(dataDict.values())
    datamax = max(dataDict.values())
    makeImages.hist(dataDict, [datamin,datamax], 0.01, [datamin,datamax], '',f'HeightAnalysis_{tag}_hist')
    #makeImages.graph(dataDict, [datamin,datamax], [1000,1150],'',f'HeightAnalysis_{tag}')
    print(exData)
