#!/usr/bin/env python3
import os
import pickle
import tkinter as tk
from tkinter import ttk
import argparse
import pmm
import datapath

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', help='kinds of module(p=PCB,b=BARE,m=ASSEMBLEDMODULE)')
    parser.add_argument('sn', help='serialnumber')
    return parser.parse_args()

class MainWindow(ttk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def drawLineX(self,canvas,x0,y0,val,w,color):
        line = x0/2 + val*15
        canvas.create_line(line, y0/2+w, line, y0/2-w, width=2, fill=color)
    def drawLineY(self,canvas,x0,y0,val,w,color):
        line = y0/2 - val*15
        canvas.create_line(x0/2-w, line, x0/2+w, line, width=2, fill=color)
    def drawOval(self,canvas,x0,y0,valx,valy,r,color):
        x=x0/2+valx*15
        y=y0/2-valy*15
        canvas.create_oval(x-r,y-r,x+r,y+r, fill=color)
    def drawSquare(self,canvas,p,x0,y0,valx,valy,dx,dy,color):
        x=x0/2+valx*15
        y=y0/2-valy*15
        canvas.create_rectangle(x-dx*7.5, y-dy*7.5, x+dx*7.5, y+dy*7.5,width=1,fill=color)
        #canvas.create_text(x,y,text=p,font=(30))
   
    def buildGuiModule(self,dic):    
        x0, y0 = 900, 900
        r = 10
        canvas = tk.Canvas(self, width=x0, height=y0,bg='white',bd=10,relief='flat')
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.create_line(x0/2, 20, x0/2, y0,width=2,arrow="first")
        canvas.create_line(0, y0/2, x0-20, y0/2,width=2,arrow="last")
        
        for k,v in dic.items():
            SN = k
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
            FmarkTR = v['FmarkTR_0_point']
            FmarkTL = v['FmarkTL_0_point']
            AsicFmarkTR = v['AsicFmarkTR_0_point']
            AsicFmarkTL = v['AsicFmarkTL_0_point']
            FmarkBR = v['FmarkBR_0_point']
            FmarkBL = v['FmarkBL_0_point']
            AsicFmarkBR = v['AsicFmarkBR_0_point']
            AsicFmarkBL = v['AsicFmarkBL_0_point']
            point = v['scanPoint']

        self.drawLineX(canvas,x0,y0,AsicL,150,'#ff0000')
        self.drawLineX(canvas,x0,y0,AsicR,150,"red")
        self.drawLineX(canvas,x0,y0,FlexL,200,"blue")
        self.drawLineX(canvas,x0,y0,FlexR,200,"blue")
        self.drawLineY(canvas,x0,y0,SensorT,150,"red")
        self.drawLineY(canvas,x0,y0,SensorB,150,"red")
        self.drawLineY(canvas,x0,y0,FlexT,200,"blue")
        self.drawLineY(canvas,x0,y0,FlexB,200,"blue")
        self.drawOval(canvas,x0,y0,FmarkTR.position[0],FmarkTR.position[1],5,"#ff7f00")
        self.drawOval(canvas,x0,y0,FmarkTL.position[0],FmarkTL.position[1],5,"#ff7f00")
        self.drawOval(canvas,x0,y0,AsicFmarkTR.position[0],AsicFmarkTR.position[1],5,"#ff0000")
        self.drawOval(canvas,x0,y0,AsicFmarkTL.position[0],AsicFmarkTL.position[1],5,"#ff0000")
        self.drawOval(canvas,x0,y0,FmarkBR.position[0],FmarkBR.position[1],5,"#ff7f00")
        self.drawOval(canvas,x0,y0,FmarkBL.position[0],FmarkBL.position[1],5,"#ff7f00")
        self.drawOval(canvas,x0,y0,AsicFmarkBR.position[0],AsicFmarkBR.position[1],5,"#ff0000")
        self.drawOval(canvas,x0,y0,AsicFmarkBL.position[0],AsicFmarkBL.position[1],5,"#ff0000")
        
        i = 0
        while i < len(dic[SN]['scanPoint']):
            point = dic[SN]['scanPoint'][i]
            #print(point['x'],'  ',point['y'],'  ',  point['z'])
            px = point['x']
            py = point['y']
            self.drawSquare(canvas,i,x0,y0,px,py, 1.14, 0.76,"#9cffff")
            i += 1
        print('point = ',len(dic[SN]['scanPoint']))

    def buildGuiPCB(self,dic):    
        x0, y0 = 900, 900
        r = 10
        canvas = tk.Canvas(self, width=x0, height=y0,bg='white',bd=10,relief='flat')
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.create_line(x0/2, 20, x0/2, y0,width=2,arrow="first")
        canvas.create_line(0, y0/2, x0-20, y0/2,width=2,arrow="last")
        
        for k,v in dic.items():
            SN = k
            print(k,v)
            FlexL = v['FlexL'].get('value')
            FlexR = v['FlexR'].get('value')
            FlexT = v['FlexT'].get('value')
            FlexB = v['FlexB'].get('value')
            point = v['scanPoint']

        self.drawLineX(canvas,x0,y0,FlexL,300,"blue")
        self.drawLineX(canvas,x0,y0,FlexR,300,"blue")
        self.drawLineY(canvas,x0,y0,FlexT,300,"blue")
        self.drawLineY(canvas,x0,y0,FlexB,300,"blue")
        
        i = 0
        while i < len(dic[SN]['scanPoint']):
            point = dic[SN]['scanPoint'][i]
            #print(point['x'],'  ',point['y'],'  ',  point['z'])
            px = point['x']
            py = point['y']
            self.drawSquare(canvas,i,x0,y0,px,py, 1.2, 0.8,"#9cffff")
            i += 1
        print('point = ',len(dic[SN]['scanPoint']))

    def buildGuiCell(self,dic):    
        x0, y0 = 900, 900
        r = 10
        canvas = tk.Canvas(self, width=x0, height=y0,bg='white',bd=10,relief='flat')
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.create_line(x0/2, 20, x0/2, y0,width=2,arrow="first")
        canvas.create_line(0, y0/2, x0-20, y0/2,width=2,arrow="last")
        
        for k,v in dic.items():
            SN = k
            AsicL = v['AsicL'].get('value')
            AsicR = v['AsicR'].get('value')
            SensorT = v['SensorT'].get('value')
            SensorB = v['SensorB'].get('value')
            PGTL = v['PGTL'].get('value')
            PGTR = v['PGTR'].get('value')
            PGTT = v['PGTT'].get('value')
            PGTB = v['PGTB'].get('value')
            point = v['scanPoint']

        self.drawLineX(canvas,x0,y0,AsicL,190,'#ffd000')
        self.drawLineX(canvas,x0,y0,AsicR,190,"red")
        self.drawLineX(canvas,x0,y0,PGTL,250,"#00d0ff")
        self.drawLineX(canvas,x0,y0,PGTR,250,"blue")
        self.drawLineY(canvas,x0,y0,SensorT,190,"#ffd000")
        self.drawLineY(canvas,x0,y0,SensorB,190,"red")
        self.drawLineY(canvas,x0,y0,PGTT,250,"#00d0ff")
        self.drawLineY(canvas,x0,y0,PGTB,250,"blue")
             
        i = 0
        while i < len(dic[SN]['scanPoint']):
            point = dic[SN]['scanPoint'][i]
            #print(point['x'],'  ',point['y'],'  ',  point['z'])
            px = point['x']
            py = point['y']
            self.drawSquare(canvas,i,x0,y0,px,py, 1.14, 0.76,"#9cffff")
            i += 1
        print('point = ',len(dic[SN]['scanPoint']))
        
        
def createWindow(dic,args):
    root = tk.Tk()
    root.geometry('900x900')
    root.title('Scan point validation')
    window = MainWindow(root)
    if args.kind == 'p':
        canvas = window.buildGuiPCB(dic)
    elif args.kind == 'b':
        canvas = window.buildGuiBare(dic)
    elif args.kind == 'm':
        canvas = window.buildGuiModule(dic)
    elif args.kind == 'c':
        canvas = window.buildGuiCell(dic)
 
    #window.drawLineX(canvas,300)
    return window

def readData(args, dn):
    appdata = None
    data = {}
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        if args.kind == 'p':
            sp = appdata.getScanProcessor('ITkPixV1xFlex.Size')
        elif args.kind == 'b':
            sp = appdata.getScanProcessor('ITkPixV1xBareModule.Size')
        elif args.kind == 'm':
            sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
        elif args.kind == 'c':
            sp = appdata.getScanProcessor('ITkPixV1xModuleCellBack.Size')
     
        if sp is None:
            return None
        patternAnalysis = sp.analysisList[0]
        sizeAnalysis = sp.analysisList[1]
        for k,v in patternAnalysis.outData.items():
            data[k] = v
        for k,v in sizeAnalysis.outData.items():
            data[k] = v
    return data

def scanPoint(args, dn):
    appdata = None
    scanDict = {}
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        if args.kind == 'p':
            sp = appdata.getScanProcessor('ITkPixV1xFlex.Size')
        elif args.kind == 'b':
            sp = appdata.getScanProcessor('ITkPixV1xBareModule.Size')
        elif args.kind == 'm':
            sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
        elif args.kind == 'c':
            sp = appdata.getScanProcessor('ITkPixV1xModuleCellBack.Size')
       
        if sp is None:
            return None
        i = 0
        while i < len(sp.scanData.points):
            point = sp.scanData.points[i].data
            scanDict[i]={'x':point['x'],'y':point['y'],'z':point['z']}
            i += 1
    return scanDict

def extractSN(args, dn):
    words = dn.split('/')
    if args.kind == 'p':
        return words[8]
    elif args.kind =='b':
        return words[8]
    elif args.kind =='m':
        return words[7]
    elif args.kind =='c':
        return words[7]

def processData(data):
    for k,v in data.items():
        print(f'SN = {k}')
        print(f'{k}: {v}')        
         
def run(args, dnames):
    data = {}
    for dn in dnames:
        sn = extractSN(args,dn)
        if sn == args.sn:
            print(sn)
            x = readData(args,dn)
            y = scanPoint(args,dn)
            if not (x and y):
                return None
            x['scanPoint'] = y
            data[sn] = x
            #processData(data)

    return data

if __name__ == '__main__':
    args = parseArgs()
    if args.kind == 'p':
        dnames = datapath.getFilelistPCB('PCB_POPULATION')
    elif args.kind == 'b':
        dnames = datapath.getFilelistBare()
    elif args.kind == 'm':
        dnames = datapath.getFilelistModule()
        #dnames = ['/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM22601021/MODULE_ASSEMBLY/001']
    elif args.kind == 'c':
        dnames = ['/nfs/space3/itkpixel/Metrology/results/MODULE/20UPGM22601092/UNKNOWN/011']
    dic = run(args, dnames)
    if dic is None:
        print('cannot draw')
    else:
        window = createWindow(dic,args)
        window.root.mainloop()
    
