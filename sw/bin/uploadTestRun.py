#!/usr/bin/env python3
import os
import argparse
import json
import itkdb

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test-results', dest='testResults',
                        type=str, default='',
                        help='Test results *.json format')
    parser.add_argument('-s', '--stage', dest='stage',
                        type=str, default='',
                        help='Set the stage to the specified one before uploading the test run')
    parser.add_argument('-l', '--location', dest='location',
                        type=str, default='',
                        help='Location of the component to be manipulated')
    return parser.parse_args()

def readTestRun(fn):
    data = None
    if os.path.exists(fn):
        with open(fn, 'r') as fin:
            data = json.load(fin)
    else:
        print(f'Test results (.json) file {fn} does not exist')
    return data

def dumpComponent(component):
    for k in component.keys():
        if k in ('id', 'code', 'serialNumber', 'project', 'institution',
                 'currentLocation', 'user', 'componentType', 'type',
                 'currentStage'):
            print(f'{k:20s} => {component[k]}')

def setComponentStage(client, component, stage):
    data = {

        'stage': stage,
        'rework': False,
        'comment': '',
        'file': {}
        }
    client.post('setComponentStage', json=data)
    
def correctTestRunData(data):
    results = data['results']
    stage = data['stage']
    if stage == 'BAREMODULERECEPTION':
        print('Correct test run data')
        results['BARE_MODULE_THICKNESS'] = results['BAREMODULE_THICKNESS']
        results['BARE_MODULE_THICKNESS_STD_DEVIATION'] = results['BAREMODULE_THICKNESS_STD_DEVIATION']
        results.pop('BAREMODULE_THICKNESS')
        results.pop('BAREMODULE_THICKNESS_STD_DEVIATION')
    elif stage == 'PCB_RECEPTION':
        results['HV_CAPACITOR_THICKNESS'] = 0.0
        results['AVERAGE_THICKNESS_POWER_CONNECTOR'] = 0.0

def run(args):
    client = itkdb.Client()
    client.user.authenticate()
    user = client.get('getUser', json={'userIdentity': client.user.identity})
    print('User associated to:  ', [institution['code'] for institution in user['institutions']])

    data = readTestRun(args.testResults)
    if data == None:
        print('Could not read the test run, finishing ...')
        return
    sn = data['component']
    institution = data['institution']
    component = client.get('getComponent', json={'component': sn})

    status = True
    serialNumber = component['serialNumber']
    location1 = component['currentLocation']['code']
    stage1 = component['currentStage']['code']
    if serialNumber != sn:
        print(f'  Serial number of the component {serialNumber} differs from the one in the test run')
        status = False
    if location != institution:
        print(f'  Current location of the component {location1} differs from the one specified in the test run: {institution}')
        status = False
    if not status:
        print('Change the location before uploading the test run')
        return

    correctTestRunData(data)
    print(data)
    print('----------------------------------------------')
    print(f'  SerialNumber       : {serialNumber}')
    print(f'  CurrentLocation    : {location1}')
    print(f'  CurrentStage       : {stage1}')
    print('----------------------------------------------')
    changeStage = False
    if args.stage != '' and stage1 != args.stage:
        changeStage = True
    if changeStage:
        print(f'    Change the stage: {stage1} -> {args.stage}')
        setComponentStage(client, args.stage)
    client.post('uploadTestRunResults', json=data)
    if changeStage:
        print(f'    Change back the stage: {args.stage} -> {stage1}')
        setComponentStage(client, stage1
if __name__ == '__main__':
    args = parseArgs()
    run(args)

