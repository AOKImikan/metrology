#!/usr/bin/env python3
import os
import pickle
import time
import argparse
import tkinter as tk
from tkinter import ttk
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import data_pcb

def drawplot(line, points, fileName='lineFit'):    
    # define matplotlib figure
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(1,1,1)
    fig.tight_layout(rect=[0.12, 0.06, 1, 0.94])
    
    # line parameters -> list 
    fitPars = line.p  # [p0, p1, p2]  p0+p1x+p2y=0

    # set points
    vx = np.array(list(map(lambda x: x[0], points) ) )
    vy = np.array(list(map(lambda x: x[1], points) ) )

    # add points
    ax.scatter(vx, vy, marker="o")

    n = len(points)
    v1 = np.array([1]*n)
    # Line: p0+p1*x+p2*y = 0
    X = np.c_[ v1, vx, vy]
    M = np.dot(X.T, X)
    xx = M[1][1] - M[1][0]*M[0][1]
    yy = M[2][2] - M[2][0]*M[0][2]
   
    # add line
    if xx > yy:  # y=ax+b
        x = np.linspace(-20,20,10)
        y = (-fitPars[0] - fitPars[1]*x)/fitPars[2]
        plt.text(0,-fitPars[0],f'{-fitPars[0]}')        
        
    else:  # x=ay+b
        y = np.linspace(-20,20,10)
        x = (-fitPars[0] - fitPars[2]*y)/fitPars[1]
        plt.text(-fitPars[0],0,f'{-fitPars[0]}')

    ax.plot(x,y)
    
    # set style
    plt.tick_params(labelsize=18)
    #ax.set_xlim(-22,22)
    #ax.set_ylim(-22,22)
    ax.set_title(f'{fileName}',fontsize=20)
    ax.set_xlabel(f'x [mm]',fontsize=18,loc='right') 
    ax.set_ylabel(f'y [mm]',fontsize=18,loc='top')

    # show hist
    plt.savefig(f'lineFit/{fileName}.jpg')  # save as jpeg
    plt.show()

