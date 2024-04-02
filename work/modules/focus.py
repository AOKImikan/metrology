#!/usr/bin/env python3
import os
import glob
import time
import pickle

import cv2
import pmm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

def parseArg():
    # make parser
    parser = argparse.ArgumentParser()
    # add argument
    parser.add_argument('module', help='module choice')
    parser.add_argument('--pickup', help='pickup area', action='store_true')

    args = parser.parse_args()  # analyze arguments
    return args

def normalize(image, lower, upper):
    normed = cv2.normalize(image, None,
                           alpha=lower, beta=upper,
                           norm_type=cv2.NORM_MINMAX)
    return normed

def stat(ndarray):
    armean = ndarray.mean()
    armean = round(armean,5)
    armin = ndarray.min()
    armax = ndarray.max()
    return armean , armin, armax

def makeSuffix(rc):
    suff = []
    i=0
    while i < rc[0]:
        j=0
        while j < rc[1]:
            char = str(i)+str(j)
            suff.append(char)
            j += 1
        i += 1
    #    
    return suff

def split(img, rc):
    height, width = img.shape
    splitHeight = height // rc[0]
    splitWidth = width // rc[1]

    #suff = makeSuffix(rc)
    suff=[]
    images = {}
    i=0
    while i < rc[0]:
        j=0
        while j < rc[1]:
            char = str(i)+str(j)
            p = np.zeros((splitHeight, splitWidth), np.uint8)
            p = img[i*splitHeight:(i+1)*splitHeight, j*splitWidth:(j+1)*splitWidth]
            images[char] = p
            suff.append(char)
            j += 1
        i += 1
  
    #print(suff)
    #print(images)
    return images

def laplacian(images):
   laps = {}
   for rc in images.keys():
       laps[rc] = cv2.Laplacian(images[rc], cv2.CV_64F)
       print(rc)
       print(round(laps[rc].var(),4))
       print(stat(laps[rc]),'\n')

def fourier(images):
    ffts = {}
    for rc, img in images.items():
        # f = np.fft.fft2(img)
        # fshift = np.fft.fftshift(f)
        # magnitude = np.log(np.abs(fshift))
        # ffts[rc] = magnitude   
        dft = cv2.dft(np.float32(img), flags = cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        #magnitude_cv = cv2.magnitude(dft_shift[:,:,0], dft_shift[:,:,1])
        magnitude_cv = 20*np.log(cv2.magnitude(dft_shift[:,:,0], dft_shift[:,:,1]))
        ffts[rc] = magnitude_cv
    return ffts

def filterMatrix(size, r1, r2):
    center = [size[0]//2, size[1]//2]
    m = np.zeros((size[0], size[1]), np.uint8)
    for i in range(center[0]-r2, center[0] + r2):
        for j in range(center[1]-r2, center[1]+r2):
            if ((i-center[0])**2 + (j-center[1])**2 < r2**2) and ((i-center[0])**2 + (j-center[1])**2 > r1**2):
                m[i][j] = 1
    return m

def analysisIntensity(ffts):
    mask0s, mask1s, mask2s, mask3s = {}, {},{},{}
    fimg = ffts['00']
    size = [fimg.shape[0], fimg.shape[1]]    
    filter0 = filterMatrix(size, 0, 50)
    print('filter 0 done')
    filter1 = filterMatrix(size, 50, 100)
    print('filter 1 done')
    filter2 = filterMatrix(size, 100, 150)
    print('filter 2 done')
    filter3 = filterMatrix(size, 150, 200)
    print('filter 3 done')
    for rc, f in ffts.items():
        mask0 = f*filter0
        mask0s[rc] = mask0
        mask1 = f*filter1
        mask1s[rc] = mask1
        mask2 = f*filter2
        mask2s[rc] = mask2
        mask3 = f*filter3
        mask3s[rc] = mask3
                
        sum0 = np.mean(mask0)
        sum1 = np.mean(mask1)
        sum2 = np.mean(mask2)
        sum3 = np.mean(mask3)
        # print(f[1000-30:1000+30, 1500-30:1500+30])
        # part1 = f[1000-300:1000+300, 1500-300:1500+300]
        # part2 = f[1000-150:1000+150, 1500-150:1500+150]
        # part3 = f[1000-50:1000+50, 1500-50:1500+50]
        # sum0 = np.sum(f) - np.sum(part1)
        # sum1 = np.sum(part1) - np.sum(part2)
        # sum2 = np.sum(part2) - np.sum(part3)
        # sum3 = np.sum(part3)

        print(rc, ':', sum0, sum1, sum2, sum3)

    return mask0s, mask1s, mask2s, mask3s

def filterCirc(fft, r):
    row, col = fft.shape
    passFilter = Image.new(mode='L',
                           size=(rpw, col),
                           color=255)
    

def showFFT(ffts, name):
    fig = plt.figure(figsize=(8,7))
    axes = fig.subplots(2,2,sharex='all',sharey='all')
    fig.suptitle(name)
    axes[0,0].set_title('00')
    axes[1,0].set_title('10')
    axes[0,1].set_title('01')
    axes[1,1].set_title('11')

    axes[0,0].imshow(ffts['00'], cmap='gray')
    axes[1,0].imshow(ffts['10'], cmap='gray')
    axes[0,1].imshow(ffts['01'], cmap='gray')
    axes[1,1].imshow(ffts['11'], cmap='gray')
    
    plt.savefig(f'tempspace/fourier_{name}.jpg')  #save as jpeg 
    #plt.show()
    

def run():
    #path = '/nfs/space3/aoki/Metrology/kekdata/2023.11/Module_20UPGM20231129_THERMAL_CYCLES_Size_Cell/*.jpg'
    #path = '/nfs/space3/aoki/Metrology/HR/ModuleData/20UPGM22601111/ASSEMBLY/Module_20UPGM22601111_ASSEMBLY_PreProduction_Size_Front/*.jpg'
    path = '/nfs/space3/aoki/Metrology/HR/images/*.jpg'
    files = glob.glob(path)
    outpath = '/nfs/space3/aoki/Metrology/work/tempspace/'
    #aims = ['Img35609.jpg','Img35536.jpg','Img69588.jpg','Img35532.jpg','Img56518.jpg','Img36047.jpg']
    aims=['Img35609.jpg','Img69588.jpg']
    i = 0
    for f in files:
        #filename =  f.split('/')[10]
        filename =  f.split('/')[7]
        name = filename.split('.')[0]
        if filename in aims :
            pass
        else:
            continue
        print(filename)

        originImg = cv2.imread(f)  # original image
        gray = cv2.cvtColor(originImg , cv2.COLOR_BGR2GRAY)
       
        # images = split(gray, [2,2])  #split gray image by 2*2
        # # images is type = dictionary

        # #laplacian(images)
        # ffts = fourier(images)
        # showFFT(ffts, name)

        # normalize
        normedImg = normalize(originImg, 0, 100)
        print('normalize done')
        gray_n = cv2.cvtColor(normedImg, cv2.COLOR_BGR2GRAY)
        print('gray done')
        images_n = split(gray_n, [2,2])
        print('split done')

        #laplacian(images_n)
        ffts_n = fourier(images_n)
        print('fourier done')
        masks = analysisIntensity(ffts_n)
        name_n = name + '_normalized'
        name0 = name + '_masked0'
        name1 = name + '_masked1'
        name2 = name + '_masked2'
        name3 = name + '_masked3'
        # showFFT(ffts_n, name_n)
        # showFFT(masks[0], name0)
        # showFFT(masks[1], name1)
        # showFFT(masks[2], name2)
        # showFFT(masks[3], name3)
        # i += 1
        #  if i > 1 :
        #      break
        
if __name__ == '__main__':
    t1 = time.time()

    run()

    #args = parseArg()

    t2 = time.time()
    elapsed_time = t2-t1
    print(f'run time : {elapsed_time}')
