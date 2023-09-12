#-----------------------------------------------------------------------
# pmm: fittools2.py
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
import statistics
from scipy.stats import norm
import scipy.signal as signal
from numpy.lib.stride_tricks import as_strided
import tkinter as tk
from PIL import Image, ImageTk


from .model import *
from .reader import *
from .view import *
from .gui import *
from .fittools import CircleFit, SlotFit
from .data2 import ImageNP, ScanData


class OuterlineFit:
    def __init__(self):
        self.outImageName = ''
        pass

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

    def convolve2d(self, image, mconv):
        img2shape = tuple(np.subtract(image.shape, mconv.shape)+1)
        subMatrices = as_strided(image, mconv.shape+img2shape, image.strides+image.strides)
        img2 = np.einsum('ij,ijkl->kl', mconv, subMatrices)
        return img2

    def my_convolve2d(self, a, conv_filter):
        submatrices = np.array([
            [a[:-2,:-2], a[:-2,1:-1], a[:-2,2:]],
            [a[1:-1,:-2], a[1:-1,1:-1], a[1:-1,2:]],
            [a[2:,:-2], a[2:,1:-1], a[2:,2:]]])
        multiplied_subs = np.einsum('ij,ijkl->ijkl',conv_filter,submatrices)
        return np.sum(np.sum(multiplied_subs, axis = -3), axis = -3)

    def extractEdge1(self, image,scanAxis, wsum=20, tgap=30):
        a = np.ones(wsum)
        b = np.ones(wsum)*(-1)
        m = np.append(a, b)
        if scanAxis == 0:
            m.resize( (1, len(m)) )
        if scanAxis == 1:
            m.resize( (len(m), 1) )
        print('Shapes before convolution')
        print(image.shape)
        print(m.shape)
        image1 = self.convolve2d(image, m)/wsum
        return image1

    def lineMatchX(self, image0, image4b, pos, r, wsum1, w_pix):
        pos2 = []
        r0 = []
        image4c = np.zeros([6000])
        xpix = 0
        for col in range(w_pix, image4b.shape[1]-w_pix, 1):
            sub = image4b[:,col-w_pix:col+w_pix]
            n = np.sum(sub)
            image4c[col] = n
            pixel = 4000
            r1 = n/pixel
            r0.append(r1)
            if r1>r:
                pos2 = np.where(image4c>(r*pixel))

        #print("pos2", pos2)
        pos2_1 = pos2[0]
        #print("pos2_1",pos2_1)
        n_p = len(pos2_1)
        pos2_left = int(pos2_1[0]) + int(w_pix+wsum1)
        pos2_right = int(pos2_1[n_p - 1]) + int(w_pix+2*(wsum1))
        print("(pos2_left, pos2_right) : ( %d, %d)" % (pos2_left, pos2_right))
        if pos == "L":
            cv2.line(image0, (pos2_left, 0), (pos2_left, 4000), (0, 0, 255), thickness=10)
            cv2.circle(image0, (pos2_left, 2000), 50, (255,255,0), -1)
            #cv2.imshow('image0.jpg', image0)
            xpix = pos2_left
        if pos == "R":
            cv2.line(image0, (pos2_right, 0), (pos2_right, 4000), (0, 0, 255), thickness=10)
            cv2.circle(image0, (pos2_right, 2000), 50, (255,255,0), -1)
            #cv2.imshow('image0.jpg', image0)
            xpix = pos2_right
            
        pos3col, pos3row = [], []
        for i in pos2[0]:
            pos3col1 = np.where(image4b[:,i]==1)
            pos3row1 = np.array([i]*len(pos3col1[0]))
            pos3col.append(pos3col1)
            pos3row.append(pos3row1)
    
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        y = np.arange(6000)
        ax.plot(y,image4c)
        ax.set_xlabel('pixel')
        ax.set_ylabel('Entries')
        #ax.title.set_text("image4c")
        fig.savefig('image_peak.png')
        
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        y = np.arange(len(r0))
        ax.plot(y,r0)
        ax.set_xlabel('pixel')
        ax.set_ylabel('ratio')
        #ax.title.set_text("ratio")
        fig.savefig('image_peak_ratio.png')
        print('LineMatchX :', xpix)
        return xpix


    def lineMatchY(self, image0, image4b, pos, r, wsum1, w_pix):
        pos2 = []
        r0 = []
        image4c = np.zeros([4000])
        ypix = 0
        for row in range(w_pix, image4b.shape[0]-w_pix, 1):
            sub = image4b[row-w_pix:row+w_pix,:]
            n = np.sum(sub)
            image4c[row] = n
            pixel = 6000
            r1 = n/pixel
            r0.append(r1)
            if r1>r:
                pos2 = np.where(image4c>(r*pixel))

        #print("pos2", pos2)
        pos2_1 = pos2[0]
        #print("pos2_1",pos2_1)
        n_p = len(pos2_1)
        pos2_top = int(pos2_1[0]) + int(w_pix+wsum1)
        pos2_bottom = int(pos2_1[n_p - 1]) + int(w_pix+2*wsum1)
        print("(pos2_top, pos2_bottom) : ( %d, %d)" % (pos2_top, pos2_bottom))
        if pos == "T":
            cv2.line(image0, (0,pos2_top), (6000,pos2_top), (0,0,255), thickness=10)
            cv2.circle(image0, (3000,pos2_top), 50, (255,255,0), -1)
            #cv2.imshow('image0.jpg', image0)
            ypix = pos2_top
        if pos == "B":
            cv2.line(image0, (0, pos2_bottom), (6000, pos2_bottom), (0, 0, 255), thickness=10)
            cv2.circle(image0, (3000,pos2_bottom), 50, (255,255,0), -1)
            #cv2.imshow('image0.jpg', image0)
            ypix = pos2_bottom
            print('ypix_bottom : ', ypix)
        
        pos3col, pos3row = [], []
        for i in pos2[0]:
            pos3row1 = np.where(image4b[i,:]==1) 
            pos3col1 = np.array([i]*len(pos3row1[0]))
            pos3col.append(pos3col1)
            pos3row.append(pos3row1)

        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        y = np.arange(4000)
        ax.plot(y,image4c)
        ax.set_xlabel('pixel')
        ax.set_ylabel('Entries')
        #ax.title.set_text("image4c")
        fig.savefig('image_peak.png')
        
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        y = np.arange(len(r0))
        ax.plot(y,r0)
        ax.set_xlabel('pixel')
        ax.set_ylabel('ratio')
        #ax.title.set_text("ratio")
        fig.savefig('image_peak_ratio.png')
        print('LineMatchY :', ypix)
        
        return ypix


    def lineMatch(self, fn, pos, r): 
        image0 = cv2.imread(fn, cv2.IMREAD_COLOR)
        image1 = cv2.cvtColor(image0, cv2.COLOR_BGR2GRAY)
        image2, image3, image4, image4b, vzerosup = 0, 0, 0, 0, 0
        xpix, ypix = 0, 0
        tgap1 = 30
        wsum1 = 20
        
        thr = 30
        
        if pos == 'L' or pos == 'R':
            image2 = self.extractEdge1(image1, 0, tgap=tgap1, wsum=wsum1)
            vzerosup = np.where(image2<thr, 0, image2)
            ret, image3 = cv2.threshold(image2, thr, 255, cv2.THRESH_TOZERO)
            image4 = np.zeros(image3.shape)
            for row in range(4000):
                peaks = signal.argrelextrema(vzerosup[row], np.greater)
                for p in peaks[0]:
                    image4[row, p] = image3[row, p]
            ret, image4b = cv2.threshold(image4, thr, 255, cv2.THRESH_BINARY)
            image4b = image4b/255
            pos1x = np.where(image4b[:,:]==1)
            #print("pos1x",pos1x)
            xpix = self.lineMatchX(image0, image4b, pos, r, wsum1, w_pix=10)
        if pos == 'T' or pos == 'B':
            image2 = self.extractEdge1(image1, 1, tgap=tgap1, wsum=wsum1)
            vzerosup = np.where(image2<thr, 0, image2)
            ret, image3 = cv2.threshold(image2, thr, 255, cv2.THRESH_TOZERO)
            image4 = np.zeros(image3.shape)
            for col in range(vzerosup.shape[1]):
                peaks = signal.argrelextrema(vzerosup[:,col], np.greater)
                for p in peaks[0]:
                    image4[p, col] = image3[p, col]
            ret, image4b = cv2.threshold(image4, thr, 255, cv2.THRESH_BINARY)
            image4b = image4b/255
            pos1 = np.where(image4b[:,:]==1)
            #print("pos1",pos1)
            ypix = self.lineMatchY(image0, image4b, pos, r, wsum1, w_pix=8)


        imagePath = 'image0.jpg'
        if self.outImageName != '':
            imagePath = self.outImageName
        cv2.imwrite(imagePath, image0)
    
        points = []
        image = "image0.png"
        points.append(CvPoint(xpix, ypix))
        
        print('xpix, ypix', xpix, ypix)
        #return (points, image)
        return (points, imagePath)
    
        
    def run(self, image, pos, r):
        #image = None
        points = []
        imageFiles = []
        imageXY = {}


        fpath = image.filePath
        x, y = image.xyOffset[0], image.xyOffset[1]
        pointsLocal, image = self.lineMatch(fpath, pos, r)
        print(f'local points size: {len(pointsLocal)}')
        frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
        for p in pointsLocal:
            point = frame.toGlobal(p)
            points.append(frame.toGlobal(p))
        imageFiles.append(os.path.basename(fpath).replace('.jpg', '_p.png'))
        fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
        imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')

        
        '''
        for i, image in enumerate(images):
            fpath = image.filePath
            x, y = image.xyOffset[0], image.xyOffset[1]
            pointsLocal, image = self.lineMatch(fpath, pos, r)
            print(f'local points size: {len(pointsLocal)}')
            frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
            for p in pointsLocal: 
                #points.append(frame.toGlobal(p))
                point = frame.toGlobal(p)
                points.append(CvPoint(point[0], point[1]))
            imageFiles.append(os.path.basename(fpath).replace('.jpg', '_p.png'))
            fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
            imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')
        '''

        figname = f'Line'
        image = ImageNP(figname, os.path.join(os.getcwd(), f'figname.pdf'))
        
        return (image, points, pointsLocal)



class CellFit:
    def __init__(self):
        pass

    def readLog(self, logname):
        imageXY = {}
        if os.path.exists(logname):
            re1 = re.compile('Photo at \(([\d+-.]+), ([\d+-.]+)\)')
            re2 = re.compile('file=(.+\.jpg)')
            f = open(logname, 'r')
            for line in f.readlines():
                if len(line)==0 or line[0]=='#': continue
                words = line.split(' ')
                fname, x, y = '', -2.0E+6, -2.0E+6
                mm = 0.001
                fname = words[3]
                x = float(words[0])*mm
                y = -float(words[1])*mm

                if fname!='' and x > -1.0E+6:
                    i = fname.rfind('\\')
                    fname = fname[i+1:]
                    imageXY[fname] = (x, y) 
        return imageXY

    def calcScale(self, w, h, xy, pos):
        w0 = 15.0 # Real physical size
        if pos == 'TL':
            x0, y0 = -15.0, 0.0
        if pos == 'TR':
            x0, y0 = 0.0, 0.0
        if pos == 'BR':
            x0, y0 = 0.0, -15.0
        if pos == 'BL':
            x0, y0 = -15.0, -15.0
    
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


    def createCanvas(self, imageFiles, points, circle, imageXY, pos):
        figPrefix='cell_01'
        w, h = 600, 600
        w1 = w
        h1 = w*4000/6000.0
        
        root = tk.Tk()
        root.title('Module area')
        root.geometry('%dx%d' % (w, h))
        
        canvas = tk.Canvas(root, width=w, height=h, background='lightgreen')
        canvas.grid(row=1, column=1)

        images = []
        for fn in imageFiles:
            fn1 = fn.replace('_p.png', '.jpg')
            scale, c, r = self.calcScale(w, h, imageXY[fn], pos)
            print('Add image %s' % fn, imageXY[fn])
            img = Image.open(fn)
            img = img.resize( (int(scale*w1), int(scale*h1) ) )
            img = ImageTk.PhotoImage(img)
            images.append(img)
            canvas.create_image(c, r, image=img, anchor=tk.CENTER)

        a, b, r = circle
        
        if pos == 'TL':
            a, b, r = CircleFit().toGlobal2(a, b, r, w=w, h=h, w0=15.0, BL=(-15.0, 0.0))    
            canvas.create_oval(a-r, b-r, a+r, b+r, outline='blue', width=2)
            canvas.update()
            canvas.postscript(file="./plot/slot_%s_TL.ps"%figPrefix, colormode='color')
            root.mainloop()
        if pos == 'TR':
            a, b, r = CircleFit().toGlobal2(a, b, r, w=w, h=h, w0=15.0, BL=(0.0, 0.0))
            canvas.create_oval(a-r, b-r, a+r, b+r, outline='blue', width=2)
            canvas.update()
            canvas.postscript(file="./plot/slot_%s_TR.ps"%figPrefix, colormode='color')
            root.mainloop()
        if pos == 'BR':
            a, b, r = CircleFit().toGlobal2(a, b, r, w=w, h=h, w0=15.0, BL=(0.0, -15.0))    
            canvas.create_oval(a-r, b-r, a+r, b+r, outline='blue', width=2)
            canvas.update()
            canvas.postscript(file="./plot/slot_%s_BR.ps"%figPrefix, colormode='color')
            root.mainloop()
        if pos == 'BL':
            a, b, r = CircleFit().toGlobal2(a, b, r, w=w, h=h, w0=15.0, BL=(-15.0, -15.0))    
            canvas.create_oval(a-r, b-r, a+r, b+r, outline='blue', width=2)
            canvas.update()
            canvas.postscript(file="./plot/slot_%s_BL.ps"%figPrefix, colormode='color')
            root.mainloop()
      
        return images, circle

    def findCircle(self, points):
        figPrefix='cell_02'
        goodPoints1 = []
        data1, data2 ,data3 = [], [], []
        thr1 = 1.5
        d1, d1_p, d1_n =  0, 0, 0

        ###
        pars1 = self.findCircle2(points)
        for i, p in enumerate(points):
            d1_m = (CircleFit().distancePointToCircle(*pars1, p))
            d1 = abs(d1_m)
            print('  Distance from circle to point[%d]=%7.4f' % (i, d1_m) )

            if d1_m > 0:
                d1_p = d1_m
                entry2 = d1_p
                data3.append(entry3)
            else:
                d1_n = d1_m
                entry3 = d1_n
                data3.append(entry3)
                        
            if d1 < thr1:
                goodPoints1.append(p)

            entry1 = d1_m
            data1.append(entry1)
            
        n1 = len(data1)
        n2 = len(data2)
        n3 = len(data3)
        print('d1_p:', n2, 'd1_n:', n3, 'ratio:', n2/n1, n3/n1)
        
        mean1 = statistics.mean(data1)
        stdev1 = statistics.stdev(data1)
        print('mean of distance1 = %f'%mean1)
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
    
        #
        fig = plt.figure()
        plt.hist(data1, bins=100, range=(-0.5, 0.5))
        plt.text(0.2, 30, "entries : %d" %n1 +"\n"+"mean   : "+"{:.5f}".format(mean1)+"\n"+"stdev   : "+"{:.7f}".format(stdev1))
        plt.xlabel('distance [mm]')
        plt.ylabel('Entries')
        fig.savefig('./plot/pl_%s_dz_1.png'% figPrefix) 
        #
        fig = plt.figure(figsize=plt.figaspect(1))
        ax = fig.add_subplot()
        draw_circle = plt.Circle((pars1[0], pars1[1]), pars1[2], fill=False)
        p = ax.scatter(vx, vy, marker='o', s=10)
        p = ax.add_artist(draw_circle)
        p = ax.set_xlabel("x [mm]")
        p = ax.set_ylabel("y [mm]")
        fig.savefig('./plot/pl_%s_xy_1.png'% figPrefix)
        circle = tuple(pars1) 
        
        return circle


    def findCircle2(self, points):
        figPrefix='cell_01'
        circle = None
        xsum, ysum = 0.0, 0.0
        num = len(points)
        for p in points:
            xsum += p.x()
            ysum += p.y()
        xpos = xsum/num
        ypos = ysum/num
        print('xpos, ypos', xpos, ypos)
        pars1 = [xpos, ypos, 0.95]
        pars_1 = [xpos, ypos, 0.95]
        pars = [xpos, ypos, 0.95]
        f = [ 0.0, 0.0, 0.0]

        #print('Initial values: ', pars1)

        pars_1 = CircleFit().fitStep(10, 0.01, pars1, points)
        pars = CircleFit().fitStep(10, 0.001, pars_1, points)
        circle = tuple(pars)
        return pars

    def run(self, images, pos):
        bigImage = None
        circle = None
        points = []
        imageFiles = []
        imageXY = {}
    
        for i, image in enumerate(images):
            fpath = image.filePath
            x, y = image.xyOffset[0], image.xyOffset[1]
            pointsLocal = CircleFit().extractPoints(fpath, (x, y), 200, 40)
            print(f'local points size: {len(pointsLocal)}')
            frame = ImageFrame( (x, y), zoom=20, width=6000, height=4000)
            for p in pointsLocal:
                points.append(frame.toGlobal(p))
            imageFiles.append(os.path.basename(fpath).replace('.jpg', '_p.png'))
            fpath2 = os.path.basename(fpath).replace('.jpg', '_p.png')
            imageXY[fpath2] = (x, y)
        print(f'N all points {len(points)}')
        
        circle = self.findCircle(points)
    
        canvas = self.createCanvas(imageFiles, points, circle, imageXY, pos)
        figname = f'CellBack'
        bigImage = ImageNP(figname, os.path.join(os.getcwd(), f'figname.pdf'))
        
        return (bigImage, circle, points)

