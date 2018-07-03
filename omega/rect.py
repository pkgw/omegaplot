# -*- mode: python; coding: utf-8 -*-
# Copyright 2011, 2012, 2014 Peter Williams
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

# Rectangular plots.

from __future__ import absolute_import, division, print_function, unicode_literals

import six
from six.moves import range as xrange
import cairo
import numpy as np

from .base import *
from .base import (_TextPainterBase, _kwordDefaulted,
                   _kwordExtract, _checkKwordsConsumed)
from .base import textMarkup as TM
from .layout import RightRotationPainter
from . import util


class RectDataHolder (DataHolder):
    AxisX = 2
    AxisY = 3

    def __init__ (self, xtype, ytype):
        self.axistypes += (xtype, ytype)

    def getMapped (self, cinfo, xform):
        imisc, fmisc, x, y = self.get (cinfo)
        x = xform.mapX (x)
        y = xform.mapY (y)
        return imisc, fmisc, x, y

    def getAllMapped (self, xform):
        imisc, fmisc, x, y = self.getAll ()
        x = xform.mapX (x)
        y = xform.mapY (y)
        return imisc, fmisc, x, y

    def getMappedXY (self, cinfo, xform):
        imisc, fmisc, x, y = self.get (cinfo)
        return xform.mapX (x[0]), xform.mapY (y[0])

    def getRawXY (self, cinfo):
        imisc, fmisc, x, y = self.get (cinfo)
        return x[0], y[0]


class RectAxis (object):
    """Generic class for a logical axis on a rectangular plot. Note that
    this class does not paint the axis; it just maps values from the bounds
    to a [0, 1] range so that the RectPlot class knows where to locate
    points.

    Implementations must have read-write attributes "min" and "max" which
    control the axis bounds."""

    min = None
    max = None
    reverse = False

    def transform (self, values):
        """Return where the given values should reside on this axis, 0
        indicating all the way towards the physical minimum of the
        plotting area, 1 indicating all the way to the maximum."""
        raise NotImplementedError ()

    def inbounds (self, values):
        """Return True for each value that is within the bounds of this axis."""
        raise NotImplementedError ()

    def normalize (self):
        if self.min > self.max:
            self.reverse = True
            self.min, self.max = self.max, self.min


class LinearAxis (RectAxis):
    """A linear logical axis for a rectangular plot."""

    def __init__ (self, min=0., max=10.):
        self.min = min
        self.max = max

    def transform (self, values):
        # The +0 forces floating-point evaluation.
        if self.reverse:
            return (self.max - (values + 0.0)) / (self.max - self.min)
        return (values + 0.0 - self.min) / (self.max - self.min)

    def inbounds (self, values):
        return np.logical_and (values >= self.min, values <= self.max)


class LogarithmicAxis (RectAxis):
    """A logarithmic logical axis for a rectangular plot."""

    def __init__ (self, logmin=-3., logmax=3.):
        self.logmin = logmin
        self.logmax = logmax
        self.reverse = False

    def getMin (self):
        return 10 ** self.logmin

    def setMin (self, value):
        if value > 0:
            self.logmin = np.log10 (value)
        else:
            self.logmin = -8

    min = property (getMin, setMin)

    def getMax (self):
        return 10 ** self.logmax

    def setMax (self, value):
        if value > 0:
            self.logmax = np.log10 (value)
        else:
            self.logmax = -8

    max = property (getMax, setMax)

    def transform (self, values):
        values = np.asarray (values)

        if values.size == 0:
            # Need to catch this since otherwise the ret.min() below
            # will cause an error.
            return np.zeros_like (values)

        valid = values > 0
        vc = np.where (valid, values, 1)

        if self.reverse:
            ret = (self.logmax - np.log10 (vc)) / (self.logmax - self.logmin)
        ret = (np.log10 (vc) - self.logmin) / (self.logmax - self.logmin)

        # For zero or negative values, return something very small and
        # smaller than the smallest valid value, to preserve ordering
        # of the data -- this is relevant for histogram-type plots
        # with out-of-bounds values on log axes.
        return np.where (valid, ret, min (-10, ret.min () - 1))

    def inbounds (self, values):
        valid = values > 0
        vc = np.where (valid, values, 1)
        lv = np.log10 (vc)

        return np.logical_and (valid, np.logical_and (lv >= self.logmin, lv <= self.logmax))


# Axis Painters

class BlankAxisPainter (object):
    """An axisPainter for the RectPlot class. Either paints nothing at
    all, or just the line on the plot with no tick marks or labels."""

    drawBaseline = True
    lineStyle = 'bgLinework'


    # FIXME: minimum size should reflect current style's
    # linewidth

    def paint (self, helper, ctxt, style):
        if not self.drawBaseline: return

        ctxt.save ()

        style.apply (ctxt, self.lineStyle)
        helper.paintBaseline (ctxt)

        ctxt.restore ()


    def spaceExterior (self, helper, ctxt, style):
        return 0, 0, 0


    def nudgeBounds (self, nudgeMode=True):
        """Modify the bounds of our axis to a superset of the inputs.
        The new bounds should be "nice" for this axis, i.e., rounded off
        to some reasonable value. For instance, for a regular base-10 linear
        axis, nudging (1, 9) should probably yield (0, 10)."""
        pass


class AxisPaintHelper (object):
    """A helper class that makes common axis-painting operations
    agnostic to the orientation of the axis we are painting. More
    specialized axis painters can look at the 'side' member of this
    class and handle cases more intelligently."""

    def __init__ (self, w, h):
        self.side = -1
        self.w = w
        self.h = h


    def paintBaseline (self, ctxt):
        if self.side == RectPlot.SIDE_TOP:
            ctxt.move_to (0, 0)
            ctxt.line_to (self.w, 0)
        elif self.side == RectPlot.SIDE_RIGHT:
            ctxt.move_to (self.w, 0)
            ctxt.line_to (self.w, self.h)
        elif self.side == RectPlot.SIDE_BOTTOM:
            ctxt.move_to (0, self.h)
            ctxt.line_to (self.w, self.h)
        elif self.side == RectPlot.SIDE_LEFT:
            ctxt.move_to (0, 0)
            ctxt.line_to (0, self.h)
        ctxt.stroke ()


    def paintTickIn (self, ctxt, loc, len):
        """Note that the coordinate system used by axis classes needs
        to be transformed to the cairo system, in which (0,0) is the
        upper left, not the bottom left."""

        if self.side == RectPlot.SIDE_TOP:
            ctxt.move_to (self.w * loc, 0)
            ctxt.rel_line_to (0, len)
        elif self.side == RectPlot.SIDE_RIGHT:
            ctxt.move_to (self.w, self.h * (1. - loc))
            ctxt.rel_line_to (-len, 0)
        elif self.side == RectPlot.SIDE_BOTTOM:
            ctxt.move_to (self.w * loc, self.h)
            ctxt.rel_line_to (0, -len)
        elif self.side == RectPlot.SIDE_LEFT:
            ctxt.move_to (0, self.h * (1. - loc))
            ctxt.rel_line_to (len, 0)
        ctxt.stroke ()


    def paintTickOut (self, ctxt, loc, len):
        self.paintTickIn (ctxt, w, h, loc, -len)


    def paintNormalTickIn (self, ctxt, loc, angle, length):
        # Not 100% confident that what we do is right, given the
        # difference between the normalized coordinates [(0,1)x(0,1)]
        # and the Cairo coordinates [(0,w)x(0,h)].

        side = self.side

        if side in (RectPlot.SIDE_TOP, RectPlot.SIDE_LEFT):
            sign = 1
        else:
            sign = -1

        if abs (angle) < np.pi/2:
            a = angle + sign * np.pi/2
        else:
            a = angle - sign * np.pi/2

        if side in (RectPlot.SIDE_LEFT, RectPlot.SIDE_RIGHT):
            a -= np.pi/2

        if side == RectPlot.SIDE_TOP:
            ctxt.move_to (self.w * loc, 0)
        elif side == RectPlot.SIDE_RIGHT:
            ctxt.move_to (self.w, self.h * (1. - loc))
        elif side == RectPlot.SIDE_BOTTOM:
            ctxt.move_to (self.w * loc, self.h)
        elif side == RectPlot.SIDE_LEFT:
            ctxt.move_to (0, self.h * (1. - loc))

        c = np.cos (a) * length
        s = np.sin (a) * length
        ctxt.rel_line_to (c, s)
        ctxt.stroke ()


    def moveToAlong (self, ctxt, loc):
        """Move to the specified position along the axis"""
        if self.side == RectPlot.SIDE_TOP:
            ctxt.move_to (self.w * loc, 0)
        elif self.side == RectPlot.SIDE_RIGHT:
            ctxt.move_to (self.w, self.h * (1. - loc))
        elif self.side == RectPlot.SIDE_BOTTOM:
            ctxt.move_to (self.w * loc, self.h)
        elif self.side == RectPlot.SIDE_LEFT:
            ctxt.move_to (0, self.h * (1. - loc))


    def relMoveIn (self, ctxt, len):
        """Perform a relative move orthogonal to the axis towards
        the interior of the plot."""
        if self.side == RectPlot.SIDE_TOP:
            ctxt.rel_move_to (0, len)
        elif self.side == RectPlot.SIDE_RIGHT:
            ctxt.rel_move_to (-len, 0)
        elif self.side == RectPlot.SIDE_BOTTOM:
            ctxt.rel_move_to (0, -len)
        elif self.side == RectPlot.SIDE_LEFT:
            ctxt.rel_move_to (len, 0)


    def relMoveOut (self, ctxt, len):
        self.relMoveIn (ctxt, -len)


    def relMoveRectOut (self, ctxt, rw, rh):
        """We are at a given place. We wish to move to a point such
        that a rectangle of width rw and height rh will be centered on
        its edge closest to the interior of the plot. We move to the
        location of the upper-left corner of the rectangle. Basically this
        is for aligning text relative to tick marks."""

        if self.side == RectPlot.SIDE_TOP:
            ctxt.rel_move_to (-rw / 2, -rh)
        elif self.side == RectPlot.SIDE_RIGHT:
            ctxt.rel_move_to (0, -rh / 2)
        elif self.side == RectPlot.SIDE_BOTTOM:
            ctxt.rel_move_to (-rw / 2, 0)
        elif self.side == RectPlot.SIDE_LEFT:
            ctxt.rel_move_to (-rw, -rh / 2)


    def setupAngledRect (self, ctxt, rw, rh):
        x, y = ctxt.get_current_point ()
        ctxt.translate (-x, -y)
        ctxt.rotate (np.pi/4)

        if self.side == RectPlot.SIDE_TOP:
            ctxt.rel_move_to (-rw, -rh)
        elif self.side == RectPlot.SIDE_RIGHT:
            ctxt.rel_move_to (0, -rh)
        elif self.side == RectPlot.SIDE_BOTTOM:
            pass
        elif self.side == RectPlot.SIDE_LEFT:
            ctxt.rel_move_to (-rw, 0)


    def spaceRectOut (self, rw, rh, angle=False):
        """Return the amount of exterior space orthogonal to the side we're on that
        is required for a rectangle aligned as described in relMoveRectOut."""

        if angle:
            return (rh + rw) * 0.707107

        if self.side == RectPlot.SIDE_TOP or self.side == RectPlot.SIDE_BOTTOM:
            return rh
        return rw


    def spaceRectAlong (self, rw, rh):
        """Return the amount of exterior space along the side we're on that is
        required for a rectangle aligned as described in relMoveRectOut."""

        if self.side == RectPlot.SIDE_TOP or self.side == RectPlot.SIDE_BOTTOM:
            return rw
        return rh


    def spaceRectPos (self, pos, rw, rh, angle=False):
        """Return the amount of space along the side we're on that is
        required for a rectangle at the given position beyond the edge of the
        plot field and behind it."""

        if not angle:
            if self.side in (RectPlot.SIDE_TOP, RectPlot.SIDE_BOTTOM):
                fwbase = bhbase = rw / 2
            else:
                fwbase = bhbase = rh / 2
        else:
            if self.side in (RectPlot.SIDE_TOP, RectPlot.SIDE_RIGHT):
                fwbase = rh * 0.707107
                bhbase = rw * 0.707107
            else:
                fwbase = rw * 0.707107
                bhbase = rh * 0.707107

        if self.side == RectPlot.SIDE_TOP:
            forward = fwbase + (pos - 1) * self.w
            behind = bhbase - pos * self.w
        elif self.side == RectPlot.SIDE_RIGHT:
            forward = fwbase - pos * self.h
            behind = bhbase + (pos - 1) * self.h
        elif self.side == RectPlot.SIDE_BOTTOM:
            forward = fwbase - pos * self.w
            behind = bhbase + (pos - 1) * self.w
        elif self.side == RectPlot.SIDE_LEFT:
            forward = fwbase + (pos - 1) * self.h
            behind = bhbase - pos * self.h

        forward = max (forward, 0)
        behind = max (behind, 0)

        return forward, behind


class LinearAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a standard linear
    axis with evenly spaced tick marks."""

    def __init__ (self, axis):
        super (LinearAxisPainter, self).__init__ ()
        self.axis = axis


    labelSeparation = 2 # in smallScale
    numFormat = '%g' # can be a function mapping float -> str
    majorTickScale = 2.5 # in largeScale
    minorTickScale = 2.5 # in smallScale
    minorTicks = 5
    autoBumpThreshold = 0.3
    tickStyle = 'bgLinework' # style ref.
    textColor = 'foreground'
    labelStyle = None
    avoidBounds = True # do not draw ticks at extremes of axes
    paintLabels = True # draw any labels at all?
    labelMinorTicks = False # draw value labels at the minor tick points?
    everyNthMajor = 1 # draw every Nth major tick label
    everyNthMinor = 1 # draw every Nth minor tick label, if labelMinorTicks is True

    def nudgeBounds (self, nudgeMode=True):
        self.axis.normalize ()
        span = self.axis.max - self.axis.min

        range_is_effectively_zero = (span == 0)

        if not range_is_effectively_zero:
            # It can happen that the span is not exactly zero, but that if we
            # further subdivide the span so as to draw ticks, we saturate our
            # floating-point precision. Check for that here, reproducing the
            # calculation of "inc" in getTickLocations; if it happens, act as
            # if the span were effecively zero.

            mip = int(np.floor(np.log10(1.0 * span)))
            if np.log10(1.0 * span) - mip < self.autoBumpThreshold:
                mip -= 1
            inc = 10.**mip / self.minorTicks
            range_is_effectively_zero = (self.axis.max - inc == self.axis.max)

        if range_is_effectively_zero:
            if self.axis.max == 0:
                self.axis.min = -1
                self.axis.max = 1
                return

            self.axis.min *= 0.95
            self.axis.max *= 1.05
            return

        # "tight" mode sticks close to the data span

        if 'tight' == nudgeMode:
            self.axis.max += 0.05 * span
            self.axis.min -= 0.05 * span
            return

        # Otherwise, we're in the standard mode where we adjust the bounds to
        # the nearest round numbers. Large integer axis bounds can cause
        # problems: np.log10 (long (1e19)) works fine, but np.log10 (long
        # (1e20)) raises an AttributeError. I imagine there's some internal
        # conversion to bignum representation. Anyway, we avoid any problems
        # by coercing to floating-point.

        mip = int (np.floor (np.log10 (1. * span))) # major interval power
        step = 10 ** mip

        newmin = int (np.floor (self.axis.min / step)) * step
        newmax = int (np.ceil (self.axis.max / step)) * step

        self.axis.min, self.axis.max = newmin, newmax


    def formatLabel (self, val):
        if callable (self.numFormat): return self.numFormat (val)
        return self.numFormat % (val)


    def getTickLocations (self):
        self.axis.normalize ()
        span = 1. * (self.axis.max - self.axis.min) # see comment in nudgeBounds()
        mip = int (np.floor (np.log10 (span))) # major interval power

        if np.log10 (span) - mip < self.autoBumpThreshold:
            # If we wouldn't have that many tickmarks, decrease MIP
            # to make the labels denser.
            mip -= 1

        # NOTE: 'inc' can fall prey to floating-point inexactness,
        # e.g. "0.2" really is 0.2 + 1.1e-17. This can be a problem
        # when the bounds have been nudged to be nice and round
        # because the inexactness may accumulate as we increment
        # 'val', resulting in the final tick not being drawn and
        # labeled because 'val' is 6 + 1e-16, not 6 exactly. To
        # combat this, we round off 'val' when it is at major tick,
        # which have nice round values.

        inc = 10. ** mip / self.minorTicks # incr. between minor ticks
        coeff = int (np.ceil (self.axis.min / inc)) # coeff. of first tick
        val = coeff * inc # location of first tick

        if val < self.axis.min:
            # Rounding errors can cause val to be out-of-bounds by
            # a miniscule amount. This only happens if it is on the
            # exteme edge of the axis, so we know what value it
            # ought to have: exactly axis.min.
            val = self.axis.min

        if val + inc == val:
            # It can happen that the values are not all identical, but that
            # their dynamic range is too fine to resolve in our numerical
            # precision. If that happens here, let's just give up.
            return []

        # If we cross zero, floating-point rounding errors cause the
        # ticks to be placed at points like 6.3e-16. Detect this case
        # and round to 0. Do it in units of the axis bounds so that a
        # plot from -1e-6 to 1e-6 will still work OK.

        if (self.axis.max <= 0. and self.axis.min >= 0.) or \
           (self.axis.min <= 0. and self.axis.max >= 0.):
            scale = max (abs (self.axis.max), abs (self.axis.min))
            zeroclamp = scale * 1e-6
        else:
            zeroclamp = None

        # We don't implement this function as a generator because in some
        # cases there is a nontrivial efficiency gain from bunching up the
        # transforms.

        values = []
        isMajors = []
        getsLabels = []
        majorCount = -1
        minorCount = coeff % self.minorTicks - 1

        while self.axis.inbounds (val):
            values.append (val)
            isMajor = coeff % self.minorTicks == 0
            isMajors.append (isMajor)

            minorCount += 1
            if isMajor:
                majorCount += 1
                minorCount = 0

            getsLabel = isMajor and (majorCount % self.everyNthMajor) == 0
            if self.labelMinorTicks:
                getsLabel = getsLabel or (minorCount % self.everyNthMinor) == 0

            getsLabels.append (getsLabel)

            # Advance value, adjusting so that the inbounds test gets a better
            # value to check.

            val += inc
            coeff += 1

            if zeroclamp and abs(val) < zeroclamp:
                val = 0.
            if coeff % self.minorTicks == 0:
                val = int (round (val / 10.**mip)) * 10**mip

        xformed = self.axis.transform (np.asarray (values))
        return zip (values, xformed, isMajors, getsLabels)


    def getLabelInfos (self, ctxt, style):
        if not self.paintLabels:
            return

        # Create the TextStamper objects all at once, so that if we
        # are using the LaTeX backend, we can generate their PNG
        # images all in one go. (That will happen upon the first
        # invocation of getSize.)

        labels = []

        for val, xformed, isMajor, getsLabel in self.getTickLocations ():
            if getsLabel:
                s = self.formatLabel (val)
                labels.append ((TextStamper (s), xformed, isMajor))

        for ts, xformed, isMajor in labels:
            w, h = ts.getSize (ctxt, style)
            yield (ts, xformed, w, h)


    def spaceExterior (self, helper, ctxt, style):
        forward = outside = backward = 0

        for ts, xformed, w, h in self.getLabelInfos (ctxt, style):
            outside = max (outside, helper.spaceRectOut (w, h))
            fw, bw = helper.spaceRectPos (xformed, w, h)
            forward = max (forward, fw)
            backward = max (backward, bw)

        if outside > 0:
            outside += self.labelSeparation * style.smallScale

        return forward, outside, backward


    def paint (self, helper, ctxt, style):
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        for val, xformed, isMajor, getsLabel in self.getTickLocations ():
            if isMajor:
                len = self.majorTickScale * style.largeScale
            else:
                len = self.minorTickScale * style.smallScale

            # If our tick would land right on the bounds of the plot field, it
            # might overplot on the baseline of the axis adjacent to ours.
            # This is ugly, so don't do it. However, this behavior can be
            # disabled by setting avoidBounds to false, so that if the
            # adjacent axes don't draw their baselines, we'll see the ticks as
            # desired.

            if not self.avoidBounds or (xformed != 0. and xformed != 1.):
                helper.paintTickIn (ctxt, xformed, len)

        style.apply (ctxt, self.labelStyle)
        tc = style.getColor (self.textColor)

        for (ts, xformed, w, h) in self.getLabelInfos (ctxt, style):
            helper.moveToAlong (ctxt, xformed)
            helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)
            helper.relMoveRectOut (ctxt, w, h)
            ts.paintHere (ctxt, tc)

LinearAxis.defaultPainter = LinearAxisPainter


class LogarithmicAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a standard logarithmic
    axis with evenly spaced tick marks."""

    def __init__ (self, axis):
        super (LogarithmicAxisPainter, self).__init__ ()
        self.axis = axis


    labelSeparation = 2 # in smallScale
    formatLogValue = False # if true, format log10(value), not the raw value
    majorTickScale = 2 # in largeScale
    minorTickScale = 2 # in smallScale
    tickStyle = 'bgLinework' # style ref.
    textColor = 'foreground'
    labelStyle = None
    avoidBounds = True # do not draw ticks at extremes of axes
    paintLabels = True # paint any labels at all?
    labelMinorTicks = False # draw value labels at the minor tick points?
    labelSomeMinorTicks = False # label 3x and 6x minor ticks?
    everyNthMajor = 1 # draw every Nth major tick label
    everyNthMinor = 1 # draw every Nth minor tick label, if labelMinorTicks is True

    def nudgeBounds (self, nudgeMode=True):
        self.axis.normalize ()

        # "tight" mode sticks close to the data span

        if 'tight' == nudgeMode:
            span = self.axis.logmax - self.axis.logmin
            self.axis.logmax += 0.05 * span
            self.axis.logmin -= 0.05 * span
            return

        # Otherwise, we're in the standard mode where we adjust the bounds
        # to the nearest whole powers.

        self.axis.logmin = np.floor (self.axis.logmin)
        self.axis.logmax = np.ceil (self.axis.logmax)


    def formatLabel (self, coeff, exp):
        if callable (self.numFormat): return self.numFormat (coeff, exp)

        if self.formatLogValue: val = exp + np.log10 (coeff)
        else: val = coeff * 10.**exp

        return self.numFormat % (val)


    def numFormat (self, coeff, exp):
        if exp >= 0 and exp < 3:
            return TM ('%.0f') % (coeff * 10.**exp)
        if exp > -3 and exp < 0:
            return TM ('%.*f') % (-exp, coeff * 10.**exp)
        if coeff == 1:
            return TM ('10^%d') % exp
        return TM ('%d*10^%d') % (coeff, exp)


    def getTickLocations (self):
        self.axis.normalize ()
        curpow = int (np.floor (self.axis.logmin))
        coeff = int (np.ceil (10. ** (self.axis.logmin - curpow)))
        if coeff == 10:
            curpow += 1
            coeff = 1

        coeffs = []
        curpows = []
        isMajors = []
        getsLabels = []
        majorCount = -1
        minorCount = coeff % 9 - 1

        while self.axis.inbounds (coeff*10.**curpow):
            coeffs.append (coeff)
            curpows.append (curpow)
            isMajor = (coeff == 1)
            isMajors.append (isMajor)

            minorCount += 1
            if isMajor:
                majorCount += 1
                minorCount = 0

            getsLabel = isMajor and (majorCount % self.everyNthMajor) == 0
            if self.labelMinorTicks:
                getsLabel = getsLabel or (minorCount % self.everyNthMinor) == 0
            elif self.labelSomeMinorTicks:
                if not isMajor:
                    getsLabel = (coeff == 3) or (coeff == 6)

            getsLabels.append (getsLabel)

            if coeff == 9:
                coeff = 1
                curpow += 1
            else:
                coeff += 1

        xformed = self.axis.transform (np.asarray (coeffs) * 10.**np.asarray (curpows))
        return zip (coeffs, curpows, xformed, isMajors, getsLabels)


    def getLabelInfos (self, ctxt, style):
        if not self.paintLabels:
            return

        # Create the TextStamper objects all at once, so that if we are using
        # the LaTeX backend, we can generate them images all in one go. (That
        # will happen upon the first invocation of doLayout.)

        labels = []

        for (coeff, exp, xformed, isMajor, getsLabel) in self.getTickLocations ():
            if getsLabel:
                s = self.formatLabel (coeff, exp)
                labels.append ((TextStamper (s), xformed, isMajor))

        for (ts, xformed, isMajor) in labels:
            w, h = ts.getSize (ctxt, style)

            yield (ts, xformed, w, h)


    def spaceExterior (self, helper, ctxt, style):
        forward = outside = backward = 0

        for ts, xformed, w, h in self.getLabelInfos (ctxt, style):
            outside = max (outside, helper.spaceRectOut (w, h))
            fw, bw = helper.spaceRectPos (xformed, w, h)
            forward = max (forward, fw)
            backward = max (backward, bw)

        if outside > 0:
            outside += self.labelSeparation * style.smallScale

        return forward, outside, backward


    def paint (self, helper, ctxt, style):
        super (LogarithmicAxisPainter, self).paint (helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        for (coeff, exp, xformed, isMajor, getsLabel) in self.getTickLocations ():
            if isMajor: len = self.majorTickScale * style.largeScale
            else: len = self.minorTickScale * style.smallScale

            # If our tick would land right on the bounds of the plot field,
            # it might overplot on the baseline of the axis adjacent to ours.
            # This is ugly, so don't do it. However, this behavior can be
            # disabled by setting avoidBounds to false, so that if the adjacent
            # axes don't draw their baselines, we'll see the ticks as desired.

            if not self.avoidBounds or (xformed != 0. and xformed != 1.):
                helper.paintTickIn (ctxt, xformed, len)

        style.apply (ctxt, self.labelStyle)
        tc = style.getColor (self.textColor)

        for (ts, xformed, w, h) in self.getLabelInfos (ctxt, style):
            helper.moveToAlong (ctxt, xformed)
            helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)
            helper.relMoveRectOut (ctxt, w, h)
            ts.paintHere (ctxt, tc)


class _LogLinMappingAxis (LinearAxis):
    def __init__ (self, logaxis):
        if not isinstance (logaxis, LogarithmicAxis):
            raise ValueError ('logaxis')

        self.logaxis = logaxis


    def _getMax (self):
        return self.logaxis.logmax

    def _setMax (self, value):
        self.logaxis.logmax = value

    max = property (_getMax, _setMax)


    def _getMin (self):
        return self.logaxis.logmin

    def _setMin (self, value):
        self.logaxis.logmin = value

    min = property (_getMin, _setMin)


def LogValueAxisPainter (axis):
    """Creates a LinearAxisPainter that renders the log values of the inputs.
    Make sure that your axis labels reflect this!"""

    fakeaxis = _LogLinMappingAxis (axis)
    return LinearAxisPainter (fakeaxis)


LogarithmicAxis.defaultPainter = LogarithmicAxisPainter


class RectField (object):
    """A rectangular field. A field is associated with X and Y axes; other objects
    use the field to map X and Y values input from the user into coordinates at which
    to paint."""

    def __init__ (self, xaxisOrField=None, yaxis=None):
        if isinstance (xaxisOrField, RectField):
            xaxis = xaxisOrField.xaxis
            yaxis = xaxisOrField.yaxis
            return

        if xaxisOrField is None: xaxisOrField = LinearAxis ()
        if yaxis is None: yaxis = LinearAxis ()

        self.xaxis = xaxisOrField
        self.yaxis = yaxis


    class Transformer (object):
        """A utility class tied to a RectField object. Has three members:

        - mapItem (spec, item): Given a sink specification and a data item, maps those
        elements corresponding to 'X' or 'Y' values in the specification
        to an appropriate floating point number using the axes associated with the
        RectField

        - mapData (spec, data): As above for a set of data items.

        - mapX (val): Transforms val to an X value within the field using
        the RectField's X axis.

        - mapY (val): Analogous to transformX.
        """

        def __init__ (self, field, width, height, weakClamp):
            self.field = field
            self.width = float (width)
            self.height = float (height)

            if weakClamp:
                self.mapX = self._mapX_weakClamp
                self.mapY = self._mapY_weakClamp
            else:
                self.mapX = self._mapX_raw
                self.mapY = self._mapY_raw

        def _mapX_raw (self, val):
            return self.field.xaxis.transform (val) * self.width

        def _mapY_raw (self, val):
            # Mathematical Y axes have 0 on the bottom, while cairo has 0 at the
            # top. The one-minus accounts for that difference. (We transform from
            # math sense to cairo sense.)

            return (1. - self.field.yaxis.transform (val)) * self.height

        def _mapX_weakClamp (self, val):
            raw = self.field.xaxis.transform (val)
            np.clip (raw, -1.0, 2.0)

            return raw * self.width

        def _mapY_weakClamp (self, val):
            raw = 1. - self.field.yaxis.transform (val)
            np.clip (raw, -1.0, 2.0)

            return raw * self.height


    def makeTransformer (self, width, height, weakClamp):
        return self.Transformer (self, width, height, weakClamp)


    def setBounds (self, xmin=None, xmax=None, ymin=None, ymax=None):
        if xmin is not None:
            self.xaxis.min = float (xmin)
        if xmax is not None:
            self.xaxis.max = float (xmax)
        if ymin is not None:
            self.yaxis.min = float (ymin)
        if ymax is not None:
            self.yaxis.max = float (ymax)


    def expandBounds (self, xmin=None, xmax=None, ymin=None, ymax=None):
        if xmin is not None:
            self.xaxis.min = min (self.xaxis.min, float (xmin))
        if xmax is not None:
            self.xaxis.max = max (self.xaxis.max, float (xmax))
        if ymin is not None:
            self.yaxis.min = min (self.yaxis.min, float (ymin))
        if ymax is not None:
            self.yaxis.max = max (self.yaxis.max, float (ymax))


from .stamps import DataThemedStamp as _DTS


class RectPlot (Painter):
    """A rectangular plot. The workhorse of omegaplot, so it better be
    good!

    Field painters have a "zheight" property that determines the Z ordering of
    drawing -- things with numerically larger Z-heights are drawn on top of
    things with smaller Z-heights. The default is 0. The axes are drawn at a
    Z-height of 1000, and the default key is drawn with a Z-height of 2000.
    Make sure to call things "zheight" since "height" of course refers to
    the laid-out dimensions of the painter.

    """
    fieldAspect = None # Aspect ratio of the plot field, None for free
    outerPadding = 3 # in smallScale

    SIDE_TOP = 0
    SIDE_RIGHT = 1
    SIDE_BOTTOM = 2
    SIDE_LEFT = 3

    _nextDataStyleNum = 0

    def __init__ (self, emulate=None):
        super (RectPlot, self).__init__ ()

        # we might want to plot two data sets with different logical axes,
        # but store default ones here to make life easier in the common case.

        if emulate is None:
            self.defaultField = RectField ()
            self.magicAxisPainters ('lbTR')
        else:
            self.defaultField = emulate.defaultField
            self.bpainter = emulate.bpainter
            self.lpainter = emulate.lpainter
            self.rpainter = emulate.rpainter
            self.tpainter = emulate.tpainter

        self.fpainters = [] # field painters
        self.opainters = [] # outer painters
        self.mainLabels = [None] * 4
        self.defaultKey = None
        self.defaultKeyOverlay = None


    def setDefaultAxes (self, xaxis, yaxis):
        self.defaultField = RectField (xaxis, yaxis)


    def setDefaultField (self, field):
        self.defaultField = field


    def paintCoordinates (self, coordsys, labelRight=False, labelTop=True):
        if coordsys.field is None:
            coordsys.field = self.defaultField

        ax = coordsys.makeAxis (RectPlot.SIDE_TOP)
        self.tpainter = ax.defaultPainter (ax)
        self.tpainter.paintLabels = labelTop
        ax = coordsys.makeAxis (RectPlot.SIDE_BOTTOM)
        self.bpainter = ax.defaultPainter (ax)
        ax = coordsys.makeAxis (RectPlot.SIDE_LEFT)
        self.lpainter = ax.defaultPainter (ax)
        ax = coordsys.makeAxis (RectPlot.SIDE_RIGHT)
        self.rpainter = ax.defaultPainter (ax)
        self.rpainter.paintLabels = labelRight
        return self


    def addKeyItem (self, item):
        if self.defaultKey is None:
            from . import layout
            self.defaultKey = layout.VBox (0)
            self.defaultKeyOverlay = AbsoluteFieldOverlay (self.defaultKey)
            self.defaultKeyOverlay.childBgStyle = {'color': 'faint'}
            self.defaultKeyOverlay.hPadding = 3
            self.defaultKeyOverlay.vPadding = 3
            self.defaultKeyOverlay.zheight = 2000
            self.add (self.defaultKeyOverlay, rebound=False)

        if isinstance (item, six.string_types):
            item = TextPainter (item)
            item.hAlign = self.defaultKeyOverlay.hAlign
            item.vAlign = self.defaultKeyOverlay.vAlign

        self.defaultKey.appendChild (item)
        return item


    def add (self, fp, autokey=True, rebound=True, nudgex='tight', nudgey='tight',
             dsn=None, field=None, zheight=0., rself=False):
        # FIXME: don't rebound if the FP doesn't have any data.

        assert (isinstance (fp, FieldPainter))

        fp.setParent (self)
        self.fpainters.append (fp)

        if getattr (fp, 'zheight', None) is None:
            fp.zheight = zheight
        self.fpainters.sort (key=lambda fp: fp.zheight)

        if field is not None:
            fp.field = field
        elif fp.field is None:
            fp.field = self.defaultField

        if fp.needsDataStyle:
            if dsn is not None:
                fp.dsn = int (dsn)
            else:
                fp.dsn = self._nextDataStyleNum
                self._nextDataStyleNum += 1

        if autokey:
            kp = fp.getKeyPainter ()
            if kp is not None:
                self.addKeyItem (kp)

        if rebound:
            self.rebound (nudgex, nudgey, field)

        if rself:
            return self # eases chaining
        return fp


    def addXY (self, *args, **kwargs):
        l = len (args)

        lines = _kwordDefaulted (kwargs, 'lines', bool, True)
        lineStyle = _kwordDefaulted (kwargs, 'lineStyle', None, None)
        stampStyle = _kwordDefaulted (kwargs, 'stampStyle', None, None)
        pointStamp = _kwordDefaulted (kwargs, 'pointStamp', None, None)
        mcolor = _kwordDefaulted (kwargs, 'mcolor', None, None)
        mcolormap = _kwordDefaulted (kwargs, 'mcolormap', None, None)

        x, y, label = None, None, 'Data'

        if l == 3:
            x, y = map (np.asarray, args[0:2])
            label = args[2]
        elif l == 2:
            x = np.asarray (args[0])

            if x.ndim != 2 or x.shape[0] != 2:
                y = np.asarray (args[1])
            else:
                # User has done 'addXY (data, label)', where data is 2xnp.
                y = x[1]
                x = x[0]
                label = args[1]
        elif l == 1:
            y = np.asarray (args[0])

            if y.ndim != 2 or y.shape[0] != 2:
                x = np.linspace (0, len (y) - 1, len (y))
            else:
                # User has done 'addXY (data)' where data is 2xN
                x = y[0]
                y = y[1]
        else:
            raise Exception ("Don't know how to handle magic addXY() args '%s'" % (args, ))

        if mcolor is not None:
            from .stamps import MultiStamp
            pointStamp = MultiStamp ('mcolor')
            if mcolormap is not None:
                pointStamp.colormap = mcolormap
        elif mcolormap is not None:
            raise ValueError ('"mcolormap" may not be specified without also specifying "mcolor"')

        dp = XYDataPainter (lines=lines, pointStamp=pointStamp, keyText=label)

        if mcolor is not None:
            dp.setFloats (mcolor, x, y)
        else:
            dp.setFloats (x, y)

        if lineStyle is not None:
            dp.lineStyle = lineStyle
        if stampStyle is not None:
            dp.stampStyle = stampStyle

        if isinstance (pointStamp, _DTS):
            pointStamp.setHolder (dp)

        return self.add (dp, **kwargs)


    def addXYErr (self, *args, **kwargs):
        from .stamps import WithYErrorBars

        l = len (args)

        lines = _kwordDefaulted (kwargs, 'lines', bool, True)
        lineStyle = _kwordDefaulted (kwargs, 'lineStyle', None, None)
        stampStyle = _kwordDefaulted (kwargs, 'stampStyle', None, None)
        pointStamp = _kwordDefaulted (kwargs, 'pointStamp', None, None)

        x, y, dy, label = None, None, None, 'Data'

        if l == 4:
            x, y, dy = map (np.asarray, args[0:3])
            label = args[3]
        elif l == 3:
            x, y, dy = map (np.asarray, args)
        elif l == 2:
            y = np.asarray (args[0])

            if y.ndim != 2 or y.shape[0] != 3:
                dy = np.asarray (args[1])
                x = np.linspace (0, len (y) - 1, len (y))
            else:
                # User has done 'addXYErr(data, label)' where data is 3xN
                x = y[0]
                dy = y[2]
                y = y[1]
                label = args[1]
        elif l == 1:
            d = np.asarray (args[0])

            if d.ndim != 2 or d.shape[0] != 3:
                # Could treat a 2xN array as l == 2 is done above ...
                raise Exception ("A single array input to addXYErr() must be 3xN; got %s" %
                                 (d.shape, ))
            x = d[0]
            y = d[1]
            dy = d[2]
        else:
            raise Exception ("Don't know how to handle magic addXYErr() args '%s'" % (args, ))

        if pointStamp is None:
            pointStamp = _DTS (None)
        errStamp = WithYErrorBars (pointStamp)

        dp = XYDataPainter (lines=lines, pointStamp=errStamp, keyText=label)
        dp.setFloats (x, y, y + dy, y - dy)
        if lineStyle is not None:
            dp.lineStyle = lineStyle
        if stampStyle is not None:
            dp.stampStyle = stampStyle

        if isinstance (pointStamp, _DTS):
            pointStamp.setHolder (dp)

        return self.add (dp, **kwargs)


    def addDF (self, df, keyText=None, **kwargs):
        """Add a Pandas dataframe as XY + maybe Err data."""

        nc = len (df.columns)

        if nc == 2:
            return self.addXY (df.iloc[:,0], df.iloc[:,1], keyText, **kwargs)

        if nc == 3:
            return self.addXYErr (df.iloc[:,0], df.iloc[:,1], df.iloc[:,2], keyText, **kwargs)

        raise ValueError ('don\'t know what to do with DataFrame input ' + str (df))


    def addHist (self, data, bins=10, range=None, weights=None, density=None, filled=False, **kwargs):
        """Compute a histogram and add it to the plot."""
        if filled:
            dpkw = _kwordExtract (kwargs, 'keyText', 'style')
        else:
            dpkw = _kwordExtract (kwargs, 'lineStyle', 'connectors', 'keyText')

        values, edges = np.histogram (data, bins, range, weights=weights, density=density)
        if edges.size != values.size + 1:
            raise RuntimeError ('using too-old numpy? got weird histogram result')

        if filled:
            dp = FilledHistogram (**dpkw)
        else:
            dp = ContinuousSteppedPainter (**dpkw)

        dp.setDataHist (edges, values)
        return self.add (dp, **kwargs)


    def addContours (self, data, rowcoords, colcoords, keyText='Contours',
                     **kwargs):
        dp = GridContours (keyText=keyText, **_kwordExtract (kwargs, 'lineStyle'))

        kadd = _kwordExtract (kwargs, 'autokey', 'rebound', 'nudgex',
                              'nudgey', 'dsn')

        dp.setData (data, rowcoords, colcoords, **kwargs)

        return self.add (dp, **kadd)


    def addHLine (self, ypos, keyText='HLine', lineStyle=None, **kwargs):
        dp = HLine (ypos, keyText=keyText, lineStyle=lineStyle)
        return self.add (dp, **kwargs)


    def addVLine (self, xpos, keyText='VLine', lineStyle=None, **kwargs):
        dp = VLine (xpos, keyText=keyText, lineStyle=lineStyle)
        return self.add (dp, **kwargs)


    def rebound (self, nudgex='tight', nudgey='tight', field=None):
        """Recalculate the bounds of the default field based on the data
        that it contains."""

        # We can't just use RectField.setBounds/expandBounds, since
        # if the first FieldPainter doesn't define all four bounds,
        # the default [0, 10, 0, 10] bounds will remain in effect.

        if field is None:
            field = self.defaultField

        bounds = [None, None, None, None]
        reducefuncs = [min, max, min, max]

        for fp in self.fpainters:
            if fp.field is not field:
                continue

            b = fp.getDataBounds ()
            for i in xrange (4):
                if b[i] is None:
                    continue
                if bounds[i] is None:
                    bounds[i] = b[i]
                else:
                    bounds[i] = reducefuncs[i] (bounds[i], b[i])

        field.setBounds (*bounds)
        self.nudgeBounds (nudgex, nudgey)
        return self


    def addOuterPainter (self, op, side, position):
        op.setParent (self)
        self.opainters.append ((op, side, position))
        return self


    def _outerPainterIndex (self, op):
        for i in xrange (0, len(self.opainters)):
            if self.opainters[i][0] is op: return i

        raise ValueError ('%s not in list of outer painters' % (op))


    def moveOuterPainter (self, op, side, position):
        idx = self._outerPainterIndex (self, op)
        self.opainters[idx] = (op, side, position)
        return self


    def _lostChild (self, child):
        try:
            self.fpainters.remove (child)
            return
        except:
            pass

        idx = self._outerPainterIndex (child)
        del self.opainters[idx]
        return


    def magicAxisPainters (self, spec):
        """Magically set the AxisPainter variables to smart
values. More precisely, the if certain sides are specified in the
'spec' argument, those sides are painted in a sensible default style;
those sides not specified in the argument are made blank (that is,
they are painted with a baseline only).

If 'spec' contains the letter 'h' (as in 'horizontal'), both the
bottom and top sides of the field are set to the same sensible
default. If it contains 'v' (as in 'vertical'), both the left and
right sides of the field are set to the same sensible default. If it
contains the letter 'b', the bottom side is painted with a sensible
default, and similarly for the letters 't' (top), 'r' (right), and 'l'
(left). Note that a spec of 'bt' is NOT equivalent to 'h': the former
will create two AxisPainter instances, while the latter will only
create one and share it between the two sides. The same goes for 'lr'
versus 'h'.  Once again, any side NOT set by one of the above
mechanisms is set to be painted with a BlankAxisPainter instance.

If any of the above letters are capitalized, the axis painter is
created as described above, but its 'paintLabels' property is set to
False, which causes the textual labels not to be painted. (Tick marks
still are painted, though.)

To be more specific, the 'sensible default' is whatever class is
pointed to by the defaultPainter attributes of the axes of the
defaultField member of the RectPlot. This class is instantiated with
the logical axis as the only argument to __init__.

Examples:

  rp.magicAxisPainters ('lbTR') is probably what you want: all sides
  have tick marks, and the bottom and left sides have labels.

  rp.magicAxisPainters ('hv') will give an IDL-style plot
  in which all sides of the field are marked with axes.

  rp.magicAxisPainters ('r') will give an unusual plot in which
  only the right side is labeled with axes.
"""

        make = lambda axis: axis.defaultPainter (axis)
        makex = lambda: make (self.defaultField.xaxis)
        makey = lambda: make (self.defaultField.yaxis)

        # If capital letters are present, remember that some
        # label-painting should be turned off, and convert to
        # lower-case so the next stage doesn't need to worry about
        # this stuff. If 'H' and 'V' are given the last relevant
        # index, the code will work out right.

        paintlabels = [True] * 4
        plinfo = dict (H=3, V=2, T=0, R=1, B=2, L=3)

        for letter, index in six.iteritems (plinfo):
            if letter in spec:
                paintlabels[index] = False
                spec = spec.replace (letter, letter.lower ())

        # Set the painters

        if 'h' in spec:
            self.bpainter = makex ()
            self.tpainter = self.bpainter
        else:
            if 'b' in spec:
                self.bpainter = makex ()
            else:
                self.bpainter = BlankAxisPainter ()

            if 't' in spec:
                self.tpainter = makex ()
            else:
                self.tpainter = BlankAxisPainter ()

        if 'v' in spec:
            self.lpainter = makey ()
            self.rpainter = self.lpainter
        else:
            if 'l' in spec:
                self.lpainter = makey ()
            else:
                self.lpainter = BlankAxisPainter ()

            if 'r' in spec:
                self.rpainter = makey ()
            else:
                self.rpainter = BlankAxisPainter ()

        # Apply the label painting stuff

        self.tpainter.paintLabels = paintlabels[0]
        self.rpainter.paintLabels = paintlabels[1]
        self.bpainter.paintLabels = paintlabels[2]
        self.lpainter.paintLabels = paintlabels[3]

        return self


    def setLinLogAxes (self, wantxlog, wantylog, xlogvalue=False, ylogvalue=False):
        df = self.defaultField
        if not df: raise Exception ('Need a default field!')

        if isinstance (df.xaxis, LinearAxis):
            xislog = False
        elif isinstance (df.xaxis, LogarithmicAxis):
            xislog = True
        else:
            raise Exception ('X axis is neither linear nor logarithmic!')

        if isinstance (df.yaxis, LinearAxis):
            yislog = False
        elif isinstance (df.yaxis, LogarithmicAxis):
            yislog = True
        else:
            raise Exception ('Y axis is neither linear nor logarithmic!')

        def logify (axis):
            if axis.min <= 0.:
                logmin = -8 # FIXME: arbitrary magic number.
            else:
                logmin = np.log10 (axis.min)

            # Axes may be running large to small ... not sure if this
            # code will work, but it has a better chance of working than
            # if it's not here.

            if axis.max <= 0.:
                logmax = -8
            else:
                logmax = np.log10 (axis.max)

            return LogarithmicAxis (logmin, logmax)

        def linify (axis):
            return LinearAxis (10. ** axis.logmin, 10. ** axis.logmax)

        if wantxlog and not xislog:
            df.xaxis = logify (df.xaxis)
        elif not wantxlog and xislog:
            df.xaxis = linify (df.xaxis)

        if wantylog and not yislog:
            df.yaxis = logify (df.yaxis)
        elif not wantylog and yislog:
            df.yaxis = linify (df.yaxis)

        # Now update any axispainters that need it.  Make the logic
        # more restrictive in case the user has some custom axes.

        def fixpainter (wantlog, axis, painter, logvalue):
            if wantlog and isinstance (painter, LinearAxisPainter):
                if logvalue:
                    newpainter = LogValueAxisPainter (axis)
                else:
                    newpainter = LogarithmicAxisPainter (axis)
            elif not wantlog and isinstance (painter, LogarithmicAxisPainter):
                newpainter = LinearAxisPainter (axis)
            else:
                return painter

            newpainter.paintLabels = painter.paintLabels
            return newpainter

        self.tpainter = fixpainter (wantxlog, df.xaxis, self.tpainter, xlogvalue)
        self.rpainter = fixpainter (wantylog, df.yaxis, self.rpainter, ylogvalue)
        self.bpainter = fixpainter (wantxlog, df.xaxis, self.bpainter, xlogvalue)
        self.lpainter = fixpainter (wantylog, df.yaxis, self.lpainter, ylogvalue)
        return self


    # X and Y axis label helpers
    # FIXME: should have a setTitle too. Not the same as a top-side
    # label since it should be centered over the whole allocation,
    # not just the field.

    def setBounds (self, xmin=None, xmax=None, ymin=None, ymax=None):
        self.defaultField.setBounds (xmin, xmax, ymin, ymax)
        return self


    def nudgeBounds (self, nudgex='tight', nudgey='tight'):
        if nudgex:
            self.bpainter.nudgeBounds (nudgex)
            self.tpainter.nudgeBounds (nudgex)
        if nudgey:
            self.lpainter.nudgeBounds (nudgey)
            self.rpainter.nudgeBounds (nudgey)
        return self


    def setSideLabel (self, side, val):
        if self.mainLabels[side] is not None:
            self._lostChild (self.mainLabels[side])

        if val is None:
            # Label is cleared, we're done.
            return

        # (To the tune of the DragNet fanfare:)
        # Hack, hack hack hack... hack, hack hack hack haaack!
        # If the text is going on a side axis, encapsulate it
        # in a RightRotationPainter, so that we can rotate it
        # later if it's awkwardly wide.

        if not isinstance (val, Painter):
            val = TextPainter (six.text_type (val))

            if side % 2 == 1:
                val = RightRotationPainter (val)

        # End hack for now. Rest is in _calcBorders.

        self.addOuterPainter (val, side, 0.5)
        self.mainLabels[side] = val


    def setXLabel (self, val):
        self.setSideLabel (self.SIDE_BOTTOM, val)
        return self


    def setYLabel (self, val):
        self.setSideLabel (self.SIDE_LEFT, val)
        return self


    def setLabels (self, xval, yval):
        self.setXLabel (xval)
        self.setYLabel (yval)
        return self


    # Sizing and configuration

    def _axisApplyHelper (self, w, h, fn, *args):
        helper = AxisPaintHelper (w, h)

        helper.side = self.SIDE_TOP
        rt = getattr (self.tpainter, fn)(helper, *args)

        helper.side = self.SIDE_RIGHT
        rr = getattr (self.rpainter, fn)(helper, *args)

        helper.side = self.SIDE_LEFT
        rl = getattr (self.lpainter, fn)(helper, *args)

        helper.side = self.SIDE_BOTTOM
        rb = getattr (self.bpainter, fn)(helper, *args)

        return (rt, rr, rb, rl)


    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        # w and h give the size of the field, bl and bt the x and y offsets to
        # get to its true upper left corner. We have to hope that our
        # container has honored our aspect ratio request.

        minwidth = minheight = 0.
        minbt = minbr = minbb = minbl = 0.

        # Field painters are easy -- their layouts are identical to our own,
        # but without borders.

        if isfinal:
            ctxt.save ()
            ctxt.translate (bl, bt)

        for fp in self.fpainters:
            li = fp.layout (ctxt, style, isfinal, w, h, 0, 0, 0, 0)
            minwidth = max (minwidth, li.minsize[0])
            minheight = max (minheight, li.minsize[1])
            minbt = max (minbt, li.minborders[0])
            minbr = max (minbr, li.minborders[1])
            minbb = max (minbb, li.minborders[2])
            minbl = max (minbl, li.minborders[3])

        if isfinal:
            ctxt.restore ()

        # Next we have to compute the sizes of the axis labels so that we know
        # how much space is left for the outer painters.

        opad = self.outerPadding * style.smallScale
        s = self._axisApplyHelper (w, h, 'spaceExterior', ctxt, style)
        axisWidths = [0.] * 4

        for i in xrange (4): # for each side ...
            # Compute axis width:
            aw = s[i][1] # at least amount of 'outside' space needed on that axis
            aw = max (aw, s[(i+1) % 4][2]) # or 'backward' space on next axis
            aw = max (aw, s[(i+3) % 4][0]) # or 'forward' space on previous axis
            axisWidths[i] = aw

        minbt = max (minbt, axisWidths[0])
        minbr = max (minbr, axisWidths[1])
        minbb = max (minbb, axisWidths[2])
        minbl = max (minbl, axisWidths[3])

        owidths = [self.border[i] - axisWidths[i] - opad for i in xrange (4)]

        # Now we need to do the outer painters. Getting their positions and
        # borders right is obnoxious.

        for op, side, pos in self.opainters:
            li = op.layout (ctxt, style, False, 0., 0., 0., 0., 0., 0.)

            # Second part of the side label rotation hack. If the
            # aspect ratio is too big, rotate.

            if op in self.mainLabels and side % 2 == 1 and \
                   isinstance (op, RightRotationPainter) and \
                   li.minsize[0] > 0 and li.minsize[1] > 0:
                aspect = float (li.minsize[0]) / li.minsize[1]

                if aspect > 3.:
                    if side == 1:
                        op.setRotation (RightRotationPainter.ROT_CW90)
                    elif side == 3:
                        op.setRotation (RightRotationPainter.ROT_CCW90)

                    li = op.layout (ctxt, style, False, 0., 0., 0., 0., 0., 0.)
            # End second part of hack.

            ow, oh = li.minsize
            obt, obr, obb, obl = li.minborders
            ofullht = obb + oh + obt
            ofullwd = obl + ow + obr

            if side == self.SIDE_TOP:
                x = bl + (w - ow) * pos - obl
                y = owidths[0] - ofullht
                minbt = max (minbt, ofullht + opad + axisWidths[0])
                minbl = max (minbl, obl)
                minbr = max (minbr, obr)
            elif side == self.SIDE_BOTTOM:
                x = bl + (w - ow) * pos - obl
                y = self.fullh - owidths[2]
                minbb = max (minbb, ofullht + opad + axisWidths[2])
                minbl = max (minbl, obl)
                minbr = max (minbr, obr)
            elif side == self.SIDE_LEFT:
                x = owidths[3] - ofullwd
                y = bt + (h - oh) * (1 - pos) - obt
                minbl = max (minbl, ofullwd + opad + axisWidths[3])
                minbt = max (minbt, obt)
                minbb = max (minbb, obb)
            elif side == self.SIDE_RIGHT:
                x = self.fullw - owidths[1]
                y = bt + (h - oh) * (1 - pos) - obt
                minbr = max (minbr, ofullwd + opad + axisWidths[1])
                minbt = max (minbt, obt)
                minbb = max (minbb, obb)

            if isfinal:
                ctxt.translate (x, y)

            li = op.layout (ctxt, style, isfinal, ow, oh, obt, obr, obb, obl)

            if isfinal:
                ctxt.translate (-x, -y)

        return LayoutInfo (minsize=(minwidth, minheight),
                           minborders=(minbt, minbr, minbb, minbl),
                           aspect=self.fieldAspect)


    def doPaint (self, ctxt, style):
        """Paint the rectangular plot: axes and data items."""

        # Needed in case there are no painters:
        i = 0
        # Needed in case zheights have been changed after construction:
        self.fpainters.sort (key=lambda fp: fp.zheight)

        # Clip to the field, then paint the field items that are below the
        # axes.

        ctxt.save ()
        ctxt.rectangle (self.border[3], self.border[0], self.width, self.height)
        ctxt.clip ()
        for i in xrange (len (self.fpainters)):
            if self.fpainters[i].zheight >= 1000:
                i -= 1
                break
            self.fpainters[i].paint (ctxt, style)
        ctxt.restore ()

        # Now axes

        ctxt.save ()
        ctxt.translate (self.border[3], self.border[0])
        self._axisApplyHelper (self.width, self.height, 'paint', ctxt, style)
        ctxt.restore ()

        # Now any higher field painters

        ctxt.save ()
        ctxt.rectangle (self.border[3], self.border[0], self.width, self.height)
        ctxt.clip ()
        for i in xrange (i + 1, len (self.fpainters)):
            self.fpainters[i].paint (ctxt, style)
        ctxt.restore ()

        # Now, outer painters.

        for (op, side, pos) in self.opainters:
            op.paint (ctxt, style)


    def extractFrameCoords (self, ctxt, fx, fy):
        """Given a Cairo context, return the coordinates of a location
        in the plot frame in that context's coordinate system. The RectPlot
        must have been configured for painting so that its coordinate system
        on the context has been established. The transformation is done by
        mapping from the plot's coordinate system to device coordinates and
        back to the context's coordinate system.

        The frame coordinates are defined such that (0,0) is the top left of
        the plot frame, (1,0) is the top right, and (0,1) is the bottom left.

        The intent of this function is to make it possible to draw zoom boxes
        from one plot to another using a painter overlaid on the plots.
        """

        assert self.matrix is not None

        ctxt.save ()
        ctxt.set_matrix (self.matrix)
        fx = fx * self.width + self.border[3]
        fy = fy * self.height + self.border[0]
        dx, dy = ctxt.user_to_device (fx, fy)
        ctxt.restore ()
        return ctxt.device_to_user (dx, dy)


    def extractFieldCoords (self, ctxt, fx, fy, field=None):
        """Given a Cairo context, return the coordinates of a location
        in a field on the plot in that context's coordinate
        system. The RectPlot must have been configured for painting so
        that its coordinate system on the context has been
        established. The transformation is done by mapping from the
        plot's coordinate system to device coordinates and back to the
        context's coordinate system.

        The coordinate system is a function of the field's axes and
        may not map to a value within the plot frame or even within
        the area for which the context is defined.

        If *field* is None, the field for which to compute the coordinates
        defaults to the plot's defaultField.

        Obviously, if you want to draw some data on the plot, you
        should add a FieldPainter to it. The intent of this function
        is to make it possible to draw zoom boxes from one plot to
        another using a painter overlaid on the plots.
        """

        if field is None:
            field = self.defaultField

        xform = field.makeTransformer (1., 1., False)
        fx = xform.mapX (fx)
        fy = xform.mapY (fy)
        return self.extractFrameCoords (ctxt, fx, fy)


# Actual field painters.

class FieldPainter (Painter):
    field = None
    needsDataStyle = False

    def doPaint (self, ctxt, style):
        if self.field is None:
            raise Exception ('Need to set field of FieldPainter before painting!')

        self.xform = self.field.makeTransformer (self.fullw, self.fullh, True)

    def setBounds (self, *args):
        self.field.setBounds (*args)

    def getDataBounds (self):
        raise NotImplementedError ()

    def getKeyPainter (self):
        raise NotImplementedError ()

    # Overrides so that you can do plot.add (foo).show () -- one is never
    # going to want to show the FieldPainter itself. (Famous last words?)

    def render (self, func):
        p = self._getParent ()
        if p is None:
            raise Exception ('cannot render() parent-less FieldPainter')
        return p.render (func)

    def sendTo (self, pager):
        p = self._getParent ()
        if p is None:
            raise Exception ('cannot sendTo() parent-less FieldPainter')
        return p.sendTo (func)

    def show (self, **kwargs):
        p = self._getParent ()
        if p is None:
            raise Exception ('cannot show() parent-less FieldPainter')
        return p.show (**kwargs)

    def save (self, filename, **kwargs):
        p = self._getParent ()
        if p is None:
            raise Exception ('cannot save() parent-less FieldPainter')
        return p.save (filename, **kwargs)

    def dump (self, **kwargs):
        p = self._getParent ()
        if p is None:
            raise Exception ('cannot dump() parent-less FieldPainter')
        return p.dump (**kwargs)


class GenericKeyPainter (Painter):
    vDrawSize = 2 # in style.largeScale
    hDrawSize = 5 # in style.largeScale
    hPadding = 3 # in style.smallScale
    textColor = 'foreground'

    def __init__ (self, owner):
        self.owner = owner

    def _getText (self):
        raise NotImplementedError ()

    def _drawLine (self):
        raise NotImplementedError ()

    def _drawStamp (self):
        raise NotImplementedError ()

    def _drawRegion (self):
        raise NotImplementedError ()

    def _applyLineStyle (self, style, ctxt):
        raise NotImplementedError ()

    def _applyStampStyle (self, style, ctxt):
        raise NotImplementedError ()

    def _applyRegionStyle (self, style, ctxt):
        raise NotImplementedError ()

    def _getStamp (self):
        raise NotImplementedError ()


    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        self.ts = TextStamper (self._getText ())
        self.tw, self.th = self.ts.getSize (ctxt, style)

        h = max (self.th, self.vDrawSize * style.largeScale)

        bl = self.hDrawSize * style.largeScale
        bl += self.hPadding * style.smallScale

        return LayoutInfo (minsize=(self.tw, h), minborders=(0, 0, 0, bl))


    def doPaint (self, ctxt, style):
        w, h = self.width, self.height
        s = style.smallScale
        dw = self.border[3] - self.hPadding * s

        if self._drawRegion ():
            ctxt.save ()
            self._applyRegionStyle (style, ctxt)
            ctxt.rectangle (0, s, dw, h - 2 * s)
            ctxt.fill ()
            ctxt.restore ()

        if self._drawLine ():
            ctxt.save ()
            self._applyLineStyle (style, ctxt)
            ctxt.move_to (0, h / 2)
            ctxt.line_to (dw, h / 2)
            ctxt.stroke ()
            ctxt.restore ()

        if self._drawStamp ():
            ctxt.save ()
            self._applyStampStyle (style, ctxt)
            self._getStamp ().paintAt (ctxt, style, dw / 2, h / 2)
            ctxt.restore ()

        ty = (h - self.th) / 2
        tc = style.getColor (self.textColor)

        self.ts.paintAt (ctxt, self.border[3], ty, tc)


class GenericDataKeyPainter (GenericKeyPainter):
    def __init__ (self, owner, drawline, drawstamp, drawregion):
        super (GenericDataKeyPainter, self).__init__ (owner)
        self._drawline_val = drawline
        self._drawstamp_val = drawstamp
        self._drawregion_val = drawregion

    def _getText (self):
        return self.owner.keyText

    def _drawLine (self):
        return self._drawline_val

    def _drawStamp (self):
        return self._drawstamp_val and (self.owner.pointStamp is not None)

    def _drawRegion (self):
        return self._drawregion_val

    def _getStamp (self):
        return self.owner.pointStamp

    def _applyLineStyle (self, style, ctxt):
        style.applyDataLine (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.lineStyle)

    def _applyStampStyle (self, style, ctxt):
        style.applyDataStamp (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.stampStyle)

    def _applyRegionStyle (self, style, ctxt):
        style.applyDataRegion (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.fillStyle)


class XYKeyPainter (GenericDataKeyPainter):
    def __init__ (self, owner):
        super (XYKeyPainter, self).__init__ (owner, True, True, False)

    def _drawLine (self):
        return self.owner.lines


class RegionKeyPainter (GenericDataKeyPainter):
    def __init__ (self, owner):
        super (RegionKeyPainter, self).__init__ (owner, True, False, True)

    def _drawLine (self):
        return self.owner.stroke

    def _drawRegion (self):
        return self.owner.fill

    def _applyLineStyle (self, style, ctxt):
        if self.owner.dsn is not None:
            style.applyDataLine (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.style)

    def _applyRegionStyle (self, style, ctxt):
        if self.owner.dsn is not None:
            style.applyDataRegion (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.style)

    def doPaint (self, ctxt, style):
        w, h = self.width, self.height
        s = style.smallScale
        dw = self.border[3] - self.hPadding * s

        ctxt.rectangle (0, s, dw, h - 2 * s)

        if self._drawRegion ():
            ctxt.save ()
            self._applyRegionStyle (style, ctxt)
            ctxt.set_line_width (0) # !!!
            ctxt.fill_preserve ()
            ctxt.restore ()

        if self._drawLine ():
            ctxt.save ()
            self._applyLineStyle (style, ctxt)
            ctxt.stroke_preserve ()
            ctxt.restore ()

        # Clear path for the text drawing
        ctxt.new_path ()
        ty = (h - self.th) / 2
        tc = style.getColor (self.textColor)
        self.ts.paintAt (ctxt, self.border[3], ty, tc)


class XYDataPainter (FieldPainter):
    lineStyle = None
    stampStyle = None
    needsDataStyle = True
    dsn = None
    lines = True
    pointStamp = None

    def __init__ (self, lines=True, pointStamp=None, keyText='Data'):
        super (XYDataPainter, self).__init__ ()

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)

        if lines is False and pointStamp is None:
            pointStamp = _DTS (self)

        self.lines = lines
        self.pointStamp = pointStamp

        if pointStamp is not None:
            pointStamp.setData (self.data)

        self.keyText = keyText


    def getDataBounds (self):
        ign, ign, xs, ys = self.data.getAll ()

        if xs.shape[1] < 1:
            return (None, None, None, None)

        return xs.min (), xs.max (), ys.min (), ys.max ()


    def getKeyPainter (self):
        if self.keyText is None: return None

        return XYKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (XYDataPainter, self).doPaint (ctxt, style)

        imisc, fmisc, allx, ally = self.data.getAllMapped (self.xform)

        if allx.shape[1] < 1: return

        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        x, y = allx[0,:], ally[0,:]

        ctxt.move_to (x[0], y[0])

        if self.lines:
            for i in xrange (1, x.size):
                ctxt.line_to (x[i], y[i])

                if i > 0 and i % 100 == 0:
                    ctxt.stroke ()
                    ctxt.move_to (x[i], y[i])

            ctxt.stroke ()

        ctxt.restore ()

        ctxt.save ()
        style.applyDataStamp (ctxt, self.dsn)
        style.apply (ctxt, self.stampStyle)

        if self.pointStamp is not None:
            self.pointStamp.paintMany (ctxt, style, self.xform)

        ctxt.restore ()


class ContinuousSteppedPainter (FieldPainter):
    """Draws histogram-style lines. If you have N horizontal segments that you
    want to plot, provide N+1 data points, with the X values giving all of the
    bin edges, from the left edge of the 1st bin through the right edge of the
    Nth bin. The final Y value is ignored.

    X values must be sorted, but may be either increasing or decreasing.
    """

    lineStyle = None
    needsDataStyle = True
    dsn = None
    connectors = True


    def __init__ (self, lineStyle=None, connectors=True, keyText='Histogram'):
        super (ContinuousSteppedPainter, self).__init__ ()

        self.lineStyle = lineStyle
        self.connectors = connectors
        self.keyText = keyText

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)


    def setDataHist (self, edges, yvals):
        edges = np.atleast_1d (edges)
        yvals = np.atleast_1d (yvals)

        if edges.size != yvals.size + 1:
            raise ValueError ('for %d y-values, need %d edges; got %d' %
                              (yvals.size, yvals.size + 1, edges.size))

        deltas = edges[1:] - edges[:-1]
        if np.any (deltas > 0) and np.any (deltas < 0):
            raise ValueError ('bin edges are not sorted')

        self.setFloats (edges, np.concatenate ((yvals, [0])))
        return self


    def setDataXY (self, xvals, yvals, first=None, last=None):
        xvals = np.atleast_1d (xvals)
        yvals = np.atleast_1d (yvals)

        if xvals.size != yvals.size:
            raise ValueError ('got %d y-values but %d xvals' %
                              (yvals.size, xvals.size))

        if first is None or last is None:
            if xvals.size < 2:
                raise ValueError ('must provide at least 2 x-values for auto-edging')
        elif xvals.size < 1:
            raise ValueError ('must provide at least 1 x-value')

        if first is not None:
            first = float (first)
        else:
            first = 1.5 * xvals[0] - 0.5 * xvals[1]

        if last is not None:
            last = float (last)
        else:
            last = 1.5 * xvals[-1] - 0.5 * xvals[-2]

        midpoints = 0.5 * (xvals[:-1] + xvals[1:])
        edges = np.concatenate (([first], midpoints, [last]))
        return self.setDataHist (edges, yvals)


    def getDataBounds (self):
        imisc, fmisc, xs, ys = self.data.getAll ()
        return xs.min (), xs.max (), ys[0][:-1].min (), ys[0][:-1].max ()


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return GenericDataKeyPainter (self, True, False, False)


    def doPaint (self, ctxt, style):
        super (ContinuousSteppedPainter, self).doPaint (ctxt, style)

        _, _, xs, ys = self.data.getMapped (self.cinfo, self.xform)
        xs, ys = xs[0], ys[0]

        if xs.size < 2:
            return

        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        prevx, prevy = xs[0], ys[0]
        ctxt.move_to (prevx, prevy)
        cmpval = None

        def mycmp(a, b): # Python 3 removed cmp()
            a = float(a) # Numpy floats yield numpy bools which don't subtract
            b = float(b)
            return (a > b) - (a < b)

        if self.connectors:
            for i in xrange (1, xs.size - 1):
                x, y = xs[i], ys[i]

                c = mycmp(x, prevx)
                if cmpval is None and c != 0:
                    cmpval = c
                elif c != cmpval and c != 0:
                    raise Exception ('arguments must be sorted in X (%s %s %s %s)'
                                     % (prevx, x, cmpval, c))

                ctxt.line_to (x, prevy)
                ctxt.line_to (x, y)
                prevx, prevy = x, y
        else:
            for i in xrange (1, xs.size - 1):
                x, y = xs[i], ys[i]

                c = mycmp(x, prevx)
                if cmpval is None and c != 0:
                    cmpval = c
                elif c != cmpval and c != 0:
                    raise Exception ('arguments must be sorted in X (%s %s %s %s)'
                                     % (prevx, x, cmpval, c))

                ctxt.line_to (x, prevy)
                ctxt.stroke ()
                ctxt.move_to (x, y)
                prevx, prevy = x, y

        ctxt.line_to (xs[-1], prevy)
        ctxt.stroke ()


class FilledHistogram (FieldPainter):
    style = 'genericBand'
    needsDataStyle = False
    dsn = None
    stroke = False
    fill = True # needed for RegionKeyPainter

    def __init__ (self, keyText='Data', style='genericBand'):
        super (FilledHistogram, self).__init__ ()

        self.style = style
        self.keyText = keyText
        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)

    def setDataHist (self, edges, values):
        edges = np.atleast_1d (edges)
        values = np.atleast_1d (values)

        if edges.size != values.size + 1:
            raise ValueError ('for %d y-values, need %d edges; got %d' %
                              (values.size, values.size + 1, edges.size))

        deltas = edges[1:] - edges[:-1]
        if np.any (deltas > 0) and np.any (deltas < 0):
            raise ValueError ('bin edges are not sorted')

        self.setFloats (edges, np.concatenate ((values, [0])))
        return self

    def getDataBounds (self):
        ign, ign, x, y = self.data.get (self.cinfo)
        return x.min (), x.max (), min (y.min (), 0), max (y.max (), 0)

    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return RegionKeyPainter (self)

    def doPaint (self, ctxt, style):
        super (FilledHistogram, self).doPaint (ctxt, style)

        ign, ign, x, y = self.data.getMapped (self.cinfo, self.xform)
        x, y = x[0], y[0]
        yzero = self.xform.mapY (0)

        ctxt.save ()
        style.apply (ctxt, self.style)

        ctxt.move_to (x[0], yzero)

        for i in xrange (1, y.size):
            if x[i] < x[i-1]:
                raise RuntimeError ('x values must be sorted')
            ctxt.line_to (x[i-1], y[i-1])
            ctxt.line_to (x[i], y[i-1])

        ctxt.line_to (x[i], yzero)
        ctxt.close_path ()
        ctxt.fill ()
        ctxt.restore ()


def _paintSteppedLines (ctxt, xls, xrs, ys, connectors):
    n = ys.size

    if not connectors:
        for i in xrange (n):
            ctxt.move_to (xls[i], ys[i])
            ctxt.line_to (xrs[i], ys[i])
            ctxt.stroke ()
    else:
        prevxr = None

        for i in xrange (n):
            xl = xls[i]
            xr = xrs[i]
            ys = ys[i]

            if prevxr is not None and (prevxr - xl) / abs (xl) > 1e-6:
                raise Exception ('Arguments must be sorted in X when using connectors '
                                 '(%f, %f, %f)' % (prevxr, xl, xl - prevxr))

            if prevxr is None:
                ctxt.move_to (xl, y)
            elif abs ((prevxr - xl) / xl) < 0.01:
                # Connector line would be vertical like we'd hope,
                # continue making the path
                ctxt.line_to (xl, y)
            else:
                # We've jumped in the X domain, so we'll start a
                # new line
                ctxt.stroke ()
                ctxt.move_to (xl, y)

            ctxt.line_to (xr, y)
            prevxr = xr

        ctxt.stroke ()


class SteppedBoundedPainter (FieldPainter):
    """X values: bin left edges, bin right edges
    Y values: measurement centers, upper bound. lower bound"""

    lineStyle = None
    fillStyle = None
    connectors = False
    dsn = None
    needsDataStyle = True


    def __init__ (self, lineStyle=None, fillStyle=None, connectors=False,
                  fillRegions=True, drawBoundLines=False, boundLineStyle=None,
                  keyText='Histogram'):
        super (SteppedBoundedPainter, self).__init__ ()

        self.lineStyle = lineStyle
        self.fillStyle = fillStyle
        self.connectors = connectors
        self.fillRegions = fillRegions
        self.drawBoundLines = drawBoundLines
        self.boundLineStyle = boundLineStyle
        self.keyText = keyText

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 2, 3)


    def getDataBounds (self):
        imisc, fmisc, allx, ally = self.data.getAll ()
        xls, xrs = allx
        yvals, yups, ydns = ally

        if len (xls) == 0:
            return None, None, None, None

        xmin = min (xls.min (), xrs.min ())
        xmax = max (xls.max (), xrs.max ())
        ymin = min (ydns.min (), yups.min ())
        ymax = max (ydns.max (), yups.max ())

        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin

        return xmin, xmax, ymin, ymax


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return GenericDataKeyPainter (self, True, False, True)


    def doPaint (self, ctxt, style):
        super (SteppedBoundedPainter, self).doPaint (ctxt, style)

        imisc, fmisc, allx, ally = self.data.getMapped (self.cinfo, self.xform)
        n = allx.shape[1]

        if n < 1:
            return

        xls, xrs = allx
        ys, yups, ydns = ally

        if self.fillRegions:
            ctxt.save ()
            style.applyDataRegion (ctxt, self.dsn)
            style.apply (ctxt, self.fillStyle)

            for i in xrange (n):
                xl, xr = allx[:,i]
                y, yup, ydn = ally[:,i]

                ctxt.rectangle (xl, ydn, xr - xl, yup - ydn)
                ctxt.fill ()

            ctxt.restore ()

        # Lines, a la regular histogram
        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)
        _paintSteppedLines (ctxt, allx[0], allx[1], ally[0], self.connectors)
        if self.drawBoundLines:
            style.apply (ctxt, self.boundLineStyle)
            _paintSteppedLines (ctxt, allx[0], allx[1], ally[1], False)
            _paintSteppedLines (ctxt, allx[0], allx[1], ally[2], False)
        ctxt.restore ()


class SteppedUpperLimitPainter (FieldPainter):
    # FIXME: should be more generic yadda yadda yadda
    # FIXME: should have some kind of generic arrow-drawing support ...
    # for now, hardcode everything.

    """X values: bin left edges, bin right edges
    Y values: upper limits"""

    lineStyle = None
    limitLineStyle = None
    fillStyle = None
    limitArrowScale = 8 # in largeScale
    limitArrowheadSize = 2.5 # in largeScale
    keyText = 'Upper Limits'
    fillRegions = True
    zeroLines = True
    dsn = None
    needsDataStyle = True


    def __init__ (self, lineStyle=None, limitLineStyle=None,
                  fillStyle=None, fillRegions=True,
                  zeroLines=True, keyText='Upper Limits'):
        super (SteppedUpperLimitPainter, self).__init__ ()

        self.lineStyle = lineStyle
        self.limitLineStyle = limitLineStyle
        self.fillStyle = fillStyle
        self.fillRegions = fillRegions
        self.zeroLines = zeroLines
        self.keyText = keyText

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 2, 1)


    def getDataBounds (self):
        imisc, fmisc, allx, ally = self.data.getAll ()
        xls, xrs = allx
        yuls = ally[0]

        if len (xls) == 0:
            return None, None, 0, None

        xmin = min (xls.min (), xrs.min ())
        xmax = max (xls.max (), xrs.max ())
        ymin = yuls.min ()
        ymax = yuls.max ()

        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin <= 0:
            raise ValueError ('Upper limits must all be positive')

        return xmin, xmax, 0, ymax


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        raise Exception ('Implement key painter!')


    def doPaint (self, ctxt, style):
        super (SteppedUpperLimitPainter, self).doPaint (ctxt, style)

        imisc, fmisc, allx, ally = self.data.getMapped (self.cinfo, self.xform)
        yzero = self.xform.mapY (0)
        n = allx.shape[1]

        if n < 1:
            return

        xls, xrs = allx
        yuls = ally[0]

        if self.fillRegions:
            ctxt.save ()
            style.applyDataRegion (ctxt, self.dsn)
            style.apply (ctxt, self.fillStyle)

            for i in xrange (n):
                xl, xr = xls[i], xrs[i]
                yul = yuls[i]

                ctxt.rectangle (xl, yzero, xr - xl, yul - yzero)
                ctxt.fill ()

            ctxt.restore ()

        # Zero lines, if desired
        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)
        if self.zeroLines:
            _paintSteppedLines (ctxt, xls, xrs, yuls * 0 + yzero, False)

        # Limit lines and arrows
        style.apply (ctxt, self.limitLineStyle)
        _paintSteppedLines (ctxt, xls, xrs, yuls, False)

        maxlen = self.limitArrowScale * style.largeScale
        hacklen = self.limitArrowheadSize * style.largeScale
        hackdx = hacklen * 0.3
        hackdy = hacklen * 0.95

        for i in xrange (n):
            xl, xr = xls[i], xrs[i]
            yul = yuls[i]
            xmid = 0.5 * (xl + xr)
            alen = min (abs (yul - yzero), maxlen)
            alen = max (alen - hackdy, 0)
            tozerosign = np.sign (yzero - yul)
            yend = yul + tozerosign * alen

            if alen > 0:
                # The arrowhead may consume all vertical space, in which case
                # don't draw the line.
                ctxt.move_to (xmid, yul)
                ctxt.line_to (xmid, yend)
                ctxt.stroke ()

            yend += hackdy
            ctxt.move_to (xmid, yend)
            ctxt.line_to (xmid + hackdx, yend - hackdy * tozerosign)
            ctxt.line_to (xmid - hackdx, yend - hackdy * tozerosign)
            ctxt.close_path ()
            ctxt.fill ()

        ctxt.restore ()


class AbsoluteFieldOverlay (FieldPainter):
    """We hack around a bit with the boundaries here. When we're used to draw an
    axis key, our inner VBox uses its boundary area to align the drawing of
    the plot symbols and text. This makes it really hard to get a nice even
    border around key area if we use the VBox's [hv]BorderSize parameters.
    Therefore, this object allows some internal padding to be applied outside
    of the layout/boundary system. This gives us a nice simple even border and
    avoids having to deal with messy boundary semantics in our containing
    RectPlot and child VBox.

    For the same reason, we have a childBgStyle and can optionally draw a
    background.

    """
    child = None
    hAlign = 0.03
    vAlign = 0.03
    hPadding = 0 # in style.smallScale
    vPadding = 0 # in style.smallScale
    childBgStyle = None

    def __init__ (self, child=None, hAlign=0.03, vAlign=0.03):
        super (AbsoluteFieldOverlay, self).__init__ ()

        self.setChild (child)

        self.hAlign = float (hAlign)
        self.vAlign = float (vAlign)


    def setChild (self, child):
        if child is self.child: return

        if self.child is not None:
            self.child.setParent (None)

        if child is None:
            child = NullPainter ()

        child.setParent (self)
        self.child = child


    def _lostChild (self, p):
        self.child = NullPainter ()
        self.child.setParent (self)


    def getDataBounds (self):
        return None, None, None, None

    def getKeyPainter (self):
        return None

    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        hpad = self.hPadding * style.smallScale
        vpad = self.vPadding * style.smallScale

        li = self.child.layout (ctxt, style, False, 0., 0., 0., 0., 0., 0.)
        fullw = li.minsize[0] + li.minborders[1] + li.minborders[3] + 2 * hpad
        fullh = li.minsize[1] + li.minborders[0] + li.minborders[2] + 2 * vpad
        dx = self.hAlign * (w - fullw)
        dy = self.vAlign * (h - fullh)

        if self.childBgStyle is not None:
            # The RectPlot always lays *us* out to the full field size, so we
            # need to save this information to draw the padded background
            # around the child.
            self._cbg_info = (dx, dy, fullw, fullh)

        if isfinal:
            ctxt.save ()
            ctxt.translate (dx + hpad, dy + vpad)

        li = self.child.layout (ctxt, style, isfinal, *li.asBoxInfo ())

        if isfinal:
            ctxt.restore ()

        return LayoutInfo (minsize=(fullw,fullh))


    def doPaint (self, ctxt, style):
        super (AbsoluteFieldOverlay, self).doPaint (ctxt, style)

        if self.childBgStyle is not None:
            dx, dy, w, h = self._cbg_info
            ctxt.save ()
            style.apply (ctxt, self.childBgStyle)
            ctxt.rectangle (dx, dy, w, h)
            ctxt.fill ()
            ctxt.restore ()

        self.child.paint (ctxt, style)


class HLine (FieldPainter):
    lineStyle = None
    needsDataStyle = True
    dsn = None

    def __init__ (self, ypos=0., keyText='HLine', lineStyle=None):
        super (HLine, self).__init__ ()

        self.ypos = ypos
        self.keyText = keyText
        self.lineStyle = lineStyle


    def getDataBounds (self):
        return (None, None, self.ypos, self.ypos)


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return GenericDataKeyPainter (self, True, False, False)


    def doPaint (self, ctxt, style):
        super (HLine, self).doPaint (ctxt, style)

        y = self.xform.mapY (self.ypos)

        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)
        ctxt.move_to (0, y)
        ctxt.line_to (self.fullw, y)
        ctxt.stroke ()
        ctxt.restore ()


class VLine (FieldPainter):
    lineStyle = None
    needsDataStyle = True
    dsn = None

    def __init__ (self, xpos=0., keyText='VLine', lineStyle=None):
        super (VLine, self).__init__ ()

        self.xpos = xpos
        self.keyText = keyText
        self.lineStyle = lineStyle


    def getDataBounds (self):
        return (self.xpos, self.xpos, None, None)


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return GenericDataKeyPainter (self, True, False, False)


    def doPaint (self, ctxt, style):
        super (VLine, self).doPaint (ctxt, style)

        x = self.xform.mapX (self.xpos)

        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)
        ctxt.move_to (x, 0)
        ctxt.line_to (x, self.fullh)
        ctxt.stroke ()
        ctxt.restore ()


class XBand (FieldPainter):
    style = 'genericBand'
    needsDataStyle = False
    dsn = None
    stroke = False
    fill = True


    def __init__ (self, xmin, xmax, stroke=False, fill=True, keyText='Band', style=None):
        super (XBand, self).__init__ ()

        self.stroke = stroke
        self.fill = fill

        if style is not None:
            self.style = style

        if xmin > xmax:
            xmin, xmax = xmax, xmin
        self.xmin, self.xmax = xmin, xmax

        self.keyText = keyText


    def getDataBounds (self):
        return self.xmin, self.xmax, None, None


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return RegionKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (XBand, self).doPaint (ctxt, style)

        mmin, mmax = self.xform.mapX (np.asarray ((self.xmin, self.xmax)))
        w = abs (mmax - mmin)
        x = min (mmin, mmax)

        ctxt.save ()
        style.apply (ctxt, self.style)
        ctxt.rectangle (x, 0, w, self.xform.height)
        if self.fill:
            ctxt.fill_preserve ()
        if self.stroke:
            ctxt.stroke ()
        ctxt.new_path () # clear path if we didn't stroke; restore() doesn't!
        ctxt.restore ()


class YBand (FieldPainter):
    # XXX: we use the same style for stroking and filling, which means
    # (AFAICT) that they'll both use the same color. If your going to do both
    # at once, that's probably not what you want. Also relevant to XBand.

    style = 'genericBand'
    needsDataStyle = False
    dsn = None
    stroke = False
    fill = True


    def __init__ (self, ymin, ymax, stroke=False, fill=True, keyText='Band', style=None):
        super (YBand, self).__init__ ()

        self.stroke = stroke
        self.fill = fill

        if style is not None:
            self.style = style

        if ymin > ymax:
            ymin, ymax = ymax, ymin
        self.ymin, self.ymax = ymin, ymax

        self.keyText = keyText


    def getDataBounds (self):
        return None, None, self.ymin, self.ymax


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return RegionKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (YBand, self).doPaint (ctxt, style)

        mmin, mmax = self.xform.mapY (np.asarray ([self.ymin, self.ymax]))
        h = abs (mmax - mmin)
        y = min (mmin, mmax)

        ctxt.save ()
        style.apply (ctxt, self.style)
        ctxt.rectangle (0, y, self.xform.width, h)
        if self.fill:
            ctxt.fill_preserve ()
        if self.stroke:
            ctxt.stroke ()
        ctxt.new_path () # clear path if we didn't stroke; restore() doesn't!
        ctxt.restore ()


class VEnvelope (FieldPainter):
    """Paint a vertical envelope region."""

    style = 'genericBand'
    needsDataStyle = False
    dsn = None
    stroke = False
    fill = True


    def __init__ (self, keyText='VEnvelope', stroke=False, fill=True):
        super (VEnvelope, self).__init__ ()

        self.stroke = stroke
        self.fill = fill
        self.keyText = keyText

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 2)


    def getDataBounds (self):
        ign, ign, x, ys = self.data.get (self.cinfo)

        if np.any (ys[0] > ys[1]):
            raise RuntimeError ('First y column must always be less than second y column.')

        return x.min (), x.max (), ys[0].min (), ys[0].max ()


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return RegionKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (VEnvelope, self).doPaint (ctxt, style)

        ign, ign, x, ys = self.data.getMapped (self.cinfo, self.xform)
        x = x[0]
        ylo, yhi = ys

        ctxt.save ()
        style.apply (ctxt, self.style)

        ctxt.move_to (x[0], yhi[0])

        for i in xrange (1, yhi.size):
            if x[i] < x[i-1]:
                raise RuntimeError ('x values must be sorted')
            ctxt.line_to (x[i], yhi[i])

        for i in xrange (yhi.size - 1, -1, -1):
            ctxt.line_to (x[i], ylo[i])

        ctxt.close_path ()

        if self.stroke: ctxt.stroke ()
        if self.fill: ctxt.fill ()

        ctxt.restore ()


class Polygon (FieldPainter):
    """Paint a polygonal region."""

    style = 'genericBand'
    needsDataStyle = False
    dsn = None
    stroke = False
    fill = True


    def __init__ (self, keyText='Polygon', stroke=False, fill=True):
        super (Polygon, self).__init__ ()

        self.stroke = stroke
        self.fill = fill
        self.keyText = keyText

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)


    def getDataBounds (self):
        ign, ign, x, y = self.data.get (self.cinfo)

        return x.min (), x.max (), y.min (), y.max ()


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return RegionKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (Polygon, self).doPaint (ctxt, style)

        ign, ign, x, y = self.data.getMapped (self.cinfo, self.xform)
        x = x[0]
        y = y[0]

        ctxt.save ()
        style.apply (ctxt, self.style)

        ctxt.move_to (x[0], y[0])

        for i in xrange (1, y.size):
            ctxt.line_to (x[i], y[i])

        ctxt.close_path ()

        if self.stroke: ctxt.stroke ()
        if self.fill: ctxt.fill ()

        ctxt.restore ()


class GridContours (FieldPainter):
    """Paint contours computed from gridded data."""

    lineStyle = None
    needsDataStyle = True
    dsn = None

    def __init__ (self, computed=None, lineStyle=None, keyText='Contours'):
        super (GridContours, self).__init__ ()

        self.lineStyle = lineStyle
        self.keyText = keyText
        self.computed = computed


    def setComputed (self, computed):
        self.computed = computed


    def setData (self, data, rowcoords, colcoords, **kwargs):
        from oputil.contourgrid import contourAuto
        self.computed = contourAuto (data, rowcoords, colcoords, **kwargs)


    def getDataBounds (self):
        if self.computed is None:
            # could return all Nones...
            raise RuntimeError ('Must set contour data before computing bounds!')

        xmin = xmax = ymin = ymax = None

        for k, cntrs in six.iteritems (self.computed):
            for cntr in cntrs:
                if xmin is None:
                    xmin = cntr[0].min ()
                    xmax = cntr[0].max ()
                    ymin = cntr[1].min ()
                    ymax = cntr[1].max ()
                else:
                    xmin = min (xmin, cntr[0].min ())
                    xmax = max (xmax, cntr[0].max ())
                    ymin = min (ymin, cntr[1].min ())
                    ymax = max (ymax, cntr[1].max ())

        return xmin, xmax, ymin, ymax


    def getKeyPainter (self):
        if self.keyText is None:
            return None
        return GenericDataKeyPainter (self, True, False, False)


    def doPaint (self, ctxt, style):
        super (GridContours, self).doPaint (ctxt, style)

        # FIXME: different line styles and this and that

        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        for k, cntrs in six.iteritems (self.computed):
            for cntr in cntrs:
                x = self.xform.mapX (cntr[0])
                y = self.xform.mapY (cntr[1])

                ctxt.move_to (x[0], y[0])

                for i in xrange (1, x.size):
                    ctxt.line_to (x[i], y[i])

                    if i > 0 and i % 100 == 0:
                        ctxt.stroke ()
                        ctxt.move_to (x[i], y[i])

                ctxt.stroke ()

        ctxt.restore ()


class ImagePainter (FieldPainter):
    """The image coordinate system is as follows. The array returned
    by allocate() is of shape (height, width). This initially sounds
    funny, but makes sense if you think about it -- the index should
    vary fastest along the image width. This indexing is analogous to
    matrix notation in Numpy and math in general.

    The image is positioned in terms of its top left and bottom right
    corners. The top left corner is painted with pixel [0,0] of the
    data array. The bottom right corner is pixel [H-1,W-1]. The bottom
    left corner is pixel [H-1,0], etc.

    The words "top", "left", etc, are then in reference to the
    (ubiquitous) convention used by Cairo, with the origin at the
    upper left, not the graph coordinate axes, which have the origin
    at the lower left. Generally, leftx < rightx but topy >
    bottomy. However, these relations may be inverted to reflect the
    image in the ways that you'd expect. The positioning convention
    above helps avoid ambiguity as to whether height is measured in
    the figure domain (higher is more up) or graph domain
    (higher is more down)

    The coordinates passed to setLocation() are the very edges of the
    image: the top left corner of the top left pixel, and the bottom
    right corner of the bottom right pixel -- in other words, the
    coordinates are not those of the relevant pixel centers.
    """

    style = None
    needsDataStyle = False
    dsn = None

    leftx = rightx = None
    topy = bottomy = None
    pattern = None

    _dtypes = {cairo.FORMAT_RGB24: np.uint32,
               cairo.FORMAT_ARGB32: np.uint32,
               cairo.FORMAT_A8: np.uint8}


    def setLocation (self, leftx, rightx, topy, bottomy):
        self.leftx = float (leftx)
        self.rightx = float (rightx)
        self.topy = float (topy)
        self.bottomy = float (bottomy)
        return self


    def allocate (self, format, width, height):
        """Returns an array of shape (height, width). See class docstring.
        """

        if format not in self._dtypes:
            raise ValueError ('image format not supported')

        dtype = self._dtypes[format]
        dsize = dtype ().itemsize
        bytestride = cairo.ImageSurface.format_stride_for_width (format, width)
        if bytestride % dsize != 0:
            raise ValueError ('unexpected stride value for format/width combination')
        itemstride = bytestride // dsize

        data = np.empty ((height, itemstride), dtype=dtype)
        self.surface = cairo.ImageSurface.create_for_data (data, format, width,
                                                           height, bytestride)
        self.pattern = cairo.SurfacePattern (self.surface)
        self.pattern.set_filter (cairo.FILTER_NEAREST)

        if itemstride == width:
            return data
        return data[:,:width]


    def wrap (self, format, data):
        data = np.atleast_2d (data)

        if data.ndim != 2:
            raise ValueError ('input array must be 2D')
        if format not in self._dtypes:
            raise ValueError ('image format not supported')
        if data.itemsize != self._dtypes[format] ().itemsize:
            # FIXME: smarter test? want flexibility about e.g. int32 v. uint32
            raise ValueError ('data itemsize does not match expectation for format')

        height, width = data.shape
        bytestride = cairo.ImageSurface.format_stride_for_width (format, width)
        if data.strides[0] != bytestride:
            raise ValueError ('stride of data array not correct for this format')

        self.surface = cairo.ImageSurface.create_for_data (data, format, width,
                                                           height, bytestride)
        self.pattern = cairo.SurfacePattern (self.surface)
        self.pattern.set_filter (cairo.FILTER_NEAREST)
        return self


    def getDataBounds (self):
        return (min (self.leftx, self.rightx), max (self.leftx, self.rightx),
                min (self.topy, self.bottomy), max (self.topy, self.bottomy))


    def getKeyPainter (self):
        return None


    def doPaint (self, ctxt, style):
        super (ImagePainter, self).doPaint (ctxt, style)

        xl = self.xform.mapX (self.leftx)
        xr = self.xform.mapX (self.rightx)
        yt = self.xform.mapY (self.topy)
        yb = self.xform.mapY (self.bottomy)

        ctxt.save ()
        style.apply (ctxt, self.style)
        ctxt.translate (xl, yt)
        ctxt.scale ((xr - xl) / self.surface.get_width (),
                    (yb - yt) / self.surface.get_height ())
        ctxt.set_source (self.pattern)
        ctxt.paint ()
        ctxt.restore ()


# Transformed coordinate axes

class RectCoordinates (object):
    def __init__ (self, field_or_plot):
        if hasattr (field_or_plot, 'defaultField'):
            self.field = field_or_plot.defaultField
        else:
            self.field = field_or_plot

    def makeAxis (self, side):
        return CoordinateAxis (self, side)

    def lin2arb (self, linx, liny):
        raise NotImplementedError ()

    def arb2lin (self, arbx, arby):
        raise NotImplementedError ()


DELTA = 1e-6

class CoordinateAxis (RectAxis):
    defaultPainter = LinearAxisPainter

    def __init__ (self, coordsys, side):
        self.coordsys = coordsys
        self.side = side


    def normalize (self):
        self.coordsys.field.xaxis.normalize ()
        self.coordsys.field.yaxis.normalize ()

        if self.min > self.max:
            self.reverse = True


    def _raw_min (self):
        cs = self.coordsys

        if self.side == RectPlot.SIDE_TOP:
            return cs.lin2arb (cs.field.xaxis.min, cs.field.yaxis.max)[0][0]
        if self.side == RectPlot.SIDE_BOTTOM:
            return cs.lin2arb (cs.field.xaxis.min, cs.field.yaxis.min)[0][0]
        if self.side == RectPlot.SIDE_LEFT:
            return cs.lin2arb (cs.field.xaxis.min, cs.field.yaxis.min)[1][0]
        if self.side == RectPlot.SIDE_RIGHT:
            return cs.lin2arb (cs.field.xaxis.max, cs.field.yaxis.min)[1][0]
        assert False, 'not reached'


    @property
    def min (self):
        if self.reverse:
            return self._raw_max ()
        return self._raw_min ()


    def _raw_max (self):
        cs = self.coordsys

        if self.side == RectPlot.SIDE_TOP:
            return cs.lin2arb (cs.field.xaxis.max, cs.field.yaxis.max)[0][0]
        if self.side == RectPlot.SIDE_BOTTOM:
            return cs.lin2arb (cs.field.xaxis.max, cs.field.yaxis.min)[0][0]
        if self.side == RectPlot.SIDE_LEFT:
            return cs.lin2arb (cs.field.xaxis.min, cs.field.yaxis.max)[1][0]
        if self.side == RectPlot.SIDE_RIGHT:
            return cs.lin2arb (cs.field.xaxis.max, cs.field.yaxis.max)[1][0]
        assert False, 'should not be reached'


    @property
    def max (self):
        if self.reverse:
            return self._raw_min ()
        return self._raw_max ()


    def transformWithDirection (self, arbvalues):
        arb = np.atleast_1d (arbvalues)
        cs = self.coordsys

        # The only predictable way to get from values in our
        # arbitrary coordinate system that map onto the field
        # is via the linear coordinate system, so we have to
        # guess linear coordinate values that should correspond
        # to the desired arbitrary values, then iterate towards
        # a better mapping.

        if self.side in (RectPlot.SIDE_TOP, RectPlot.SIDE_BOTTOM):
            if self.side == RectPlot.SIDE_TOP:
                yval = cs.field.yaxis.max
            else:
                yval = cs.field.yaxis.min

            w = 0.5 * (cs.lin2arb (cs.field.xaxis.min, yval)[1] +
                       cs.lin2arb (cs.field.xaxis.max, yval)[1])
            lin = cs.arb2lin (arb, w)[0]
            lin2arb = lambda lin: cs.lin2arb (lin, yval)[0]
            norm = cs.field.xaxis.transform
            def dorthdnorm (lin):
                # Y axis is inverted sense
                do = cs.lin2arb (lin, yval + DELTA)[0] - \
                    cs.lin2arb (lin, yval)[0]
                dn = cs.field.yaxis.transform (yval - DELTA) - \
                    cs.field.yaxis.transform (yval)
                return do / dn
        elif self.side in (RectPlot.SIDE_LEFT, RectPlot.SIDE_RIGHT):
            if self.side == RectPlot.SIDE_RIGHT:
                xval = cs.field.xaxis.max
            else:
                xval = cs.field.xaxis.min

            w = 0.5 * (cs.lin2arb (xval, cs.field.yaxis.min)[0] +
                       cs.lin2arb (xval, cs.field.yaxis.max)[0])
            lin = cs.arb2lin (w, arb)[1]
            lin2arb = lambda lin: cs.lin2arb (xval, lin)[1]
            norm = cs.field.yaxis.transform
            def dorthdnorm (lin):
                do = cs.lin2arb (xval + DELTA, lin)[1] - \
                    cs.lin2arb (xval, lin)[1]
                dn = cs.field.xaxis.transform (xval + DELTA) - \
                    cs.field.xaxis.transform (xval)
                return do / dn
        else:
            assert False, 'should not be reached'

        # Do the iteration, with some obnoxious setup necessary so
        # that we can check relative errors with the possibility of
        # having places where arb == 0.

        w = np.where (arb != 0)
        if w[0].size == arb.size:
            arbscale = arb
        else:
            arbscale = arb.copy ()
            arbscale[np.where (arb == 0)] = np.abs (arb[w]).min ()

        for iternum in xrange (64):
            err = arb - lin2arb (lin)

            if not np.any (np.abs (err) / arbscale > 1e-6):
                break

            dlindarb = DELTA / (lin2arb (lin + DELTA) - lin2arb (lin))
            lin += err * dlindarb
        else:
            raise ValueError ('cannot converge on transformed values for %s' %
                              arbvalues)

        # Now, get the angle between the arbitrary coordinate system
        # and the linear coordsys, expressed in the normalized coordinates.

        darbdnorm = ((lin2arb (lin + DELTA) - lin2arb (lin)) /
                     (norm (lin + DELTA) - norm (lin)))
        dodn = dorthdnorm (lin)
        return norm (lin), np.arctan2 (dodn, darbdnorm)


    def inbounds (self, arbvalues):
        return np.logical_and (arbvalues >= self.min, arbvalues <= self.max)


    def transform (self, arbvalues):
        return self.transformWithDirection (arbvalues)[0]
