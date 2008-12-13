"""Classes that draw small icons at a given point.
Mainly useful for marking specific data points."""

# Import names with underscores so that we don't need
# to manually specify an __all__.

import cairo as _cairo
import math as _math
import numpy as _N
from base import Stamp

_defaultStampSize = 5

# import stride_tricks
# _N.broadcast_arrays = stride_tricks.broadcast_arrays

class RStamp (Stamp):
    # A R(ect)Stamp is a stamp usually associated
    # with a RectDataHolder and rendered onto a RectPlot.
    # The paint/paintAt functions paint a data-free
    # "sample" stamp only. The paintMany function
    # paints the stamp multiple times according to the data
    # contained in the RectDataHolder.

    data = None


    def setData (self, data):
        if self.data is not None:
            raise Exception ('Cannot reuse RStamp instance.')
        
        self.data = data
        # when overriding: possibly register data columns
        # and stash cinfo


    def paintAt (self, ctxt, style, x, y):
        # This paints a data-free "sample" version of
        # the stamp.
        data = self._getSampleValues (style, x, y)
        data = [_N.atleast_1d (q) for q in data]

        self._paintData (ctxt, style, _N.atleast_1d (x), 
                         _N.atleast_1d (y), data)


    def paintMany (self, ctxt, style, xform):
        imisc, fmisc, allx, ally = self.data.getAllMapped (xform)
        x = allx[0]
        y = ally[0]

        data = self._getDataValues (style, xform)
        data = _N.broadcast_arrays (x, *data)[1:]

        self._paintData (ctxt, style, x, y, data)


    def _paintData (self, ctxt, style, x, y, data):
        raise NotImplementedError ()


    def _getSampleValues (self, style, x, y):
        # When implementing, return a tuple of scalars
        # that can be used by _paintData in array form.
        # If subclassing, chain to the parent and
        # combine your tuples and the parent's tuples
        raise NotImplementedError ()


    def _getDataValues (self, style, xform):
        # Implement similalry to _getSampleValues. 
        # It's expected that data values will
        # come from self.data.getMapped (cinfo, xform)
        # for some cinfo
        raise NotImplementedError ()


class PrimaryRStamp (RStamp):
    # A primary RStamp is one that actually draws a plot
    # symbol. It has builtin properties "size" and "rot"
    # that can be used to control how the symbol is plotted.
    # Both can be either specified to be a constant or 
    # be stored in the dataholder.

    def __init__ (self, size=None, rot=0):
        if size is None: size = _defaultStampSize

        self.size = size
        self.rot = rot


    def setData (self, data):
        RStamp.setData (self, data)

        if self.size < 0:
            self.sizeCInfo = data.register (0, 1, 0, 0)
        else:
            self.sizeCInfo = None

        if self.rot < 0:
            self.rotCInfo = data.register (0, 1, 0, 0)
        else:
            self.rotCInfo = None


    def _getSampleValues (self, style, x, y):
        if self.sizeCInfo is None:
            s = self.size
        else:
            s = _defaultStampSize

        if self.rotCInfo is None:
            r = self.rot
        else:
            r = 0

        return (s, r)


    def _getDataValues (self, style, xform):
        if self.sizeCInfo is None:
            s = self.size
        else:
            imisc, fmisc, x, y = self.data.get (self.sizeCInfo)
            s = -self.size * fmisc[0]

        if self.rotCInfo is None:
            r = self.rot
        else:
            imisc, fmisc, x, y = self.data.get (self.rotCInfo)
            r = -self.rot * fmisc[0]

        return (s, r)


    def _paintData (self, ctxt, style, x, y, mydata):
        sizes, rots = mydata

        for i in xrange (0, x.size):
            ctxt.save ()
            ctxt.translate (x[i], y[i])
            ctxt.rotate (rots[i])
            self._paintOne (ctxt, style, sizes[i])
            ctxt.restore ()


    def _paintOne (self, ctxt, style, size):
        raise NotImplementedError ()


# These functions actually paint a symbol

def symCircle (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    ctxt.new_sub_path () # prevents leading line segment to arc beginning
    ctxt.arc (0, 0, size * style.smallScale / 2, 0, 2 * _math.pi)
    go ()

def symUpTriangle (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    s = size * style.smallScale
        
    ctxt.move_to (0, -0.666666 * s)
    ctxt.rel_line_to (s/2, s)
    ctxt.rel_line_to (-s, 0)
    ctxt.rel_line_to (s/2, -s)
    go ()

def symDownTriangle (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    s = size * style.smallScale
        
    ctxt.move_to (0, s * 0.666666)
    ctxt.rel_line_to (-s/2, -s)
    ctxt.rel_line_to (s, 0)
    ctxt.rel_line_to (-s/2, s)
    go ()

def symDiamond (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    s2 = size * style.smallScale / 2
        
    ctxt.move_to (0, -s2)
    ctxt.rel_line_to (s2, s2)
    ctxt.rel_line_to (-s2, s2)
    ctxt.rel_line_to (-s2, -s2)
    ctxt.rel_line_to (s2, -s2)
    go ()

def symBox (ctxt, style, size, fill):
    s = size * style.smallScale / _math.sqrt (2)
        
    ctxt.rectangle (-0.5 * s, -0.5 * s, s, s)

    if fill: ctxt.fill ()
    else: ctxt.stroke ()

def symX (ctxt, style, size):
    s = size * style.smallScale / _math.sqrt (2)
        
    ctxt.move_to (-0.5 * s, -0.5 * s)
    ctxt.rel_line_to (s, s)
    ctxt.stroke ()
    ctxt.move_to (-0.5 * s, 0.5 * s)
    ctxt.rel_line_to (s, -s)
    ctxt.stroke ()
        
def symPlus (ctxt, style, size):
    s = size * style.smallScale
        
    ctxt.move_to (-0.5 * s, 0)
    ctxt.rel_line_to (s, 0)
    ctxt.stroke ()
    ctxt.move_to (0, -0.5 * s)
    ctxt.rel_line_to (0, s)
    ctxt.stroke ()

# Stamps drawing these symbols

class Circle (PrimaryRStamp):
    def __init__ (self, fill=True, **kwargs):
        PrimaryRStamp.__init__ (self, **kwargs)
        self.fill = fill


    def _paintOne (self, ctxt, style, size):
        symCircle (ctxt, style, size, self.fill)


class UpTriangle (PrimaryRStamp):
    def __init__ (self, fill=True, **kwargs):
        PrimaryRStamp.__init__ (self, **kwargs)
        self.fill = fill


    def _paintOne (self, ctxt, style, size):
        symUpTriangle (ctxt, style, size, self.fill)

class DownTriangle (PrimaryRStamp):
    def __init__ (self, fill=True, **kwargs):
        PrimaryRStamp.__init__ (self, **kwargs)
        self.fill = fill


    def _paintOne (self, ctxt, style, size):
        symDownTriangle (ctxt, style, size, self.fill)
    

class Diamond (PrimaryRStamp):
    def __init__ (self, fill=True, **kwargs):
        PrimaryRStamp.__init__ (self, **kwargs)
        self.fill = fill


    def _paintOne (self, ctxt, style, size):
        symDiamond (ctxt, style, size, self.fill)


class Box (PrimaryRStamp):
    # size measures the box in style.smallScale; this is
    # reduced by sqrt(2) so that the area of the Box and
    # Diamond stamps are the same for the same values of size.


    def __init__ (self, fill=True, **kwargs):
        PrimaryRStamp.__init__ (self, **kwargs)
        self.fill = fill


    def _paintOne (self, ctxt, style, size):
        symBox (ctxt, style, size, self.fill)
    

class X (PrimaryRStamp):
    # size gives the length the X in style.smallScale; corrected by
    # sqrt(2) so that X and Plus lay down the same amount of "ink"

    def _paintOne (self, ctxt, style, size):
        symX (ctxt, style, size)
    

class Plus (PrimaryRStamp):
    # size gives the side length of the plus in style.smallScale

    def _paintOne (self, ctxt, style, size):
        symPlus (ctxt, style, size)
    

# This special PrimaryRStamp plots a symbol that's a function of
# a style number used for data themes. This allows us to abstract
# the use of different symbols for different datasets in a plot

class DataThemedStamp (PrimaryRStamp):
    def __init__ (self, snholder, size=None, rot=0):
        super (DataThemedStamp, self).__init__ (size, rot)
        self.setHolder (snholder)
        
    def setHolder (self, snholder):
        self.snholder = snholder


    def _paintOne (self, ctxt, style, size):
        if self.snholder is None:
            raise Exception ('Need to call setHolder before painting DataThemedStamp!')

        sn = self.snholder.primaryStyleNum
        style.data.getSymbolFunc (sn) (ctxt, style, size)


# Here are some utility stamps that are *not*
# primary stamps. They build on top of other stamps
# to provide useful effects. Namely, error bars.

class WithYErrorBars (RStamp):
    def __init__ (self, substamp):
        self.substamp = substamp


    def setData (self, data):
        # Have the substamp register whatever it
        # needs.

        self.substamp.setData (data)

        # And register our own data needs.

        RStamp.setData (self, data)
        self.cinfo = data.register (0, 0, 0, 2)


    def _paintData (self, ctxt, style, x, y, mydata):
        y1, y2 = mydata[0:2]
        subdata = mydata[2:]

        self.substamp._paintData (ctxt, style, x, y, subdata)

        for i in xrange (0, x.size):
            ctxt.move_to (x[i], y1[i])
            ctxt.line_to (x[i], y2[i])
            ctxt.stroke ()

    
    def _getSampleValues (self, style, x, y):
        subd = self.substamp._getSampleValues (style, x, y)

        dy = 4 * style.smallScale
        return (y - dy, y + dy) + subd


    def _getDataValues (self, style, xform):
        subd = self.substamp._getDataValues (style, xform)

        imisc, fmisc, x, y = self.data.getMapped (self.cinfo, xform)
        return (y[0], y[1]) + subd

        
class WithXErrorBars (RStamp):
    def __init__ (self, substamp):
        self.substamp = substamp


    def setData (self, data):
        # Have the substamp register whatever it
        # needs.

        self.substamp.setData (data)

        # And register our own data needs.

        RStamp.setData (self, data)
        self.cinfo = data.register (0, 0, 2, 0)


    def _paintData (self, ctxt, style, x, y, mydata):
        x1, x2 = mydata[0:2]
        subdata = mydata[2:]

        self.substamp._paintData (ctxt, style, x, y, subdata)

        for i in xrange (0, x.size):
            ctxt.move_to (x1[i], y[i])
            ctxt.line_to (x2[i], y[i])
            ctxt.stroke ()

    
    def _getSampleValues (self, style, x, y):
        subd = self.substamp._getSampleValues (style, x, y)

        dx = 4 * style.smallScale
        return (x - dx, x + dx) + subd


    def _getDataValues (self, style, xform):
        subd = self.substamp._getDataValues (style, xform)

        imisc, fmisc, x, y = self.data.getMapped (self.cinfo, xform)
        return (x[0], x[1]) + subd
