#!/usr/bin/env python3

import sys

def configToScanFile(fnameIn, fnameOut):
    fin = open(fnameIn, 'r')
    fout = open(fnameOut, 'w')
    if fin==None or fout==None:
        return
    line1 = True
    for line in fin.readlines():
        if len(line)==0 or line[0]=='#':
            continue
        words = line.split()
        print(words)
        if len(words)>=3 and (words[2].find('Path')>=0 or words[2].find('Pad')>=0):
            continue
        else:
            if line1:
                fout.write(line)
                line1 = False
            else:
                fout.write('%s %s\n' % (words[0], words[1]))
    fin.close()
    fout.close()

if __name__ == '__main__':
    if len(sys.argv)>2:
        fnameIn = sys.argv[1]
        fnameOut = sys.argv[2]
        configToScanFile(fnameIn, fnameOut)
