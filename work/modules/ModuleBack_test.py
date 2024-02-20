#!/usr/bin/env python3
import os
import pickle
import time
import argparse
import glob
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datapath
from pmm.model import *
from pmm.reader import *
from pmm.design import *
from pmm.prec import *
from pmm.workflow import *
from pmm.tools import *

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('--df', help='make analysis dataframe')
    args = parser.parse_args()  # analyze arguments
    return args

# data.pickle -> ScanProcessor
def LoadData(dn):
    sp = None
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModuleCellBack.Size')
    return sp

def commonAppend(commonslist,tags,commons,tag):
      commonslist[0].append(commons[0])    # serial number
      commonslist[1].append(commons[1])    # qc stage
      commonslist[2].append(commons[2])  # scan number
      tags.append(tag)     # tag
      
def heightDataCnvDataFrame(SN,qc,num,dn):
    # define list dor dataframe
    snlist, qclist, numlist = [],[],[]
    values, tags = [],[]
   
    # open pickle
    appdata = None
    sp = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModuleCellBack.Height')
    if sp:
        pass
    else:
        return None
    heightAnalysis = sp.analysisList[0]
    
    # pattern analysis result
    for k,v in heightAnalysis.outData.items():
        snlist.append(SN)
        qclist.append(qc)
        numlist.append(num)
        tags.append(k)
        values.append(v.get('value'))

    # make dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['tags']=tags
    df['values']=values
   
    return df
    
# analysis -> dataframe
def analyDataCnvDataFrame(SN,qc,num,dn):
    print(dn)
    # define list dor dataframe
    snlist, qclist, numlist = [],[],[]
    values, tags, vType = [],[],[]
    commons = [SN, qc, num]
    commonslist = [snlist, qclist, numlist]

    # open pickle
    sp =LoadData(dn)
    if sp:
        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
    else:
        return None
    
    ##repeat##
    for k,v in sizeAnalysis.outData.items():
        tag = k
        values.append(v.get('value'))
        vType.append('size')
        commonAppend(commonslist,tags,commons, tag)
        
    # pattern analysis result
    for k,v in patternAnalysis.outData.items():
        if('point'in k):
            # get tag (match for scan tag)
            key = k.split('_')
            tag = key[0]
            # add data to list
            if v is None:
                pass
            else:
                values.append(v.position[0])  # Fill detect x
                vType.append('detect_x')
                commonAppend(commonslist,tags,commons, tag)
                values.append(v.position[1])  # Fill detect y
                vType.append('detect_y')
                commonAppend(commonslist,tags,commons, tag)
                
        if('line'in k):
            # get tag (match for scan tag)
            key = k.split('_')
            tag = key[0]
            # add data to list
            if v is None:
                pass
            else:
                values.append(v.p[0])  # Fill line parameter0
                vType.append('line_p0')
                commonAppend(commonslist,tags,commons, tag)
                values.append(v.p[1])  # Fill line parameter1
                vType.append('line_p1')
                commonAppend(commonslist,tags,commons, tag)
                values.append(v.p[2])  # Fill line parameter2
                vType.append('line_p2')
                commonAppend(commonslist,tags,commons, tag)
                
    # make dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['tags']=tags
    df['valueType']=vType
    df['values']=values
    
    return df

# scanData -> dataframe
def scanPointCnvDataframe(SN,qc,num,dn):
    # define list for dataframe
    snlist, qclist, numlist = [],[],[]
    scanList_x ,scanList_y, scanList_z, scanList_tags,scanList_imPath = [],[],[],[],[]

    # open pickle
    sp = LoadData(dn)
    if sp is None:
        return None
    i = 0
    while i < len(sp.scanData.points):
        # add data to list
        snlist.append(SN)    # serial number
        qclist.append(qc)    # qc stage
        numlist.append(num)  # scan number
        
        # get scan point (center of image)
        point = sp.scanData.points[i]
        # add data to list
        scanList_x.append(point.get('x'))  # x 
        scanList_y.append(point.get('y'))  # y
        scanList_z.append(point.get('z'))  # z
        scanList_tags.append(point.get('tags')[0])      # tag
        scanList_imPath.append(point.get('imagePath'))  # image path
        i += 1  # repeat parameter
        
    # define dataframe with serial number
    df=pd.DataFrame({'serial_number':snlist})
    # add data to dataframe
    df['qc_stage']=qclist
    df['scan_num']=numlist
    df['scan_x']=scanList_x
    df['scan_y']=scanList_y
    df['scan_z']=scanList_z
    df['tags']=scanList_tags
    df['image_path']=scanList_imPath
    
    return df

# get serial number from directory path
def extractSN(dn):
    words = dn.split('/')
    sn = words[7]
    print('SN = ', sn)
    return sn

# get QC stage from directory path
def extractQcStage(dn):
    words = dn.split('/')
    qcstage = words[8]
    #print("qcStage=",qcstage)
    return qcstage

# get Metrology number from directory path
def extractMetrologyNum(dn):
    words = dn.split('/')
    num = words[9]
    return num

def CnvDF(dnames):
    # define the aimed dataframe
    scanDFs = pd.DataFrame()
    analyDFs = pd.DataFrame()
    heightDFs = pd.DataFrame()
    
    i = 0
    # repeat for each serial number
    for dn in dnames:
        # get serial number and qc stage
        sn = extractSN(dn)
        qcstage = extractQcStage(dn)
        number = extractMetrologyNum(dn)
        # convert from pickle to dataframe
        analydf = analyDataCnvDataFrame(sn,qcstage,number,dn)
        heightdf = heightDataCnvDataFrame(sn,qcstage,number,dn)        
        scandf = scanPointCnvDataframe(sn,qcstage,number,dn)

        # concat each serial numbers
        analyDFs = pd.concat([analyDFs,analydf],ignore_index=True)
        heightDFs = pd.concat([heightDFs,heightdf],ignore_index=True)
        scanDFs = pd.concat([scanDFs,scandf],ignore_index=True)
        i += 1
        #if i > 2:
        #    break

    print(scanDFs)
    print(analyDFs)
    print(heightDFs)
    # save the created data
    analyDFs.to_pickle("data/MODULEBACK_AnalysisData.pkl")
    scanDFs.to_pickle("data/MODULEBACK_ScanData.pkl")
    heightDFs.to_pickle("data/MODULEBACK_HeightData.pkl")
    analyDFs.to_csv("data/MODULEBACK_AnalysisData.csv")
    scanDFs.to_csv("data/MODULEBACK_ScanData.csv")
    heightDFs.to_csv("data/MODULEBACK_HeightData.csv")

    print("save as data/MODULEBACK_****Data")
#
def correctHeight(points, refPlane):
    fmt = '5.4f'
    points2 = []
    for p in points:
        z = roundF(refPlane.distance(p),fmt)
        points2.append(Point([p[0], p[1], z]) )
    return points2

def generateColors(num):
    base_colors = list(mcolors.TABLEAU_COLORS.values())
    num_base_colors = len(base_colors)
    colors = []
    for i in range(num):
        color = base_colors[i % num_base_colors]
        colors.append(color)
    print(colors)
    return colors

def scatter3D(points, marker_size=50):
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(projection='3d')
    num = 10
    #generated_colors = generateColors(num)
    f=0.7
    for p in points:
        x = p.position[0]
        y = p.position[1]
        z = p.position[2]
        if z > 1.0:
            print(x, y, z)
            continue
        if z < 0.6:
            print(x, y, z)
            continue
        print(x, y, z)
        ax.scatter(x,y,z, s=marker_size, color='#FF7700',alpha=f)
        f += 0.01
    #
    ax.set_xlabel(f'x [mm]',fontsize=18)
    ax.set_ylabel(f'y [mm]',fontsize=18) 
    ax.set_zlabel(f'Height [mm]',fontsize=18)

    plt.show()

def bar3D(points,bar_width=0.8):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    
    for p in points:
        x = p.position[0]
        y = p.position[1]
        z = p.position[2]
        ax.bar(x,y,z, width=bar_width,color='#FF7700',zdir='y',alpha=0.8)
    #
    plt.show()
    
def contour3D(points, l):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    x, y, z = [],[],[]
    for p in points:
        x.append(p.position[0])
        y.append(p.position[1])
        z.append(p.position[2])
    ax.contour(x,y,z, levels=l)
    #
    plt.show()

def devidePoints(points, xy):
    x1, y1, z1 = [],[],[]
    x2, y2, z2 = [],[],[]
    x3, y3, z3 = [],[],[]
    i = 0
    if xy =='x':
        for p in points:
            if i < 3:
                x1.append(p.position[0])        
                y1.append(p.position[1])
                z1.append(p.position[2])
            elif 2 < i < 6:
                x2.append(p.position[0])        
                y2.append(p.position[1])
                z2.append(p.position[2])
            elif 5 < i:
                x3.append(p.position[0])        
                y3.append(p.position[1])
                z3.append(p.position[2])
            i += 1
    if xy =='y':
        for p in points:
            if i%3 == 0:
                x1.append(p.position[0])        
                y1.append(p.position[1])
                z1.append(p.position[2])
            elif i%3 == 1:
                x2.append(p.position[0])        
                y2.append(p.position[1])
                z2.append(p.position[2])
            elif i%3 == 2:
                x3.append(p.position[0])        
                y3.append(p.position[1])
                z3.append(p.position[2])
            i += 1
        
    if xy == 'x':
        print(y1,y2,y3)
        labels = [f'y = {y1[0]}', f'y = {y2[0]}',f'y = {y3[0]}']
    elif xy =='y':
        print(x1,x2,x3)
        labels = [f'x = {x1[0]}', f'x = {x2[0]}',f'x = {x3[0]}']
        
    if xy == 'x':
        return labels, [x1, x2, x3],[z1,z2,z3]
    elif xy =='y':
        return labels, [y1, y2, y3],[z1,z2,z3]
    
def plot2D(points, xy, filename):
    dp = devidePoints(points, xy)
    fig = plt.figure(figsize=(8,7))
    fig.subplots_adjust(left=0.15)
    fig.subplots_adjust(bottom=0.1)
    ax = fig.add_subplot(1,1,1)

    
    labels = dp[0]
    xs = dp[1]
    ys = dp[2]

    ax.scatter(xs[0], ys[0], label=labels[0])
    ax.scatter(xs[1], ys[1], label=labels[1])
    ax.scatter(xs[2], ys[2], label=labels[2])
    #
    plt.legend()
    plt.tick_params(labelsize=18)
    if filename:
        ax.set_title(f'{filename}',fontsize=20)
    else:
        pass
    if xy == 'x':
        ax.set_xlabel(f'x[mm]',fontsize=18, loc='right') 
    if xy == 'y':
        ax.set_xlabel(f'y[mm]',fontsize=18, loc='right') 
    ax.set_ylabel(f'Height[mm]',fontsize=18, loc='top')

    #
    plt.legend()
    plt.tick_params(labelsize=18)
    if filename:
        ax.set_title(f'{filename}',fontsize=20)
    else:
        pass
    if xy == 'x':
        ax.set_xlabel(f'x[mm]',fontsize=18, loc='right') 
    if xy == 'y':
        ax.set_xlabel(f'y[mm]',fontsize=18, loc='right') 
    ax.set_ylabel(f'Height[mm]',fontsize=18, loc='top')

    # show hist
    if filename:
        plt.savefig(f'Cell/{filename}.jpg')  #save as jpeg
        logger.info(f'save as Cell/{filename}.jpg')
    else:
        pass
    plt.show()
    
def plot(points, filename='PGT_Z',minmax=None):
    fig = plt.figure(figsize=(8,7))
    fig.subplots_adjust(left=0.15)
    fig.subplots_adjust(bottom=0.1)
    ax = fig.add_subplot(1,1,1)
    if minmax:
        ax.set_ylim(minmax[0], minmax[1])
        
    #x,y=[],[]
    Xvalues = [[],[],[],[],[],[],[],[],[],[],[]]
    Zvalues = [[],[],[],[],[],[],[],[],[],[],[]]
    i = -1
    colors = ['#FF0000','#FF7000','#FFcc00','#0000ff','#0070ff',
              '#00bb00','#00bbbb','#FF5ead','#00ff00','#00c0c0','#c000c0']
    sortedPoints = sorted(points, key=lambda p:p.position[1])
    currentY = None
    for p in sortedPoints:
        x,y,z = p.position
        print(x, y, z)
        if z > 1.0:
            print('large Z!!',x,y,z)
            continue
        if y != currentY :
            i += 1
            #print(i)
            Xvalues[i].append(x)
            Zvalues[i].append(z)
            ax.scatter(x, z, label=f'y = {y}',color=colors[i])            
            currentY = y
        else:
            Xvalues[i].append(x)
            Zvalues[i].append(z)
            ax.scatter(x, z, color=colors[i])       
        #x.append(i)        
        #y.append(p.position[2])
    for ii in range(8):
        ax.plot(Xvalues[ii],Zvalues[ii],color=colors[ii],alpha=0.4)
    
    #
    plt.legend(loc='upper right')
    plt.tick_params(labelsize=18)
    if filename:
        ax.set_title(f'{filename}',fontsize=20)
    else:
        pass
    ax.set_xlabel(f'x [mm]',fontsize=18, loc='right') 
    ax.set_ylabel(f'Height [mm]',fontsize=18, loc='top')

    # show hist
    if filename:
        plt.savefig(f'Cell/{filename}.jpg')  #save as jpeg
        logger.info(f'save as Cell/{filename}.jpg')
    else:
        pass
    plt.show()

def angle(outData, tag1, tag2, hv):
    fmt = '5.4f'
    name1 = tag1 + '_line'
    name2 = tag2 + '_line'
    line1 = outData[name1]
    line2 = outData[name2]
    angleA = line1.angle(line2)
    angleA = angleA*180.0/math.pi
    angleA = roundF(angleA, fmt)
    if hv =='v':
        dir1, dir2 = [0.0, 1.0], [0.0, 1.0]
    elif hv == 'h':
        dir1, dir2 = [1.0, 0.0], [1.0, 0.0]
    dir1 = line1.direction()
    dir2 = line2.direction()    
    a, b = dir1[0], dir1[1]
    p, q = dir2[0], dir2[1]
    c = a*p + b*q   # dot produt
    s = -b*p + a*q  # cross product
    angleB = math.acos(c)*180.0/math.pi
    if s < 0.0: angleB *= -1.0
    angleB = roundF(angleB, fmt)

    return angleB

def lineInfo(patternAnalysis,sn):
    fmt = '5.5f'
    xlist, ylist = [],[]
    namelist, taglist= [],[]
    for k,v in patternAnalysis.outData.items():                
        if('line'in k):
            # get tag (match for scan tag)
            key = k.split('_')
            tag = key[0]
            # add data to list
            if v is None:
                pass
            else:
                lineDir = v.direction()
                theta = math.acos(lineDir[0])
                pi4 = math.pi/4
                if (pi4 < theta < pi4*3) or (pi4*5 < theta < pi4*7):  # tate
                    point = [roundF(v.xAtY(0.0),fmt), 0.0]
                else:  # yoko
                    point = [0.0, roundF(v.yAtX(0.0),fmt)]
                #values.append(v.p[0])  # Fill line parameter0
                
                print(f'{tag} point : ',point)
                xlist.append(point[0])
                ylist.append(point[1])
                namelist.append('point')
                taglist.append(tag)
                                
                lineDir[0] = roundF(lineDir[0], fmt)
                lineDir[1] = roundF(lineDir[1], fmt)
                xlist.append(lineDir[0])
                ylist.append(lineDir[1])
                namelist.append('direction')
                taglist.append(tag)
                print(f'{tag} direction : ',lineDir)
    df=pd.DataFrame({'tag':taglist})
    df['name'] = namelist
    df['x'] = xlist
    df['y'] = ylist
    #print(df)
    df.to_csv(f'data/lineanalysisData_{sn}.csv')
    
def analysis(dn):
    print(dn)
    sn = extractSN(dn)
    sp = LoadData(dn)
    if sp is None:
        print('None Data')
        return
    scanData = sp.scanData
    if sp:
        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
        outData = patternAnalysis.outData
    
    #print(f'angle L PGT, Asic : ',angle(outData,'PGTL','AsicL', 'v'))
    #print(f'angle R PGT, Asic : ',angle(outData,'PGTR','AsicR', 'v'))
    #print(f'angle T PGT, Sensor : ',angle(outData,'PGTT','SensorT', 'h'))
    #print(f'angle B PGT, Sensor : ',angle(outData,'PGTB','SensorB', 'h'))
    #print(scanData.allTags())
    PGTPoints = scanData.pointsWithTag('PGT')
    PGTedge1 = scanData.pointsWithTag('PGTL')
    PGTedge2 = scanData.pointsWithTag('PGTR')
    PGTedge3 = scanData.pointsWithTag('PGTT')
    PGTedge4 = scanData.pointsWithTag('PGTB')
    AsicPointsL = scanData.pointsWithTag('AsicL')
    AsicPointsR = scanData.pointsWithTag('AsicR')
    AsicPoints = AsicPointsL + AsicPointsR
    #print(AsicPoints)
    AsicPlane = fitPlane(AsicPoints)
    PGTPoints = correctHeight(PGTPoints, AsicPlane[0])
    PGTedge1 = correctHeight(PGTedge1, AsicPlane[0])
    PGTedge2 = correctHeight(PGTedge2, AsicPlane[0])
    PGTedge3 = correctHeight(PGTedge3, AsicPlane[0])
    PGTedge4 = correctHeight(PGTedge4, AsicPlane[0])
    
    ps = []
    for p in PGTPoints:
        ps.append(p)
    for p in PGTedge1:
        ps.append(p)
    for p in PGTedge2:
        ps.append(p)
    for p in PGTedge3:
        ps.append(p)
    for p in PGTedge4:
        ps.append(p)
    
    #lineInfo(patternAnalysis,sn)
    scatter3D(ps)
    #plot2D(PGTPoints, 'x', 'correctZ_plot_x')
    #plot2D(PGTPoints, 'y', 'correctZ_plot_y')
    #plot(ps, f'PGT_z_sortY_{sn}')# [0.680, 0.725])
    #contour3D(PGTPoints,10)
    #bar3D(PGTPoints, 0.8)

if __name__ == '__main__':
    t1 = time.time()
    args = parseArg()
    dnames = datapath.getFilelistModuleBack()
    
    print(f'counts of module : {len(dnames)}')    

    if args.df:
        CnvDF(dnames)
    else:
        for dn in dnames:
            analysis(dn)
    
    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
    
