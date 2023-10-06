#!/usr/bin/env python3
import os
import time
import pickle
import tkinter as tk
from tkinter import ttk
import pmm
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import FmarkMarginPlot

def histMargin(df):
    # define matplotlib figure
    fig = plt.figure(figsize=(10,9))
    ax = fig.add_subplot(1,1,1)
    # fill margin list 
    ax.hist(df['margin'], bins=50)

    ax.set_title('Fmark\'s margin')
    ax.set_xlabel('margin')
    ax.set_ylabel('unmber of serialnumber and tag')
    # show hist
    plt.show()

def marginHist_special(df, binrange):
    # get tag name
    name = df.loc[0,'tags']
    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)
    
    # fill margin list
    bins = np.arange(np.nanmin(df['margin'].to_list()),
                     np.nanmax(df['margin'].to_list()), binrange)
    n = ax.hist(df['margin'], bins=bins, alpha=1, histtype="stepfilled",
                edgecolor='black')

    # set hist style
    plt.tick_params(labelsize=18)
    ax.set_title(f'{name} margin',fontsize=20)
    ax.set_xlabel('mm',fontsize=18,loc='right')
    ax.set_ylabel(f'events/{binrange}mm',fontsize=18,loc='top')

    # save histgram
    plt.savefig(f'resultsHist/margin/{name}.jpg')  #save as jpeg
    print(f'save as resultsHist/margin/{name}.jpg')

    # show hist
    plt.show()

    
def calculateMargin(df):
    # copy dataframe (for safety)
    marginDF = df.copy()
    
    # calculate delta x,y
    marginDF['delta_x'] = marginDF['detect_x']-marginDF['scan_x']
    marginDF['delta_y'] = marginDF['detect_y']-marginDF['scan_y']
    # calculate delta squared
    marginDF['margin^2'] = marginDF['delta_x']**2+marginDF['delta_y']**2
    # pandas series -> numpy ndarray
    a = marginDF['margin^2'].values
    # calculate sqrt
    marginlist = np.sqrt(a)
    marginDF['margin'] = pd.DataFrame(marginlist)

    # drop unnecessary columns (inplace means alter original dataframe)
    marginDF.drop(columns=['detect_x','detect_y','scan_x','scan_y','margin^2'],
                  inplace=True)
    return marginDF

def mergeDF(scanData,anaData,tag):
    # group scandata dataframe by tags
    grouptag_scan = scanData.groupby(['tags'])   
    # extract by specified tag
    extract_scan = grouptag_scan.get_group((tag))
    # group analysis data by tags
    grouptag_ana = anaData.groupby(['tags'])
    # extract by specified tag
    extract_ana = grouptag_ana.get_group((tag))
    # get standard deviation
    std = extract_scan['scan_z'].std()
    mean = extract_scan['scan_z'].mean()

    # 'inner' means merge only the rows where sn col exists in both data
    merged_df = pd.merge(extract_scan, extract_ana,
                         on=['serial_number','qc_stage','scan_num','tags'],
                         how='inner')
    return merged_df

def marginDF_special(scanData, anaData, args):
    # get focus tag
    tag = args

    # merge 2 data
    merged_df = mergeDF(scanData, anaData, tag)  # return is dataframe

    # create margin data as dataframe
    margin_df = calculateMargin(merged_df)  # return is dataframe

    # save the created data
    margin_df.to_pickle('data/margin/{}.pkl'.format(tag))
    margin_df.to_csv('data/margin/{}.csv'.format(tag))    
    print('save file to "data/margin/{}.pkl"'.format(tag))
    
    return margin_df

def allFmark(scanData, anaData):
    # get all tag list from analysis data
    taglist = anaData['tags'].unique()
    allmerged_df = pd.DataFrame()
    for tag in taglist:
        if 'Fmark' in tag: #extract rows with 'Fmark'
            #merge 2 data
            merged_df = mergeDF(scanData, anaData, tag) #return is dataframe
            allmerged_df = pd.concat([allmerged_df,merged_df],ignore_index=True)

    # create margin data as dataframe
    margin_df = calculateMargin(allmerged_df) #return is dataframe

    # save the created data
    margin_df.to_pickle('data/margin/Fmarkmargin.pkl')
    margin_df.to_csv('data/margin/Fmarkmargin.csv')
    print(margin_df)
    print('save file to "data/margin/Fmarkmargin.pkl"')

    ex = margin_df[margin_df['margin']>0.3]
    print('margin = ' , ex['margin'])
    print('serial number = ' , ex['serial_number'])
    print('tag = ' , ex['tags'])
    print('scan z = ' , ex['scan_z'])
    print('image path = ' , ex['image_path'])
    # make hist
    histMargin(margin_df)

def run(scanData, anaData, args):
    if args.asic:
        if args.asic=='TL':
            # make dataframe margin information
            df = marginDF_special(scanData, anaData, 'AsicFmarkTL')
            # make hist of margin
            marginHist_special(df,0.01)
            if args.plot:
                # plot scan point with image center
                FmarkMarginPlot.plotPoint(scanData,anaData,'AsicFmarkTL')

        elif args.asic=='TR':
            df = marginDF_special(scanData, anaData, 'AsicFmarkTR')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'AsicFmarkTR')
        
        elif args.asic=='BL':
            df = marginDF_special(scanData, anaData, 'AsicFmarkBL')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'AsicFmarkBL')

        elif args.asic=='BR':
            df = marginDF_special(scanData, anaData, 'AsicFmarkBR')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'AsicFmarkBR')


    elif args.flex:
        if args.flex=='TL':
            df = marginDF_special(scanData, anaData, 'FmarkTL')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'FmarkTL')

        elif args.flex=='TR':
            df = marginDF_special(scanData, anaData, 'FmarkTR')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'FmarkTR')

        elif args.flex=='BL':
            df = marginDF_special(scanData, anaData, 'FmarkBL')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'FmarkBL')

        elif args.flex=='BR':
            df = marginDF_special(scanData, anaData, 'FmarkBR')
            marginHist_special(df,0.01)
            if args.plot:
                FmarkMarginPlot.plotPoint(scanData,anaData,'FmarkBR')
    #elif args.sside:
        
    else:
        print('Error: No such Command. type option -h or --help')
        
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    
    # make parser
    parser = argparse.ArgumentParser()
    
    # add argument
    parser.add_argument('-a', '--asic', help='asic fmark', choices=['TL','TR','BL','BR'])
    parser.add_argument('-f', '--flex', help='flex fmark', choices=['TL','TR','BL','BR'])
    parser.add_argument('--sside', help='sensor side', choices=['T','B'])
    parser.add_argument('--fside', help='flex side', choices=['L','R','T','B'])
    parser.add_argument('--aside', help='asic side', choices=['L','R'])
    
    parser.add_argument('-p', '--plot', help='make plot?',  action='store_true')

    args = parser.parse_args()  # analyze arguments
    
    # open data as dataframe
    with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)
        
    # run main
    run(scanData, analysisData, args)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  

    
