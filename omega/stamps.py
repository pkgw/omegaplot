# Copyright 2011, 2012 Peter Williams
#
# This file is part of omegaplot.
#
# Omegaplot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Omegaplot is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Omegaplot. If not, see <http://www.gnu.org/licenses/>.

"""Classes that draw small icons at a given point.
Mainly useful for marking specific data points."""

# Import names with underscores so that we don't need
# to manually specify an __all__.

import numpy as np
from base import Stamp
from math import pi, sqrt

_defaultStampSize = 5

# import stride_tricks
# np.broadcast_arrays = stride_tricks.broadcast_arrays

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
        data = [np.atleast_1d (q) for q in data]

        self._paintData (ctxt, style, np.atleast_1d (x),
                         np.atleast_1d (y), data)


    def paintMany (self, ctxt, style, xform):
        imisc, fmisc, allx, ally = self.data.getAllMapped (xform)
        x = allx[0]
        y = ally[0]

        data = self._getDataValues (style, xform)
        data = np.broadcast_arrays (x, *data)[1:]

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
    ctxt.arc (0, 0, size * style.smallScale / 2, 0, 2 * pi)
    go ()

def symUpTriangle (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    s = size * style.smallScale

    ctxt.move_to (0, -0.666666 * s)
    ctxt.rel_line_to (s/2, s)
    ctxt.rel_line_to (-s, 0)
    ctxt.close_path ()
    go ()

def symDownTriangle (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    s = size * style.smallScale

    ctxt.move_to (0, s * 0.666666)
    ctxt.rel_line_to (-s/2, -s)
    ctxt.rel_line_to (s, 0)
    ctxt.close_path ()
    go ()

def symDiamond (ctxt, style, size, fill):
    if fill: go = ctxt.fill
    else: go = ctxt.stroke

    s2 = size * style.smallScale / 2

    ctxt.move_to (0, -s2)
    ctxt.rel_line_to (s2, s2)
    ctxt.rel_line_to (-s2, s2)
    ctxt.rel_line_to (-s2, -s2)
    ctxt.close_path ()
    go ()

def symBox (ctxt, style, size, fill):
    s = size * style.smallScale / sqrt (2)

    ctxt.rectangle (-0.5 * s, -0.5 * s, s, s)

    if fill: ctxt.fill ()
    else: ctxt.stroke ()

def symX (ctxt, style, size, fill=False):
    # "fill" not honored here, but allow it for signature compatibility.
    s = size * style.smallScale / sqrt (2)

    ctxt.move_to (-0.5 * s, -0.5 * s)
    ctxt.rel_line_to (s, s)
    ctxt.stroke ()
    ctxt.move_to (-0.5 * s, 0.5 * s)
    ctxt.rel_line_to (s, -s)
    ctxt.stroke ()

def symPlus (ctxt, style, size, fill=False):
    # "fill" not honored here, but allow it for signature compatibility.
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

        dsn = self.snholder.dsn
        style.data.getSymbolFunc (dsn) (ctxt, style, size)


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


# Arrow painting

def arrow (ctxt, x, y, direction, length, headsize):
    dperp = headsize * 0.95
    dpara = headsize * 0.3

    if length < 0:
        if direction == 'left':
            newdir = 'right'
        elif direction == 'right':
            newdir = 'left'
        elif direction == 'top':
            newdir = 'bottom'
        elif direction == 'bottom':
            newdir = 'top'

        length = -length
        direction = newdir

    llength = max (length - dperp, 0)

    if direction == 'left':
        dlx, dly = -llength, 0
        dh1x, dh1y = 0, dpara
        dh2x, dh2y = -(length - llength), dpara
    elif direction == 'right':
        dlx, dly = llength, 0
        dh1x, dh1y = 0, -dpara
        dh2x, dh2y = length - llength, -dpara
    elif direction == 'top':
        dlx, dly = 0, -llength
        dh1x, dh1y = -dpara, 0
        dh2x, dh2y = -dpara, -(length - llength)
    elif direction == 'bottom':
        dlx, dly = 0, llength
        dh1x, dh1y = dpara, 0
        dh2x, dh2y = dpara, length - llength
    else:
        raise ValueError ('unrecognized arrow direction "%s"' % direction)

    if llength != 0:
        ctxt.move_to (x, y)
        ctxt.rel_line_to (dlx, dly)
        ctxt.stroke ()

    ctxt.move_to (x + dlx + dh1x, y + dly + dh1y)
    ctxt.rel_line_to (-2 * dh1x, -2 * dh1y)
    ctxt.rel_line_to (dh2x, dh2y)
    ctxt.close_path ()
    ctxt.fill ()


class _WithArrow (RStamp):
    """
    This is a confusing class here. The whole point of limit arrows as
    opposed to error bars is that the arrow length is not particularly
    meaningful, so it is specified in style units (largeScale) and not
    tied to rectangular X or Y values.

    However, we will often have limit arrows pointing toward some
    limiting value (say, zero!), and it is ugly to have the arrows
    overshoot that value. So this stamp adds a data column of either X
    or Y type (depending on *direction*) here called "towards": for
    each point, the arrow goes from the X-or-Y value towards
    "towards", without overshooting it. (I.e., the length has a
    maximum of the specified length in style units, but may be shorter
    if necessary.)

    This means that for *direction*, 'left' and 'right', and 'top' and
    'bottom', are essentially equivalent. The only place where the
    particular value matters is in the key (cf getSampleValues).

    Additionally, we may want to draw a set of points where some have
    arrows and some do not. To allow this, if *length* is None,
    another column of type floating-misc is added, specifying per-row
    arrow lengths. If one of these is zero, no arrow is drawn for that
    point.

    Finally, we can either draw on top of a substamp, or use a default.
    The default draws a narrow bar perpendicular to the arrow and is
    activated by setting *substamp* to None.

    So, by default, with up-down arrows, the dataholder pattern becomes

    [x, y, y-arrow-towards]

    With left-right arrows, it's

    [x, x-arrow-towards, y]

    With variably-lengthed up-down arrows, it's

    [arrowlength, x, y, y-arrow-towards]
    """

    def __init__ (self, substamp, direction, length, headsize, keylength):
        self.substamp = substamp
        self.direction = direction
        self.length = length # in style.largeScale, or None
        self.headsize = headsize # in style.largeScale
        self.keylength = keylength
        self.lengthCInfo = None


    def setData (self, data):
        if self.substamp is not None:
            self.substamp.setData (data)

        super (_WithArrow, self).setData (data)

        if self.direction in ('left', 'right'):
            self.towardsCInfo = data.register (0, 0, 1, 0)
        else:
            self.towardsCInfo = data.register (0, 0, 0, 1)

        if self.length is None:
            self.lengthCInfo = data.register (0, 1, 0, 0)


    def _getSampleValues (self, style, x, y):
        if self.substamp is None:
            subd = ()
        else:
            subd = self.substamp._getSampleValues (style, x, y)

        l = self.keylength * style.largeScale

        if self.direction == 'left':
            v = x - l
        elif self.direction == 'right':
            v = x + l
        elif self.direction == 'top':
            v = y - l
        elif self.direction == 'bottom':
            v = y + l

        return (v, l) + subd


    def _getDataValues (self, style, xform):
        if self.substamp is None:
            subd = ()
        else:
            subd = self.substamp._getDataValues (style, xform)

        imisc, fmisc, x, y = self.data.getMapped (self.towardsCInfo, xform)

        if self.direction in ('left', 'right'):
            towards = x[0]
        else:
            towards = y[0]

        if self.length is not None: # fixed length for all arrows
            l = self.length * style.largeScale
        else: # length varies from arrow to arrow
            imisc, fmisc, x, y = self.data.getMapped (self.lengthCInfo, xform)
            l = fmisc[0] * style.largeScale

        return (towards, l) + subd


    def _paintData (self, ctxt, style, x, y, mydata):
        towards, lengths = mydata[:2]
        subdata = mydata[2:]
        isx = self.direction in ('left', 'right')

        if self.substamp is not None:
            self.substamp._paintData (ctxt, style, x, y, subdata)

        if isx:
            ref = x
            dirs = ['left', 'right']
        else:
            ref = y
            dirs = ['top', 'bottom']

        for i in xrange (x.size):
            if self.substamp is None:
                # Draw our little perpendicular bar, copying the sizing logic
                # used in arrow ()
                if isx:
                    ctxt.move_to (x[i], y[i] - 0.3 * self.headsize * style.largeScale)
                    ctxt.line_to (x[i], y[i] + 0.3 * self.headsize * style.largeScale)
                    ctxt.stroke ()
                else:
                    ctxt.move_to (x[i] - 0.3 * self.headsize * style.largeScale, y[i])
                    ctxt.line_to (x[i] + 0.3 * self.headsize * style.largeScale, y[i])
                    ctxt.stroke ()

            if lengths[i] != 0:
                # This one gets drawn. Figure out the effective
                # direction and length, set by the relation between
                # the data coordinate and towards, and do it.
                l = min (abs (towards[i] - ref[i]), lengths[i])
                d = dirs[ref[i] < towards[i]]
                arrow (ctxt, x[i], y[i], d, l, self.headsize * style.largeScale)


class WithDownArrow (_WithArrow):
    def __init__ (self, substamp=None, length=7, headsize=3, keylength=0):
        super (WithDownArrow, self).__init__ (substamp, 'bottom', length,
                                              headsize, keylength)


class WithUpArrow (_WithArrow):
    def __init__ (self, substamp=None, length=7, headsize=3, keylength=0):
        super (WithUpArrow, self).__init__ (substamp, 'top', length,
                                            headsize, keylength)


class WithLeftArrow (_WithArrow):
    def __init__ (self, substamp=None, length=7, headsize=3, keylength=0):
        super (WithLeftArrow, self).__init__ (substamp, 'left', length,
                                              headsize, keylength)


class WithRightArrow (_WithArrow):
    def __init__ (self, substamp=None, length=7, headsize=3, keylength=0):
        super (WithRightArrow, self).__init__ (substamp, 'right', length,
                                               headsize, keylength)


# The all-in-wonder MultiStamp.

_ms_features = {
    'cnum': (1, 0, 0, 0),
    'fill': (1, 0, 0, 0),
    'shape': (1, 0, 0, 0),
    'size': (0, 1, 0, 0),
    'tlines': (1, 0, 0, 0),
    'ux': (1, 0, 2, 0),
    'uy': (1, 0, 0, 2),
}

def _rotated_triangle (rot):
    def paint (ctxt, style, size, fill):
        ctxt.save ()
        ctxt.rotate (rot)
        symUpTriangle (ctxt, style, size, fill)
        ctxt.restore ()

    return paint


class MultiStamp (RStamp):
    features = None
    fixedfill = True
    fixedlinestyle = None
    fixedshape = 0
    fixedsize = _defaultStampSize
    extracolors = []

    _cnum_cinfo = None
    _fill_cinfo = None
    _shape_cinfo = None
    _size_cinfo = None
    _tlines_cinfo = None
    _ux_cinfo = None
    _uy_cinfo = None

    def __init__ (self, *features):
        for f in features:
            if f not in _ms_features:
                raise ValueError ('unrecognized feature "%s"' % f)
        self.features = features


    def setData (self, data):
        super (MultiStamp, self).setData (data)

        for f in self.features:
            setattr (self, '_' + f + '_cinfo', data.register (*_ms_features[f]))


    def paintAt (self, ctxt, style, x, y):
        pass # TODO


    def paintMany (self, ctxt, style, xform):
        imisc, fmisc, allx, ally = self.data.getAllMapped (xform)
        x = allx[0]
        y = ally[0]

        docnum = self._cnum_cinfo is not None
        dofill = self._fill_cinfo is not None
        doshape = self._shape_cinfo is not None
        dosize = self._size_cinfo is not None
        dotlines = self._tlines_cinfo is not None
        doux = self._ux_cinfo is not None
        douy = self._uy_cinfo is not None

        if docnum:
            cnums = self.data.get (self._cnum_cinfo)[0][0]

        if dofill:
            fills = self.data.get (self._fill_cinfo)[0][0]
        else:
            fill = self.fixedfill

        if doshape:
            shapes = self.data.get (self._shape_cinfo)[0][0]

        if dosize:
            sizes = self.data.get (self._size_cinfo)[1][0]
        else:
            size = self.fixedsize

        if doux:
            d = self.data.getMapped (self._ux_cinfo, xform)
            xlimstyles = d[0][0]
            uxs = d[2]
        else:
            uxkind = 'n'

        if douy:
            d = self.data.getMapped (self._uy_cinfo, xform)
            ylimstyles = d[0][0]
            uys = d[3]
        else:
            uykind = 'n'

        if dotlines:
            lineinfo = self.data.get (self._tlines_cinfo)[0][0]
            linegroups = {}

            for i in xrange (x.size):
                idx = lineinfo[i]
                if idx == 0:
                    continue
                linegroups.setdefault (idx, []).append (i)

            ctxt.save ()
            style.apply (ctxt, self.fixedlinestyle)

            for points in linegroups.itervalues ():
                n = len (points)
                if n < 2:
                    continue

                ctxt.move_to (x[points[0]], y[points[0]])
                for i in xrange (1, n):
                    ctxt.line_to (x[points[i]], y[points[i]])
                ctxt.stroke ()

            ctxt.restore ()

        for i in xrange (x.size):
            ctxt.save ()

            if docnum:
                if cnums[i] < 0:
                    ctxt.set_source_rgb (*self.extracolors[-cnums[i] - 1])
                else:
                    ctxt.set_source_rgb (*style.colors.getDataColor (cnums[i]))

            if doshape:
                symfunc = style.data.getStrictSymbolFunc (shapes[i])
            else:
                symfunc = style.data.getStrictSymbolFunc (self.fixedshape)

            if dosize:
                size = sizes[i]

            if dofill:
                fill = fills[i]

            if doux:
                xls = xlimstyles[i]

                if xls == -1:
                    uxkind = 'u' # upper limit
                elif xls == 1:
                    uxkind = 'l' # lower
                elif uxs[0,i] == x[i] and uxs[1,i] == x[i]:
                    uxkind = 'n' # none
                else:
                    uxkind = 'b' # error bars

            if douy:
                yls = ylimstyles[i]

                if yls == -1:
                    uykind = 'u' # upper limit
                elif yls == 1:
                    uykind = 'l' # lower
                elif uys[0,i] == y[i] and uys[1,i] == y[i]:
                    uykind = 'n' # none
                else:
                    uykind = 'b' # error bars

            if uxkind == 'u':
                if uykind == 'u':
                    symfunc = _rotated_triangle (-0.75 * np.pi)
                elif uykind == 'l':
                    symfunc = _rotated_triangle (-0.25 * np.pi)
                else:
                    symfunc = _rotated_triangle (-0.5 * np.pi)
            elif uxkind == 'l':
                if uykind == 'u':
                    symfunc = _rotated_triangle (0.75 * np.pi)
                elif uykind == 'l':
                    symfunc = _rotated_triangle (0.25 * np.pi)
                else:
                    symfunc = _rotated_triangle (0.5 * np.pi)
            elif uykind == 'u':
                symfunc = _rotated_triangle (np.pi)
            elif uykind == 'l':
                symfunc = _rotated_triangle (0)

            if uxkind == 'b':
                #ctxt.set_line_width (style.sizes.thickLine)
                ctxt.move_to (uxs[0,i], y[i])
                ctxt.line_to (uxs[1,i], y[i])
                ctxt.stroke ()

            if uykind == 'b':
                ctxt.move_to (x[i], uys[0,i])
                ctxt.line_to (x[i], uys[1,i])
                ctxt.stroke ()

            ctxt.translate (x[i], y[i])
            symfunc (ctxt, style, size, fill)
            ctxt.restore ()
