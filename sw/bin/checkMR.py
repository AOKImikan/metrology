#!/usr/bin/env python3

import argparse

import pmm

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gui', dest='gui', 
                        type=bool, default=True, 
                        help='Use GUI')
    args = parser.parse_args()
    return args

def startGui(args):
    w = pmm.PmmWindow()
    w.buildGui()
    w.startLoop()

if __name__ == '__main__':
    args = parseArgs()
    if args.gui:
        startGui(args)
