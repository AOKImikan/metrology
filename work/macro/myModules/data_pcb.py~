import glob
import os

def specialize(sn, num):
    path = '/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/'+sn+'/BAREMODULERECEPTION/'+num
    return path 

def getFilelist():
    dnames = []  # define path list
    files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/20UPG*")

    specialSNs = {
    }
    for k,v in specialSNs.items():
        dnames.append(specialize(k,v))

    for fn in files:
        sn = fn.split('/')[8]
        if sn in specialSNs:
            continue
        
        filepath = fn + '/BAREMODULERECEPTION'  # stage
        if os.path.exists(filepath):  
            scanNumList = glob.glob(filepath+'/*')
            scanNumList.sort()
            count = len(scanNumList)
            dnames.append(scanNumList[count-1])
    return dnames
