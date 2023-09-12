#!/usr/bin/env python3
import os
import pickle
import sys
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
    
def calculateMargin(df):
    #copy dataframe (for safety)
    marginDF = df.copy()
    
    #calculate delta x,y
    marginDF['delta_x'] = marginDF['detect_x']-marginDF['scan_x']
    marginDF['delta_y'] = marginDF['detect_y']-marginDF['scan_y']
    #calculate delta squared
    marginDF['margin^2'] = marginDF['delta_x']**2+marginDF['delta_y']**2
    #pandas series -> numpy ndarray
    a = marginDF['margin^2'].values
    #calculate sqrt
    marginlist = np.sqrt(a)
    marginDF['margin'] = pd.DataFrame(marginlist)

    #drop unnecessary columns (inplace means alter original dataframe)
    marginDF.drop(columns=['detect_x','detect_y','scan_x','scan_y','margin^2'],
                  inplace=True)
    return marginDF

def mergeDF(scanData,anaData,tag):
    #group scandata dataframe by tags
    grouptag_scan = scanData.groupby(['tags'])   
    #extract by specified tag
    extract_scan = grouptag_scan.get_group((tag))
    #group analysis data by tags
    grouptag_ana = anaData.groupby(['tags'])
    #extract by specified tag
    extract_ana = grouptag_ana.get_group((tag))
    #get standard deviation
    std = extract_scan['scan_z'].std()
    mean = extract_scan['scan_z'].mean()

    #'inner' means merge only the rows where sn col exists in both data
    merged_df = pd.merge(extract_scan, extract_ana,
                         on=['serial_number','qc_stage','scan_num','tags'],
                         how='inner')
    return merged_df

def specialTag(scanData, anaData, args):
    #get focus tag
    tag = args[1]

    #merge 2 data
    merged_df = mergeDF(scanData, anaData, tag) #return is dataframe

    #create margin data as dataframe
    margin_df = calculateMargin(merged_df) #return is dataframe

    #save the created data
    margin_df.to_pickle('data/margin/{}.pkl'.format(tag))
    margin_df.to_csv('data/margin/{}.csv'.format(tag))

def allFmark(scanData, anaData):
    #get all tag list from analysis data
    taglist = anaData['tags'].unique()
    allmerged_df = pd.DataFrame()
    for tag in taglist:
        if 'Fmark' in tag: #extract rows with 'Fmark'
            #merge 2 data
            merged_df = mergeDF(scanData, anaData, tag) #return is dataframe
            allmerged_df = pd.concat([allmerged_df,merged_df],ignore_index=True)

    #create margin data as dataframe
    margin_df = calculateMargin(allmerged_df) #return is dataframe

    #save the created data
    margin_df.to_pickle('data/margin/Fmarkmargin.pkl')
    margin_df.to_csv('data/margin/Fmarkmargin.csv')    
    
if __name__ == '__main__':
    #get argument
    args = sys.argv
    
    #open data as dataframe
    with open(f'data/ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)
        
    if len(args)>1:
        specialTag(scanData, analysisData, args)
    if len(args)==1:
        allFmark(scanData, analysisData)
