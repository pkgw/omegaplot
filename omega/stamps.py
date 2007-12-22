"""Classes that draw small icons at a given point.
Mainly useful for marking specific data points."""

# Do this so that we don't need to manually specify
# an __all__.

import cairo as _cairo
import math as _math

_defaultStampSize = 5

class Stamp (object):
    axisInfo = (0, 0, 0, 0)
    mainStyle = 'genericStamp'

    def paint (self, ctxt, style, imisc, fmisc, allx, ally):
        ctxt.save ()
        style.apply (ctxt, self.mainStyle)
        self.doPaint (ctxt, style, imisc, fmisc, allx, ally)
        ctxt.restore ()

class Dot (Stamp):
    size = _defaultStampSize # diameter of dot in style.smallScale
    
    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        ctxt.arc (allx[0], ally[0], self.size * style.smallScale / 2, 0, 2 * _math.pi)
        ctxt.fill ()

class Circle (Stamp):
    size = _defaultStampSize # diameter of circle in style.smallScale
    
    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        ctxt.arc (allx[0], ally[0], self.size * style.smallScale / 2, 0, 2 * _math.pi)
        ctxt.stroke ()

class UpTriangle (Stamp):
    size = _defaultStampSize # size of triangle in style.smallScale

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        s = self.size * style.smallScale
        
        ctxt.move_to (allx[0], ally[0] - s * 0.666666)
        ctxt.rel_line_to (s/2, s)
        ctxt.rel_line_to (-s, 0)
        ctxt.rel_line_to (s/2, -s)
        ctxt.stroke ()
    
class DownTriangle (Stamp):
    size = _defaultStampSize # size of triangle in style.smallScale

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        s = self.size * style.smallScale
        
        ctxt.move_to (allx[0], ally[0] + s * 0.666666)
        ctxt.rel_line_to (-s/2, -s)
        ctxt.rel_line_to (s, 0)
        ctxt.rel_line_to (-s/2, s)
        ctxt.stroke ()
    
class X (Stamp):
    size = _defaultStampSize # size of the X in style.smallScale; corrected by
    # sqrt(2) so that X and Plus lay down the same amount of "ink"

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        s = self.size * style.smallScale / _math.sqrt (2)
        x, y = allx[0], ally[0]
        
        ctxt.move_to (x - s/2, y - s/2)
        ctxt.rel_line_to (s, s)
        ctxt.stroke ()
        ctxt.move_to (x - s/2, y + s/2)
        ctxt.rel_line_to (s, -s)
        ctxt.stroke ()
    
class Plus (Stamp):
    size = _defaultStampSize # size of the + in style.smallScale

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        s = self.size * style.smallScale
        x, y = allx[0], ally[0]
        
        ctxt.move_to (x - s/2, y)
        ctxt.rel_line_to (s, 0)
        ctxt.stroke ()
        ctxt.move_to (x, y - s/2)
        ctxt.rel_line_to (0, s)
        ctxt.stroke ()
    
class Box (Stamp):
    size = _defaultStampSize # size of the box in style.smallScale; this is
    # reduced by sqrt(2) so that the area of the Box and
    # Diamond stamps are the same for the same values of size.

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        s = self.size * style.smallScale / _math.sqrt (2)
        
        ctxt.rectangle (allx[0] - s/2, ally[0] - s/2, s, s)
        ctxt.stroke ()
    
class Diamond (Stamp):
    size = _defaultStampSize # size of the diamond in style.smallScale

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        s2 = self.size * style.smallScale / 2

        ctxt.move_to (allx[0], ally[0] - s2)
        ctxt.rel_line_to (s2, s2)
        ctxt.rel_line_to (-s2, s2)
        ctxt.rel_line_to (-s2, -s2)
        ctxt.rel_line_to (s2, -s2)
        ctxt.stroke ()

class WithSizing (Stamp):
    def __init__ (self, substamp):
        self.substamp = substamp
        
        self.axisInfo = list (substamp.axisInfo)
        self.axisInfo[1] += 1

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        self.substamp.size = fmisc[0]
        self.substamp.doPaint (ctxt, style, imisc, fmisc[1:], allx, ally)
    
class WithYErrorBars (Stamp):
    def __init__ (self, substamp):
        self.substamp = substamp

        self.axisInfo = list (substamp.axisInfo)
        self.axisInfo[3] += 2

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        self.substamp.doPaint (ctxt, style, imisc, fmisc, allx, ally)

        ctxt.move_to (allx[0], ally[1])
        ctxt.line_to (allx[0], ally[2])
        ctxt.stroke ()

class WithXErrorBars (Stamp):
    def __init__ (self, substamp):
        self.substamp = substamp

        self.axisInfo = list (substamp.axisInfo)
        self.axisInfo[2] += 2

    def doPaint (self, ctxt, style, imisc, fmisc, allx, ally):
        self.substamp.doPaint (ctxt, style, imisc, fmisc, allx, ally)

        ctxt.move_to (allx[1], ally[0])
        ctxt.line_to (allx[2], ally[0])
        ctxt.stroke ()
