#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab
import numpy as np
import pandas as pd
import pmm
import re
import time
import argparse
import matplotlib.pyplot as plt
    
def hist(df, name, arg, AF):
    # define histgram name
    histname = name + '_' + arg

    binrange = 0.01

    # define matplotlib figure
    fig = plt.figure(figsize=(8,7))
    ax = fig.add_subplot(1,1,1)

    # paint required area
    #ax.axvspan(require[0], require[1], color='yellow', alpha=0.5)
      
    # fill data
    bins = np.arange(np.nanmin(df[histname].to_list()),np.nanmax(df[histname].to_list()), binrange)
    n = ax.hist(df[histname], bins=bins, alpha=1, histtype="stepfilled",edgecolor='black')

    # show text of required area
    #ax.text(require[0]-2*binrange, np.amax(n[0]), f'{require[0]}',
     #       color='#ff5d00',size=14)
    #ax.text(require[1]-5*binrange, np.amax(n[0]), f'{require[1]}',
     #       color='#ff5d00',size=14)

    # set hist style
    plt.tick_params(labelsize=18)
    ax.set_title(f'{AF} {name}_{arg}',fontsize=20)
    ax.set_xlabel('mm',fontsize=18,loc='right') 
    ax.set_ylabel(f'events/{binrange}mm',fontsize=18,loc='top')

    plt.savefig(f'resultsHist/validateSQ/{AF}_{histname}_hist.jpg')  #save as jpeg

    plt.show()

class MainWindow(ttk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def buildGui(self,exdf):
        def drawLine(self,x0,y0,r1,r2,color):
            x1 = x0/2 + r1[0]*15
            x2 = x0/2 + r2[0]*15
            y1 = y0/2 - r1[1]*15
            y2 = y0/2 - r2[1]*15
            canvas.create_line(x1,y1,x2,y2, width=2, fill=color)
        def drawLineX(self,x0,y0,val,w,color):
            line = x0/2 + val*15
            canvas.create_line(line, y0/2+w, line, y0/2-w, width=2, fill=color)
        def drawLineY(self,x0,y0,val,w,color):
            line = y0/2 - val*15
            canvas.create_line(x0/2-w, line, x0/2+w, line, width=2, fill=color)
        def drawOval(self,x0,y0,valx,valy,r,color):
            x=x0/2+valx*15
            y=y0/2-valy*15
            canvas.create_oval(x-r,y-r,x+r,y+r, fill=color)
        def drawSquare(self,p,x0,y0,valx,valy,dx,dy,color):
            x=x0/2+valx*15
            y=y0/2-valy*15
        
        x0, y0 = 900, 900
        canvas = tk.Canvas(self, width=x0, height=y0,bg='white',bd=10,relief='flat')
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.create_line(x0/2, 20, x0/2, y0,width=2,arrow="first")
        canvas.create_line(0, y0/2, x0-20, y0/2,width=2,arrow="last")

        taglist = ['FmarkTL', 'FmarkTR', 'FmarkBL', 'FmarkBR']
        TL = coordinate(exdf, 'FmarkTL')
        TR = coordinate(exdf, 'FmarkTR')
        BL = coordinate(exdf, 'FmarkBL')
        BR = coordinate(exdf, 'FmarkBR')
        
        # calculate distances 
        TLTR = calculateDistance(exdf, 'FmarkTL','FmarkTR')
        TRBR = calculateDistance(exdf, 'FmarkTR','FmarkBR')
        BLBR = calculateDistance(exdf, 'FmarkBL','FmarkBR')
        TLBL = calculateDistance(exdf, 'FmarkTL','FmarkBL')
        # calculate angles
        angleBL = calculateAngle(exdf, 'FmarkTL','FmarkBL','FmarkBR')
        angleTR = calculateAngle(exdf, 'FmarkTL','FmarkTR','FmarkBR')

        # draw fmarks
        drawOval(self,x0,y0,TL[0],TL[1],5,"#ff7f00")
        drawOval(self,x0,y0,TR[0],TR[1],5,"#ff7f00")
        drawOval(self,x0,y0,BL[0],BL[1],5,"#ff7f00")
        drawOval(self,x0,y0,BR[0],BR[1],5,"#ff7f00")
        # draw line connectiong Fmarks
        drawLine(self,x0,y0,TL,TR,"#00a0a0")  
        drawLine(self,x0,y0,TL,BL,"#00a0a0")
        drawLine(self,x0,y0,TR,BR,"#00a0a0")
        drawLine(self,x0,y0,BL,BR,"#00a0a0")
        
        # write distance and angle on canvas
        canvas.create_text(350,140,text=f'{TLTR:.4g}',fill="#00a0a0",
                           font=("",16))  # TL to TR
        canvas.create_text(350,750,text=f'{BLBR:.4g}',fill="#00a0a0",
                           font=("",16))  # BL to BR
        canvas.create_text(150,350,text=f'{TLBL:.4g}',angle=90,
                           fill="#00a0a0",font=("",16))  # TL to BL
        canvas.create_text(750,350,text=f'{TRBR:.4g}',angle=90,
                           fill="#00a0a0",font=("",16))  # TR to BR
        canvas.create_text(220,710,text=f'{angleBL:.4g}',font=("",16))  # TL-BL-BR
        canvas.create_text(680,180,text=f'{angleTR:.4g}',font=("",16))  # TL-TR-BR    
             
def coordinate(exdf,tagname):
    query = exdf.query(f'tags == "{tagname}"').index[0]
    x = exdf.loc[query,'detect_x']
    y = exdf.loc[query,'detect_y']
    return x,y

def calculateDistance(exdf, name1, name2):
    r1 = coordinate(exdf, name1)
    r2 = coordinate(exdf, name2)
    dx = r1[0]-r2[0]
    dy = r1[1]-r2[1]
    distance = np.sqrt(dx**2+dy**2)
    return distance

def calculateAngle(exdf, name1, name2, name3):
    r1 = np.array(coordinate(exdf, name1))
    r2 = np.array(coordinate(exdf, name2))
    r3 = np.array(coordinate(exdf, name3))
    r12 = r2 - r1
    r23 = r3 - r2
    costheta = np.dot(r12,r23)/(np.linalg.norm(r12)*np.linalg.norm(r23))
    radian= np.arccos(np.clip(costheta, -1.0, 1.0))
    angle = np.degrees(radian)
    return angle

def badSN(df):
    rows = ['Qty', 'min', 'max', 'mean', 'std', 'requirement min', 'requirement max']
    summary = pd.DataFrame(index=rows)
    ngSN = pd.DataFrame(columns=['serial_num'])
    
    names = ['range_T','range_B','range_L','range_R','angle_BL','angle_TR']
    for name in names:
        std = np.nanstd(df[name].to_list())    # get data value std deviation
        mean = np.nanmean(df[name].to_list())  # get data value mean
        minimum = np.nanmin(df[name].to_list())  # get data value min
        maximum = np.nanmax(df[name].to_list())  # get data value max
        quantity = df[name].count()
        if 'angle' in name:
            reqmin = 89.9
            reqmax = 90.1
        if 'range' in name:
            reqmin = mean - 2*std
            reqmax = mean + 2*std
            
        values = pd.DataFrame([quantity, minimum, maximum, mean, std, reqmin, reqmax],index=rows,columns=[name])
        summary = pd.concat([summary, values],axis=1)
    
        filterd_min = df[df[name] < reqmin]
        filterd_max = df[df[name] > reqmax]
        ex = pd.concat([filterd_min[['serial_num', name]],
                        filterd_max[['serial_num', name]]])
        ngSN = pd.merge(ngSN, ex, on='serial_num',how='outer')
    return summary, ngSN
 
def valSquare(df, AF):
    listT,listB,listL,listR = [],[],[],[]
    listBL,listTR = [],[]
    listSN = []
    # group analysis data by tags
    grouptag_ana = df.groupby(['serial_number'])
    snList = df['serial_number'].unique()    
    for sn in snList:
        exdf = grouptag_ana.get_group((sn))
        listSN.append(sn)
        listT.append(calculateDistance(exdf, f'{AF}TL',f'{AF}TR'))
        listR.append(calculateDistance(exdf, f'{AF}TR',f'{AF}BR'))
        listB.append(calculateDistance(exdf, f'{AF}BL',f'{AF}BR'))
        listL.append(calculateDistance(exdf, f'{AF}TL',f'{AF}BL'))
        listBL.append(calculateAngle(exdf, f'{AF}TL',f'{AF}BL',f'{AF}BR'))
        listTR.append(calculateAngle(exdf, f'{AF}TL',f'{AF}TR',f'{AF}BR'))
    df = pd.DataFrame()
    df['serial_num']=listSN
    df['range_T']=listT
    df['range_B']=listB
    df['range_L']=listL
    df['range_R']=listR
    df['angle_BL']=listBL
    df['angle_TR']=listTR

    badsnDF = badSN(df)
    
    badsnDF[0].to_csv(f'data/validateSQ/{AF}_RangeAndAngle_summary.csv')
    badsnDF[1].to_csv(f'data/validateSQ/{AF}_RangeAndAngle_badSN.csv')
    df.to_csv(f'data/validateSQ/{AF}_RangeAndAngle.csv')
    
    return df

def saveCanvas():
    x = root.winfo_x() + canvas.winfo_x()
    y = root.winfo_y() + canvas.winfo_y()
    x1 = x + canvas.winfo_width()
    y1 = y + canvas.winfo_height()
    image = ImageGrab.grab(bbox=(x,y,x1,y1))

    image.save("canvas/canvas.png")
    print('save as canvas.png')
    
def createWindow(df):
    root = tk.Tk()
    window = MainWindow(root)
    # group analysis data by tags
    grouptag_ana = df.groupby(['serial_number'])
    # get serial number list
    snList = df['serial_number'].unique()
    
    for sn in snList:
        root.geometry('900x900')
        root.title(f'analyze fmark validation {sn}')
        extract_ana = grouptag_ana.get_group((sn))
        canvas = window.buildGui(extract_ana)
        #saveCanvas()

    return window

def run(df, args):
    # calculate range and angle
    # and save csv
    if args.AF == 'F':
        resultDF = valSquare(analysisData,'Fmark')
        # make hist
        if args.ranges:
            hist(resultDF, 'range', args.ranges, 'Fmark')
        elif args.angles:
            hist(resultDF, 'angle', args.angles, 'Fmark')
        else:
            print('no command. -h or --help ')

    if args.AF == 'A':
        resultDF = valSquare(analysisData,'AsicFmark')
        # make hist
        if args.ranges:
            hist(resultDF, 'range', args.ranges, 'AsicFmark')
        elif args.angles:
            hist(resultDF, 'angle', args.angles, 'AsicFmark')
        else:
            print('no command. -h or --help ')

    # draw canvas
    # but it can't save 
    #window = createWindow(analysisData)
    #window.root.mainloop()
    
if __name__ == '__main__':
    t1 = time.time()  # get initial timestamp
    
    # make parser
    parser = argparse.ArgumentParser()

    # add argument
    parser.add_argument('AF', help='Asic or Flex?')
    parser.add_argument('-r','--ranges', help='range', choices=['T','B','L','R'])
    parser.add_argument('-a', '--angles', help='angle', choices=['TR','BL'])
    
    args = parser.parse_args()  # analyze arguments
        
    #open data as dataframe
    with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    # main
    run(analysisData, args)

    t2 = time.time()  # get final timestamp
    elapsed_time = t2-t1  # calculate run time
    print(f'run time : {elapsed_time}')  
