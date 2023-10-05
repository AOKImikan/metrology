#!/usr/bin/env python3
#------------------------------------------------------------------------
# Take the inputJSON as the base and use some data from the secondaryJSON
# to overwrite data in the base, and output the modified contents to the
# outputJSON.
# 
# inputJSON + secondaryJSON (partial) --> outputJSON
#
#------------------------------------------------------------------------
import os, sys
import argparse
import json
import pmm

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-json', dest='inputJson',
                        type=str, default='', 
                        help='Input JSON file with upload data')
    parser.add_argument('-s', '--secondary-json', dest='secondaryJson',
                        type=str, default='', 
                        help='Output JSON file name')
    parser.add_argument('-o', '--output-json', dest='outputJson',
                        type=str, default='', 
                        help='Output JSON file name')
    parser.add_argument('-e', '--show-examples', dest='showExamples',
                        action='store_true', default=False,
                        help='Show examples')
    return parser.parse_args()

def showExamples():
    print('Examples:')
    cmd = os.path.basename(sys.argv[0])
    print(f'{cmd} -i base.json -s partiallyNew.json -o new.json')
    
def readData(fn):
    data = None
    if os.path.exists(fn):
        with open(fn, 'r') as fin:
            data = json.load(fin)
    else:
        print(f'File {fn} does not exist')
    return data

def modifyHeightData(data, secData):
    r1 = data['results']
    r2 = secData['results']
    if data['componentType'] == 'MODULE':
        keys = [
            'AVERAGE_THICKNESS', 'STD_DEVIATION_THICKNESS', 
            'THICKNESS_VARIATION_PICKUP_AREA', 
            'THICKNESS_INCLUDING_POWER_CONNECTOR', 
            'HV_CAPACITOR_THICKNESS', 
        ]
        for key in keys:
            r1[key] = r2[key]

def saveData(data, fn):
    if os.path.exists(fn):
        print(f'File {fn} already exists, will not overwrite')
    else:
        dn = os.path.dirname(fn)
        if dn == '' or os.path.isdir(dn):
            with open(fn, 'w') as fout:
                print(f'Saving modified data to {os.path.abspath(fn)}')
                json.dump(data, fout, indent=2)

def run(args):
    data = readData(args.inputJson)
    secData = readData(args.secondaryJson)
    if data and secData:
        modifyHeightData(data, secData)
        saveData(data, args.outputJson)
    pass

if __name__ == '__main__':
    args = parseArgs()
    if args.showExamples:
        showExamples()
        sys.exit(0)
    run(args)
    
