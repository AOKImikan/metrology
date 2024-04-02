#!/usr/bin/env python3
import os
import time
import pickle
import tkinter as tk
from tkinter import ttk
#import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import makeImages

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('module', help='module choice')
    parser.add_argument('-t', '--tag', help='show z hist of that tag')
    parser.add_argument('--pickup', help='pickup area', action='store_true')
    parser.add_argument('--capcon', help='capcitor and connector', action='store_true')
    parser.add_argument('-a', help='all tag scan z plot', action='store_true')
    parser.add_argument('--stat', help='z statistics', action='store_true')
    
    args = parser.parse_args()  # analyze arguments
    return args
def plot2(df):
    fig = plt.figure(figsize=(10,5))
    axes = fig.subplots(1,2,sharey='all')
    pltdata = df.groupby(['tags'])
    data1 = pltdata.get_group(('HVCapacitor'))
    data2 = pltdata.get_group(('Connector'))
    axes[0].annotate(f'$\sigma={data1["scan_z"].std():.5f}$',
                     xy=(0.05, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0].annotate(f'entries={data1["scan_z"].count()}',
                     xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)

    axes[1].annotate(f'$\sigma={data2["scan_z"].std():.5f}$',
                     xy=(0.55, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1].annotate(f'entries={data2["scan_z"].count()}',
                     xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
  
    axes[0].set_title('HVCapacitor')
    axes[1].set_title('Connector')
    axes[0].hist(data1['scan_z'])
    axes[1].hist(data2['scan_z'])
    plt.show()

def plot4(df):
    fig = plt.figure(figsize=(10,9))
    axes = fig.subplots(2,2,sharex='all',sharey='all')
    pltdata=df.groupby(['tags'])
    data1=pltdata.get_group(('Pickup1'))
    data2=pltdata.get_group(('Pickup2'))
    data3=pltdata.get_group(('Pickup3'))
    data4=pltdata.get_group(('Pickup4'))
    axes[0,0].annotate(f'$\sigma={data1["scan_z"].std():.5f}$',
                       xy=(0.01, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0,0].annotate(f'entries={data1["scan_z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[1,0].annotate(f'$\sigma={data2["scan_z"].std():.5f}$',
                       xy=(0.51, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1,0].annotate(f'entries={data2["scan_z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[0,1].annotate(f'$\sigma={data3["scan_z"].std():.5f}$',
                       xy=(0.01, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0,1].annotate(f'entries={data3["scan_z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[1,1].annotate(f'$\sigma={data4["scan_z"].std():.5f}$',
                       xy=(0.01, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1,1].annotate(f'entries={data4["scan_z"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
   
    axes[0,0].set_title('Pickup1')
    axes[1,0].set_title('Pickup2')
    axes[0,1].set_title('Pickup3')
    axes[1,1].set_title('Pickup4')

    axes[0,0].hist(data1['scan_z'])
    axes[1,0].hist(data2['scan_z'])
    axes[0,1].hist(data3['scan_z'])
    axes[1,1].hist(data4['scan_z'])
    plt.show()

def summary(scanData, taglist):
    normal = pd.DataFrame()
    Cell = pd.DataFrame()
    analysisDF = pd.DataFrame(columns=['mean_normal','mean_Cell','std_normal','std_Cell'])
    #analysisDF = pd.DataFrame()
    print(analysisDF)
    #ngSNDF = pd.DataFrame()
    
    for tag in taglist:
        devideDFs = exTagAndDevideCell(tag,scanData)
        mean_n = round(devideDFs[0]['scan_z'].mean(),3)
        std_n = round(devideDFs[0]['scan_z'].std(),5)
        require_n = [mean_n-0.05, mean_n+0.05]
        mean_c = round(devideDFs[1]['scan_z'].mean(),3)
        std_c = round(devideDFs[1]['scan_z'].std(),5)
        require_c = [mean_c-0.05, mean_c+0.05]
    
        # make short df and concat!?
        shortDF = pd.DataFrame({'mean_normal':[mean_n],'mean_Cell':[mean_c],
                                'std_normal':[std_n], 'std_Cell':[std_c]},index=[tag])
        print(shortDF)
        analysisDF = pd.concat([analysisDF, shortDF],axis=0,join='outer')
        
    print(analysisDF)    
    #save the created data
    analysisDF.to_csv("scan_z_summary.csv")
    #ngSNDF.to_csv("scan_z_badSN.csv")
    print('analysis data save as scan_z_summary')

    
def calcSigma(data, width=3):
    mean = np.mean(data)
    stddev = np.std(data)
    reqmin = mean - stddev*width
    reqmax = mean + stddev*width
    return [reqmin, reqmax]

def makeDictionary(df):
    snGroup = df.groupby('serial_number')
    dataDict = snGroup['scan_z'].apply(list).to_dict()
    dataList = df['scan_z'].tolist()
    return dataDict, dataList
    
def JigResidual(tag, df):
    def calcResidual(row):
        sn = row['serial_number']
        res = row['scan_z'] - means_jig[sn]
        return res

    groupdata_tag = df.groupby(['tags'])
    groupdata_tagSN = df.groupby(['tags', 'serial_number'])
    means = groupdata_tagSN['scan_z'].mean(numeric_only=True)
    means_jig = means.loc['Jig']
    plotdata = groupdata_tag.get_group((tag))
    plotdata = plotdata.drop(['scan_x', 'scan_y','qc_stage',
                              'image_path','scan_num','tags'],axis=1)
        
    plotdata.loc[:, 'residual_z'] = plotdata.apply(calcResidual, axis=1)
    plotdata = plotdata.drop('scan_z',axis = 1)
    #plotdata['residual'] = plotdata.apply(lambda row: row['scan_z'] - means_jig[row['serial_number']], axis=1)
    snGroup = plotdata.groupby('serial_number')
    dataDict = snGroup['residual_z'].apply(list).to_dict()
    #dataDict = dict(zip(plotdata['serial_number'], plotdata['residual_z']))
    datalist = plotdata['residual_z'].tolist()    

    return dataDict, datalist

def exTagData(tag, df):
    groupdata_tag = df.groupby(['tags'])
    plotdata = groupdata_tag.get_group((tag))

    # drop {{z > 50mm}} data
    # plotdata.drop(plotdata[plotdata['scan_z'] > 50].index, inplace=True)
    # plotdata.drop(plotdata[plotdata['scan_z'] > 7.5].index, inplace=True)

    snGroup = plotdata.groupby('serial_number')    
    dataDict = snGroup['scan_z'].apply(list).to_dict()
    
    #dataDict = dict(zip(plotdata['serial_number'], plotdata['scan_z']))
    datalist = plotdata['scan_z'].tolist()
    
    return dataDict, datalist

def exTagAndDevideCell(tag, df, threshold):
    def calcResidual(row):
        sn = row['serial_number']
        res = row['scan_z'] - means_jig_s[sn]
        return res
    groupdata_tag = df.groupby(['tags'])
    plotdata = groupdata_tag.get_group((tag))
    plotdata = plotdata.drop(['scan_x', 'scan_y','qc_stage',
                              'image_path','scan_num','tags'],axis=1)
  
    groupdata_tagSN = df.groupby(['tags', 'serial_number'])
    means = groupdata_tagSN['scan_z'].mean(numeric_only=True)
    means_jig_s = means.loc['Jig']
    
    means_jig = means_jig_s.to_frame('mean_Jigz')
    means_jig.reset_index(inplace=True)
    means_jig = means_jig.rename(columns={'index':'serial_number'})

    plotdata.loc[:, 'residual_z'] = plotdata.apply(calcResidual, axis=1)
    plotdata = plotdata.drop('scan_z',axis = 1)
    
    means_jig['flag'] = means_jig['mean_Jigz'].apply(lambda x: 'normal' if x > threshold else 'Cell')
   
    flags = means_jig.drop('mean_Jigz',axis=1)
    plotdata = plotdata.merge(flags)
    plotdata = plotdata.rename(columns={'residual_z':'scan_z'})
    normalDF = plotdata.groupby('flag').get_group('normal')
    CellDF = plotdata.groupby('flag').get_group('Cell')
    
    # print(normalDF)
    # print(CellDF)
    
    return normalDF, CellDF

def devidePlot(tag, df, args):
    th = 7.6
    devideData = exTagAndDevideCell(tag,df, th)

    normaldata = makeDictionary(devideData[0])    
    Celldata = makeDictionary(devideData[1])

    normalFn = f'scan_z_{tag}_normal_MODULE'  # file name
    CellFn = f'scan_z_{tag}_Cell_MODULE'      # file name

    def twoplot(data, fn):
        dataList = data[1]
        dataDict = data[0]
        # exclude data
        exList = [i for i in dataList if i < 9]
    
        mean = np.mean(exList)
        require = [round(mean-0.05, 3), round(mean+0.05, 3)]
        minmax = [round(mean-0.20, 3), round(mean+0.20, 3)]
        numberRange = [1000,1200]
    
        print('dataDict length : ', len(dataDict))
        print('dataList length : ', len(dataList))
    
        badSN, summary = makeImages.getBadSN(dataDict, exList, require)
        
        #makeImages.graph(dataDict, require, numberRange, 'mm', fn)
        makeImages.hist(dataDict, require, 0.005, minmax, 'mm', fn)
        return badSN, summary

    badSN_n, summary_n = twoplot(normaldata, normalFn)
    badSN_c, summary_c = twoplot(Celldata, CellFn)

    return summary_n, summary_c
        
def plot(tag, df, args):
    module = args.module
    #exdata = exTagData(tag, scanData)
    exdata = JigResidual(tag, scanData)

    dataDict = exdata[0]
    dataList = exdata[1]

    filename = f'{tag}_{module}'
    #filename = 'test_Jig_PCB'
    if args.module == 'MODULE':
        numberRange = [1000,1200]
    elif args.module == 'PCB':
        numberRange = [1000,1200]
    elif args.module == 'BAREMODULE':
        numberRange = [2000, 2035]
       
    #require = calcSigma(dataList, 2)

    # exclude data
    exList = [i for i in dataList if i < 7.5] 
    mean = np.mean(exList)
    require = [round(mean-0.05, 3), round(mean+0.05, 3)]
    minmax = [round(mean-0.20,3), round(mean+0.20, 3)]
    #minmax = [4.8,8.5]
    
    print('dataDict length : ', len(dataDict))
    print('dataList length : ', len(dataList))
    
    badSN, summary = makeImages.getBadSN(dataDict, exList, require)
    
    # makeImages.graph(dataDict, require, numberRange, 'mm',
    #                  f'graph_scan_z_{filename}')
    makeImages.hist(dataDict, require, 0.005, minmax, 'mm',
                    f'scan_z_{filename}')
    
    if args.a:
        return badSN, summary
    else:
        return 
    
def run(args, scanData, analysisData):    
    if args.module == 'MODULE':
        taglist = [
            'Jig', 'Pickup1', 'Pickup2', 'Pickup3', 'Pickup4',
            'FmarkTR', 'FmarkBR', 'FmarkBL', 'FmarkTL',
            'AsicFmarkTR', 'AsicFmarkBR', 'AsicFmarkBL', 'AsicFmarkTL',
            'HVCapacitor', 'Connector',
            'AsicR', 'SensorB', 'AsicL','SensorT',
            'FlexL', 'FlexT', 'FlexR', 'FlexB']
    elif args.module == 'PCB':
        taglist = [
            'Jig', 'HoleTL', 'SlotBR',
            'Pickup1', 'Pickup2', 'Pickup3', 'Pickup4',
            'FmarkTL', 'FmarkBL', 'FmarkBR', 'FmarkTR',
            'HVCapacitor', 'Connector',
            'FlexB','FlexT', 'FlexL', 'FlexR'
        ]
    elif args.module == 'BAREMODULE':
        taglist = [
            'Jig',
            'AsicT', 'AsicB',
            'SensorL', 'SensorB', 'SensorR', 'SensorT',
            'SensorZ'
        ]
        
    if args.tag:  # tag choice
        #print(scanData['tags'].unique())
        if args.module == 'MODULE':
            devidePlot(args.tag, scanData, args)
        else:
            plot(args.tag, scanData, args)
    elif args.a:
        summaryAll = pd.DataFrame(index=['std','mean','min','max','quantity','req_min','req_max','bad_ratio'])
        print(summaryAll)
        # badDF = pd.DataFrame(columns=['serial_number'])
        # badDF.set_index('serial_number', inplace=True)
        for tag in taglist:
            #plot1(tag, scanData, args.module)
            print(tag)
            if args.module == 'MODULE':
                summary_n, summary_c = devidePlot(tag, scanData, args)
                summary_n = summary_n.rename(columns={0:tag+'_normal'})
                summary_c = summary_c.rename(columns={0:tag+'_cell'})
                print(summary_n)
                print(summary_c)
                summaryAll = pd.concat([summaryAll,summary_n,summary_c],axis=1)
            else:
                badSN, summary = plot(tag, scanData, args)
                badSN = badSN.rename(columns={'data':tag})
                summary = summary.rename(columns={0:tag})
                print(summary)
                summaryAll = pd.concat([summaryAll,summary],axis=1)
                #badSN.to_csv(f'./zdata/badSN_{args.module}_{tag}.csv')
                # badSN.set_index('serial_number', inplace=True)
                # badDF = pd.merge(badDF, badSN, left_index=True, right_index=True,
                #                  how='outer')
                # badDF = pd.merge(badDF, badSN, how='outer')
                # badDF.set_index(['serial_number',
                #                  badDF.groupby('serial_number').cumcount()],
                #                 inplace=True)
                # badDF = badDF.drop_duplicates(subset='serial_number')
                # badDF = pd.concat([badDF, badSN], axis=1)
               
        print('finish')
        print(summaryAll)
        summaryAll.to_csv(f'./zdata/summaryAll_{args.module}.csv')
        
        # print(badDF)
        # badDF.to_csv(f'./zdata/badSN_{args.module}.csv')
        # print('save bad SN data > work/zdata/badSN_****.csv')

    elif args.stat:
        summary(scanData, taglist)
        
    elif args.pickup:
        plot4(scanData)
    elif args.capcon:
        plot2(scanData)
    else:
        print('no argument! type -h or --help')    

if __name__ == '__main__':
    t1 = time.time()
    args = parseArg()
    
    # assign read file path 
    if args.module == 'MODULE':
        with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
            scanData = pickle.load(fin)
        with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
            analysisData = pickle.load(fin)
    elif args.module == 'PCB':
        with open(f'data/PCB_ScanData.pkl', 'rb') as fin:
            scanData = pickle.load(fin)
        with open(f'data/PCB_AnalysisData.pkl', 'rb') as fin:
            analysisData = pickle.load(fin)
    elif args.module == 'BAREMODULE':
        with open(f'data/BAREMODULE_ScanData.pkl', 'rb') as fin:
            scanData = pickle.load(fin)
        with open(f'data/BAREMODULE_AnalysisData.pkl', 'rb') as fin:
            analysisData = pickle.load(fin)
        
    run(args, scanData, analysisData)    

    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
