#--------------------------------------------------------------------
# Pixel Module Metrology (View)
# 
# Unit: mm
# Module coordinate system: origin at the middle
#                           x (towards right) and y (towards top)
#--------------------------------------------------------------------

class SLine:
    def __init__(self):
        self.startPoint = [0, 0]
        self.endPoint = [0, 0]
    def angle(self):
        dx = endPoint[0] - startPoint[0]
        dy = endPoint[1] - startPoint[1]
        angle = -999.0
        if dx == 0.0 and dy == 0.0:
            return angle
        else:
            angle = math.atan2(dy, dx)
        return angle

class ModuleView:
    def __init__(self):
        self.viewBox = [ -25.0, -25.0, 50.0, 50.0 ] # (x, y, w, h)
        self.points = []
        self.lines = []
        self.circles = []
    def addPoint(self, point, options={}):
        self.points.append( (point, options) )
        pass
    def addLine(self, line, options={}):
        self.lines.append( (line, options) )
        pass
    def addCircle(self, circle, options={}):
        self.circles.append( (circle, options) )
        pass
    def toSvg(self):
        s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%8.5f %8.5f %8.5f %8.5f">\n' % (self.viewBox[0], self.viewBox[1], self.viewBox[2], self.viewBox[3])
        indent = '  '
        for x in self.lines:
            s += indent + self.lineToSvg(x)
        for x in self.circles:
            s += indent + self.circleToSvg(x)
        for x in self.points:
            s += indent + self.pointToSvg(x)
        s += '</svg>\n'
        return s
    def pointToSvg(self, p):
        #print(p)
        a = p[0]
        opts = p[1]
        r = 0.02
        s = '<circle cx="%7.5f" cy="%7.5f" ' % (a[0], a[1])
        stroke, fill = 'black', 'none'
        for k, v in opts.items():
            if k == 'stroke':
                stroke = v
            elif k == 'fill':
                fill = v
            elif k == 'stroke-width':
                s += 'stroke-width="%7.5f" ' % v
            elif k == 'r':
                s += 'r="%7.5f" ' % v
            else:
                pass
        s += 'stroke="%s" fill="%s"' % (stroke, fill)
        s += '/>\n'
        return s
    def lineToSvg(self, line):
        s = '<line x=%8.5f y=%8.5f />'
        return s
    def circleToSvg(self, c):
        x = c
        m = {}
        if type(c) == type(()):
            x = c[0]
            m = c[1]
        s = '<circle cx=%8.5f cy=%8.5f r=%8.5f />\n' % (x.cx, x.cy, x.r)
        return s
