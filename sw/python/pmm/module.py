#-----------------------------------------------------------------------
# pmm/module.py
# -------------
# Module design parameters
#-----------------------------------------------------------------------

mm = 1.0
um = 1.0E-3

class Rd53aModule: # Outer
    # Size
    SensorX = 34700*um # length
    SensorY = 41100*um # width
    AsicX = 18845*um # height
    AsicY = 20110*um # width
    AsicGapX = 140*um
    AsicGapY = 140*um
    AsicQuadX = AsicX*2 + AsicGapX
    AsicQuadY = AsicY*2 + AsicGapY
    FlexX = 20110*um
    FlexY = 20110*um
    SensorZ = 150*um
    AsicZ = 150*um
    GlueZ= 50*um
    FlexZ= 180*um
    # Coordinates
    SensorT = SensorY/2.0
    SensorB = -SensorY/2.0
    SensorL = SensorX/2.0
    SensorR = -SensorX/2.0
    AsicT = AsicQuadY/2.0
    AsicB = -AsicQuadY/2.0
    AsicL = AsicQuadX/2.0
    AsicR = -AsicQuadX/2.0
    FlexT = FlexY/2.0
    FlexB = -FlexY/2.0
    FlexL = FlexX/2.0
    FlexR = -FlexX/2.0
