#!/usr/bin/env python3
import os, sys
import argparse
import pickle
import math
import cv2
import numpy as np
import scipy.signal as signal

from pmm import *

image1 = '../data/KEKQ18/tray-1picf_66/Img8988.jpg'

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', dest='input',
                        type=str, default=image1, 
                        help='Input image file')
    parser.add_argument('-o', '--output-file', dest='output', 
                        type=str, default='prec1.pickle', 
                        help='Name of the output file (.pickle)')
    parser.add_argument('--wsum', dest='wsum', 
                        type=int, default=20, 
                        help='GapFinder parameter, width')
    parser.add_argument('--tgap', dest='tgap', 
                        type=int, default=20, 
                        help='GapFinder parameter, threshold')
    parser.add_argument('--cosAngleMin', dest='cosAngleMin', 
                        type=float, default=0.1, 
                        help='SegmentFinder parameter, cosAngleMin')
    parser.add_argument('--distanceMax', dest='distanceMax', 
                        type=float, default=10.0, 
                        help='SegmentFinder parameter, distanceMax [pixels]')
    parser.add_argument('--connectDistMax', dest='connectDistMax', 
                        type=float, default=250.0, 
                        help='SegmentFinder parameter, connectDistMax [pixels]')
    parser.add_argument('--nPointsOnLine', dest='nPointsOnLine', 
                        type=int, default=5, 
                        help='Number of points on the line')
    parser.add_argument('--searchRect', dest='searchRect', 
                        type=str, default='', 
                        help='Search rectangle (csv). Example: 100,100,3000,3000')
    parser.add_argument('--scanWidth', dest='scanWidth', 
                        type=int, default=10, 
                        help='Width (pixels) of the band used for the edge detection scan')
    parser.add_argument('--scanInterval', dest='scanInterval', 
                        type=int, default=100, 
                        help='ScanInterval (pixels) in the y-direction when doing a edge detection scan in x-direction and vice versa')
    parser.add_argument('--offset', dest='offset', 
                        type=str, default='0,0', 
                        help='Offset (x, y) [mm] of this photo')
    parser.add_argument('--zoom', dest='zoom', 
                        type=int, default=20, 
                        help='Zoom of the lense (1, 2, 5, 10 or 20)')

    parser.add_argument('--target', dest='target', 
                        type=str, default='', 
                        help='Target pattern name [Line|Circle|Vertex]*. Use --show-targets to show examples on how to specify target patterns')
    parser.add_argument('--show-targets', dest='showTargets', 
                        action='store_true', default=False, 
                        help='Show target pattern specification')
    parser.add_argument('--figure-file', dest='figureFile', 
                        type=str, default='pr1.jpg', 
                        help='Name of the figure file to be saved')
    parser.add_argument('--pickle-file', dest='pickleFile', 
                        type=str, default='data_pr1.pickle', 
                        help='Name of the pickle file to save data')
    parser.add_argument('-b', '--batch-mode', dest='batchMode', 
                        action='store_true', default=False, 
                        help='Run in batch mode (do not show plots)')

    args = parser.parse_args()
    return args

def drawPatterns(img, args, hobjects, vobjects, vertices, circles):
    hpoints, hlines, hlines2, hline = hobjects #hobjects[0], hobjects[1], hobjects[2], hobjects[3]
    vpoints, vlines, vlines2, vline = vobjects #vobjects[0], vobjects[1], vobjects[2], vobjects[3]

    cv2.namedWindow('pr1', cv2.WINDOW_NORMAL)
    r = 20
    red, blue, rg, bg = (0, 0, 255), (255, 0, 0), (0, 255, 255), (255, 255, 0)
    dred, dblue = (0, 0, 128), (128, 0, 0)
    green = (0, 255, 0)

    # H objects
    for p in hpoints:
        cv2.circle(img, (int(p.x()), int(p.y())), r, blue, -1)
    for line in hlines:
        p1 = tuple(map(lambda x: int(x), (line.start.x(), line.start.y())))
        p2 = tuple(map(lambda x: int(x), (line.end.x(), line.end.y())))
        cv2.line(img, p1, p2, blue, 20)
    for line in hlines2:
        p1 = tuple(map(lambda x: int(x), (line.start.x(), line.start.y())))
        p2 = tuple(map(lambda x: int(x), (line.end.x(), line.end.y())))
        cv2.line(img, p1, p2, bg, 7)
    if hline:
        p1 = tuple(map(lambda x: int(x), (hline.start.x(), hline.start.y())))
        p2 = tuple(map(lambda x: int(x), (hline.end.x(), hline.end.y())))
        cv2.line(img, p1, p2, bg, 25)

    # V objects
    for p in vpoints:
        cv2.circle(img, (int(p.x()), int(p.y())), r, red, -1)
    for line in vlines:
        p1 = tuple(map(lambda x: int(x), (line.start.x(), line.start.y())))
        p2 = tuple(map(lambda x: int(x), (line.end.x(), line.end.y())))
        cv2.line(img, p1, p2, red, 20)
    for line in vlines2:
        p1 = tuple(map(lambda x: int(x), (line.start.x(), line.start.y())))
        p2 = tuple(map(lambda x: int(x), (line.end.x(), line.end.y())))
        cv2.line(img, p1, p2, rg, 7)
    if vline:
        p1 = tuple(map(lambda x: int(x), (vline.start.x(), vline.start.y())))
        p2 = tuple(map(lambda x: int(x), (vline.end.x(), vline.end.y())))
        cv2.line(img, p1, p2, rg, 25)

    for p in vertices:
        x, y = p.point.x(), p.point.y()
        cv2.circle(img, (int(x), int(y)), int(r*1.5), green, -1)
    
    for c in circles:
        if len(c)==3:
            print('circle',c)
            cv2.circle(img, (int(c[0]), int(c[1]) ), int(c[2]), blue, 10)

    if not args.batchMode:
        cv2.imshow('pr1', img)
        cv2.resizeWindow('pr1', 600, 400)
        cv2.waitKey(0)
    cv2.imwrite(args.figureFile, img)
    
def printResults(patterns, offset, zoom=0):
    if type(patterns.target) == Vertex:
        p = patterns.target.point
        c, r = p.x(), p.y()
        pixelSize = pixelSizeForZoom(zoom)
        frame = ImageFrame(offset, zoom)
        p2 = frame.toGlobal( [c, r] )
        print('Vertex (c, r)=(%d, %d), global (x, y)=(%6.3f, %6.3f)' % \
              (c, r, p2.x(), p2.y()) )
        pass

def runPatternRec1(args):
    rect = ()
    if args.searchRect != '':
        words = args.searchRect.split(',')
        print('runPatternRec1 on sub-region: %s' % words)
        if len(words) == 4:
            c1 = int(words[0])
            r1 = int(words[1])
            c2 = int(words[2])
            r2 = int(words[3])
            rect = (c1, r1, c2, r2)
    img = cv2.imread(args.input, cv2.IMREAD_COLOR)
    print('Rect before calling', rect)
    print('scanInterval in runPatternRec1 {}'.format(args.scanInterval))
    patterns = patternRec1(img, rect=rect, 
                           targetString=args.target, 
                           wsum=args.wsum, 
                           tgap=args.tgap, 
                           cosAngleMin=args.cosAngleMin, 
                           distanceMax=args.distanceMax, 
                           connectDistMax=args.connectDistMax, 
                           scanInterval=args.scanInterval, 
                           scanWidth=args.scanWidth)

    pointsH = patterns.hpoints
    hlines = patterns.hsegments
    hlines2 = patterns.hlines
    pointsV = patterns.vpoints
    vlines = patterns.vsegments
    vlines2 = patterns.vlines
    scanData = patterns.scanData
    hline, vline = None, None

    target = PatternSelector(args.target)
    if target.type == 'Line':
        if abs(target.lineAngle)<30.0:
            nalong = 0
            hline = patterns.target
            if target.row!=None:
                for p in pointsH:
                    if abs(p.y() - target.row) < 20.0: nalong += 1
            print('Target{0}: '.format(target) )
            print('  Point detection: nPointsAll={0}, nPointsAlong={1}'\
                  .format(len(pointsH), nalong) )
            if hline:
                print('  Line detection: FOUND')
                print('    {}'.format(str(hline) ) )
                print('    nPointsOnLine={0}, nLineLength={1:6.1f}'\
                      .format(len(hline.points), hline.length() ) )
            else:
                print('  Line detection: NOT FOUND')
        else:
            nalong = 0
            vline = patterns.target
            if target.column!=None:
                for p in pointsV:
                    if abs(p.x() - target.column) < 30.0: nalong += 1
            print('Target{0}: '.format(target) )
            print('  Point detection: nPointsAll={0}, nPointsAlong={1}'\
                  .format(len(pointsV), nalong) )
            if vline:
                print('  Line detection: FOUND')
                print('    {}'.format(str(vline) ) )
                print('    nPointsOnLine={0}, nLineLength={1:6.1f}'\
                      .format(len(vline.points), vline.length() ) )
            else:
                print('  Line detection: NOT FOUND')
    elif target.type == 'Vertex':
        vertices = patterns.vertices
    else:
        pass
    gh, gv = False, False
    if args.target.find('LineH')>=0: gh = True
    if args.target.find('LineV')>=0: gv = True
    if args.target.find('Vertex')>=0:
        gh = True
        gv = True
    hobjects = ([], [], [], None)
    vobjects = ([], [], [], None)
    vertexObjects = []
    if gh: hobjects = (pointsH, hlines, hlines2, hline)
    if gv: vobjects = (pointsV, vlines, vlines2, vline)
    if args.target.find('Vertex')>=0:
        vertexObjects = []
        if patterns.target != None:
            vertexObjects = [ patterns.target ]
    circles = patterns.circles

    offset = list(map(lambda x: float(x), args.offset.split(',') ) )
    printResults(patterns, offset, args.zoom)

    drawPatterns(img, args, hobjects, vobjects, vertexObjects, circles)

    fout = open(args.pickleFile, 'wb')
    pickle.dump(scanData, fout)
    fout.close()

if __name__ == '__main__':
    args = parseArgs()
    print(args)
    run = True
    if args.showTargets:
        print('Target pattern specification examples (comma-separated string without a white space)')
        print('  * LineH [horizontal line]')
        print('  * LineH,col1000,row1200 [horizontal line near (col,row)]')
        print('  * Line30deg [line in direction of 30 degrees from the horizontal axis]')
        print('  * Vertex,col2000,row3000 [vertex near (col, row)]')
        run = False

    if run:
        runPatternRec1(args)
