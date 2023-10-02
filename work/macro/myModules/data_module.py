import glob
import os

def specialize(sn, num):
    path = '/nfs/space3/aoki/Metrology/HR/MODULE/'+sn+'/MODULE_ASSEMBLY/'+num
    return path 

def getFilelist():
    dnames = []  # define path list
    #files = glob.glob("/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM*")
    files = glob.glob("/nfs/space3/aoki/Metrology/HR/MODULE/20UPGM*")

    specialSNs = {
        '20UPGM22601066':'nan',
        '20UPGM22601034':'001',
        '20UPGM22601049':'005',
        '20UPGM22601027':'001',  # only 001
        '20UPGM22601038':'001',  # only 001
        '20UPGM22601026':'001',  # 001 is bad data
        '20UPGM22601030':'001',  # only 001
        '20UPGM22601045':'001',  # only 001
    }
    for k,v in specialSNs.items():
        dnames.append(specialize(k,v))

    for fn in files:
        sn = fn.split('/')[7]
        if sn in specialSNs:
            continue
        
        filepath = fn + '/MODULE_ASSEMBLY'  # stage
        if os.path.exists(filepath):  
            scanNumList = glob.glob(filepath+'/*')
            scanNumList.sort()
            count = len(scanNumList)
            dnames.append(scanNumList[count-1])
    return dnames
