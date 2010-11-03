# Rectangular plots.

import numpy as N
from base import *
from base import (_TextPainterBase, _kwordDefaulted,
                  _kwordExtract, _checkKwordsConsumed)
from layout import RightRotationPainter


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

    def transform (self, values):
        """Return where the given values should reside on this axis, 0
        indicating all the way towards the physical minimum of the
        plotting area, 1 indicating all the way to the maximum."""
        raise NotImplementedError ()

    def inbounds (self, values):
        """Return True for each value that is within the bounds of this axis."""
        raise NotImplementedError ()


class LinearAxis (RectAxis):
    """A linear logical axis for a rectangular plot."""

    def __init__ (self, min=0., max=10.):
        self.min = min
        self.max = max

    def transform (self, values):
        # The +0 forces floating-point evaluation.
        return (values + 0.0 - self.min) / (self.max - self.min)

    def inbounds (self, values):
        return N.logical_and (values >= self.min, values <= self.max)


class LogarithmicAxis (RectAxis):
    """A logarithmic logical axis for a rectangular plot."""

    def __init__ (self, logmin=-3., logmax=3.):
        self.logmin = logmin
        self.logmax = logmax

    def getMin (self):
        return 10 ** self.logmin
    
    def setMin (self, value):
        if value > 0:
            self.logmin = N.log10 (value)
        else:
            self.logmin = -8

    min = property (getMin, setMin)
    
    def getMax (self):
        return 10 ** self.logmax
    
    def setMax (self, value):
        if value > 0:
            self.logmax = N.log10 (value)
        else:
            self.logmax = -8

    max = property (getMax, setMax)
    
    def transform (self, values):
        valid = values > 0
        vc = N.where (valid, values, 1)

        ret = (N.log10 (vc) - self.logmin) / (self.logmax - self.logmin)
        return N.where (valid, ret, -10)

    def inbounds (self, values):
        valid = values > 0
        vc = N.where (valid, values, 1)
        lv = N.log10 (vc)
        
        return N.logical_and (valid, N.logical_and (lv >= self.logmin, lv <= self.logmax))


class DiscreteAxis (RectAxis):
    """A discrete logical axis for a rectangular plot. That is,
    the abscissa values are integers and mapped to sequential points along
    the axis with even spacing."""

    # If true, and there are N abscissae, map values to 1 / (N + 0.5) to
    # N / (N + 0.5), so that no data points land on the left and right edges
    # of the field. If false, map them to 0 / (N - 1) to (N - 1) / (N - 1),
    # so that the first value lands on the left edge and the last value on
    # the right edge.
    
    padBoundaries = True

    def __init__ (self, min, max):
        self.min = float (min)
        self.max = float (max)

        assert self.min < self.max

    def ordinates (self):
        return xrange (int (N.ceil (self.min)), int (N.floor (self.max)) + 1)

    def inbounds (self, values):
        return N.logical_and (value >= self.min, value <= self.max)
    
    def transform (self, values):
        # Coerce floating-point evaluation in either case.
        
        if self.padBoundaries:
            ret = (values - self.min + 0.5) / (self.max + 1.0 - self.min)
        else:
            ret = (values - self.min + 0.0) / (self.max - self.min)

        return ret


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


    def nudgeBounds (self):
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

        
    def spaceRectOut (self, rw, rh):
        """Return the amount of exterior space orthogonal to the side we're on that
        is required for a rectangle aligned as described in relMoveRectOut."""

        if self.side == RectPlot.SIDE_TOP or self.side == RectPlot.SIDE_BOTTOM:
            return rh
        return rw


    def spaceRectAlong (self, rw, rh):
        """Return the amount of exterior space along the side we're on that is
        required for a rectangle aligned as described in relMoveRectOut."""

        if self.side == RectPlot.SIDE_TOP or self.side == RectPlot.SIDE_BOTTOM:
            return rw
        return rh


    def spaceRectPos (self, pos, rw, rh):
        """Return the amount of space along the side we're on that is
        required for a rectangle at the given position beyond the edge of the
        plot field and behind it."""

        if self.side == RectPlot.SIDE_TOP:
            forward = rw / 2 + (pos - 1) * self.w
            behind = rw / 2 - pos * self.w
        elif self.side == RectPlot.SIDE_RIGHT:
            forward = rh / 2 - pos * self.h
            behind = rh / 2 + (pos - 1) * self.h
        elif self.side == RectPlot.SIDE_BOTTOM:
            forward = rw / 2 - pos * self.w
            behind = rw / 2 + (pos - 1) * self.w
        elif self.side == RectPlot.SIDE_LEFT:
            forward = rh / 2 + (pos - 1) * self.h
            behind = rh / 2 - pos * self.h

        forward = max (forward, 0)
        behind = max (behind, 0)

        return forward, behind


class LinearAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a standard linear
    axis with evenly spaced tick marks."""
    
    def __init__ (self, axis):
        BlankAxisPainter.__init__ (self)

        if not isinstance (axis, LinearAxis):
            raise Exception ('Giving linearAxisPainter a '
                             'non-linearAxis axis')
        
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

    
    def nudgeBounds (self):
        span = self.axis.max - self.axis.min

        if span == 0:
            if self.axis.max == 0:
                self.axis.min = -1
                self.axis.max = 1
                return

            self.axis.min *= 0.95
            self.axis.max *= 1.05
            return
        
        if span < 0.: raise ValueError ('Illegal axis range: min > max.')
        
        mip = int (N.floor (N.log10 (span))) # major interval power
        step = 10 ** mip

        #if span / step > 8:
        #    # upgrade to bigger range
        #    mip += 1
        #    step *= 10
        
        newmin = int (N.floor (self.axis.min / step)) * step
        newmax = int (N.ceil (self.axis.max / step)) * step
        
        #print 'NB:', span, N.log10 (span), mip, step, newmin, newmax

        self.axis.min, self.axis.max = newmin, newmax

    
    def formatLabel (self, val):
        if callable (self.numFormat): return self.numFormat (val)
        return self.numFormat % (val)


    def getTickLocations (self):
        # Tick spacing variables
        
        span = self.axis.max - self.axis.min

        if span <= 0.: raise ValueError ('Illegal axis range: min >= max.')
        
        mip = int (N.floor (N.log10 (span))) # major interval power

        #print 'GTL:', span, N.log10 (span), mip
        
        if N.log10 (span) - mip < self.autoBumpThreshold:
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
        coeff = int (N.ceil (self.axis.min / inc)) # coeff. of first tick
        val = coeff * inc # location of first tick

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

        while self.axis.inbounds (val):
            v = self.axis.transform (val)
            yield (val, v, coeff % self.minorTicks == 0)

            val += inc
            coeff += 1

            # Adjust the value here so that the inbounds
            # test gets a better value to check.
            if zeroclamp and abs(val) < zeroclamp:
                val = 0.
            if coeff % self.minorTicks == 0:
                val = int (round (val / 10.**mip)) * 10**mip


    def getLabelInfos (self, ctxt, style):
        if not self.paintLabels:
            return

        # Create the TextStamper objects all at once, so that if we
        # are using the LaTeX backend, we can generate their PNG
        # images all in one go. (That will happen upon the first
        # invocation of getSize.)
        
        labels = []
        
        for (val, xformed, isMajor) in self.getTickLocations ():
            if not isMajor and not self.labelMinorTicks: continue

            s = self.formatLabel (val)

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
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        for (val, xformed, isMajor) in self.getTickLocations ():
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

LinearAxis.defaultPainter = LinearAxisPainter


class LogarithmicAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a standard logarithmic
    axis with evenly spaced tick marks."""

    def __init__ (self, axis):
        BlankAxisPainter.__init__ (self)

        if not isinstance (axis, LogarithmicAxis):
            raise Exception ('Giving logarithmicAxisPainter a'
                             'non-logarithmicAxis axis')
        
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


    def nudgeBounds (self):
        self.axis.logmin = N.floor (self.axis.logmin)
        self.axis.logmax = N.ceil (self.axis.logmax)


    def formatLabel (self, coeff, exp):
        if callable (self.numFormat): return self.numFormat (coeff, exp)

        if self.formatLogValue: val = exp + N.log10 (coeff)
        else: val = coeff * 10.**exp
        
        return self.numFormat % (val)


    def numFormat (self, coeff, exp):
        if exp >= 0 and exp < 3:
            return '$%.0f$' % (coeff * 10.**exp)
        if exp > -3 and exp < 0:
            return '$%.*f$' % (-exp, coeff * 10.**exp)

        if coeff == 1:
            return '$10^{%d}$' % exp

        return r'$%d\cdot\!10^{%d}$' % (coeff, exp)

    
    def getTickLocations (self):
        # Tick spacing variables

        curpow = int (N.floor (self.axis.logmin))
        coeff = int (N.ceil (10. ** (self.axis.logmin - curpow)))

        while self.axis.inbounds (coeff*10.**curpow):
            v = self.axis.transform (coeff*10.**curpow)
            maj = coeff == 1
            
            yield (coeff, curpow, v, maj)

            if coeff == 9:
                coeff = 1
                curpow += 1
            else:
                coeff += 1


    def getLabelInfos (self, ctxt, style):
        if not self.paintLabels:
            return

        # Create the TextStamper objects all at once, so that if we
        # are using the LaTeX backend, we can generate them images all
        # in one go. (That will happen upon the first invocation of
        # getMinimumSize.)
        
        labels = []
        
        for (coeff, exp, xformed, isMajor) in self.getTickLocations ():
            if self.labelMinorTicks:
                pass
            elif self.labelSomeMinorTicks:
                if not isMajor and coeff != 3 and coeff != 6: continue
            else:
                if not isMajor: continue

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
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        for (coeff, exp, xformed, isMajor) in self.getTickLocations ():
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


class DiscreteAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a tick mark and label
    for each item of a DiscreteAxis. Overriding the formatLabel property
    gives an easy way to use a DiscreteAxis for many common discrete cases:
    days of the week, members, etc."""
    
    def __init__ (self, axis, formatLabel=None):
        BlankAxisPainter.__init__ (self)

        if not isinstance (axis, DiscreteAxis):
            raise Exception ('Giving DiscreteAxisPainter a'
                             'non-DiscreteAxis axis')
        
        self.axis = axis
        self.formatLabel = formatLabel or self.genericFormat


    ticksBetween = False
    labelSeparation = 2 # in smallScale
    tickScale = 2 # in largeScale
    tickStyle = 'bgLinework' # style ref.
    textColor = 'foreground'
    labelStyle = None


    def genericFormat (self, v): return str(v)

    
    def spaceExterior (self, helper, ctxt, style):
        stampers = []

        # Create all of the stampers in this first loop
        # so that if we're running LaTeX (e.g.) they're
        # all processed at once, rather than one at a time.

        for i in self.axis.ordinates ():
            s = self.formatLabel (i)
            stampers.append (TextStamper (s))

        # Ok, now we can measure things.

        outside = forward = behind = 0

        for (i, x) in enumerate (self.axis.ordinates ()):
            ts = stampers[i]
            w, h = ts.getSize (ctxt, style)
            x = self.axis.transform (x)

            outside = max (outside, helper.spaceRectOut (w, h))
            fw, bh = helper.spaceRectPos (x, w, h)
            forward = max (forward, fw)
            behind = max (behind, bh)

            stampers[i] = (ts, w, h)

        if outside > 0:
            outside += self.labelSeparation * style.smallScale

        self.stampers = stampers
        return forward, outside, behind


    def paint (self, helper, ctxt, style):
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        vals = self.axis.transform (N.asarray (self.axis.ordinates ()))

        for v in vals:
            helper.paintTickIn (ctxt, v, self.tickScale * style.largeScale)
            
        tc = style.getColor (self.textColor)
        
        for ((ts, w, h), val) in zip (self.stampers, vals):
            helper.moveToAlong (ctxt, val)
            helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)
            helper.relMoveRectOut (ctxt, w, h)
            ts.paintHere (ctxt, tc)

DiscreteAxis.defaultPainter = DiscreteAxisPainter


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
            N.clip (raw, -1.0, 2.0)

            return raw * self.width
        
        def _mapY_weakClamp (self, val):
            raw = 1. - self.field.yaxis.transform (val)
            N.clip (raw, -1.0, 2.0)

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


from stamps import DataThemedStamp as _DTS


class RectPlot (Painter):
    """A rectangular plot. The workhorse of omegaplot, so it better be
    good!"""
    
    fieldAspect = None # Aspect ratio of the plot field, None for free
    outerPadding = 3 # in smallScale
    
    SIDE_TOP = 0
    SIDE_RIGHT = 1
    SIDE_BOTTOM = 2
    SIDE_LEFT = 3

    _nextDataStyleNum = 0
    
    def __init__ (self, emulate=None):
        Painter.__init__ (self)
        
        # we might want to plot two data sets with different logical axes,
        # but store default ones here to make life easier in the common case.

        if emulate is None:
            self.defaultField = RectField ()
            self.magicAxisPainters ('lb')
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


    def addKeyItem (self, item):
        if self.defaultKey is None:
            import layout
            self.defaultKey = layout.VBox (0)
            self.defaultKeyOverlay = AbsoluteFieldOverlay (self.defaultKey)
            self.add (self.defaultKeyOverlay, rebound=False)

        if isinstance (item, basestring):
            item = TextPainter (item)
            item.hAlign = self.defaultKeyOverlay.hAlign
            item.vAlign = self.defaultKeyOverlay.vAlign

        self.defaultKey.appendChild (item)

    
    def add (self, fp, autokey=True, rebound=True, nudgex=True, nudgey=True,
             dsn=None):
        # FIXME: don't rebound if the FP doesn't have any data.
        
        assert (isinstance (fp, FieldPainter))
        
        fp.setParent (self)
        self.fpainters.append (fp)
        
        if fp.field is None:
            fp.field = self.defaultField

        if fp.needsPrimaryStyle:
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
            self.rebound (nudgex, nudgey)

        return fp


    def addXY (self, *args, **kwargs):
        l = len (args)

        lines = _kwordDefaulted (kwargs, 'lines', bool, True)
        lineStyle = _kwordDefaulted (kwargs, 'lineStyle', None, None)
        pointStamp = _kwordDefaulted (kwargs, 'pointStamp', None, None)

        x, y, label = None, None, 'Data'
        
        if l == 3:
            x, y = map (N.asarray, args[0:2])
            label = args[2]
        elif l == 2:
            x, y = map (N.asarray, args)
        elif l == 1:
            y = N.asarray (args[0])
            x = N.linspace (0, len (y) - 1, len (y))
        else:
            raise Exception ("Don't know how to handle magic addXY() args '%s'" % args)

        dp = XYDataPainter (lines=lines, pointStamp=pointStamp, keyText=label)
        dp.setFloats (x, y)
        if lineStyle is not None: dp.lineStyle = lineStyle
        
        if isinstance (pointStamp, _DTS):
            pointStamp.setHolder (dp)

        return self.add (dp, **kwargs)

    
    def addXYErr (self, *args, **kwargs):
        from stamps import WithYErrorBars
        
        l = len (args)

        lines = _kwordDefaulted (kwargs, 'lines', bool, True)
        lineStyle = _kwordDefaulted (kwargs, 'lineStyle', None, None)
        pointStamp = _kwordDefaulted (kwargs, 'pointStamp', None, None)

        x, y, dy, label = None, None, None, 'Data'
        
        if l == 4:
            x, y, dy = map (N.asarray, args[0:3])
            label = args[3]
        elif l == 3:
            x, y, dy = map (N.asarray, args)
        elif l == 2:
            y, dy = map (N.asarray, args)
            x = N.linspace (0, len (y) - 1, len (y))
        else:
            raise Exception ("Don't know how to handle magic addXYErr() args '%s'" % args)

        if pointStamp is None:
            pointStamp = _DTS (None)
        errStamp = WithYErrorBars (pointStamp)

        dp = XYDataPainter (lines=lines, pointStamp=errStamp, keyText=label)
        dp.setFloats (x, y, y + dy, y - dy)
        if lineStyle is not None: dp.lineStyle = lineStyle
        
        if isinstance (pointStamp, _DTS):
            pointStamp.setHolder (dp)

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

    
    def rebound (self, nudgex=True, nudgey=True, field=None):
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

    
    def addOuterPainter (self, op, side, position):
        op.setParent (self)
        self.opainters.append ((op, side, position))


    def _outerPainterIndex (self, op):
        for i in xrange (0, len(self.opainters)):
            if self.opainters[i][0] is op: return i

        raise ValueError ('%s not in list of outer painters' % (op))


    def moveOuterPainter (self, op, side, position):
        idx = self._outerPainterIndex (self, op)
        self.opainters[idx] = (op, side, position)

    
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
        values. More precisely, the if certain sides are specified in
        the 'spec' argument, those sides are painted in a sensible default
        style; those sides not specified in the argument are made blank
        (that is, they are painted with a baseline only).

        If 'spec' contains the letter 'h' (as in 'horizontal'), both
        the bottom and top sides of the field are set to the same
        sensible default. If it contains 'v' (as in 'vertical'), both
        the left and right sides of the field are set to the same
        sensible default. If it contains the letter 'b', the bottom
        side is painted with a sensible default, and similarly for the
        letters 't' (top), 'r' (right), and 'l' (left). Note that a spec
        of 'bt' is NOT equivalent to 'h': the former will create two
        AxisPainter instances, while the latter will only create one and
        share it between the two sides. The same goes for 'lr' versus 'h'.
        Once again, any side NOT set by one of the above mechanisms is
        set to be painted with a BlankAxisPainter instance.
        
        To be more specific, the 'sensible default' is whatever class
        is pointed to by the defaultPainter attributes of the axes of
        the defaultField member of the RectPlot. This class is
        instantiated with the logical axis as the only argument to
        __init__.

        Examples:

           rp.magicAxisPainters ('lb') will give a classical plot
           in which the left and bottom sides of the field are marked with axes.

           rp.magicAxisPainters ('hv') will give an IDL-style plot
           in which all sides of the field are marked with axes.

           rp.magicAxisPainters ('r') will give an unusual plot in which
           only the right side is labeled with axes.
        """

        def make (axis): return axis.defaultPainter (axis)
        def makex (): return make (self.defaultField.xaxis)
        def makey (): return make (self.defaultField.yaxis)
        
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
                logmin = N.log10 (axis.min)

            # Axes may be running large to small ... not sure if this
            # code will work, but it has a better chance of working than
            # if it's not here.
            
            if axis.max <= 0.:
                logmax = -8
            else:
                logmax = N.log10 (axis.max)
                
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

        # Now update any axispainters that need it.
        # Make the logic more restrictive in case the
        # user has some custom axes.
        
        def fixpainter (wantlog, axis, painter, logvalue):
            if wantlog and isinstance (painter, LinearAxisPainter):
                if logvalue:
                    return LogValueAxisPainter (axis)
                else:
                    return LogarithmicAxisPainter (axis)
            elif not wantlog and isinstance (painter, LogarithmicAxisPainter):
                return LinearAxisPainter (axis)
            return painter

        self.tpainter = fixpainter (wantxlog, df.xaxis, self.tpainter, xlogvalue)
        self.rpainter = fixpainter (wantylog, df.yaxis, self.rpainter, ylogvalue)
        self.bpainter = fixpainter (wantxlog, df.xaxis, self.bpainter, xlogvalue)
        self.lpainter = fixpainter (wantylog, df.yaxis, self.lpainter, ylogvalue)

    
    # X and Y axis label helpers
    # FIXME: should have a setTitle too. Not the same as a top-side
    # label since it should be centered over the whole allocation,
    # not just the field.
    
    def setBounds (self, xmin=None, xmax=None, ymin=None, ymax=None):
        self.defaultField.setBounds (xmin, xmax, ymin, ymax)


    def nudgeBounds (self, nudgex=True, nudgey=True):
        if nudgex:
            self.bpainter.nudgeBounds ()
            self.tpainter.nudgeBounds ()
        if nudgey:
            self.lpainter.nudgeBounds ()
            self.rpainter.nudgeBounds ()

    
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
            val = TextPainter (str (val))

            if side % 2 == 1:
                val = RightRotationPainter (val)
                
        # End hack for now. Rest is in _calcBorders.

        self.addOuterPainter (val, side, 0.5)
        self.mainLabels[side] = val


    def setXLabel (self, val):
        self.setSideLabel (self.SIDE_BOTTOM, val)

        
    def setYLabel (self, val):
        self.setSideLabel (self.SIDE_LEFT, val)


    def setLabels (self, xval, yval):
        self.setXLabel (xval)
        self.setYLabel (yval)


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


    def _calcOuterSpace (self, ctxt, style):
        any = [False] * 4
        self.osizes = []

        # For each side of the plot, we record the maximum border and
        # interior sizes both along and away from that side.

        d = N.zeros ((4, 6))
        work = N.zeros (6)

        for (op, side, pos) in self.opainters:
            any[side] = True
            sz = op.getMinimumSize (ctxt, style)

            # Second part of the side label rotation hack. If the
            # aspect ratio is too big, rotate.

            if op in self.mainLabels and side % 2 == 1 and \
                   isinstance (op, RightRotationPainter) and \
                   sz[0] > 0 and sz[1] > 0:
                aspect = float (sz[0]) / sz[1]

                if aspect > 3.:
                    if side == 1:
                        op.setRotation (RightRotationPainter.ROT_CW90)
                    elif side == 3:
                        op.setRotation (RightRotationPainter.ROT_CCW90)
                
                    sz = op.getMinimumSize (ctxt, style)

            # End second part of hack.
            # Record minimum sizing so configurePainting can put this painter
            # in the right spot. (We always paint outer painters at their
            # minimum sizes.)

            self.osizes.append (sz)

            # Translate the outer painter's sizing information from the x/y
            # plane to the along/away "plane"

            work[0] = sz[side + 2] # border size farther from axis
            work[1] = sz[1 - (side % 2)] # interior size away from axis
            work[2] = sz[((side + 2) % 4) + 2] # border size nearer to axis
            work[3] = sz[((side + 1) % 4) + 2] # b sz to right of axis looking away from it
            work[4] = sz[side % 2] # interior size along axis
            work[5] = sz[((side + 3) % 4) + 2] # b sz to left of axis looking away from it

            # Now accumulate that information in the table for this side

            d[side] = N.maximum (d[side], work)

        # The minimum sizes of the outer painters along their axes also constrain
        # the sizes of the main plot field.

        minfw = max (d[0,4], d[2,4])
        minfh = max (d[1,4], d[3,4])

        # Finally done.

        return d, minfw, minfh


    def getMinimumSize (self, ctxt, style):
        # Get minimum size of plot field based on field painters.

        fsizes = N.zeros (6)

        for fp in self.fpainters:
            fsizes = N.maximum (fsizes, fp.getMinimumSize (ctxt, style))

        fw = fsizes[0] + fsizes[3] + fsizes[5]
        fh = fsizes[1] + fsizes[2] + fsizes[4]
        self.fsizes = fsizes

        # Compute bounds information for the outer painters.  The
        # outer painters can force the plot field to be bigger since
        # they must fit within it.

        obd, minofw, minofh = self._calcOuterSpace (ctxt, style)
        self.outer_border_data = obd
        opad = self.outerPadding * style.smallScale
        fw = max (fw, minofw)
        fh = max (fh, minofh)

        # Now do so for the axes. We use the current minimum field size
        # to guess how much the axis labels are going to overlap from one side
        # of the plot to adjacent sides. (Preview of coming attractions.)

        axspace = self._axisApplyHelper (fw, fh, 'spaceExterior', ctxt, style)

        # The minimal border can be tricky. It's easy to compute the minimum
        # size along each size based on the extent of the axis labels and
        # outer painters sticking out of that side:

        border = [0] * 4

        for i in xrange (4):
            ospace = obd[i][0:3].sum ()
            if ospace > 0:
                # only add padding space if there are painters on this side
                ospace += opad

            # However, axis labels can overlap from their assigned sides
            # onto the sides adjacent to them. This is particularly a
            # problem with totally empty sides, since any content on the
            # adjacent sides will require a little bit of a
            # border. Unfortunately, we can't know how much an axis label
            # will overlap until we know the actual width and height of
            # the plot. We were conservative and used the minimum possible
            # field size, which would lead to the maximum possible
            # overlap.

            aspace = axspace[i][1]
            aspace = max (aspace, axspace[(i + 1) % 4][2])
            aspace = max (aspace, axspace[(i + 3) % 4][0])

            border[i] = aspace + ospace
            #print i, axspace[i], obd[i][0:3], opad, border[i]

        return fw, fh, border[0], border[1], border[2], border[3]


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (RectPlot, self).configurePainting (ctxt, style, w, h,
                                                  bt, br, bb, bl)

        # w and h give the size of the field, bl and bt the x and y
        # offsets to get to its upper left corner.
        
        # FIXME: this new model prevents us from being able to specify
        # the aspect ratio of the field. That logic will have to land
        # somewhere else. Preserving the code here.

        #if self.fieldAspect is not None:
        #    cur = float (fieldw) / fieldh

        #    if cur > self.fieldAspect:
        #        # Wider than desired ; bump up left/right margins
        #        want_fieldw = fieldh * self.fieldAspect
        #        fdelta_x = (fieldw - want_fieldw) / 2
        #        fieldw = want_fieldw
        #    elif cur < self.fieldAspect:
        #        # Taller than desired ; bump up top/bottom margins
        #        want_fieldh = fieldw / self.fieldAspect
        #        fdelta_y = (fieldh - want_fieldh) / 2
        #        fieldh = want_fieldh

        # Configure the field painters, which is easy. We just give them
        # the smallest possible borders that will make them all happy.

        fsizes = self.fsizes
        fpw = w - fsizes[3] - fsizes[5]
        fph = h - fsizes[2] - fsizes[4]

        ctxt.save ()
        ctxt.translate (bl, bt)

        for fp in self.fpainters:
            fp.configurePainting (ctxt, style, fpw, fph, *fsizes[2:])

        ctxt.restore ()

        # Now that we know how large the field is, we need to compute
        # the actual bounds of the axis labels. While doing this, we
        # verify that there's enough space for the outer painters.

        obd = self.outer_border_data
        opad = self.outerPadding * style.smallScale
        s = self._axisApplyHelper (w, h, 'spaceExterior', ctxt, style)
        axisWidths = [0.] * 4

        for i in xrange (4):
            aw = s[i][1]
            aw = max (aw, s[(i+1) % 4][2])
            aw = max (aw, s[(i+3) % 4][0])

            ow = obd[i,0] + obd[i,1] + obd[i,2]
            if ow > 0:
                ow += opad

            if aw + ow > self.border[i]:
                #print i, aw, obd[i,0:3], opad, self.border[i]
                raise RuntimeError ('Not enough space for axis labels and outside painters')

            axisWidths[i] = aw

        # Now we need to do the outer painters. Getting their position
        # and borders right is obnoxious.

        owidths = [self.border[i] - axisWidths[i] - opad for i in xrange (4)]

        for i in xrange (len (self.osizes)):
            op, side, pos = self.opainters[i]
            ow, oh, obt, obr, obb, obl = self.osizes[i]

            if side == self.SIDE_TOP:
                x = bl + (w - ow) * pos - obl
                y = owidths[0] - obd[0,2] - oh - obt
                obb = obd[0,2]
            elif side == self.SIDE_BOTTOM:
                x = bl + (w - ow) * pos - obl
                y = self.fullh - owidths[2]
                obt = obd[2,2]
            elif side == self.SIDE_LEFT:
                x = owidths[3] - obd[3,2] - ow - obl
                y = bt + (h - oh) * (1 - pos) - obt
                obr = obd[3,2]
            elif side == self.SIDE_RIGHT:
                x = self.fullw - owidths[1]
                y = bt + (h - oh) * (1 - pos) - obt
                obl = obd[1,2]

            ctxt.translate (x, y)
            op.configurePainting (ctxt, style, ow, oh, obt, obr, obb, obl)
            ctxt.translate (-x, -y)


    def doPaint (self, ctxt, style):
        """Paint the rectangular plot: axes and data items."""

        # Clip to the field, then paint the field items.
        
        ctxt.save ()
        ctxt.rectangle (self.border[3], self.border[0],
                        self.width, self.height)
        ctxt.clip ()
        
        for fp in self.fpainters:
            fp.paint (ctxt, style)

        ctxt.restore ()

        # Axes

        ctxt.save ()
        ctxt.translate (self.border[3], self.border[0])
        self._axisApplyHelper (self.width, self.height, \
                               'paint', ctxt, style)
        ctxt.restore ()

        # Now, outer painters
        
        for (op, side, pos) in self.opainters:
            op.paint (ctxt, style)


# Actual field painters.

class FieldPainter (Painter):
    field = None
    needsPrimaryStyle = False
    
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
    
    def _applyLineStyle (self, style, ctxt):
        raise NotImplementedError ()

    def _applyStampStyle (self, style, ctxt):
        raise NotImplementedError ()

    def _getStamp (self):
        raise NotImplementedError ()


    def getMinimumSize (self, ctxt, style):
        self.ts = TextStamper (self._getText ())
        self.tw, self.th = self.ts.getSize (ctxt, style)

        h = max (self.th, self.vDrawSize * style.largeScale)

        bl = self.hDrawSize * style.largeScale
        bl += self.hPadding * style.smallScale

        return self.tw, h, 0, 0, 0, bl

    
    def doPaint (self, ctxt, style):
        w, h = self.width, self.height
        dw = self.border[3] - self.hPadding * style.smallScale

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


class XYKeyPainter (GenericKeyPainter):
    def _getText (self):
        return self.owner.keyText


    def _drawLine (self):
        return self.owner.lines


    def _drawStamp (self):
        return self.owner.pointStamp is not None
    

    def _applyLineStyle (self, style, ctxt):
        style.applyDataLine (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.lineStyle)


    def _applyStampStyle (self, style, ctxt):
        style.applyDataStamp (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.stampStyle)


    def _getStamp (self):
        return self.owner.pointStamp


class XYDataPainter (FieldPainter):
    lineStyle = None
    stampStyle = None
    needsPrimaryStyle = True
    dsn = None
    lines = True
    pointStamp = None
    
    def __init__ (self, lines=True, pointStamp=None, keyText='Data'):
        Painter.__init__ (self)
        
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


class LineOnlyKeyPainter (GenericKeyPainter):
    def _getText (self):
        return self.owner.keyText


    def _drawLine (self):
        return True


    def _drawStamp (self):
        return False
    

    def _applyLineStyle (self, style, ctxt):
        style.applyDataLine (ctxt, self.owner.dsn)
        style.apply (ctxt, self.owner.lineStyle)


    def _applyStampStyle (self, style, ctxt):
        pass


class DiscreteSteppedPainter (FieldPainter):
    lineStyle = None
    needsPrimaryStyle = True
    dsn = None
    connectors = True
    

    def __init__ (self, lineStyle=None, connectors=True, keyText='Histogram'):
        Painter.__init__ (self)

        self.lineStyle = lineStyle
        self.connectors = connectors
        
        self.data = RectDataHolder (DataHolder.AxisTypeInt,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)

        self.keyText = keyText


    def getDataBounds (self):
        ign, ign, xs, ys = self.data.getAll ()

        return xs.min (), xs.max (), ys.min (), ys.max ()

        
    def getKeyPainter (self):
        if self.keyText is None: return None
        
        return LineOnlyKeyPainter (self)

    
    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

        axis = self.field.xaxis
        if not isinstance (axis, DiscreteAxis):
            raise Exception ('Field axis must be a DiscreteAxis')

        imisc, fmisc, allx, ally = self.data.get (self.cinfo)
        
        if allx.shape[1] < 1: return

        idxs = axis.valuesToIndices (allx[0])
        nidx = axis.numAbscissae ()
        xpos = axis.transformIndices (axis.allIndices ()) * self.fullw
        ys = self.xform.mapY (ally[0])
        
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        for i in xrange (0, ys.size):
            idx = idxs[i]
            y = ys[i]

            if idx == 0:
                xleft = 0.0
            else:
                xleft = (xpos[idx] + xpos[idx-1]) / 2

            if idx == nidx - 1:
                xright = self.fullw
            else:
                xright = (xpos[idx] + xpos[idx+1]) / 2

            # FIXME: if drawing connectors, we should really do a
            # bunch of line-tos and one stroke, so that say dashed
            # lines work out OK.
            
            if self.connectors and i > 0:
                if idx <= previdx:
                    raise Exception ('Data must be sorted by X to draw connectors')

                if xleft == prevxright:
                    ctxt.move_to (xleft, prevy)
                    ctxt.line_to (xleft, y)
                    ctxt.stroke ()
            
            ctxt.move_to (xleft, y)
            ctxt.line_to (xright, y)
            ctxt.stroke ()

            prevy = y
            prevxright = xright
            previdx = idx


class ContinuousSteppedPainter (FieldPainter):
    """The X values are the left edges of the bins."""
    
    lineStyle = None
    needsPrimaryStyle = True
    dsn = None
    connectors = True

    
    def __init__ (self, lineStyle=None, connectors=True, keyText='Histogram'):
        Painter.__init__ (self)

        self.lineStyle = lineStyle
        self.connectors = connectors
        
        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)

        self.keyText = keyText


    def _calcMaxX (self, d):
        # FIXME: assuming data are sorted in X. We check in doPaint ()
        # but could stand to check here too.

        if d.size == 1:
            return 2 * d[0]
        elif d.size == 0:
            return 0.0
        
        return 2 * d[-1] - d[-2]

    
    def getDataBounds (self):
        imisc, fmisc, xs, ys = self.data.getAll ()

        return xs.min (), self._calcMaxX (xs[0]), ys.min (), ys.max ()

        
    def getKeyPainter (self):
        if self.keyText is None: return None
        
        return LineOnlyKeyPainter (self)

    
    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

        xs, ys = self.data.getRawXY (self.cinfo)
        finalx = self.xform.mapX (self._calcMaxX (xs))
        xs = self.xform.mapX (xs)
        ys = self.xform.mapY (ys)
        
        if xs.size < 1: return

        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        prevx, prevy = xs[0], ys[0]
        ctxt.move_to (prevx, prevy)

        if self.connectors:
            for i in xrange (1, xs.size):
                x, y = xs[i], ys[i]
                if x <= prevx:
                    raise Exception ('Arguments must be sorted in X')
                
                ctxt.line_to (x, prevy)
                ctxt.line_to (x, y)

                prevx, prevy = x, y
        else:
            for i in xrange (1, xs.size):
                x, y = xs[i], ys[i]
                if x <= prevx:
                    raise Exception ('Arguments must be sorted in X')
                
                ctxt.line_to (x, prevy)
                ctxt.stroke ()

                ctxt.move_to (x, y)

                prevx, prevy = x, y

        ctxt.line_to (finalx, prevy)
        ctxt.stroke ()


class SteppedBoundedPainter (FieldPainter):
    """X values: bin left edges, bin right edges
    Y values: measurement centers, upper bound. lower bound"""

    lineStyle = None
    fillStyle = None
    connectors = False
    dsn = None
    needsPrimaryStyle = True


    def __init__ (self, lineStyle=None, fillStyle=None, connectors=False,
                  keyText='Histogram'):
        super (SteppedBoundedPainter, self).__init__ ()

        self.lineStyle = lineStyle
        self.fillStyle = fillStyle
        self.connectors = connectors
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
        return LineOnlyKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (SteppedBoundedPainter, self).doPaint (ctxt, style)

        imisc, fmisc, allx, ally = self.data.getMapped (self.cinfo, self.xform)
        n = allx.shape[1]

        if n < 1:
            return

        xls, xrs = allx
        ys, yups, ydns = ally

        # Rectangular regions
        style.applyDataRegion (ctxt, self.dsn)
        style.apply (ctxt, self.fillStyle)

        for i in xrange (n):
            xl, xr = allx[:,i]
            y, yup, ydn = ally[:,i]

            ctxt.rectangle (xl, ydn, xr - xl, yup - ydn)
            ctxt.fill ()

        # Lines, a la regular histogram
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        if not self.connectors:
            for i in xrange (n):
                xl, xr = allx[:,i]
                y = ally[0,i]

                ctxt.move_to (xl, y)
                ctxt.line_to (xr, y)
                ctxt.stroke ()
        else:
            prevxr = None

            for i in xrange (n):
                xl, xr = allx[:,i]
                y = ally[0,i]

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


class AbsoluteFieldOverlay (FieldPainter):
    child = None
    hAlign = 0.0
    vAlign = 0.0
    hPadding = 3 # in style.smallScale
    vPadding = 3 # in style.smallScale


    def __init__ (self, child=None, hAlign=0.0, vAlign=0.0):
        Painter.__init__ (self)

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


    def getMinimumSize (self, ctxt, style):
        h = self.hPadding * style.smallScale
        v = self.vPadding * style.smallScale

        # FIXME: ignoring padding requests of the child.
        self.chsize = sz = self.child.getMinimumSize (ctxt, style)
        return sz[0], sz[1], sz[2] + v, sz[3] + h, sz[4] + v, sz[5] + h


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (AbsoluteFieldOverlay, self).configurePainting (ctxt, style, w, h,
                                                              bt, br, bb, bl)

        # The width and height that we are given are the size of the entire
        # plot field. We place the child at its minimal size inside the field,
        # aligned according to hAlign and vAlign, so that its non-border edges
        # land on the edge of the non-border region of the field.

        dx = bl - self.chsize[5] + self.hAlign * (w - self.chsize[0])
        dy = bt - self.chsize[2] + self.vAlign * (h - self.chsize[1])

        ctxt.save ()
        ctxt.translate (dx, dy)
        self.child.configurePainting (ctxt, style, *self.chsize)
        ctxt.restore ()


    def getDataBounds (self):
        return None, None, None, None


    def getKeyPainter (self): return None

    
    def doPaint (self, ctxt, style):
        super (AbsoluteFieldOverlay, self).doPaint (ctxt, style)
        self.child.paint (ctxt, style)


class HLine (FieldPainter):
    lineStyle = None
    needsPrimaryStyle = True
    dsn = None

    def __init__ (self, ypos=0., keyText='HLine', lineStyle=None):
        super (HLine, self).__init__ ()

        self.ypos = ypos
        self.keyText = keyText
        self.lineStyle = lineStyle


    def getDataBounds (self):
        return (None, None, self.ypos, self.ypos)


    def getKeyPainter (self):
        if self.keyText is None: return None

        return LineOnlyKeyPainter (self)


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
    needsPrimaryStyle = True
    dsn = None

    def __init__ (self, xpos=0., keyText='VLine', lineStyle=None):
        super (VLine, self).__init__ ()

        self.xpos = xpos
        self.keyText = keyText
        self.lineStyle = lineStyle


    def getDataBounds (self):
        return (self.xpos, self.xpos, None, None)


    def getKeyPainter (self):
        if self.keyText is None: return None

        return LineOnlyKeyPainter (self)


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
    needsPrimaryStyle = False
    dsn = None
    stroke = False
    fill = True

    
    def __init__ (self, xmin, xmax, stroke=False, fill=True, keyText='Band'):
        Painter.__init__ (self)

        self.stroke = stroke
        self.fill = fill
        
        if xmin > xmax: xmin, xmax = xmax, xmin
        self.xmin, self.xmax = xmin, xmax
        
        self.keyText = keyText


    def getDataBounds (self):
        return self.xmin, self.xmax, None, None


    def getKeyPainter (self):
        # FIXME
        return None

    
    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

        mmin, mmax = self.xform.mapX (N.asarray ((self.xmin, self.xmax)))
        w = abs (mmax - mmin)
        x = min (mmin, mmax)
        
        ctxt.save ()
        style.apply (ctxt, self.style)
        ctxt.rectangle (x, 0, w, self.xform.height)
        if self.stroke: ctxt.stroke ()
        if self.fill: ctxt.fill ()
        ctxt.restore ()


class VEnvelope (FieldPainter):
    """Paint a vertical envelope region."""

    style = 'genericBand'
    needsPrimaryStyle = False
    dsn = None
    stroke = False
    fill = True


    def __init__ (self, keyText='VEnvelope', stroke=False, fill=True):
        Painter.__init__ (self)

        self.stroke = stroke
        self.fill = fill
        self.keyText = keyText

        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 2)


    def getDataBounds (self):
        ign, ign, x, ys = self.data.get (self.cinfo)

        if N.any (ys[0] > ys[1]):
            raise RuntimeError ('First y column must always be less than second y column.')

        return x.min (), x.max (), ys[0].min (), ys[0].max ()


    def getKeyPainter (self):
        # FIXME
        return None


    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

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
    needsPrimaryStyle = False
    dsn = None
    stroke = False
    fill = True


    def __init__ (self, keyText='Polygon', stroke=False, fill=True):
        Painter.__init__ (self)

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
        # FIXME
        return None


    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

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
    needsPrimaryStyle = True
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

        for k, cntrs in self.computed.iteritems ():
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
        if self.keyText is None: return None

        return LineOnlyKeyPainter (self)


    def doPaint (self, ctxt, style):
        super (GridContours, self).doPaint (ctxt, style)

        # FIXME: different line styles and this and that

        ctxt.save ()
        style.applyDataLine (ctxt, self.dsn)
        style.apply (ctxt, self.lineStyle)

        for k, cntrs in self.computed.iteritems ():
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
