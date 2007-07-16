"""Classes that draw small icons at a given point.
Mainly useful for marking specific data points."""

# Do this so that we don't need to manually specify
# an __all__.

import cairo as _cairo
import math as _math

_defaultStampSize = 5

class Stamp (object):
    stampSpec = 'XY'
    mainStyle = 'genericStamp'

    def paint (self, ctxt, style, data):
        ctxt.save ()
        style.apply (ctxt, self.mainStyle)
        self.doPaint (ctxt, style, data)
        ctxt.restore ()

class SizedDot (Stamp):
    stampSpec = 'XYF' # size of dot in style.smallScale

    def doPaint (self, ctxt, style, data):
        ctxt.arc (data[0], data[1], data[2] * style.smallScale, 0, 2 * _math.pi)
        ctxt.fill ()

class Dot (Stamp):
    size = _defaultStampSize # diameter of dot in style.smallScale
    
    def doPaint (self, ctxt, style, data):
        ctxt.arc (data[0], data[1], self.size * style.smallScale / 2, 0, 2 * _math.pi)
        ctxt.fill ()

class Circle (Stamp):
    size = _defaultStampSize # diameter of circle in style.smallScale
    
    def doPaint (self, ctxt, style, data):
        ctxt.arc (data[0], data[1], self.size * style.smallScale / 2, 0, 2 * _math.pi)
        ctxt.stroke ()

class UpTriangle (Stamp):
    size = _defaultStampSize # size of triangle in style.smallScale

    def doPaint (self, ctxt, style, data):
        s = self.size * style.smallScale
        
        ctxt.move_to (data[0], data[1] - s * 0.666666)
        ctxt.rel_line_to (s/2, s)
        ctxt.rel_line_to (-s, 0)
        ctxt.rel_line_to (s/2, -s)
        ctxt.stroke ()
    
class DownTriangle (Stamp):
    size = _defaultStampSize # size of triangle in style.smallScale

    def doPaint (self, ctxt, style, data):
        s = self.size * style.smallScale
        
        ctxt.move_to (data[0], data[1] + s * 0.666666)
        ctxt.rel_line_to (-s/2, -s)
        ctxt.rel_line_to (s, 0)
        ctxt.rel_line_to (-s/2, s)
        ctxt.stroke ()
    
class X (Stamp):
    size = _defaultStampSize # size of the X in style.smallScale; corrected by
    # sqrt(2) so that X and Plus lay down the same amount of "ink"

    def doPaint (self, ctxt, style, data):
        s = self.size * style.smallScale / _math.sqrt (2)
        x, y = data
        
        ctxt.move_to (x - s/2, y - s/2)
        ctxt.rel_line_to (s, s)
        ctxt.stroke ()
        ctxt.move_to (x - s/2, y + s/2)
        ctxt.rel_line_to (s, -s)
        ctxt.stroke ()
    
class Plus (Stamp):
    size = _defaultStampSize # size of the + in style.smallScale

    def doPaint (self, ctxt, style, data):
        s = self.size * style.smallScale
        x, y = data
        
        ctxt.move_to (x - s/2, y)
        ctxt.rel_line_to (s, 0)
        ctxt.stroke ()
        ctxt.move_to (data[0], y - s/2)
        ctxt.rel_line_to (0, s)
        ctxt.stroke ()
    
class Box (Stamp):
    size = _defaultStampSize # size of the box in style.smallScale; this is
    # reduced by sqrt(2) so that the area of the Box and
    # Diamond stamps are the same for the same values of size.

    def doPaint (self, ctxt, style, data):
        s = self.size * style.smallScale / _math.sqrt (2)
        
        ctxt.rectangle (data[0] - s/2, data[1] - s/2, s, s)
        ctxt.stroke ()
    
class Diamond (Stamp):
    size = _defaultStampSize # size of the diamond in style.smallScale

    def doPaint (self, ctxt, style, data):
        s2 = self.size * style.smallScale / 2

        ctxt.move_to (data[0], data[1] - s2)
        ctxt.rel_line_to (s2, s2)
        ctxt.rel_line_to (-s2, s2)
        ctxt.rel_line_to (-s2, -s2)
        ctxt.rel_line_to (s2, -s2)
        ctxt.stroke ()

class DotYErrorBars (Dot):
    stampSpec = 'XYYY' # x, y, lower error bound, upper error bound

    def doPaint (self, ctxt, style, data):
        Dot.doPaint (self, ctxt, style, data[0:2])

        ctxt.move_to (data[0], data[2])
        ctxt.line_to (data[0], data[3])
        ctxt.stroke ()

class CrossYErrorBars (X):
    stampSpec = 'XYYY' # x, y, lower error bound, upper error bound

    def doPaint (self, ctxt, style, data):
        X.doPaint (self, ctxt, style, data[0:2])

        ctxt.move_to (data[0], data[2])
        ctxt.line_to (data[0], data[3])
        ctxt.stroke ()

class BoxYErrorBars (Box):
    stampSpec = 'XYYY' # x, y, lower error bound, upper error bound

    def doPaint (self, ctxt, style, data):
        Box.doPaint (self, ctxt, style, data[0:2])

        ctxt.move_to (data[0], data[2])
        ctxt.line_to (data[0], data[3])
        ctxt.stroke ()

class CrossXErrorBars (X):
    stampSpec = 'XYXX' # x, y, lower error bound, upper error bound

    def doPaint (self, ctxt, style, data):
        X.doPaint (self, ctxt, style, data[0:2])

        ctxt.move_to (data[2], data[1])
        ctxt.line_to (data[3], data[1])
        ctxt.stroke ()
