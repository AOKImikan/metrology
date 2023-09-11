#!/usr/bin/env python3

import os
import argparse

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--scanConfigFile', dest='scanConfigFile',
                        type=str, default='ScanConfig.txt', 
                        help='Name of the scan config file (input)')
    parser.add_argument('-p', '--scanPointsFile', dest='scanPointsFile',
                        type=str, default='scanPoints.txt', 
                        help='Name of the scan points file (output)')
    return parser.parse_args()

def config2Points(configFile, pointsFile):
    fin = None
    if os.path.exists(configFile):
        fin = open(configFile, 'r')
    else:
        print('Input ScanConfig file %s does not exist' % configFile)
        return -1
    if os.path.exists(pointsFile):
        print('Output file %s already exists. Remove it first' % pointsFile)
        return -2
    fout = open(pointsFile, 'w')
    sc = configFile.replace('.txt', '').replace('ScanConfig_', 'ScanConfig:')
    fout.write('0 %s\n' % sc)
    for line in fin.readlines():
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue
        words = line.split()
        x, y, z = 0, 0, 0
        if len(words) >= 2:
            x = -float(words[0])
            y = -float(words[1])
        fout.write('%7.3f %7.3f\n' % (x, y) )
    fout.close()
if __name__ == '__main__':
    args = parseArgs()
    config2Points(args.scanConfigFile, args.scanPointsFile)
    
