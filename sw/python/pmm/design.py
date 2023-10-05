#--------------------------------------------------------------------
# Pixel Module Metrology Analysis (Design specification)
# 
# Unit: mm
# Module coordinate system: origin at the middle
#                           x (towards right) and y (towards top)
#--------------------------------------------------------------------
import math
import logging

from pmm.prec import *
from pmm.model import *

logger = logging.getLogger(__name__)

class SensorOuter150um:
    def __init__(self):
        self.lengthX = 40.300
        self.lengthY = 41.100
        self.thickness = 0.150
    def xmin(self):
        return -self.lengthX/2
    def xmax(self):
        return self.lengthX/2
    def ymin(self):
        return -self.lengthY/2
    def ymax(self):
        return self.lengthY/2

class AsicRd53a:
    def __init__(self):
        self.lengthX = 21.050
        self.lengthY = 20.100
        self.thickness = 0.150
    def xmin(self):
        return -self.lengthX/2
    def xmax(self):
        return self.lengthX/2
    def ymin(self):
        return -self.lengthY/2
    def ymax(self):
        return self.lengthY/2

class FlexRd53a:
    def __init__(self):
        self.lengthX = 40.5
        self.lengthY = 40.5
        self.thickness = 0.150
        self.heightHvCapacitor = 2.275
        self.heightZifConnector = 1.675
        pass
    def xmin(self):
        return -self.lengthX/2
    def xmax(self):
        return self.lengthX/2
    def ymin(self):
        return -self.lengthY/2
    def ymax(self):
        return self.lengthY/2

class TargetData:
    def __init__(self, name, ptype, x, y, r=None):
        self.name = name
        self.ptype = ptype
        self.x = x
        self.y = y
        self.r = r

    def value(self):
        v = None
        if self.ptype == 'LineH':
            v = self.y
        elif self.ptype == 'LineV':
            v = self.x
        elif self.ptype == 'Vertex':
            v = (self.x, self.y)
        elif self.ptype == 'Circle':
            v = (self.x, self.y, self.r)
        return v

class ComponentDesign:
    def __init__(self):
        self.targetData = {}
        self.valueToleranceData = {}
    def isInTolerance(self, key, value):
        status = 'None'
        if key in self.valueToleranceData.keys():
            v, t = self.valueToleranceData[key]
            if v and t:
                vmin = v - t
                vmax = v + t
                if value >= vmin and value <= vmax:
                    status = 'Pass'
                else:
                    status = 'Fail'
            else:
                status = 'NoCheck'
        return status
    def targetString(self, tag, offsetXY, zoom):
        tdata = None
        s = ''
        return s
    def dump(self):
        pass
    
class BareModuleFront(ComponentDesign):
    def __init__(self):
        super().__init__()
        self.asic = AsicRd53a()
        self.sensor = SensorOuter150um()
        self.flex = FlexRd53a()
        self.bumpThickness = 0.025
        self.glueThickness = 0.040
        self.heightEnvelope = 2.44
        self.sensorHeight = self.sensor.thickness
        self.asicX = self.asic.lengthY
        self.asicY = self.asic.lengthX
        self.sensorX = self.sensor.lengthY
        self.sensorY = self.sensor.lengthX
        self.asicHeight = self.sensorHeight + self.bumpThickness + self.asic.thickness
        self.flexHeight = self.asicHeight + self.glueThickness + self.flex.thickness
        x = self.asicX
        y = self.asicY
        x2 = self.asicX/2
        y2 = self.asicY/2
        dh = 0.140/2
        print('x=', x, 'y=', y, 'x2 =',x2, 'y2=', y2, 'dh=', dh)
        self.targetData = {
            'Jig': TargetData('Jig', '', 0.0, 0.0),
            'JigT': TargetData('Jig', '', 0.0, 0.0),
            'JigB': TargetData('Jig', '', 0.0, 0.0),
            'JigL': TargetData('Jig', '', 0.0, 0.0),
            'JigR': TargetData('Jig', '', 0.0, 0.0),
            'AsicT': TargetData('AsicT', 'LineH', 0.0, y2), 
            'AsicB': TargetData('AsicB', 'LineH', 0.0, -y2),
            'AsicL': TargetData('AsicL', 'LineV', -x2, 0.0),
            'AsicR': TargetData('AsicR', 'LineV', x2, 0.0),
            'Asic1T': TargetData('Asic1T', 'LineH', -(dh+x2), -dh), 
            'Asic1B': TargetData('Asic1B', 'LineH', -(dh+x2), -(dh+y) ), 
            'Asic1L': TargetData('Asic1L', 'LineV', -(dh+x), -(dh+y2) ), 
            'Asic1R': TargetData('Asic1R', 'LineV', -dh, -(dh+y2) ), 
            'Asic2T': TargetData('Asic2T', 'LineH', dh+x2, -dh), 
            'Asic2B': TargetData('Asic2B', 'LineH', dh+x2, -dh-y), 
            'Asic2L': TargetData('Asic2L', 'LineV', dh, -(dh+y2) ), 
            'Asic2R': TargetData('Asic2R', 'LineV', dh+x, -(dh+y2) ), 
            'Asic3T': TargetData('Asic3T', 'LineH', dh+x2, dh+y), 
            'Asic3B': TargetData('Asic3B', 'LineH', dh+x2, dh), 
            'Asic3L': TargetData('Asic3L', 'LineV', dh, dh+y2), 
            'Asic3R': TargetData('Asic3R', 'LineV', dh+x, dh+y2), 
            'Asic4T': TargetData('Asic4T', 'LineH', -(dh+x2), dh+y), 
            'Asic4B': TargetData('Asic4B', 'LineH', -(dh+x2), dh), 
            'Asic4L': TargetData('Asic4L', 'LineV', -(dh+x), dh+y2), 
            'Asic4R': TargetData('Asic4R', 'LineV', -dh, dh+y2), 
            'SensorT': TargetData('SensorT', 'LineH', 0.0, self.sensor.xmax()),
            'SensorB': TargetData('SensorB', 'LineH', 0.0, self.sensor.xmin()),
            'SensorL': TargetData('SensorL', 'LineV', self.sensor.ymin(), 0.0),
            'SensorR': TargetData('SensorR', 'LineV', self.sensor.ymax(), 0.0),
        }
        self.nominalValues = {
            'AsicX':   (42.187+0.07/2, 0.070/2),
            'AsicY':   (40.255+0.07/2, 0.070/2),
            'SensorX':   (39.500+0.05/2, 0.050/2),
            'SensorY':   (41.100+0.05/2, 0.100),
            'AsicZ':   (0.150+0.025/2, (0.025+0.010)/2), 
            'SensorZ':   (0.325+0.09/2, (0.09+0.04)/2), 
            }
    def targetString(self, tag, offsetXY, zoom):
        tdata = None
        s = ''
        return s

class Rd53aModule:
    def __init__(self):
        self.asic = AsicRd53a()
        self.sensor = SensorOuter150um()
        self.flex = FlexRd53a()
        self.bumpThickness = 0.025
        self.glueThickness = 0.040
        self.heightEnvelope = 2.44
        self.sensorHeight = self.sensor.thickness
        self.asicX = self.asic.lengthX*2 + 0.140
        self.asicY = self.asic.lengthY*2 + 0.140
        self.asicHeight = self.sensorHeight + self.bumpThickness + self.asic.thickness
        self.flexHeight = self.asicHeight + self.glueThickness + self.flex.thickness

        self.targetData = {
            'AsicT': TargetData('AsicT', 'LineH', 0.0, self.asicY/2),
            'AsicB': TargetData('AsicB', 'LineH', 0.0, -self.asicY/2),
            'AsicL': TargetData('AsicL', 'LineV', -self.asicX/2, 0.0),
            'AsicR': TargetData('AsicR', 'LineV', self.asicX/2, 0.0),
            'SensorT': TargetData('SensorT', 'LineH', 0.0, self.sensor.ymax()),
            'SensorB': TargetData('SensorB', 'LineH', 0.0, self.sensor.ymin()),
            'SensorL': TargetData('SensorL', 'LineV', self.sensor.xmin(), 0.0),
            'SensorR': TargetData('SensorR', 'LineV', self.sensor.xmax(), 0.0),
            'FlexT': TargetData('FlexT', 'LineH', 0.0, self.flex.ymax()),
            'FlexB': TargetData('FlexB', 'LineH', 0.0, self.flex.ymin()),
            'FlexL': TargetData('FlexL', 'LineV', self.flex.xmin(), 0.0),
            'FlexR': TargetData('FlexR', 'LineV', self.flex.xmax(), 0.0),
            'Jig': TargetData('Jig', '', 0.0, 0.0),
            'JigT': TargetData('Jig', '', 0.0, 0.0),
            'JigB': TargetData('Jig', '', 0.0, 0.0),
            'JigL': TargetData('Jig', '', 0.0, 0.0),
            'JigR': TargetData('Jig', '', 0.0, 0.0),
            'Pickup1': None, 
            'Pickup2': None, 
            'Pickup3': None, 
            'Pickup4': None,
            'FlexPadsL': None, 
            'FlexPadsR': None, 
            'FlexConnector': None, 
            'FlexHvCapacitor': None,
            'FmarkTL': TargetData('FmarkTL', 'Circle', 0.0, 0.0), 
            'FmarkBL': TargetData('FmarkBL', 'Circle', 0.0, 0.0), 
            'FmarkBR': TargetData('FmarkBR', 'Circle', 0.0, 0.0), 
            'FmarkTR': TargetData('FmarkTR', 'Circle', 0.0, 0.0), 
            'AsicFmarkTL': TargetData('AsicFmarkTL', 'Circle', 0.0, 0.0), 
            'AsicFmarkBL': TargetData('AsicFmarkBL', 'Circle', 0.0, 0.0), 
            'AsicFmarkBR': TargetData('AsicFmarkBR', 'Circle', 0.0, 0.0), 
            'AsicFmarkTR': TargetData('AsicFmarkTR', 'Circle', 0.0, 0.0), 
        }
        zcell = 0.680 + 0.090 # cell + adhesive
        self.valueToleranceData = {
            'Jig': (None, 0.020), 
            'Asic': (0.150+zcell, 0.040), 
            'Sensor': (0.325+zcell, 0.058), 
            'Flex': (0.600+zcell, 0.085), 
            'Pickup1': (0.600+zcell, 0.085), 
            'Pickup2': (0.600+zcell, 0.085), 
            'Pickup3': (0.600+zcell, 0.085), 
            'Pickup4': (0.600+zcell, 0.085), 
            'FlexLSide': (0.600+zcell, 0.085), 
            'FlexRSide': (0.600+zcell, 0.085), 
            'Z_mean': (0.600+zcell, 0.085), 
            'Z_stddev': (0.025, 0.025), 
            'Connector': (1.425+zcell, 0.168), 
            'HVCapacitor': (2.025+zcell, 0.228), 
            'AsicToFlexL': (0.840, 0.050), 
            'AsicToFlexR': (0.840, 0.050), 
            'SensorToFlexT': (0.315, 0.050), 
            'SensorToFlexB': (0.280, 0.050), 
            'Angle (deg.)': (90.0, 10.0), 
            'AsicX': (42.137, 0.020), 
            'AsicY': (40.335, 0.020), 
            'SensorX': (39.500, 0.005), 
            'SensorY': (41.100, 0.005), 
            'FlexX': (40.210, 0.020), 
            'FlexY': (40.450, 0.020),
            'dz(max-min)': (0.00, 0.025), 
            'Angle1': (0.00, 0.100), 
            'Angle2': (0.00, 0.100), 
            'z(average)': (0.00, 0.025), 
        }
    def isInTolerance(self, key, value):
        status = 'None'
        if key in self.valueToleranceData.keys():
            v, t = self.valueToleranceData[key]
            if v and t:
                vmin = v - t
                vmax = v + t
                if value >= vmin and value <= vmax:
                    status = 'Pass'
                else:
                    status = 'Fail'
            else:
                status = 'NoCheck'
        return status

    def targetString(self, tag, offsetXY, zoom):
        tdata = None
        s = ''
        if tag in self.targetData.keys():
            tdata = self.targetData[tag]
        if tdata != None:
            xy = [tdata.x, tdata.y]
            cr = globalToLocal(xy, offsetXY, zoom)
            hlines = [ a+b for a in ('Asic','Sensor','Flex') for b in ('T','B')]
            vlines = [ a+b for a in ('Asic','Sensor','Flex') for b in ('L','R')]
            if tdata.name in hlines:
                s = '{0},col{1},row{2}'.format(tdata.ptype, 3000, cr[1])
            elif tdata.name in vlines:
                s = '{0},col{1},row{2}'.format(tdata.ptype, cr[0], 2000)
        return s

    def dump(self):
        print('Asic')
        print('  X=%6.3f, Y=%6.3f, thickness=%6.3f' %\
              (self.asic.lengthX, self.asic.lengthY, self.asic.thickness) )
        print('Sensor')
        print('  X=%6.3f, Y=%6.3f, thickness=%6.3f' %\
              (self.sensor.lengthX, self.sensor.lengthY, self.sensor.thickness) )
        print('Flex')
        print('Flex height: %6.3f' % self.flexHeight)
        keys = list(self.targetData.keys())
        keys.sort()
        for k in keys:
            v = self.targetData[k]
            if v != None:
                v = v.value()
            print('  {0:20s} : {1}'.format(k, v) )
        pass

class ITkPixV11Module(Rd53aModule):
    def __init__(self):
        super().__init__()
        self.nominalValues = {
            'FlexX':   (39.600, 0.100),
            'FlexY':   (40.300, 0.100),
            'SensorY': (41.100, 0.050),
            'AsicX':   (42.190, 0.050),
            'PickupZ': (0.550, 0.050),
            'HVCapacitorZ': (2.251, 0.200), 
            'ConnectorZ':   (1.971, 0.100),
            'Angle': (0.0, 10.0), 
            'FmarkDistanceTR_x': (2.212, 0.100), 
            'FmarkDistanceTR_y': (0.750, 0.100), 
            'FmarkDistanceBL_x': (2.212, 0.100), 
            'FmarkDistanceBL_y': (0.750, 0.100), 
            }

class ITkPixV1xFlex:
    def __init__(self):
        super().__init__()
        flexX = 40.2
        flexY = 40.5
        self.targetData = {
            'FlexT': TargetData('FlexT', 'LineH', flexY/2, 0.0), 
            'FlexB': TargetData('FlexB', 'LineH', -flexY/2, 0.0), 
            'FlexL': TargetData('FlexL', 'LineV', 0.0, -flexX/2), 
            'FlexR': TargetData('FlexR', 'LineV', 0.0, flexX/2), 
            'HoleTL': TargetData('HoleTL', 'BigCircle', -flexX/2, flexY/2), 
            'SlotBR': TargetData('SlotBR', 'BigSlot', flexX/2, -flexY/2),
            'FiducialTL': TargetData('FiducialTL', 'Circle', -flexX/2, -flexY/2),
            'FiducialBR': TargetData('FiducialBR', 'Circle', flexX/2, flexY/2),
        }
        self.nominalValues = {
            'FlexX':   (39.600, 0.100),
            'FlexY':   (40.300, 0.100),
            'PickupZ': (0.200, 0.050),
            'HVCapacitorZ': (1.901, 0.200), 
            'ConnectorZ':   (1.621, 0.100),
            'HoleTL_diameter':   (3.000, 0.100),
            'SlotBR_width':   (3.000, 0.100),
            }
 
def createModule(componentType):
    component = None
    #logger.info(f'Create module design for {componentType}')
    if componentType == 'Rd53aModule':
        component = Rd53aModule()
    elif componentType == 'ITkPixV1xModule':
        component = ITkPixV11Module()
    elif componentType in ('ITkPixV1xBareModule', 'Rd53aBareModule'):
        logger.info(f'  design selected for BareModuleFront')
        component = BareModuleFront()
    elif componentType == 'ITkPixV1xFlex':
        component = ITkPixV1xFlex()
    #logger.info(f'  design {component}')
    return component
