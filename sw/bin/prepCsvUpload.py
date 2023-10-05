#!/usr/bin/env python3
import os, sys
import argparse
import pickle
import json
import datetime

import pyexcel
import pmm

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--db-file', dest='dbFile',
                        type=str, default='', 
                        help='Input db.json file')
    parser.add_argument('-t', '--template-csv-file', dest='templateCsvFile',
                        type=str, default='', 
                        help='Template *.csv file')
    parser.add_argument('-s', '--sn', dest='SN',
                        type=str, default='', 
                        help='Serial number of the component')
    parser.add_argument('-o', '--output-csv-file', dest='outputCsvFile',
                        type=str, default='out.csv', 
                        help='Output *.csv file')
    
    return parser.parse_args()

def roundF(x, fmt='%6.3f'):
    x2 = x
    if type(x).__name__ in ('float', 'float64'):
        x2 = fmt % a
    elif type(x).__name__ == 'list':
        y = []
        for a in x:
            aa = a
            if type(a).__name__ in ('float', 'float64'):
                aa = fmt % a
            y.append(aa)
        x2 = y
    return x2

def boolStr(tf):
    x = ''
    if tf:
        x = 'TRUE'
    else:
        x = 'FALSE'
    return x

def createMaps(sheet):
    columns = sheet.columns()
    m1, m2 = {}, {}
    for ic, column in enumerate(columns):
        c1, c2 = column[0], column[1]
        if type(c1) == type(''): c1 = c1.strip()
        if type(c2) == type(''): c2 = c2.strip()
        m1[c1] = ic
        m2[c2] = ic
    return m1, m2

def outputPcb(data, sheet):
    propertyNames = [ 'CUTVERSION', 'OPERATOR' ]
    resultKeys = [
        'X_DIMENSION', 'Y_DIMENSION', 'X-Y_DIMENSION_WITHIN_ENVELOP',
        'AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS',
        'STD_DEVIATION_THICKNESS_FECHIP_PICKUP_AREAS',
        'HV_CAPACITOR_THICKNESS', 'HV_CAPACITOR_WITHIN_ENVELOP', 
        'AVERAGE_THICKNESS_POWER_CONNECTOR', 
        'DIAMETER_DOWEL_HOLE_A', 'WIDTH_DOWEL_SLOT_B',
        ]
    row1map, row2map = createMaps(sheet)
    nrows = sheet.number_of_rows()
    irow = nrows
    properties_offset = 7
    results_offset = properties_offset + 6
    sheet[irow,0] = irow-1
    sheet[irow,1] = data['component']
    sheet[irow,2] = data['componentType']
    sheet[irow,3] = data['stage']
    sheet[irow,4] = data['testType']
    sheet[irow,5] = data['date']
    sheet[irow,6] = str(data['runNumber'])
    # Properties
    for ip, pn in enumerate(propertyNames):
        value = ''
        if ip == 0: value = '1'
        sheet[irow,properties_offset+2*ip+0] = pn
        sheet[irow,properties_offset+2*ip+1] = value
    sheet[irow,properties_offset+4] = boolStr(True)
    sheet[irow,properties_offset+5] = boolStr(False)
    # Results
    results = data['results']
    for ir, key in enumerate(resultKeys):
        value = results[key]
        if type(value) == type([]):
            value = str(value).replace('[', '{').replace(']', '}')
        else:
            if type(value) == type(True):
                value = boolStr(value)
        sheet[irow,results_offset+2*ir+0] = key
        sheet[irow,results_offset+2*ir+1] = value
    pass

def run(dataFile, csvFile, args=None):
    fn_data = dataFile
    fn_out = args.outputCsvFile
    #
    # Read CSV template
    sheet = None
    if os.path.exists(fn_out):
        sheet = pyexcel.get_sheet(file_name=fn_out)
    else:
        fn_csvTemplate = args.templateCsvFile
        sheet = pyexcel.get_sheet(file_name=fn_csvTemplate)
    print(fn_data)
    fin = open(fn_data, 'r')
    data = json.load(fin)
    #
    if data['componentType'] == 'PCB':
        outputPcb(data, sheet)
    pyexcel.save_as(array=sheet, dest_file_name=fn_out,
                    dest_delimiter=',')
    print(f'Created CSV file to upload as {fn_out}')
    
if __name__ == '__main__':
    args = parseArgs()
    dataFile = args.dbFile
    templateFile = args.templateCsvFile
    input_ready = True
    if not os.path.exists(dataFile):
        print(f'Input data file {dataFile} does not exist')
        input_ready = False
    if not os.path.exists(templateFile):
        print(f'CSV template {templateFile} does not exist')
        input_ready = False
    #
    if input_ready:
        run(dataFile, templateFile, args)
    else:
        sys.exit(-1)
        
        
