#!/usr/bin/env python3

import os
import argparse
import pmm
import cv2

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logFile', dest='logFile', 
                        type=str, default='', 
                        help='Log file with (x, y, z, [photo])')
    parser.add_argument('--scanConfigFile', dest='scanConfigFile', 
                        type=str, default='', 
                        help='Scan config file')
    parser.add_argument('-z', '--zoom', dest='zoom', 
                        type=int, default=20, 
                        help='Scan config file')
    parser.add_argument('--searchWindow', dest='searchWindow', 
                        type=float, default=0.3, 
                        help='Search window [mm] in the image to look for patterns')
    return parser.parse_args()

def editImage(imgFile, imgOut, rects=[], circle=None):
    if os.path.exists(imgFile):
        img = cv2.imread(imgFile, cv2.IMREAD_COLOR)
    else:
        print('Image file %s does not exist' % (imgFile) )
        return
    lines = pmm.findLine(img)
    G = (0, 255, 0)
    if type(lines)!=type(None):
        for x in lines:
            plist = x[0]
            cv2.line(img, pt1=plist[0:2], pt2=plist[2:4], color=G, thickness=10)
    #
    for rect in rects:
        print(rect)
        p1, p2 = rect
        #color = (29, 214, 43)
        color = (0, 0, 255)
        cv2.rectangle(img, pt1=p1, pt2=p2, color=color, thickness=8)
    print('Save image to %s' % (imgOut) )
    cv2.imwrite(imgOut, img)

def scanSummary(logFile, configFile, zoom=20, searchWindow=0.3):
    if not (os.path.exists(logFile) and os.path.exists(configFile)):
        print('File does not exist')
        return -2
    reader = pmm.ReaderB4v1()
    cpoints = pmm.readScanConfig(configFile)
    points = reader.readPoints(logFile)
    scanDir = os.path.dirname(logFile)
    print(scanDir)

    nc = len(cpoints)
    n = len(points)
    if nc == 0 or len(cpoints) != nc:
        print('Number of points in the log file is different from the config {0}<->{1}'.format(n, nc) )
        return -1
    print('Read {0} points from log file {1}'.format(n, logFile) )

    dx, dy = searchWindow, searchWindow
    dxy = pmm.CvPoint(dx, -dy)
    module = pmm.Rd53aModule()
    results = pmm.MetrologyResults2()
    for i in range(nc):
        p = points[i]
        cp = cpoints[i]
        if len(p)>3:
            imgFile = p[3]
            imgPath = os.path.join(scanDir, imgFile)
            cp.imgFile = imgPath
            print('Point[{0}] {1}: offset=({2:6.3f}, {3:6.3f}), tags={4}'.\
                  format(i, p[3], p[0], p[1], cp.tags) )
            offset = pmm.CvPoint(p[0], p[1])
            frame = pmm.ImageFrame(offset, zoom)
            #
            targetKeys = module.targetData.keys()
            tags = cp.tags.split(',')
            rects = []
            for tag in tags:
                if tag not in targetKeys:
                    print('  Tag {} not expected'.format(tag))
                    continue
                target = module.targetData[tag]
                if tag.find('Jig')>=0: continue
                print('  {0} -> ({1:6.3f}, {2:6.3f})'.format(tag, target.x, target.y))
                tPos = pmm.CvPoint(target.x, target.y)
                pTL = tPos - dxy
                pBR = tPos + dxy
                dcr = dx/frame.pixelSize
                crTL = frame.toCR(pTL)
                crBR = frame.toCR(pBR)
                if target.ptype == 'LineH':
                    crTL.position.x = frame.width/2 - dcr
                    crBR.position.x = frame.width/2 + dcr
                if target.ptype == 'LineV':
                    crTL.position.y = frame.height/2 - dcr
                    crBR.position.y = frame.height/2 + dcr
                print('  region (CR): (%4d, %4d) - (%4d, %4d)' % \
                      (crTL[0], crTL[1], crBR[0], crBR[1]) )
                inFile = os.path.join(scanDir, os.path.basename(imgFile))
                outFile = os.path.join('./figures', os.path.basename(imgFile))
                p1 = int(crTL.x()), int(crTL.y())
                p2 = int(crBR.x()), int(crBR.y())
                p1 = frame.trimCR(p1)
                p2 = frame.trimCR(p2)
                outFile1 = outFile.replace('.jpg', '_detail.jpg')
                ts = '%s,col%d,row%d' % \
                     (target.ptype, int((p2[0]-p1[0])/2), int((p2[1]-p1[1])/2))
                cmd = 'prec1.py -i %s --figure-file %s --target %s --searchRect=%d,%d,%d,%d' %\
                      (inFile, outFile1, ts, p1[0], p1[1], p2[0], p2[1])
                print(cmd)
                rects.append( (p1, p2) )
            #editImage(inFile, outFile, rects=rects)
        else:
            print('Photo[{0}] is missing, tags={1}'.format(i, cp.tags))
    #results.setSizeResults(points, cpoints)
    #pmm.precScanPoints(results.sizeResults)

if __name__ == '__main__':
    args = parseArgs()
    scanSummary(args.logFile, args.scanConfigFile, 
                args.zoom, args.searchWindow)
