#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
import pmm

class MainWindow(ttk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def buildGui(self,dic):
        def drawLineX(self,x0,y0,val,w,color):
            line = x0/2 + val*10
            canvas.create_line(line, y0/2+w, line, y0/2-w, width=2, fill=color)
        def drawLineY(self,x0,y0,val,w,color):
            line = y0/2 - val*10
            canvas.create_line(x0/2-w, line, x0/2+w, line, width=2, fill=color)
        def drawOval(self,x0,y0,valx,valy,r,color):
            x=x0/2+valx*10
            y=y0/2-valy*10
            canvas.create_oval(x-r,y-r,x+r,y+r, fill=color)
        def drawSquare(self):
            canvas.create_oval(x0-r, y0-r, x0+r, y0+r, fill='red')
   
            
        x0, y0 = 600, 600
        r = 10
        canvas = tk.Canvas(self, width=x0, height=y0,bg='white',bd=10,relief='flat')
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.create_line(x0/2, 20, x0/2, y0,width=2,arrow="first")
        canvas.create_line(0, y0/2, x0-20, y0/2,width=2,arrow="last")
        for k, v in dic.items():
            AsicL = v['AsicL'].get('value')
            AsicR = v['AsicR'].get('value')
            SensorT = v['SensorT'].get('value')
            SensorB = v['SensorB'].get('value')
            FlexL = v['FlexL'].get('value')
            FlexR = v['FlexR'].get('value')
            FlexT = v['FlexT'].get('value')
            FlexB = v['FlexB'].get('value')
            FmarkTR = v['FmarkTR_0_point']
            FmarkTL = v['FmarkTL_0_point']
            AsicFmarkTR = v['AsicFmarkTR_0_point']
            AsicFmarkTL = v['AsicFmarkTL_0_point']
            FmarkBR = v['FmarkBR_0_point']
            FmarkBL = v['FmarkBL_0_point']
            AsicFmarkBR = v['AsicFmarkBR_0_point']
            AsicFmarkBL = v['AsicFmarkBL_0_point']
        
        drawLineX(self,x0,y0,AsicL,150,'#ff0000')
        drawLineX(self,x0,y0,AsicR,150,"red")
        drawLineX(self,x0,y0,FlexL,200,"blue")
        drawLineX(self,x0,y0,FlexR,200,"blue")
        drawLineY(self,x0,y0,SensorT,150,"red")
        drawLineY(self,x0,y0,SensorB,150,"red")
        drawLineY(self,x0,y0,FlexT,200,"blue")
        drawLineY(self,x0,y0,FlexB,200,"blue")
        drawOval(self,x0,y0,FmarkTR.position[0],FmarkTR.position[1],5,"#ff7f00")
        drawOval(self,x0,y0,FmarkTL.position[0],FmarkTL.position[1],5,"#ff7f00")
        drawOval(self,x0,y0,AsicFmarkTR.position[0],AsicFmarkTR.position[1],5,"green")
        drawOval(self,x0,y0,AsicFmarkTL.position[0],AsicFmarkTL.position[1],5,"green")
        drawOval(self,x0,y0,FmarkBR.position[0],FmarkBR.position[1],5,"#ff7f00")
        drawOval(self,x0,y0,FmarkBL.position[0],FmarkBL.position[1],5,"#ff7f00")
        drawOval(self,x0,y0,AsicFmarkBR.position[0],AsicFmarkBR.position[1],5,"green")
        drawOval(self,x0,y0,AsicFmarkBL.position[0],AsicFmarkBL.position[1],5,"green")
               
def createWindow(dic):
    root = tk.Tk()
    root.geometry('600x600')
    root.title('Scan point validation')
    window = MainWindow(root)
    canvas = window.buildGui(dic)
    #window.drawLineX(canvas,300)
    return window

def readData(dn):
    appdata = None
    data = {}
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
        config = appdata.config
        print('Pattern analysis output data')
        for k,v in patternAnalysis.outData.items():
            data[k] = v
            #print(f'  {k}: {v}\n')
        print('Size analysis output data')
        for k,v in sizeAnalysis.outData.items():
            data[k] = v
            #print(f'  {k}: {v}')
    return data

def extractSN(dn):
    words = dn.split('/')
    return words[9]

def processData(data):
    for k, v in data.items():
        #
        #
        a=v['FmarkBL_0_x']
        for k2, v2 in a.items():
            print(f'{k2} : {v2} \n')
        print(type(a))
        print(dir(a))
        print(f'SN = {k}')
         
def run(dnames):
    data = {}
    for dn in dnames:
        x = readData(dn)
        sn = extractSN(dn)
        data[sn] = x
        #processData(data)
    return data

if __name__ == '__main__':
    dnames = [
        '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22110427/MODULE_ASSEMBLY/001'
        ]
    dic = run(dnames)
    #window = createWindow(dic)
    #window.root.mainloop()
    
