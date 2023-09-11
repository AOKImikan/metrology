#!/usr/bin/env python3

import os
import argparse

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--logFile', dest='logFile',
                        type=str, default='log.txt', 
                        help='Name of the log file (input)')
    parser.add_argument('-c', '--scanConfigFile', dest='scanConfigFile',
                        type=str, default='scanconfig.txt', 
                        help='Name of the scan config file (output)')
    return parser.parse_args()

def log2Config(logFile, configFile):
    fin = None
    if os.path.exists(logFile):
        fin = open(logFile, 'r')
    else:
        print('Input log file %s does not exist' % logFile)
        return -1
    if os.path.exists(configFile):
        print('Output file %s already exists. Remove it first' % configFile)
        return -2
    fout = open(configFile, 'w')
    sc = configFile.replace('ScanConfig_', 'ScanConfig:')
    sc = sc.replace('.txt', '')
    fout.write('#%s\n' % sc)
    for line in fin.readlines():
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue
        words = line.split()
        x, y, z = 0, 0, 0
        if len(words) == 3:
            x = float(words[0])*0.001
            y = -float(words[1])*0.001
            z = float(words[2])
        fout.write('%7.3f %7.3f\n' % (x, y) )
    fout.close()
if __name__ == '__main__':
    args = parseArgs()
    log2Config(args.logFile, args.scanConfigFile)
    
