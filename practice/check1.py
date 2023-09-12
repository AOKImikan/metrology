#!/usr/bin/python3
import pickle
import pmm
import matplotlib.pyplot as plt

def openPickle():
    fname = '/nfs/space3/tkohno/atlas/ITkPixel/Metrology/pmmWork/MODULE/20UPGPQ2110110/PCB_RECEPTION_MODULE_SITE/002/data.pickle'
    fin = open(fname, 'rb')
    data = pickle.load(fin)
    return data

def run():
    data = openPickle()
    data = data.deserialize()
    sp = data.scanProcessors['ITkPixV1xModule.Size']
    points = sp.scanData.points
    vx = list(map(lambda p: p.get('x'), points))
    vy = list(map(lambda p: p.get('y'), filter(lambda x: x.get('y')>0.0, points)))
    vz = list(map(lambda p: p.get('z'), points))
    p0 = points[0]
    
    print(p0.get('index'),p0.get('x'), p0.get('tags'), p0.get('imagePath'))

    fig = plt.figure()
    
    ax = fig.add_subplot(2, 2, 1)
    ax.plot(vx)

    ax = fig.add_subplot(2, 2, 2)
    ax.plot(vy)

    ax = fig.add_subplot(2, 2, 3)
    ax.plot(vz)

    ax = fig.add_subplot(2, 2, 4)
    #ax.plot(vx, vy, linestyle='none', marker=',', markersize=20)
    plt.show()
    
if __name__ == '__main__':
    run()
    
