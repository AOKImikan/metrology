#!/usr/bin/env python3

import os, sys
import re
import pickle
import numpy as np
import matplotlib.pyplot as plt

import argparse

def inspectScans(args):
    fin = None
    jdata = None
    if os.path.exists(args.pickleFile):
        fin = open(args.pickleFile, 'rb')
        pdata = pickle.load(fin)

    if args.listContents:
        if pdata:
            for k in pdata.keys():
                print(k)
        return
    elif args.scanName!='':
        data = None
        if args.scanName in pdata.keys():
            data = pdata[args.scanName]
            print('data ready', data)
            x = np.arange(len(data))
            print('x ', x)
            plt.plot(x, data)
            plt.show()
        else:
            print('Cannot find scan %s' % (args.scanName) )
    pass

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list-contents', dest='listContents', 
                        action='store_true', default=False, 
                        help='List contents of the pickle file')
    parser.add_argument('-f', '--pickle-file', dest='pickleFile', 
                        type=str, default='', 
                        help='Filename of the picke file')
    parser.add_argument('-s', '--scanName', dest='scanName', 
                        type=str, default='', 
                        help='Plot the scan results')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parseArgs()
    inspectScans(args)
