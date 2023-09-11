#-----------------------------------------------------------------------
# pmm: fittools.py
#-----------------------------------------------------------------------
import os, sys
import argparse
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import linalg
from mpl_toolkits.mplot3d import axes3d
#import statistics
from scipy.stats import norm
import tkinter as tk
from PIL import Image, ImageTk

from .model import *
from .reader import *
from .view import *
from .gui import *
from .acommon import *
from .data2 import ImageNP, ScanData

class CircleFit:
    def __init__(self):
        self.outputDir = '.'
        pass

    def setOutputDir(self, dname):
        self.outputDir = dname
        
    def readLog(self, logname):
        imageXY = {}
        if os.path.exists(logname):
            re1 = re.compile('Photo at \(([\d+-.]+), ([\d+-.]+)\)')
            re2 = re.compile('file=(.+\.jpg)')
            f = open(logname, 'r')
            for line in f.readlines():
                if len(line)==0 or line[0]=='#': continue
                mg1 = re1.search(line)
                mg2 = re2.search(line)
                fname, x, y = '', -2.0E+6, -2.0E+6
                if mg1:
                    mm = 0.001
                    x, y = float(mg1.group(1))*mm, float(mg1.group(2))*mm
                if mg2:
                    fname = mg2.group(1)
                if fname!='' and x > -1.0E+6:
                    i = fname.rfind('\\')
                    fname = fname[i+1:]
                    imageXY[fname] = (x, y)
        return imageXY
    
    def decodeFileArg(self, fileInfo):
        words = fileInfo.split(',')
        if len(words)==3:
            fname = words[0]
            x = float(words[1])
            y = float(words[2])
            return (fname, x, y)
        else:
            return None
    
    def toGlobal(self, x, y, w, h, w0, BL):
        dw, dh = w0/w, w0/h
        c = int( (x - BL[0])/dw)
        r = int(h - ( (y - BL[1])/dh) )
        return (c, r)

    def toGlobal2(self, x, y, l, w, h, w0, BL):
        dw, dh = w0/w, w0/h
        c = int( (x - BL[0])/dw)
        r = int(h - ( (y - BL[1])/dh) )
        l2 = l/dw
        print('l=', l, ', dw=', dw, ' => ', l2)
        return (c, r, l2)

    def calcScale(self, w, h, xy):
        w0 = 15.0 # Real physical size
        #x0, y0 = -30.0, -30.0
        x0, y0 = -30.0, 15.0
        
        w1 = dx20*6000 # Physical size of the region in the image
        wp = 600
        hp = 400
        scale = w1/w0
        x, y = xy[0], xy[1]
    
        dw, dh = w0/w, w0/h
        x, y = xy
        c, r = self.toGlobal(x, y, w, h, w0, (x0, y0))
        #c = int( (x - x0)/dw)
        #r = int(h - ( (y - y0)/dh) )
        print('c, r = ', c, r)
        return (scale, c, r)


    def createCanvas(self, imageFiles, points, circle, imageXY):
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b'
        w, h = 600, 600
        w1 = w
        h1 = w*4000/6000.0
        
        root = tk.Tk()
        root.title('Module area')
        root.geometry('%dx%d' % (w, h))
        
        canvas = tk.Canvas(root, width=w, height=h, background='lightgreen')
        canvas.grid(row=1, column=1)
    
        print(imageFiles)
        print(imageXY)
        
        images = []
        for fn in imageFiles:
            fn1 = fn.replace('_p.png', '.jpg')
            scale, c, r = self.calcScale(w, h, imageXY[fn])
            print('Add image %s' % fn, imageXY[fn])
            img = Image.open(fn)
            img = img.resize( (int(scale*w1), int(scale*h1) ) )
            img = ImageTk.PhotoImage(img)
            images.append(img)
            canvas.create_image(c, r, image=img, anchor=tk.CENTER)
    
        a, b, r = circle
        a, b, r = self.toGlobal2(a, b, r, w=w, h=h, w0=15.0, BL=(-30.0, 15.0))
        canvas.create_oval(a-r, b-r, a+r, b+r, outline='blue', width=2)
        canvas.update()
        canvas.postscript(file="./plot/slot_%s_TL.ps"%figPrefix, colormode='color')
        
        figname = f'bigCircle'
        canvas.postscript(file=f'{figname}.ps', colormode='color')
        os.system(f'convert {figname}.ps {figname}.jpg')
        root.mainloop()
        return canvas
    
    def findEdge(self, img, wsum, tgap, thr1=50, thr2=100):
        #return cv2.Canny(img, thr1, thr2)
        output = {}
        points1 = locateEdgePoints1(img, 0, output, wsum=wsum, tgap=tgap)
        points2 = locateEdgePoints1(img, 1, output, wsum=wsum, tgap=tgap)
        if len(points1) > len(points2):
            points = points1
        else:
            points = points2
        return points
    
    def findCircle(self, points):
        figPrefix='JPFlex30_b_TL'    
        goodPoints1 = []
        goodPoints2 = []
        data1 = []
        data2 = []
        #thr1 = 0.12
        thr1 = 0.5
        thr2 = 0.05
        d1 = 0
        d2 = 0
        
        ###
        pars1 = self.findCircle1(points)
        for i, p in enumerate(points):
            d1_m = (self.distancePointToCircle(*pars1, p))
            d1 = abs(d1_m)
            #print('  Distance from circle to point[%d]=%7.4f' % (i, d1_m) )
            if d1 < thr1:
                goodPoints1.append(p)
                entry1 = d1_m
                data1.append(entry1)
    
        n1 = len(data1)
        #mean1 = statistics.mean(data1)
        #stdev1 = statistics.stdev(data1)
        #print('mean of distance1 = %f'%mean1)
        print('pars1')
        print(pars1)
    
        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(points):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
            vx = np.array(vx1)
            vy = np.array(vy1)
                    

        pars2 = self.findCircle2(goodPoints1)
        for i, p in enumerate(goodPoints1):
            d2_m = (self.distancePointToCircle(*pars2, p))
            d2 = abs(d2_m)
            print('  Distance from circle to goodpoint1[%d]=%7.4f' % (i, d2_m) )
            if d2 < thr2:
                goodPoints2.append(p)
                data2.append(d2_m)
    
        n2 = len(data2)
        #mean2 = statistics.mean(data2)
        #stdev2 = statistics.stdev(data2)
        #print('mean of distance2 = %f'%mean2)
        print('pars2')
        print(pars2)
    
        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(goodPoints1):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
            vx = np.array(vx1)
            vy = np.array(vy1)
        
        circle = tuple(pars2)
        return circle
    
    
    def findCircle1(self, points):
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
        pars1 = [xpos, ypos, 1.45]
        pars = [xpos, ypos, 1.45]
        f = [ 0.0, 0.0, 0.0]
        alpha = 0.001
        data = []
        print('Initial values: ', pars)
        
        for i in range(3):
            f[0] = -self.dCda(pars1[0], pars1[1], pars1[2], points)
            f[1] = -self.dCdb(pars1[0], pars1[1], pars1[2], points)
            f[2] = -self.dCdr(pars1[0], pars1[1], pars1[2], points)
            #print(f)
            fnorm = 0.0
            for k in range(3):
                fnorm += f[k]**2
                fnorm = math.sqrt(fnorm)
            for k in range(3):
                f[k] = f[k]/fnorm
            for k in range(3):
                pars[k] = pars1[k] + alpha*f[k]
                pars[0] = -27.0
                pars[1] = 27.0
                pars[2] = 1.45
                pars1 = pars
                circle = tuple(pars)
                
        print(f'parameters after findCircle1 {pars}')
        return pars
    
    
    def fitStep(self, n, alpha, pars1, points):
        pars, f = [0.0, 0.0, 0.0],  [0.0, 0.0, 0.0]
                        
        for i in range(n):
            f[0] = -self.dCda(pars1[0], pars1[1], pars1[2], points)
            f[1] = -self.dCdb(pars1[0], pars1[1], pars1[2], points)
            f[2] = -self.dCdr(pars1[0], pars1[1], pars1[2], points)
            print(f, len(points))
            fnorm = 0.0
            for k in range(3):
                fnorm += f[k]**2
                fnorm = math.sqrt(fnorm)
            for k in range(3):
                f[k] = f[k]/fnorm
            for k in range(3):
                pars[k] = pars1[k] + alpha*f[k]
            entry1 = pars[0]
            entry2 = pars[1]
            entry3 = pars[2]
            pars1 = pars
       
        return pars
    
    
    def findCircle2(self, points):
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b_TL'
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
        pars1 = [xpos, ypos, 1.5]
        f = [ 0.0, 0.0, 0.0]
            
        print('Initial values: ', pars1, ' N points', len(points))
    
        pars_1= self.fitStep(100, 0.01, pars1, points)
        pars= self.fitStep(100, 0.001, pars_1, points)
        print(f'In findCircle2 pars_1: {pars_1}')
        print(f'In findCircle2 pars: {pars}')
                
        circle = tuple(pars)
        return pars

    def showImage(self, wn, img, points, toShow=True, fout=None):
        img2 = img.copy()
        if points!=None:
            for p in points:
                col = int(p.x())
                row = int(p.y())
                cv2.circle(img2, (col, row), 100, color=(0,0,255), thickness=-1)
        if toShow:
            window = cv2.namedWindow(wn, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(wn, 600, 400)
            cv2.imshow(wn, img2)
            cv2.waitKey(0)
        if fout!=None and fout!='':
            cv2.imwrite(fout, img2)
            
    def extractPoints(self, fn, xy, wsum, tgap):
        img = None
        x, y = xy[0], xy[1]
        if os.path.exists(fn):
            print('Open image %s taken at (%6.3f, %6.3f)' % (fn, x, y) )
            img = cv2.imread(fn, cv2.IMREAD_COLOR)
            img0 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img1 = cv2.GaussianBlur(img0, (5, 5), 0) #11, 11
            points = self.findEdge(img1, wsum, tgap, 10, 15)
        else:
            print('Image path %s does not exist' % fpath)
            return
        
        print('N points: %d' % len(points))
        fn2 = os.path.basename(fn).replace('.jpg', '_p.png')
        self.showImage('Points', img, points, toShow=False, fout=fn2)
        return points
    
    def dCda(self, a, b, r, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            sum3 = 0.0
        for p in points:
            sum3 += (a-p.x())/math.sqrt( (a-p.x())**2 + (b-p.y())**2)
            c = n*a - xsum - r*sum3
        return c
    
    def dCdb(self, a, b, r, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            ysum += p.y()
            sum3 = 0.0
        for p in points:
            sum3 += (b-p.y())/math.sqrt( (a-p.x())**2 + (b-p.y())**2)
            c = n*b - ysum - r*sum3
        return c
    
    def dCdr(self, a, b, r, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        for p in points:
            sum1 += math.sqrt( (a-p.x())**2 + (b-p.y())**2)
            c = n*r - sum1
        return c
    
    def distancePointToCircle(self, a, b, r, point):
        d = (math.sqrt( (a-point.x())**2 + (b-point.y())**2) - r)
        return d

    def run(self, images):        
        bigImage = None
        circle = None
        points = []
        imageFiles = []
        imageXY = {}
    
        dir0 = os.getcwd()
        os.chdir(self.outputDir)

        for i, image in enumerate(images):
            fpath = image.filePath
            x, y = image.xyOffset[0], image.xyOffset[1]
            pointsLocal = self.extractPoints(fpath, (x, y), wsum=200, tgap=12) #tgap
            print(f'local points size: {len(pointsLocal)}')
            frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
            for p in pointsLocal:
                points.append(frame.toGlobal(p))
            fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
            imageFiles.append(fpath2)
            imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')
        circle = self.findCircle(points)

        canvas = self.createCanvas(imageFiles, points, circle, imageXY)
        figname = f'bigCircle'
        #bigImage = ImageNP(figname, os.path.join(os.getcwd(), f'figname.pdf'))        
        #bigImage = ImageNP(figname, os.path.join(moduleDir, figname+'.jpg'))
        bigImage = ImageNP(figname, os.path.join(os.getcwd(), figname+'.jpg'))
        os.chdir(dir0)
        
        return (bigImage, circle, points)


class SlotFit:
    def __init__(self):
        self.outputDir = '.'
        pass

    def setOutputDir(self, dname):
        self.outputDir = dname

    def decodeFileArg(self, fileInfo):
        words = fileInfo.split(',')
        if len(words)==3:
            fname = words[0]
            x = float(words[1])
            y = float(words[2])
            return (fname, x, y)
        else:
            return None

    def toGlobal2(self, x, y, cr, sl1, sl2, sl3, theta, w, h, w0, BL):
        dw, dh = w0/w, w0/h
        c = int( (x - BL[0])/dw)
        r = int(h - ( (y - BL[1])/dh) )
        l2 = cr/dw
        l3 = sl1/dw
        l4 = sl2/dw
        l5 = sl3/dw
        print('l2=', l2, ', dw=', dw, ' => ', l3)
        return (c, r, l2, l3, l4, l5)

    def calcScale(self, w, h, xy):
        w0 = 15.0 # Real physical size
        x0, y0 = 15.0, -30.0
        
        w1 = dx20*6000 # Physical size of the region in the image
        wp = 600
        hp = 400
        scale = w1/w0
        x, y = xy[0], xy[1]
        
        dw, dh = w0/w, w0/h
        x, y = xy
        c, r = CircleFit().toGlobal(x, y, w, h, w0, (x0, y0))

        print('c, r = ', c, r)
        return (scale, c, r)

    def createCanvas(self, imageFiles, points, circle, imageXY):
        #title=args.FlexNumber
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b_BR'
        w, h = 600, 600
        w1 = w
        h1 = w*4000/6000.0
        l3 = 0
        
        root = tk.Tk()
        root.title('Module area')
        root.geometry('%dx%d' % (w, h))
        
        canvas = tk.Canvas(root, width=w, height=h, background='lightgreen')
        canvas.grid(row=1, column=1)
        
        images = []
        for fn in imageFiles:
            fn1 = fn.replace('_p.png', '.jpg')
            scale, c, r = self.calcScale(w, h, imageXY[fn])
            print('Add image %s' % fn, imageXY[fn])
            img = Image.open(fn)
            img = img.resize( (int(scale*w1), int(scale*h1) ) )
            img = ImageTk.PhotoImage(img)
            images.append(img)
            canvas.create_image(c, r, image=img, anchor=tk.CENTER)

        a, b, r, l1, l2, theta = circle
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        a, b, r, l1, l2, l3 = self.toGlobal2(a, b, r, l1, l2, l3, theta=3*math.pi/4, w=w, h=h, w0=15.0, BL=(15.0, -30.0))
        
        canvas.create_oval(a-r-l2*math.cos(theta)/2, b-r+l2*math.sin(theta)/2, a+r-l2*math.cos(theta)/2, b+r+l2*math.sin(theta)/2, outline='blue', width=2)
        canvas.create_oval(a-r+l2*math.cos(theta)/2, b-r-l2*math.sin(theta)/2, a+r+l2*math.cos(theta)/2, b+r-l2*math.sin(theta)/2, outline='cyan', width=2)
        canvas.create_line(a-l1*math.cos(theta)/2+l3/2*math.sin(theta), b+l1*math.sin(theta)/2+l3/2*math.cos(theta), a+l1*math.cos(theta)/2+l3/2*math.sin(theta), b-l1*math.sin(theta)/2+l3/2*math.cos(theta), fill='green', width=2)
        canvas.create_line(a-l1*math.cos(theta)/2-l3/2*math.sin(theta), b+l1*math.sin(theta)/2-l3/2*math.cos(theta), a+l1*math.cos(theta)/2-l3/2*math.sin(theta), b-l1*math.sin(theta)/2-l3/2*math.cos(theta), fill='orange', width=2)
        
        canvas.update()
        canvas.postscript(file="./plot/slot_%s_BR.ps"%figPrefix, colormode='color')
        
        figname = f'bigSlot'
        canvas.postscript(file=f'{figname}.ps', colormode='color')
        os.system(f'convert {figname}.ps {figname}.jpg')
        root.mainloop()
        
        return images, circle

    
    def findCircle(self, points):
        #figPrefix=args.FlexNumber
        figPrefix='JPFlex30_b_BR'
        goodPoints1, goodPoints2, goodPoints3 = [], [], []
        data1, data2, data3 = [], [], []
        #thr1 = 0.22
        thr1 = 1.0
        thr2 = 0.80 #7
        thr3 = 0.5 #5
        d1, d2, d3 = 0, 0, 0
        
        ###
        pars1 = self.findCircle1(points)
        d1_dC1, d1_dC2, d1_dL1, d1_dL2 = [], [], [], []
        for i, p in enumerate(points):
            d1_m, pos1 = self.distancePointToCircle(*pars1, p)
            d1 = abs(d1_m)
            print(pos1)
            print('  Distance from circle to point[%d]=%7.4f' % (i, d1_m) )
            if d1 < thr1:
                goodPoints1.append(p)
            entry1 = d1_m
            if (pos1 == 'dC1'):
                d1_dC1.append(d1_m)
            elif (pos1 == 'dC2'):
                d1_dC2.append(d1_m)
            elif (pos1 == 'dL1'):
                d1_dL1.append(d1_m)
            else:
                d1_dL2.append(d1_m)
            data1.append(entry1)

        n1 = len(data1)
        #mean1 = statistics.mean(data1)
        #stdev1 = statistics.stdev(data1)
        #print('mean of distance1 = %f'%mean1)
        print('pars1')
        print(pars1)

        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(points):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
        vx = np.array(vx1)
        vy = np.array(vy1)

        ###
        pars2 = self.findCircle2(goodPoints1)
        d2_dC1, d2_dC2, d2_dL1, d2_dL2 = [], [], [], []
        
        for i, p in enumerate(goodPoints1):
            d2_m, pos2 = (self.distancePointToCircle(*pars2, p))
            d2 = abs(d2_m)
            print(pos2)
            print('  Distance from circle to goodpoint1[%d]=%7.4f' % (i, d2_m) )
            if d2 < thr2:
                goodPoints2.append(p)
            if (pos2 == 'dC1'):
                d2_dC1.append(d2_m)
            elif (pos2 == 'dC2'):
                d2_dC2.append(d2_m)
            elif (pos2 == 'dL1'):
                d2_dL1.append(d2_m)
            else:
                d2_dL2.append(d2_m)
            data2.append(d2_m)
            
        n2 = len(data2)
        #mean2 = statistics.mean(data2)
        #stdev2 = statistics.stdev(data2)
        #print('mean of distance2 = %f'%mean2)
        print('pars2')
        print(pars2)
        
        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(goodPoints1):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
        vx = np.array(vx1)
        vy = np.array(vy1)
    
        ###
        pars3 = self.findCircle2(goodPoints2)
        d3_dC1, d3_dC2, d3_dL1, d3_dL2 = [], [], [], []
    
        for i, p in enumerate(goodPoints2):
            d3_m, pos3 = self.distancePointToCircle(*pars3, p)
            d3 = abs(d3_m)
            print(pos3)
            print('  Distance from circle to goodpoint2[%d]=%7.4f' % (i, d3_m) )
            if d3 < thr3:
                goodPoints3.append(p)
            if (pos3 == 'dC1'):
                d3_dC1.append(d3_m)
            elif (pos3 == 'dC2'):
                d3_dC2.append(d3_m)
            elif (pos3 == 'dL1'):
                d3_dL1.append(d3_m)
            else:
                d3_dL2.append(d3_m)
            data3.append(d3_m)
    
        n3 = len(data3)
        #mean3 = statistics.mean(data3)
        #stdev3 = statistics.stdev(data3)
        #print('mean of distance3 = %f'%mean3)
        print('pars3')
        print(pars3)

        outliers = []
        vx1, vy1= [], []
        for i, p in enumerate(goodPoints2):
            if i in outliers: continue
            vx1.append(p[0])
            vy1.append(p[1])
        vx = np.array(vx1)
        vy = np.array(vy1)
          
        circle = tuple(pars3)
        return circle
    


    def findCircle1(self, points):
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
                
        pars1 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars2 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars3 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars4 = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        pars = [xpos, ypos, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars1 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars2 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars3 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars4 = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        #pars = [27.0, -27.0, 1.6, 1.0, 1.0, 3*math.pi/4]
        
        f = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        alpha1 = 0.001
        alpha2 = 0.0001
        print('Initial vaues: ', pars)

        for i in range(3):
            f[0] = -self.dC1da(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[1] = -self.dC1db(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[2] = -self.dC1dr(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[3] = 0
            f[4] = -self.dC1dl2(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[5] = -self.dC1dtheta(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            #print(f)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars1[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars1=pars
            
        for i in range(3):
            f[0] = -self.dC2da(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[1] = -self.dC2db(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[2] = -self.dC2dr(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[3] = 0
            f[4] = -self.dC2dl2(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[5] = -self.dC2dtheta(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars2[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars2=pars
               
        
        for i in range(3):
            f[0] = -self.dL1da(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[1] = -self.dL1db(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[2] = 0
            f[3] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[4] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[5] = -self.dL1dtheta(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars3[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars3=pars
        
        
        for i in range(3):
            f[0] = -self.dL2da(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[1] = -self.dL2db(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[2] = 0
            f[3] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[4] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[5] = -self.dL2dtheta(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars4[k] + alpha1*f[k]
                pars[0] = 27
                pars[1] = -27
                pars[2] = 1.55
                #pars[3] = 1.0
            pars4=pars

        circle = tuple(pars)
        return circle
        
    def fitStep(self, nstep, alpha1, alpha2, pars1, pars2, pars3, pars4, points):
        pars = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        f = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        dataC1, dataC2, dataL1, dataL2 = [], [], [], []
        
        for i in range(nstep):
            f[0] = -self.dC1da(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[1] = -self.dC1db(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[2] = -self.dC1dr(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[3] = 0
            f[4] = -self.dC1dl2(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            f[5] = -self.dC1dtheta(pars1[0], pars1[1], pars1[2], pars1[3], pars1[4], pars1[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars1[k] + alpha2*f[k]
                entryC1 = pars[2]
            dataC1.append(entryC1)
            pars1=pars
            
        for i in range(nstep):
            f[0] = -self.dC2da(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[1] = -self.dC2db(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[2] = -self.dC2dr(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[3] = 0
            f[4] = -self.dC2dl2(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            f[5] = -self.dC2dtheta(pars2[0], pars2[1], pars2[2], pars2[3], pars2[4], pars2[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars2[k] + alpha2*f[k]
                entryC2 = pars[2]
            dataC2.append(entryC2)
            pars2=pars
        
        for i in range(nstep):
            f[0] = -self.dL1da(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[1] = -self.dL1db(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[2] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[3] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[4] = -self.dL1dl3(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            f[5] = -self.dL1dtheta(pars3[0], pars3[1], pars3[2], pars3[3], pars3[4], pars3[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars3[k] + alpha2*f[k]
            pars3=pars
        
        
        for i in range(nstep):
            f[0] = -self.dL2da(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[1] = -self.dL2db(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[2] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[3] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[4] = -self.dL2dl3(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            f[5] = -self.dL2dtheta(pars4[0], pars4[1], pars4[2], pars4[3], pars4[4], pars4[5], points)
            fnorm = 0.0
            for k in range(6):
                fnorm += f[k]**2
            fnorm = math.sqrt(fnorm)
            for k in range(6):
                f[k] = f[k]/fnorm
            for k in range(6):
                pars[k] = pars4[k] + alpha2*f[k]
            pars4=pars

        circle = tuple(pars)
        return pars, circle

    def findCircle2(self, points):
        figPrefix='JPFlex30_b_BR'
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
                
        #pars1 = [27.0, -27.0, 1.58, 1.02, 1.02, 3*math.pi/4]
        pars1 = [xpos, ypos, 1.58, 1.02, 1.02, 3*math.pi/4]
        print('Initial values: ', pars1)
        
        pars_1, circle_1 = self.fitStep(100, 0.01, 0.0001, pars1, pars1, pars1, pars1, points)
        pars, circle = self.fitStep(100, 0.001, 0.0001, pars_1, pars_1, pars_1, pars_1, points)
        #pars, circle = fitStep(10, 0.001, 0.0001, pars1, pars1, pars1, pars1, points)
        
        return circle

    def dC1da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
        sum3 = 0.0
        for p in points:
            sum3 += (a-p.x()+(l2*math.cos(theta)/2))/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = n*a - xsum + n*l2*math.cos(theta)/2- r*sum3
        return c

    def dC1db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            ysum += p.y()
        sum3 = 0.0
        for p in points:
            sum3 += (b-p.y()+(l2*math.sin(theta)/2))/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = n*b - ysum + n*l2*math.sin(theta)/2 - r*sum3
        return c

    def dC1dr(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        for p in points:
            sum1 += math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = n*r - sum1
        return c

    def dC1dl2(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += ((a-p.x())*math.cos(theta)+(b-p.y())*math.sin(theta)+l2/2)/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = -xsum*math.cos(theta) + n*a*math.cos(theta) - ysum*math.sin(theta) + n*b*math.sin(theta) + n*l2/2 - r*sum1
        return c

    def dC1dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += (-(a-p.x())*math.sin(theta)*l2+(b-p.y())*math.cos(theta)*l2)/math.sqrt( (a-p.x()+(l2*math.cos(theta)/2))**2 + (b-p.y()+(l2*math.sin(theta)/2))**2)
        c = -n*l2*a*math.sin(theta) + l2*math.sin(theta)*xsum + n*l2*b*math.cos(theta) - l2*math.cos(theta)*ysum - r*sum1
        return c

    def dC2da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
        sum3 = 0.0
        for p in points:
            sum3 += (a-p.x()+(-l2*math.cos(theta)/2))/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*a - xsum - n*l2*math.cos(theta)/2- r*sum3
        return c

    def dC2db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            ysum += p.y()
        sum3 = 0.0
        for p in points:
            sum3 += (b-p.y()+(-l2*math.sin(theta)/2))/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*b - ysum - n*l2*math.sin(theta)/2 - r*sum3
        return c

    def dC2dr(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        for p in points:
            sum1 += math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*r - sum1
        return c

    def dC2dl2(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += ((-a+p.x())*math.cos(theta)+(-b+p.y())*math.sin(theta)+l2/2)/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = xsum*math.cos(theta) - n*a*math.cos(theta) + ysum*math.sin(theta) - n*b*math.sin(theta) + n*l2/2 - r*sum1
        return c

    def dC2dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        for p in points:
            sum1 += ((a-p.x())*math.sin(theta)*l2-(b-p.y())*math.cos(theta)*l2)/math.sqrt( (a-p.x()+(-l2*math.cos(theta)/2))**2 + (b-p.y()+(-l2*math.sin(theta)/2))**2)
        c = n*l2*a*math.sin(theta) - l2*math.sin(theta)*xsum - n*l2*b*math.cos(theta) + l2*math.cos(theta)*ysum - r*sum1
        return c

    def dL1da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.sin(theta)*math.cos(theta)*ysum + math.sin(theta)*math.sin(theta)*xsum - n*a*math.sin(theta)*math.sin(theta) + n*b*math.sin(theta)*math.cos(theta) - n*l3/2*math.sin(theta)
        return c

    def dL1db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.cos(theta)*math.cos(theta)*ysum + math.sin(theta)*math.cos(theta)*xsum - n*a*math.cos(theta)*math.sin(theta) + n*b*math.cos(theta)*math.cos(theta) - n*l3/2*math.cos(theta)
        return c

    def dL1dl3(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = math.sin(theta)*xsum - math.cos(theta)*ysum - n*a*math.sin(theta) + n*b*math.cos(theta) - n*l3/2
        return c

    def dL1dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        for p in points:
            sum1 += (-math.cos(theta)*p.y()+math.sin(theta)*p.x()-a*math.sin(theta)+b*math.cos(theta)-l3/2)*(math.sin(theta)*p.y()+math.cos(theta)*p.x()-a*math.cos(theta)-b*math.sin(theta))
        c = sum1
        return c

    def dL2da(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.sin(theta)*math.cos(theta)*ysum + math.sin(theta)*math.sin(theta)*xsum - n*a*math.sin(theta)*math.sin(theta) + n*b*math.sin(theta)*math.cos(theta) + n*l3/2*math.sin(theta)
        return c

    def dL2db(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.cos(theta)*math.cos(theta)*ysum + math.sin(theta)*math.cos(theta)*xsum - n*a*math.cos(theta)*math.sin(theta) + n*b*math.cos(theta)*math.cos(theta) + n*l3/2*math.cos(theta)
        return c

    def dL2dl3(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        xsum, ysum = 0.0, 0.0
        for p in points:
            xsum += p.x()
            ysum += p.y()
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        c = -math.cos(theta)*ysum + math.sin(theta)*xsum - n*a*math.sin(theta) + n*b*math.cos(theta) + n*l3/2
        return c

    def dL2dtheta(self, a, b, r, l1, l2, theta, points):
        c = 0.0
        n = len(points)
        sum1 = 0.0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        for p in points:
            sum1 += (-math.cos(theta)*p.y()+math.sin(theta)*p.x()-a*math.sin(theta)+b*math.cos(theta)+l3/2)*(math.sin(theta)*p.y()+math.cos(theta)*p.x()-a*math.cos(theta)-b*math.sin(theta))
        c = sum1
        return c


    def distancePointToCircle(self, a, b, r, l1, l2, theta, point):
        data = []
        d = 0
        l3 = math.sqrt(4*r**2-(l1-l2)**2)
        dC1 = abs(math.sqrt( (a+l2*math.cos(theta)/2-point.x())**2 + (b+l2*math.sin(theta)/2-point.y())**2) - r)
        dC2 = abs(math.sqrt( (a-l2*math.cos(theta)/2-point.x())**2 + (b-l2*math.sin(theta)/2-point.y())**2) - r)
        dL1 = abs((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) - l3/2))
        dL2 = abs((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) + l3/2))
        v1 = np.array([math.cos(theta), math.sin(theta)])
        X = np.array([point.x(), point.y()])
        C1 = np.array([a, b])+np.array([l2*math.cos(theta)/2, l2*math.sin(theta)/2])
        C2 = np.array([a, b])-np.array([l2*math.cos(theta)/2, l2*math.sin(theta)/2])
    
        if np.dot(v1, (X-C1))<=0:
            dC1 = 100
        if np.dot(v1, (X-C2))>=0:
            dC2 = 100
            
        if (min(dC1, dC2, dL1, dL2) == dC1):
            d =  (math.sqrt( (a+l2*math.cos(theta)/2-point.x())**2 + (b+l2*math.sin(theta)/2-point.y())**2) - r)
            pos = 'dC1'
        elif (min(dC1, dC2, dL1, dL2) == dC2):
            d =  (math.sqrt( (a-l2*math.cos(theta)/2-point.x())**2 + (b-l2*math.sin(theta)/2-point.y())**2) - r)
            pos = 'dC2'
        elif (min(dC1, dC2, dL1, dL2) == dL1):
            d = ((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) - l3/2))
            pos = 'dL1'
        else:
            d = - ((point.x()*math.sin(theta)-point.y()*math.cos(theta)-a*math.sin(theta)+b*math.cos(theta) + l3/2))
            pos = 'dL2'
            
        entry = d, pos
        data.append(entry)
        return d, pos

    def run(self, images):        
        bigImage = None
        circle = None
        points = []
        imageFiles = []
        imageXY = {}

        moduleDir = getModel().config.moduleDir()
        d0 = os.getcwd()
        if not moduleDir.startswith('/'):
            moduleDir = os.path.join(d0, moduleDir)
        os.chdir(moduleDir)
        
        for i, image in enumerate(images):
            fpath = image.filePath
            x, y = image.xyOffset[0], image.xyOffset[1]
            pointsLocal = CircleFit().extractPoints(fpath, (x, y), wsum=200, tgap=12) #tgap 10-20
            print(f'local points size: {len(pointsLocal)}')
            frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
            for p in pointsLocal:
                points.append(frame.toGlobal(p))
            fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
            imageFiles.append(fpath2)
            imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')
        circle = self.findCircle(points)
        
        canvas = self.createCanvas(imageFiles, points, circle, imageXY)
        figname = f'bigSlot'
        bigImage = ImageNP(figname, os.path.join(os.getcwd(), figname+'.jpg'))
        os.chdir(d0)
        
        return (bigImage, circle, points)

