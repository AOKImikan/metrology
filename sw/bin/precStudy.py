#!/usr/bin/env python3

import os
import argparse
import time

import cv2

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--image-file', dest='imageFile', \
                        type=str, default='', 
                        help='Image file name')
    parser.add_argument('-p', '--parameters', dest='parameters', \
                        type=str, default='', 
                        help='Parameters to optimize')
    parser.add_argument('-t', '--target',
                        type=str, default='Line',
                        help='Target pattern (Line, Circle)')
    return parser.parse_args()

def cb_none(x):
    #print('param1 => %d' % x)
    pass

def precStudy(args):
    imageFile = args.imageFile
    target = args.target

    wnOrig = 'wnOrig'
    wnEdge = 'wnEdge'
    #wOrig = cv2.namedWindow(wnOrig, cv2.WINDOW_NORMAL)
    window = cv2.namedWindow(wnEdge, cv2.WINDOW_NORMAL)

    blur_size = 1
    blur_amp = 1
    canny_thr1 = 20
    canny_thr2 = 10
    circle_dp = 1
    circle_minDist = 100
    circle_p1 = 20
    circle_p2 = 20
    circle_minR = 10
    circle_maxR = 4000
    if target == 'Line':
        cv2.createTrackbar('blur_size', wnEdge, 0, 50, cb_none)
        cv2.createTrackbar('blur_amp', wnEdge, 0, 100, cb_none)
        cv2.createTrackbar('canny_thr1', wnEdge, 0, 255, cb_none)
        cv2.createTrackbar('canny_thr2', wnEdge, 0, 255, cb_none)
    elif target == 'Circle':
        cv2.createTrackbar('blur_size', wnEdge, 0, 50, cb_none)
        cv2.createTrackbar('blur_amp', wnEdge, 0, 100, cb_none)
        cv2.createTrackbar('circle_dp', wnEdge, 1, 10, cb_none)
        cv2.createTrackbar('circle_minDist', wnEdge, 1, 2000, cb_none)
        cv2.createTrackbar('circle_p1', wnEdge, 1, 255, cb_none)
        cv2.createTrackbar('circle_p2', wnEdge, 1, 1000, cb_none)
        cv2.createTrackbar('circle_minR', wnEdge, 0, 10, cb_none)
        cv2.createTrackbar('circle_maxR', wnEdge, 0, 4000, cb_none)
    #cv2.resizeWindow(wnOrig, 320, 480)
    cv2.resizeWindow(wnEdge, 320, 480)

    img, imgbw = None, None
    imgEdge = None
    if os.path.exists(imageFile):
        img = cv2.imread(imageFile, cv2.IMREAD_COLOR)
        imgbw = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        print('No image is available')
        return -1

    oldpars = []
    
    cv2.imshow(wnEdge, imgbw)
    
    while True:
        print('Check parameters')
        blur_size = cv2.getTrackbarPos('blur_size', wnEdge)
        blur_amp = cv2.getTrackbarPos('blur_amp', wnEdge)
        if target == 'Line':
            canny_thr1 = cv2.getTrackbarPos('canny_thr1', wnEdge)
            canny_thr2 = cv2.getTrackbarPos('canny_thr2', wnEdge)
            pars = [blur_size, blur_amp, canny_thr1, canny_thr2]
        elif target == 'Circle':
            circle_dp = cv2.getTrackbarPos('circle_dp', wnEdge)
            circle_minDist = cv2.getTrackbarPos('circle_minDist', wnEdge)
            circle_p1 = cv2.getTrackbarPos('circle_p1', wnEdge)
            circle_p2 = cv2.getTrackbarPos('circle_p2', wnEdge)
            circle_minR = cv2.getTrackbarPos('circle_minR', wnEdge)
            circle_maxR = cv2.getTrackbarPos('circle_maxR', wnEdge)
            pars = [blur_size, blur_amp, \
                    circle_dp, circle_minDist, circle_p1, circle_p2, circle_minR, circle_maxR]
            print(pars)
            
        if pars == oldpars:
            print('No change in parameters')
            continue
        else:
            if target == 'Circle' and circle_dp <= 0: continue
            print('Update image with new parameters')
            if target == 'Line':
                s = blur_size*2 + 1
                imgblur = cv2.GaussianBlur(imgbw.copy(), (s, s), blur_amp)
                imgEdge = cv2.Canny(imgblur, canny_thr1, canny_thr2)
            elif target == 'Circle':
                s = blur_size*2 + 1
                imgblur = cv2.GaussianBlur(imgbw.copy(), (s, s), blur_amp)
                circles = []
                #circles = cv2.HoughCircles(imgblur, cv2.HOUGH_GRADIENT, 
                #                           circle_dp, circle_minDist, 
                #                           circle_p1, circle_p2)# , circle_minR, circle_maxR)
                #circles = circles[0]
                imgEdge = imgblur.copy()
                for c in circles:
                    cv2.circle(imgEdge, c[0:2], c[2], (255, 0, 0), 10)

        print('Print edge in a window')
        cv2.imshow(wnEdge, imgEdge)
        key = cv2.waitKey(1) & 0xff
        if key == 'c':
            break
        time.sleep(0.1)


if __name__ == '__main__':
    args = parseArgs()
    precStudy(args)
    
