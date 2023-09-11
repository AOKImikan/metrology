#!/usr/bin/env python3

import os, sys
import pmm
import argparse
import pickle

fname_height = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/tray-1bowf_497//log.txt'
fname_pickup = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/tray-1bowf_498//log.txt'
fname_size = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/KEKQ17/tray-1size_12/log.txt'
fname_planarityVacOn = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/tray-1bowf_499/log.txt'
fname_planarityVacOff = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/tray-1bowf_500/log.txt'

scanName = 'KEKQ15'
def pickleName():
    return '%s.pickle' % scanName

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gui', dest='gui', 
                        default=False, action='store_true', 
                        help='Enable GUI to run')
    parser.add_argument('--data-dir', dest='dataDir', 
                        default='/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/20210706', type=str, 
                        help='Location of the measurement data where each measuremnts are to be found')
    #
    parser.add_argument('--read-size', dest='readSize', 
                        default='', type=str, 
                        help='Read size measurements')
    parser.add_argument('--dump-size', dest='dumpSize', 
                        default='', type=str, 
                        help='Dump size results to file')
    #
    parser.add_argument('--read-photo', dest='readPhoto', 
                        default='', type=str, 
                        help='Read size scan measurements')
    parser.add_argument('--dump-photo', dest='dumpPhoto', 
                        default='', type=str, 
                        help='Dump photo scan results to file')
    #
    parser.add_argument('--format', dest='format', 
                        default='B4v1', type=str, 
                        help='Format of the measurement log.txt')
    parser.add_argument('--scan-config', dest='scanConfig', 
                        default='', type=str, 
                        help='Configuration describing the location of the scan points')

    return parser.parse_args()

def startGui(args):
    w = pmm.PmmWindow()
    w.buildGui()
    w.startLoop()
    #w.loadImage('/nfs/space3/tkohno/atlas/ITkPixel/Metrology/data/20210706/tray-1size_12/Img8488.jpg')

if __name__ == '__main__':
    args = parse_args()
    if args.gui:
        startGui(args)
        sys.exit(0)

    pickleFile = pickleName()
    results = pmm.MetrologyResults1()
    #results.load(pickleFile)

    reader = pmm.ReaderB4v1()
    #pmm.checkHeight(fname_height, reader)
    #pmm.checkPickup(fname_pickup, reader)
    if args.readSize!='':
        fname = args.readSize+'/log.txt'
        if args.readSize!='/':
            fname = os.path.join(args.dataDir, args.readSize, 'log.txt')
        pmm.checkSize(fname, reader, results.sizeResults)
    if args.readPhoto!='':
        fname = args.readPhoto+'/log.txt'
        if args.readPhoto!='/':
            fname = os.path.join(args.dataDir, args.readPhoto, 'log.txt')
        scanConfigFile = ''
        if args.scanConfig!='':
            scanConfigFile = os.path.join(args.dataDir, args.scanConfig)
        pmm.checkPhoto(fname, reader, results.photoResults, scanConfigFile)
    #pmm.checkPlanarity(fname_planarityVacOff, fname_planarityVacOn, reader)

    #startGui(args)

    if args.dumpSize!='':
        results.sizeResults.dump(args.dumpSize)
    if args.dumpPhoto!='':
        results.photoResults.dump(args.dumpPhoto)

    #results.sizeResults.showSummary()
    #pmm.inspectSizeResults(results.sizeResults)

    results.save(pickleFile)
