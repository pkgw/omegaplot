"""Classes that draw small icons at a given point.
Mainly useful for marking specific data points."""

# Do this so that we don't need to manually specify
# an __all__.

import cairo as _cairo
import math as _math

class Stamp (object):
    sinkSpec = ''
    mainStyle = 'genericStamp'
    
    def paint (self, ctxt, style, x, y, data):
        ctxt.save ()
        style.apply (ctxt, self.mainStyle)
        self.doPaint (ctxt, style, x, y, data)
        ctxt.restore ()

class SizedDot (Stamp):
    sinkSpec = 'F' # size of dot in style.smallScale

    def doPaint (self, ctxt, style, x, y, data):
        ctxt.arc (x, y, data[0] * style.smallScale, 0, 2 * _math.pi)
        ctxt.fill ()

class Dot (Stamp):
    size = 3 # diameter of dot in style.smallScale
    
    def doPaint (self, ctxt, style, x, y, data):
        ctxt.arc (x, y, self.size * style.smallScale / 2, 0, 2 * _math.pi)
        ctxt.fill ()

class Circle (Stamp):
    size = 3 # diameter of circle in style.smallScale
    
    def doPaint (self, ctxt, style, x, y, data):
        ctxt.arc (x, y, self.size * style.smallScale / 2, 0, 2 * _math.pi)
        ctxt.stroke ()

class UpTriangle (Stamp):
    size = 3 # size of triangle in style.smallScale

    def doPaint (self, ctxt, style, x, y, data):
        s = self.size * style.smallScale
        
        ctxt.move_to (x, y - s * 0.666666)
        ctxt.rel_line_to (s/2, s)
        ctxt.rel_line_to (-s, 0)
        ctxt.rel_line_to (s/2, -s)
        ctxt.stroke ()
    
class DownTriangle (Stamp):
    size = 3 # size of triangle in style.smallScale

    def doPaint (self, ctxt, style, x, y, data):
        s = self.size * style.smallScale
        
        ctxt.move_to (x, y + s * 0.666666)
        ctxt.rel_line_to (-s/2, -s)
        ctxt.rel_line_to (s, 0)
        ctxt.rel_line_to (-s/2, s)
        ctxt.stroke ()
    
class X (Stamp):
    size = 3 # size of the X in style.smallScale; corrected by
    # sqrt(2) so that X and Plus lay down the same amount of "ink"

    def doPaint (self, ctxt, style, x, y, data):
        s = self.size * style.smallScale / _math.sqrt (2)
        
        ctxt.move_to (x - s/2, y - s/2)
        ctxt.rel_line_to (s, s)
        ctxt.stroke ()
        ctxt.move_to (x - s/2, y + s/2)
        ctxt.rel_line_to (s, -s)
        ctxt.stroke ()
    
class Plus (Stamp):
    size = 3 # size of the + in style.smallScale

    def doPaint (self, ctxt, style, x, y, data):
        s = self.size * style.smallScale
        
        ctxt.move_to (x - s/2, y)
        ctxt.rel_line_to (s, 0)
        ctxt.stroke ()
        ctxt.move_to (x, y - s/2)
        ctxt.rel_line_to (0, s)
        ctxt.stroke ()
    
class Box (Stamp):
    size = 3 # size of the box in style.smallScale; this is
    # reduced by sqrt(2) so that the area of the Box and
    # Diamond stamps are the same for the same values of size.

    def doPaint (self, ctxt, style, x, y, data):
        s = self.size * style.smallScale / _math.sqrt (2)
        
        ctxt.rectangle (x - s/2, y - s/2, s, s)
        ctxt.stroke ()
    
class Diamond (Stamp):
    size = 3 # size of the diamond in style.smallScale

    def doPaint (self, ctxt, style, x, y, data):
        s2 = self.size * style.smallScale / 2

        ctxt.move_to (x, y - s2)
        ctxt.rel_line_to (s2, s2)
        ctxt.rel_line_to (-s2, s2)
        ctxt.rel_line_to (-s2, -s2)
        ctxt.rel_line_to (s2, -s2)
        ctxt.stroke ()
    
