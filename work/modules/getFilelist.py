#!/usr/bin/env python3
import glob
import sys
import os

args = sys.argv
files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/20UPG*")
dnames = []
for fn in files:
    filepath = fn + '/BAREMODULERECEPTION'
    if os.path.exists(filepath) :
        scanNumList = glob.glob(filepath+'/*')
        scanNumList.sort()
        count = len(scanNumList)
        dnames.append(scanNumList[count-1])
print(dnames)
