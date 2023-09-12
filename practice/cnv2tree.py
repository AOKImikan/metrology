#!/usr/bin/python3
import os
import numpy as np
import ROOT

class PointData:
    def __init__(self, sn='', x=0.0, y=0.0, z=0.0, tags=[], imageFile=''):
        self.createData()
        self.setData(sn, x, y, z, tags, imageFile)
        
    def setData(self, sn='', x=0.0, y=0.0, z=0.0, tags=[], imageFile=''):
        self.setSerialNumber(sn)
        self.setX(x)
        self.setY(y)
        self.setZ(z)
        self.setTags(tags)
        self.setImageFile(imageFile)

    def setSerialNumber(self, sn):
        self.serialNumber.clear()
        self.serialNumber.append(sn)

    def setImageFile(self, imageFile):
        self.imageFile.clear()
        self.imageFile.append(imageFile)

    def setTags(self, tags):
        self.tags.clear()
        for tag in tags:
            self.tags.push_back(tag)

    def setX(self, x):
        self.x[0] = x
        
    def setY(self, y):
        self.y[0] = y
        
    def setZ(self, z):
        self.z[0] = z
        
    def createData(self):
        self.serialNumber = ROOT.string()
        self.x = np.empty( (1), dtype='float32')
        self.y = np.empty( (1), dtype='float32')
        self.z = np.empty( (1), dtype='float32')
        self.tags = ROOT.vector('std::string')()
        self.imageFile = ROOT.string()
        
def createTree(treeName, data):
    t = ROOT.TTree(treeName, 'Metrology scan points')
    t.Branch('serialNumber', data.serialNumber)
    t.Branch('x', data.x, 'x/F')
    t.Branch('y', data.y, 'y/F')
    t.Branch('z', data.z, 'z/F')
    t.Branch('tags', data.tags)
    t.Branch('imageFile', data.imageFile)
    return t

def run():
    treeName = 't'
    fileName = 'summary.root'
    tags = 'A,B'
    data = PointData(sn='20UPGM', x=1.1, y=2.1, z=3.15, tags=tags.split(','),
                     imageFile='abc.jpg')
    fin = ROOT.TFile.Open(fileName, 'RECREATE')
    t = createTree(treeName, data)
    t.SetDirectory(fin)
    #
    for i in range(100):
        if (i%10)==0:
            data.setSerialNumber(f'20UPGM__{int(i/10):03d}')
        if (i%10) == 0:
            data.setTags(['A'])
        elif (i%10) == 1:
            data.setTags(['B'])
        elif (i%10) == 2:
            data.setTags(['C'])
        elif (i%10) == 3:
            data.setTags(['D'])
        elif (i%10) >= 4:
            data.setTags(['E', 'F', 'G', 'H'])
        data.setX(i)
        data.setY(1000 + i)
        data.setZ(10000 + i)
        t.Fill()
    #
    t.Write()
    fin.Write()
    fin.Close()
    
if __name__ == '__main__':
    run()
    
