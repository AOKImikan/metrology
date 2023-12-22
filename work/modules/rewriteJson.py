#!/usr/bin/env python3
import pickle
import json
import os
import math
import logging
import pmm
from pmm.model import *
from pmm.tools import *

logger = logging.getLogger(__name__)

def LoadData(dn):
    appdata = None
    if os.path.exists(dn):
        with open(f'{dn}/data.pickle', 'rb') as fin:
            appdata = pickle.load(fin)
            appdata = appdata.deserialize()
    if appdata:
        sp = appdata.getScanProcessor('ITkPixV1xModule.Size')
    return sp

def calcDist(points):
    fmt = '5.3f'
    p1 = points[0]
    p2 = points[1]
    dx = roundF(math.fabs(p1[0]-p2[0]), fmt)
    dy = roundF(math.fabs(p1[1]-p2[1]), fmt)
    return [dx,dy]

def getPoints(sp, tag):  # name is TL or BR
    points = []
    tag1 = 'AsicFmark' + tag + '_0_point'
    tag2 = 'Fmark' + tag + '_0_point'
    patternAnalysis = sp.analysisList[0]
    for k,v in patternAnalysis.outData.items():
        if (tag1 in k) or (tag2 in k):
            if v is None:
                logger.warning(f'nodata!')
                return None
            else:
                points.append([v.position[0], v.position[1]])  # Fill detect x
    return points

def main():
    dnames = []
    with open('./filelist.txt') as f:
        for line in f:
            directory = os.path.dirname(line)
            dnames.append(directory)
    #dnames1 = ['/nfs/space3/aoki/Metrology/HR/MODULE/20UPGM22601088/MODULE_ASSEMBLY/001'] #test
    for dn in dnames:
        logger.info(f'load {dn}')
        
        inputdb = dn + '/db_v0.json'
        outputdb = dn + '/db.json'
        input_file = open(inputdb,'r')
        #output_file = open(outputdb,'r')

        data = json.load(input_file)
        results = data['results']
        print(results)
            
        sp = LoadData(dn)
        pointsTL = getPoints(sp,'TL')
        pointsBR = getPoints(sp,'BR')
        if (pointsTL is None) or (pointsBR is None):
            pass
        else:
            distTL = calcDist(pointsTL)
            distBR = calcDist(pointsBR)
            print(distTL, distBR)
            results['PCB_BAREMODULE_POSITION_TOP_RIGHT'] = distTL
            results['PCB_BAREMODULE_POSITION_BOTTOM_LEFT'] = distBR
            print(results)
            #json.dump(data, output_file, indent=2)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
