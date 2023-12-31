#!/usr/bin/env python3
import os
import pickle
import logging
import ROOT

logger = logging.getLogger(__name__)

dirs = [
    '../results/PCB/20UPGPQ2601015/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601016/PCB_POPULATION/004', 
    '../results/PCB/20UPGPQ2601020/PCB_POPULATION/002', 
    '../results/PCB/20UPGPQ2601021/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601022/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601023/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601024/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601025/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601026/PCB_POPULATION/002', 
    '../results/PCB/20UPGPQ2601027/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601029/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601030/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601031/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601032/PCB_POPULATION/002', 
    '../results/PCB/20UPGPQ2601033/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601034/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601035/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601036/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601037/PCB_POPULATION/001', 
    '../results/PCB/20UPGPQ2601038/PCB_POPULATION/001'
]

def readData(parFunc, parName):
    values = []
    pickleName = 'data.pickle'
    fname = ''
    for dn in dirs:
        fname = os.path.join(dn, pickleName)
        if not os.path.exists(fname):
            logger.error(f'File ${fname} does not exist')
            continue
        with open(fname, 'rb') as fin:
            data = pickle.load(fin)
            data = data.deserialize()
            x = parFunc(data, parName)
            values.append(x)
    return values

def createHist(parName, values, nbins, xmin, xmax):
    h = ROOT.TH1F(f'h_{parName}', '', nbins, xmin, xmax)
    for x in values:
        h.Fill(x)
    h.SetFillStyle(3001)
    h.SetFillColor(ROOT.kBlue)
    return h
    
if __name__ == '__main__':
    def accessSizeValue(doc, parName):
        sp = doc.scanProcessors['ITkPixV1xFlex.Size']
        data = sp.analysisList[1].outData
        return data[parName].get('value')
    def accessHeightValue(doc, parName):
        sp = doc.scanProcessors['ITkPixV1xFlex.Height']
        data = sp.analysisList[0].outData
        return data[parName].get('value')
    def accessHeightError(doc, parName):
        sp = doc.scanProcessors['ITkPixV1xFlex.Height']
        data = sp.analysisList[0].outData
        return data[parName].get('error')
    #
    logging.basicConfig(level=logging.INFO)
    ROOT.gStyle.SetOptStat(111111)
    fout = ROOT.TFile.Open('work/pars20230519.root', 'RECREATE')
    #
    parName = 'FlexX'
    values = readData(accessSizeValue, parName)
    h = createHist(parName, values, 100, 39.400, 39.800)
    h.Write()
    #
    parName = 'FlexY'
    values = readData(accessSizeValue, parName)
    h = createHist(parName, values, 100, 40.000, 40.600)
    h.Write()
    #
    parName = 'PickupZ'
    values = readData(accessHeightValue, parName)
    h = createHist(parName, values, 100, 0.150, 0.250)
    h.Write()
    #
    parName = 'PickupZ'
    values = readData(accessHeightError, parName)
    h = createHist(parName+'_stddev', values, 100, 0.0, 0.03)
    h.Write()
    #
    parName = 'HVCapacitorZ'
    values = readData(accessHeightValue, parName)
    h = createHist(parName, values, 100, 1.0, 2.500)
    h.Write()
    #
    parName = 'ConnectorZ'
    values = readData(accessHeightValue, parName)
    h = createHist(parName, values, 100, 1.0, 2.000)
    h.Write()
    #
    #fout.Write()
    
