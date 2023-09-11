#-----------------------------------------------------------------------
# ScanConfig list
# ---------------
# Format:
# x    y     TagList     [Scan]
# 20.0 -18.0 FlexT,FlexL size,height
#-----------------------------------------------------------------------

class ScanConfigList:
    def __init__(self):
        self.pickupList = []
        self.heightList = []
        self.sizeList = []
        self.flatnessList = []
        self.setup()

    def setup(self):
        self.setupRd53aModule()
        self.setupITkPixV10Module()

    def extendLists(self, pickupList, heightList, sizeList, flatnessList):
        self.extendPickupList(pickupList)
        self.extendHeightList(heightList)
        self.extendSizeList(sizeList)
        self.extendFlatnessList(flatnessList)

    def extendPickupList(self, v):
        allList = self.pickupList
        for x in v:
            if not x in allList:
                allList.append(x)
    def extendHeightList(self, v):
        allList = self.heightList
        for x in v:
            if not x in allList:
                allList.append(x)
    def extendSizeList(self, v):
        allList = self.sizeList
        for x in v:
            if not x in allList:
                allList.append(x)
    def extendFlatnessList(self, v):
        allList = self.flatnessList
        for x in v:
            if not x in allList:
                allList.append(x)

    def setupRd53aModule(self):
        pickupList = [
            'Rd53aModule_pickup_20220312',
            'Rd53aModule_pickup_20220216',
        ]
        heightList = [
            'Rd53aModule_height_20220312',
            'Rd53aModule_height_20220216', 
            'height_v1.0', 
        ]
        sizeList = [
            'Rd53aModule_size_20220312', 
            'Rd53aModule_size_v1.1', 'Rd53aModule_size_v20210713.1',
        ]
        flatnessList = [
            #'Rd53aModule_flatness_v1.0', 
        ]
        self.extendLists(pickupList, heightList, sizeList, flatnessList)

    def setupITkPixV10Module(self):
        pickupList = [
        ]
        heightList = [
            'ITkPixV1.0Flex_v1.0', 
            'ITkpixv1.0Module_height_20220414', 
        ]
        sizeList = [
            'ITkPixV1.0Flex_v1.0', 
            'ITkpixv1.0Module_size_20220318',
        ]
        flatnessList = [
        ]
        self.extendLists(pickupList, heightList, sizeList, flatnessList)

