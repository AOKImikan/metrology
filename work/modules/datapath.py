import glob
import os

def getFilelistModule():
    dnames = []  # define path list
    #files = glob.glob("/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM*")
    files = glob.glob("/nfs/space3/aoki/Metrology/HR/MODULE/20UPGM*")

    specialSNs = {
        '20UPGM22601022':'006',  # remeasured module
        '20UPGM22601026':'001',  # 001 is bad data
        '20UPGM22601027':'001',  # only 001
        '20UPGM22601029':'002',  # remeasured module
        '20UPGM22601030':'001',  # only 001
        '20UPGM22601034':'002',  # remeasured module
        '20UPGM22601035':'002',  # remeasured module
        '20UPGM22601036':'011',  # remeasured module
        '20UPGM22601038':'002',  # remeasured module
        '20UPGM22601042':'003',  # remeasured module
        '20UPGM22601045':'002',  # remeasured module
        '20UPGM22601046':'002',  # remeasured module
        '20UPGM22601047':'002',  # remeasured module
        '20UPGM22601049':'005',  # remeasured module
        '20UPGM22601051':'002',  # remeasured module
        '20UPGM22601061':'002',  # remeasured module
        '20UPGM22601066':'001',
        '20UPGM22601083':'001',  # 002,003 None data
    }
    for k,v in specialSNs.items():
        path = '/nfs/space3/aoki/Metrology/HR/MODULE/'+k+'/MODULE_ASSEMBLY/'+v
        dnames.append(path)

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

def getFilelistPCB(stage):
    dnames = []  # define path list
    files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/20UPGPQ*")
   
    specialSNs = {
        '20UPGPQ2601195':'n',
        '20UPGPQ2601132':'n',
        '20UPGPQ2601101':'001',
        '20UPGPQ2601158':'002',  # v1.1
        '20UPGPQ2601095':'003',  # 004 is not available        
    }
    for k,v in specialSNs.items():
        path = '/nfs/space3/aoki/Metrology/kekdata/Metrology/PCB/'+k+'/'+ stage +'/'+v
        dnames.append(path)

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

def getFilelistBare():
    dnames = []  # define path list
    files = glob.glob("/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/20UPG*")

    specialSNs = {
        '20UPGB42399001':'n',
        '20UPGB42399002':'n',
        '20UPGB42399003':'n',
        '20UPGB42302021':'n',
        '20UPGB42302022':'n'
     }
    for k,v in specialSNs.items():
        path = '/nfs/space3/aoki/Metrology/kekdata/Metrology/BARE_MODULE/'+k+'/BAREMODULERECEPTION/'+v
        dnames.append(path)

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

def getFilelistModuleBack():
    dnames = []  # define path list
    files = glob.glob('/nfs/space3/itkpixel/Metrology/results/MODULE/20UPGM*')
    #files = glob.glob("/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM*")

    specialSNs = {
        '20UPGM20231129':'n',
    }
    for k,v in specialSNs.items():
        path = '/nfs/space3/itkpixel/Metrology/results/MODULE/'+k+'/UNKNOWN/'+v
        #path = '/nfs/space3/aoki/Metrology/HR/MODULE/'+k+'/UNKNOWN/'+v
        dnames.append(path)

    for fn in files:
        sn = fn.split('/')[7]
        if sn in specialSNs:
            continue
        
        filepath = fn + '/UNKNOWN'  # stage
        if os.path.exists(filepath):  
            scanNumList = glob.glob(filepath+'/*')
            scanNumList.sort()
            count = len(scanNumList)
            dnames.append(scanNumList[count-1])
    return dnames
