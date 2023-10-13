import glob
import os

def specialize(sn, num,stage):
    path = '/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/'+sn+'/'+ stage +'/'+num
    return path 

def getFilelist(stage):
    dnames = []  # define path list
    files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/20UPGPQ*")
   
    specialSNs = {
        '20UPGPQ2601132':'n',
        '20UPGPQ2601158':'n',
        '20UPGPQ2601154':'n',
        '20UPGPQ2601167':'n',
        '20UPGPQ2601013':'n',
        '20UPGPQ2601027':'n',
        '20UPGPQ2601032':'n',
        '20UPGPQ2601168':'n',
        '20UPGPQ2601169':'n',
        '20UPGPQ2601171':'n',
        '20UPGPQ2601176':'n',
        '20UPGPQ2601177':'n',
        '20UPGPQ2601178':'n',
        '20UPGPQ2601179':'n',
        '20UPGPQ2601180':'n',
        '20UPGPQ2601181':'n',
        '20UPGPQ2601101':'001'
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
