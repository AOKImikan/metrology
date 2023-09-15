#!/usr/bin/env python3
import glob
import sys

args = sys.argv
files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/20UPG*")
files_2 = []
i=0
while i<len(files):
    name = files[i]+'/PCB_RECEPTION_MODULE_SITE/001'
    files_2.append(name)
    i += 1
print(files_2)
