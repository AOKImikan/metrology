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
import matplotlib.pyplot as plt

def hist4(df):
    fig = plt.figure(figsize=(10,9))
    axes = fig.subplots(2,2,sharex='col',sharey='all')
    axes[0,0].annotate(f'$\sigma={df["range_T"].std():.5f}$',
                       xy=(0.6, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0,0].annotate(f'entries={df["range_T"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
    axes[0,0].annotate(f'mean={df["range_T"].mean():.4g}',
                       xy=(0.6, 0.8), xycoords='axes fraction', fontsize=15)
   
    axes[1,0].annotate(f'$\sigma={df["range_B"].std():.5f}$',
                       xy=(0.6, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1,0].annotate(f'entries={df["range_B"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
    axes[1,0].annotate(f'mean={df["range_B"].mean():.4g}',
                       xy=(0.6, 0.8), xycoords='axes fraction', fontsize=15)
   
    axes[0,1].annotate(f'$\sigma={df["range_L"].std():.5f}$',
                       xy=(0.6, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0,1].annotate(f'entries={df["range_L"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
    axes[0,1].annotate(f'mean={df["range_L"].mean():.4g}',
                       xy=(0.6, 0.8), xycoords='axes fraction', fontsize=15)

    axes[1,1].annotate(f'$\sigma={df["range_R"].std():.5f}$',
                       xy=(0.6, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1,1].annotate(f'entries={df["range_R"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
    axes[1,1].annotate(f'mean={df["range_R"].mean():.4g}',
                       xy=(0.6, 0.8), xycoords='axes fraction', fontsize=15)
    
    axes[0,0].set_title('range_T',fontsize=16)
    axes[1,0].set_title('range_B',fontsize=16)
    axes[0,1].set_title('range_L',fontsize=16)
    axes[1,1].set_title('range_R',fontsize=16)
  #  axes.set_xticks(labelsize=16)

    axes[0,0].hist(df['range_T'], bins=10, alpha=1, histtype="stepfilled",edgecolor='black')
    axes[1,0].hist(df['range_B'], bins=10, alpha=1, histtype="stepfilled",edgecolor='black')
    axes[0,1].hist(df['range_L'], bins=10, alpha=1, histtype="stepfilled",edgecolor='black')
    axes[1,1].hist(df['range_R'], bins=10, alpha=1, histtype="stepfilled",edgecolor='black')
    # set hist style
    axes[0,0].tick_params(labelsize=16)
    axes[0,1].tick_params(labelsize=16)
    axes[1,0].tick_params(labelsize=16)
    axes[1,1].tick_params(labelsize=16)
    plt.savefig(f'resultsHist/AsicFmark_range_hist.jpg')  #save as jpeg
    plt.show()
    
def hist2(df):
    fig = plt.figure(figsize=(10,5))
    axes = fig.subplots(1,2,sharex='col',sharey='all')
    axes[0].annotate(f'$\sigma={df["angle_TR"].std():.5f}$',
                       xy=(0.1, 0.9), xycoords='axes fraction', fontsize=15)
    axes[0].annotate(f'entries={df["angle_TR"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
    axes[0].annotate(f'mean={df["angle_TR"].mean():.4g}',
                       xy=(0.1, 0.8), xycoords='axes fraction', fontsize=15)
   
    axes[1].annotate(f'$\sigma={df["angle_BL"].std():.5f}$',
                       xy=(0.6, 0.9), xycoords='axes fraction', fontsize=15)
    axes[1].annotate(f'entries={df["angle_BL"].count()}',
                       xy=(0.01, 1.01), xycoords='axes fraction', fontsize=15)
    axes[1].annotate(f'mean={df["angle_BL"].mean():.4g}',
                       xy=(0.6, 0.8), xycoords='axes fraction', fontsize=15)

    axes[0].set_title('angle_TR',fontsize=16)
    axes[1].set_title('angle_BL',fontsize=16)
  #  axes.set_xticks(labelsize=16)

    axes[0].hist(df['angle_TR'], bins=10, alpha=1, histtype="stepfilled",edgecolor='black')

    axes[1].hist(df['angle_BL'], bins=10, alpha=1, histtype="stepfilled",edgecolor='black')

    # set hist style
    axes[0].tick_params(labelsize=16)
    axes[1].tick_params(labelsize=16)
    plt.savefig(f'resultsHist/AsicFmark_angle_hist.jpg')  #save as jpeg
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

        taglist = ['AsicFmarkTL', 'AsicFmarkTR', 'AsicFmarkBL', 'AsicFmarkBR']
        TL = coordinate(exdf, 'AsicFmarkTL')
        TR = coordinate(exdf, 'AsicFmarkTR')
        BL = coordinate(exdf, 'AsicFmarkBL')
        BR = coordinate(exdf, 'AsicFmarkBR')
        
        # calculate distances 
        TLTR = calculateDistance(exdf, 'AsicFmarkTL','AsicFmarkTR')
        TRBR = calculateDistance(exdf, 'AsicFmarkTR','AsicFmarkBR')
        BLBR = calculateDistance(exdf, 'AsicFmarkBL','AsicFmarkBR')
        TLBL = calculateDistance(exdf, 'AsicFmarkTL','AsicFmarkBL')
        # calculate angles
        angleBL = calculateAngle(exdf, 'AsicFmarkTL','AsicFmarkBL','AsicFmarkBR')
        angleTR = calculateAngle(exdf, 'AsicFmarkTL','AsicFmarkTR','AsicFmarkBR')

        # draw fmarks
        drawOval(self,x0,y0,TL[0],TL[1],5,"#ff7f00")
        drawOval(self,x0,y0,TR[0],TR[1],5,"#ff7f00")
        drawOval(self,x0,y0,BL[0],BL[1],5,"#ff7f00")
        drawOval(self,x0,y0,BR[0],BR[1],5,"#ff7f00")
        # draw line connectiong AsicFmarks
        drawLine(self,x0,y0,TL,TR,"#00a0a0")  
        drawLine(self,x0,y0,TL,BL,"#00a0a0")
        drawLine(self,x0,y0,TR,BR,"#00a0a0")
        drawLine(self,x0,y0,BL,BR,"#00a0a0")
        
        # write distance and angle on canvas
        canvas.create_text(350,130,text=f'{TLTR:.4g}',fill="#00a0a0",
                           font=("",16))  # TL to TR
        canvas.create_text(350,760,text=f'{BLBR:.4g}',fill="#00a0a0",
                           font=("",16))  # BL to BR
        canvas.create_text(120,350,text=f'{TLBL:.4g}',angle=90,
                           fill="#00a0a0",font=("",16))  # TL to BL
        canvas.create_text(780,350,text=f'{TRBR:.4g}',angle=90,
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
 
def valSquare(df):
    listT,listB,listL,listR = [],[],[],[]
    listBL,listTR = [],[]
    listSN = []
    # group analysis data by tags
    grouptag_ana = df.groupby(['serial_number'])
    snList = df['serial_number'].unique()
    print(df['tags'].unique())
    for sn in snList:
        exdf = grouptag_ana.get_group((sn))
        listSN.append(sn)
        listT.append(calculateDistance(exdf, 'AsicFmarkTL','AsicFmarkTR'))
        listR.append(calculateDistance(exdf, 'AsicFmarkTR','AsicFmarkBR'))
        listB.append(calculateDistance(exdf, 'AsicFmarkBL','AsicFmarkBR'))
        listL.append(calculateDistance(exdf, 'AsicFmarkTL','AsicFmarkBL'))
        listBL.append(calculateAngle(exdf, 'AsicFmarkTL','AsicFmarkBL','AsicFmarkBR'))
        listTR.append(calculateAngle(exdf, 'AsicFmarkTL','AsicFmarkTR','AsicFmarkBR'))
    df = pd.DataFrame()
    df['serial_num']=listSN
    df['range_T']=listT
    df['range_B']=listB
    df['range_L']=listL
    df['range_R']=listR
    df['angle_BL']=listBL
    df['angle_TR']=listTR

    df.to_csv('data/AsicFmarkRangeAndAngle.csv')
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
        root.title(f'analyze Asic fmark validation {sn}')
        extract_ana = grouptag_ana.get_group((sn))
        canvas = window.buildGui(extract_ana)
        #saveCanvas()

    return window         

if __name__ == '__main__':
    #open data as dataframe
    with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
        scanData = pickle.load(fin)
    with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
        analysisData = pickle.load(fin)

    # calculate range and angle
    # and save csv 
    result = valSquare(analysisData)
    hist4(result)
    
    # draw canvas
    # but it can't save 
    #window = createWindow(analysisData)
    #window.root.mainloop()
