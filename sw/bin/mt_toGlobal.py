#!/usr/bin/env python3

z_umPerPulse = 0.156 # um/pulse (AF)
NEAREND = 334791*z_umPerPulse # [um]

def toGlobal(xyz):
    r = 1.0E-3
    x = -xyz[0]*r
    y = -xyz[1]*r
    z = (NEAREND - xyz[2])*r
    return [x, y, z]

def readLog2(logfile):
    f = open(logfile, 'r')
    data = []
    for line in f.readlines():
        if len(line)==0 or line[0]=='#': continue
        words = line.split()
        x = float(words[0])
        y = float(words[1])
        z = float(words[2])
        jpg = words[3]
        xyz = toGlobal([x, y, z])
        entry = xyz + [jpg]
        data.append(entry)
    f.close()
    return data
        
def readMTFile(filename):
    f = open(filename, 'r')
    data = []
    for line in f.readlines():
        if len(line)==0 or line[0]=='#': continue
        words = line.split()
        imageFile = words[0]
        c1 = float(words[1])
        r1 = float(words[2])
        c2 = float(words[3])
        r2 = float(words[4])
        name = words[5]
        c = (x1+x2)/2.0
        r = (y1+y2)/2.0
        entry = [ imageFile, c, r, name ]
        data.append(entry)
    f.close()

def createMap(data):
    m = {} # string -> data
    for x in data:
        m[x[3]] = x
    return m

if __name__ == '__main__':
    logFile = '../data/20211201/tray-1pic_83/log2.txt'
    mtFile = '../data/20211201/tray-1pic_83/log2.txt'
    data = readLog2(logFile)
    logMap = createMap(data)
    zoom = 2
    #dataMT = readMTFile(mtFile)
    dataMT = [
        [ 'Img15780.jpg', 3000, 2000 ], 
        [ 'Img15790.jpg', 3001, 2001 ], 
    ]
    dx20 = (0.39E-3)/2.0
    dx = dx20*20/zoom # pixel size at zoom=2
    print('Pixel size {} [mm]'.format(dx))
    for data in dataMT:
        img = data[0]
        xydata = logMap[img]
        #print(data, xydata)
        col = data[1]
        row = data[2]
        X = xydata[0]
        Y = xydata[1]
        x = -X + (col-3000)*dx
        y = -Y + -(row-2000)*dx
        print('(col,row)=({0:6.3f},{1:6.3f}), (X,Y)=({2:6.3f},{3:6.3f}) => (x,y)=({4:6.3f},{5:6.3f})'.format(col, row, X, Y, x, y) )



