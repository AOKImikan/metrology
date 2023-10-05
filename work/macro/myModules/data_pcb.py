import glob
import os

def specialize(sn, num,stage):
    path = '/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/'+sn+'/'+ stage +'/'+num
    return path 

def getFilelist(stage):
    dnames = []  # define path list
    files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/20UPGPQ*")
   
    specialSNs = {
        '20UPGPQ2601115':'n'
    }
    for k,v in specialSNs.items():
        dnames.append(specialize(k,v,stage))

    for fn in files:
        sn = fn.split('/')[8]
        if sn in specialSNs:
            continue
        
        filepath = fn + '/' + stage  # stage
       
        if os.path.exists(filepath):  
            scanNumList = glob.glob(filepath+'/*')
            scanNumList.sort()
            count = len(scanNumList)
            dnames.append(scanNumList[count-1])

    return dnames
