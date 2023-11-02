#!/usr/bin/env python3
import pickle
import pandas as pd
import argparse

def getData(scanData, sn, tagname):
    # serial number is exist?
    if sn in scanData['serial_number'].values:
        pass
    else:
        print('no serial number!')
        return

    # extract by serial number and tag
    group1 = scanData.groupby('serial_number')
    exDF_sn = group1.get_group(sn)  # extract serial number
    group2 = exDF_sn.groupby('tags')
    exDF_tag = group2.get_group(tagname)  # extract scan tag

    # delete unneccesary columns
    df = exDF_tag.drop(['qc_stage'], axis=1)

    # get image path
    imagepath = df['image_path'].iloc[0]
    directry = imagepath.split('/')
    filepath = ''
    for d in directry:
        if '.jpg' in d:
            break
        else:
            filepath = filepath + d + '/'
    print('file path :')
    print(filepath)  # print directry path

    # set images file name column
    df['filename'] = df['image_path'].str.split('/').str.get(-1)
    df = df.drop('image_path', axis=1)  # delete image_path column

    # set print option
    pd.set_option('display.max_rows',None)
    pd.set_option('display.max_columns',None)
    
    print(df)
    
if __name__ == '__main__':
    # make parser
    parser = argparse.ArgumentParser()

    # add argument
    parser.add_argument('sn', help='serial number')
    parser.add_argument('tag', help='tag name')
    
    parser.add_argument('-f', '--flex', help='PCB, Flex', action='store_true')
    parser.add_argument('-b', '--bare', help='BAREMODULE', action='store_true')
    parser.add_argument('-m', '--module', help='MODULE ASSEMBLY', action='store_true')

    args = parser.parse_args()  # analyze arguments

    if args.flex:
        with open(f'data/PCB_ScanData.pkl', 'rb') as fin:
            scanData = pickle.load(fin)
        with open(f'data/PCB_AnalysisData.pkl', 'rb') as fin:
            analysisData = pickle.load(fin)
            
        getData(scanData, args.sn, args.tag)
        
    elif args.bare:
        with open(f'data/BAREMODULE_ScanData.pkl', 'rb') as fin:
            scanData = pickle.load(fin)
        with open(f'data/BAREMODULE_AnalysisData.pkl', 'rb') as fin:
            analysisData = pickle.load(fin)

        getData(scanData, args.sn, args.tag)
                
    elif args.module:
        with open(f'data/MODULE_ScanData.pkl', 'rb') as fin:
            scanData = pickle.load(fin)
        with open(f'data/MODULE_AnalysisData.pkl', 'rb') as fin:
            analysisData = pickle.load(fin)

        getData(scanData, args.sn, args.tag)

    else:
        print('no command! type -h or --help')            
