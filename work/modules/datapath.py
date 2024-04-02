import glob
import os

def getFilelistModule():
    dnames = []  # define path list
    #files = glob.glob("/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM*")
    files = glob.glob("/nfs/space3/aoki/Metrology/HR/MODULE/20UPGM*")

    specialSNs = {
        '20UPGM22601022':'009',  # remeasured module  # 006 has no TR data  # 004 thicknes bad
        '20UPGM22601026':'002',  # 001 is bad data -> must remeasure!
        '20UPGM22601027':'001',  # only 001
        '20UPGM22601029':'002',  # remeasured module -> db_v2.json
        '20UPGM22601030':'001',  # only 001
        '20UPGM22601034':'002',  # remeasured module -> db_v2.json
        '20UPGM22601035':'002',  # remeasured module -> db_v2.json
        '20UPGM22601036':'011',  # remeasured module -> db_v2.json
        '20UPGM22601038':'002',  # remeasured module -> db_v2.json
        '20UPGM22601042':'003',  # remeasured module -> db_v2.json
        '20UPGM22601045':'002',  # remeasured module -> db_v2.json
        '20UPGM22601046':'002',  # remeasured module -> db_v2.json
        '20UPGM22601047':'002',  # remeasured module -> db_v2.json
        '20UPGM22601049':'005',  # remeasured module -> db_v2.json
        '20UPGM22601051':'002',  # remeasured module -> db_v2.json
        '20UPGM22601061':'002',  # remeasured module -> db_v2.json
        '20UPGM22601066':'003',  # re analyze
        '20UPGM22601076':'002',  # re analyze
        '20UPGM22601083':'001',  # 002,003 None data
        '20UPGM22601095':'001',  # 002,003,004 : cell back data
        '20UPGM22601125':'001',  # 002 Fmark is 0.0
        '20UPGM22601131':'001',  # 002 Fmark is 0.0
        '20UPGM22601137':'001',  # 002,003 None data
        '20UPGM22601138':'001',  # 002,004,005 None data, 003 BL is 0.0
        '20UPGM22601139':'001',  # 002,003,004 : cell back data
        '20UPGM22601140':'001',  # 002 None data
        '20UPGM22601141':'001',  # 002 None data
        '20UPGM22601143':'003',  # only 003 available
        '20UPGM22601146':'001',  # 002,003 Fmark 0.0, 004,005 : cell back data
        '20UPGM22601147':'001',  # 002 : cell back data
        '20UPGM22601148':'001',  # 002 : cell back data
        '20UPGM22601149':'001',  # 002-007 : cell back data
        '20UPGM22601150':'001',  # 002 : cell back data
        '20UPGM22601151':'001',  # 002,003 : cell back data
        '20UPGM22601152':'001',  # 002-008 : cell back data
        '20UPGM22601153':'001',  # 002-008 : cell back data
        '20UPGM22601155':'003',  # 002,004 : cell back data
        '20UPGM22601157':'001',  # 002 : cell back data
        '20UPGM22601158':'003',  # 004-006 : cell back data
        '20UPGM22601159':'001',  # 002 : cell back data
        '20UPGM22601160':'005',  # 006-010 : cell back data
        '20UPGM22601161':'001',  # 002-006 : cell back data
        '20UPGM22601162':'001',  # 002,003 : cell back data
        '20UPGM22601167':'001',  # 002 : cell back data
        '20UPGM22601168':'003',  # 002,004 : cell back data
        '20UPGM22601169':'003',  # 002,004,005 : cell back data
        '20UPGM22601171':'001',  # 002 : cell back data
        '20UPGM22601172':'001',  # 002 : cell back data
        '20UPGM22601176':'003',  # 002,004 : cell back data
        '20UPGM22601177':'001',  # 002-004 : cell back data
        '20UPGM22601180':'001',  # 002,003 : cell back data
        '20UPGM22601181':'001',  # 002,003 : cell back data
        '20UPGM22601182':'001',  # 002 : cell back data
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
        '20UPGPQ2601155':'001',
        '20UPGPQ2601159':'001',
        '20UPGPQ2601195':'n',
        '20UPGPQ2601105':'n',
        '20UPGPQ2601132':'n',
        '20UPGPQ2601101':'001',
        '20UPGPQ2601108':'005',
        '20UPGPQ2601158':'n',  # v1.1 002 is available
        '20UPGPQ2601095':'003',  # 004 is not available
        '20UPGPQ2601162':'n',  # different virsion?
        '20UPGPQ2601071':'n',  # different virsion?
        '20UPGPQ2601106':'n',  # different virsion?
        '20UPGPQ2601041':'n',  # different virsion?
        '20UPGPQ2601089':'n',  # different virsion?
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
    #files = glob.glob('/nfs/space3/aoki/Metrology/HR/MODULE/20UPGM*')
    files = glob.glob('/nfs/space3/itkpixel/Metrology/results/MODULE/20UPGM*')
    #files = glob.glob("/nfs/space3/tkohno/atlas/ITkPixel/Metrology/HR/MODULE/20UPGM*")

    specialSNs = {
        '20UPGM22601133':'003',
        '20UPGM22601134':'003',
        #'20UPGM22601136':'001',   
        '20UPGM22601137':'003', 
        #'20UPGM22601138':'004',
        #'20UPGM22601140':'001',
        #'20UPGM22601141':'001',
        # '20UPGM22601092':'011',
        # '20UPGM22601092':'n',
        # '20UPGM22601098':'022',
        # '20UPGM22601095':'n',
        # '20UPGM226XXXXX':'n',
        # '20UPGM22601133':'019',
        # '20UPGM22601136':'n',
        # '20UPGM22601137':'n',
    }

    for k,v in specialSNs.items():
        path = '/nfs/space3/itkpixel/Metrology/results/MODULE/'+k+'/MODULE_ASSEMBLY/'+v
        #path = '/nfs/space3/aoki/Metrology/HR/MODULE/'+k+'/MODULE_ASSEMBLY/'+v
        dnames.append(path)

    # for fn in files:
    #     sn = fn.split('/')[7]
    #     if sn in specialSNs:
    #         continue
        
    #     filepath = fn + '/UNKNOWN'  # stage
    #     if os.path.exists(filepath):  
    #         scanNumList = glob.glob(filepath+'/*')
    #         scanNumList.sort()
    #         count = len(scanNumList)
    #         dnames.append(scanNumList[count-1])
    return dnames
