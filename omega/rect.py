# Rectangular plots.

import numpy as N
from base import *
from base import _TextPainterBase, _kwordDefaulted, _checkKwordsConsumed
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
        """Return how much space is required exterior to the plot field to
        paint this axis correctly. First element is orthogonal to the side
        we're on, second is along it."""
        return 0, 0

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
        
class LinearAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a standard linear
    axis with evenly spaced tick marks."""
    
    def __init__ (self, axis):
        BlankAxisPainter.__init__ (self)

        if not isinstance (axis, LinearAxis):
            raise Exception ('Giving linearAxisPainter a'
                             'non-linearAxis axis')
        
        self.axis = axis

    labelSeparation = 2 # in smallScale
    numFormat = '%g' # can be a function mapping float -> str
    majorTickScale = 2.5 # in largeScale
    minorTickScale = 2.5 # in smallScale
    minorTicks = 5
    tickStyle = 'bgLinework' # style ref.
    textColor = 'foreground'
    labelStyle = None
    avoidBounds = True # do not draw ticks at extremes of axes
    labelMinorTicks = False # draw value labels at the minor tick points?

    def nudgeBounds (self):
        span = self.axis.max - self.axis.min

        if span <= 0.: raise ValueError ('Illegal axis range: min >= max.')
        
        mip = N.floor (N.log10 (span)) # major interval power
        step = 10. ** mip

        #if span / step > 8:
        #    # upgrade to bigger range
        #    mip += 1
        #    step *= 10
        
        newmin = N.floor (self.axis.min / step) * step
        newmax = N.ceil (self.axis.max / step) * step
        
        #print 'NB:', span, N.log10 (span), mip, step, newmin, newmax

        self.axis.min, self.axis.max = newmin, newmax
    
    def formatLabel (self, val):
        if callable (self.numFormat): return self.numFormat (val)
        return self.numFormat % (val)

    def getTickLocations (self):
        # Tick spacing variables
        
        span = self.axis.max - self.axis.min

        if span <= 0.: raise ValueError ('Illegal axis range: min >= max.')
        
        mip = N.floor (N.log10 (span)) # major interval power

        #print 'GTL:', span, N.log10 (span), mip
        
        if N.log10 (span) - mip < 0.3:
            # If we wouldn't have that many tickmarks, decrease MIP
            # to make the labels denser.
            mip -= 1
            
        inc = 10. ** mip / self.minorTicks # incr. between minor ticks
        coeff = int (N.ceil (self.axis.min / inc)) # coeff. of first tick
        val = coeff * inc # location of first tick

        # If we cross zero, floating-point rounding errors cause the
        # ticks to be placed at points like 6.3e-16. Detect this case
        # and round to 0. Do it in units of the axis bounds so that a
        # plot from -1e-6 to 1e-6 will still work OK.

        if (self.axis.max < 0. and self.axis.min > 0.) or \
           (self.axis.min < 0. and self.axis.max > 0.):
            scale = max (abs (self.axis.max), abs (self.axis.min))
            zeroclamp = scale * 1e-6
        else:
            zeroclamp = None
        
        while self.axis.inbounds (val):
            if zeroclamp and abs(val) < zeroclamp:
                val = 0.
            
            v = self.axis.transform (val)
            yield (val, v, coeff % self.minorTicks == 0)

            val += inc
            coeff += 1

    def getLabelInfos (self, ctxt, style):
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
        outside, along = 0, 0
        
        for (ts, xformed, w, h) in self.getLabelInfos (ctxt, style):
            outside = max (outside, helper.spaceRectOut (w, h))
            along = max (along, helper.spaceRectAlong (w, h))

        return outside + self.labelSeparation * style.smallScale, along

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
    numFormat = '$10^{%d}$' # can be a function mapping float -> str
    formatLogValue = True # if true, format log10(x value), not the raw x value
    majorTickScale = 2 # in largeScale
    minorTickScale = 2 # in smallScale
    tickStyle = 'bgLinework' # style ref.
    textColor = 'foreground'
    labelStyle = None
    avoidBounds = True # do not draw ticks at extremes of axes
    labelMinorTicks = False # draw value labels at the minor tick points?

    def nudgeBounds (self):
        self.axis.logmin = N.floor (self.axis.logmin)
        self.axis.logmax = N.ceil (self.axis.logmax)

    def formatLabel (self, val):
        if self.formatLogValue: val = N.log10 (val)
        
        if callable (self.numFormat): return self.numFormat (val)
        return self.numFormat % (val)

    def getTickLocations (self):
        # Tick spacing variables

        curpow = int (N.floor (self.axis.logmin))
        inc = 10. ** curpow
        coeff = int (N.ceil (10. ** self.axis.logmin / inc)) - 1
        val = inc * (coeff + 1)

        if coeff == 0:
            # The loop bumps this up again.
            curpow -= 1
            inc /= 10.
            
        while self.axis.inbounds (val):
            v = self.axis.transform (val)

            if coeff % 9 == 0:
                # Avoid rounding errors by nudging our variables.
                curpow += 1
                inc = 10. ** curpow
                val = inc
                yield (val, v, True)
            else:
                yield (val, v, False)

            val += inc
            coeff += 1

    def getLabelInfos (self, ctxt, style):
        # Create the TextStamper objects all at once, so that if we
        # are using the LaTeX backend, we can generate them images all
        # in one go. (That will happen upon the first invocation of
        # getMinimumSize.)
        
        labels = []
        
        for (val, xformed, isMajor) in self.getTickLocations ():
            if not isMajor and not self.labelMinorTicks: continue

            s = self.formatLabel (val)

            labels.append ((TextStamper (s), xformed, isMajor))

        for (ts, xformed, isMajor) in labels:
            w, h = ts.getSize (ctxt, style)

            yield (ts, xformed, w, h)

    def spaceExterior (self, helper, ctxt, style):
        outside, along = 0, 0
        
        for (ts, xformed, w, h) in self.getLabelInfos (ctxt, style):
            outside = max (outside, helper.spaceRectOut (w, h))
            along = max (along, helper.spaceRectAlong (w, h))

        return outside + self.labelSeparation * style.smallScale, along

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

        for i in self.axis.ordinates ():
            s = self.formatLabel (i)
            stampers.append (TextStamper (s))

        outside, along = 0, 0

        for i in range (0, len (stampers)):
            ts = stampers[i]
            w, h = ts.getSize (ctxt, style)
            outside = max (outside, helper.spaceRectOut (w, h))
            along = max (along, helper.spaceRectAlong (w, h))
            stampers[i] = (ts, w, h)

        self.stampers = stampers
        
        return outside + self.labelSeparation * style.smallScale, along
    
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

    _nextPrimaryStyleNum = 0
    
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
    
    def add (self, fp, autokey=True, rebound=True, nudgex=True, nudgey=True):
        # FIXME: don't rebound if the FP doesn't have any data.
        
        assert (isinstance (fp, FieldPainter))
        
        fp.setParent (self)
        self.fpainters.append (fp)
        
        if fp.field is None:
            fp.field = self.defaultField

        if fp.needsPrimaryStyle:
            fp.primaryStyleNum = self._nextPrimaryStyleNum
            self._nextPrimaryStyleNum += 1
        
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

        x, y, label = None, None, None
        
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

        if label is None:
            label = 'Data'

        dp = XYDataPainter (lines=lines, pointStamp=pointStamp, keyText=label)
        dp.setFloats (x, y)
        if lineStyle is not None: dp.lineStyle = lineStyle
        
        fp = self.add (dp, **kwargs)

        if isinstance (pointStamp, _DTS):
            pointStamp.setHolder (dp)

        return fp
    
    def addXYErr (self, *args, **kwargs):
        from stamps import WithYErrorBars
        
        l = len (args)

        lines = _kwordDefaulted (kwargs, 'lines', bool, True)
        lineStyle = _kwordDefaulted (kwargs, 'lineStyle', None, None)
        pointStamp = _kwordDefaulted (kwargs, 'pointStamp', None, None)

        x, y, dy, label = None, None, None, None
        
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

        if label is None:
            label = 'Data'

        if pointStamp is None:
            pointStamp = _DTS (None)
        pointStamp = WithYErrorBars (pointStamp)
        
        dp = XYDataPainter (lines=lines, pointStamp=pointStamp, keyText=label)
        dp.setFloats (x, y, y + dy, y - dy)
        if lineStyle is not None: dp.lineStyle = lineStyle
        
        fp = self.add (dp, **kwargs)

        if isinstance (pointStamp, _DTS):
            pointStamp.setHolder (dp)

        return fp
        
    
    def rebound (self, nudgex=True, nudgey=True):
        """Recalculate the bounds of the default field based on the data
        that it contains."""

        first = True

        for fp in self.fpainters:
            if fp.field is not self.defaultField:
                continue

            if first:
                self.defaultField.setBounds (*fp.getDataBounds ())
                first = False
            else:
                self.defaultField.expandBounds (*fp.getDataBounds ())

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

    def setLinLogAxes (self, wantxlog, wantylog):
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
        
        def fixpainter (wantlog, axis, painter):
            if wantlog and isinstance (painter, LinearAxisPainter):
                return LogarithmicAxisPainter (axis)
            elif not wantlog and isinstance (painter, LogarithmicAxisPainter):
                return LinearAxisPainter (axis)
            return painter

        self.tpainter = fixpainter (wantxlog, df.xaxis, self.tpainter)
        self.rpainter = fixpainter (wantylog, df.yaxis, self.rpainter)
        self.bpainter = fixpainter (wantxlog, df.xaxis, self.bpainter)
        self.lpainter = fixpainter (wantylog, df.yaxis, self.lpainter)
    
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
                
        # End hack for now. Rest is in _calcOuterExtents.

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

    def _calcOuterExtents (self, ctxt, style):
        trueoe = [0] * 4
        allocoe = [0] * 4
        any = [False] * 4
        
        T, R, B, L = 0, 1, 2, 3
        
        for (op, side, pos) in self.opainters:
            any[side] = True
            w, h = op.getMinimumSize (ctxt, style)

            # Second part of the side label rotation hack. If the
            # aspect ratio is too big, rotate.

            if op in self.mainLabels and side % 2 == 1 and \
                   isinstance (op, RightRotationPainter) and \
                   w > 0 and h > 0:
                aspect = float (w) / h

                if aspect > 3.:
                    if side == R:
                        op.setRotation (RightRotationPainter.ROT_CW90)
                    elif side == L:
                        op.setRotation (RightRotationPainter.ROT_CCW90)
                
                    w, h = h, w

            # End second part of hack.
            
            if side == T:
                trueoe[T] = max (trueoe[T], h)
                allocoe[L] = max (allocoe[L], w * (1 - pos))
                allocoe[R] = max (allocoe[R], w * pos)
            elif side == B:
                trueoe[B] = max (trueoe[B], h)
                allocoe[L] = max (allocoe[L], w * (1 - pos))
                allocoe[R] = max (allocoe[R], w * pos)
            elif side == L:
                trueoe[L] = max (trueoe[L], w)
                allocoe[B] = max (allocoe[B], h * (1 - pos))
                allocoe[T] = max (allocoe[T], h * pos)
            elif side == R:
                trueoe[R] = max (trueoe[R], w)
                allocoe[B] = max (allocoe[B], h * (1 - pos))
                allocoe[T] = max (allocoe[T], h * pos)

        opad = self.outerPadding * style.smallScale

        for i in range (0, 4):
            if any[i]: trueoe[i] += opad
            allocoe[i] = max (allocoe[i], trueoe[i])

        return trueoe, allocoe
    
    def _calcExteriors (self, exteriors, s):
        # s has four elements, one for each side of the plot,
        # indexed by the RectPlot.SIDE_X constants. Each element is a
        # tuple with two values. The first value is the amount of space
        # away from that side that is necessary, and the second value is
        # the amount of space along that side that is necessary. So if we
        # need 10 units above the top, sideinfo[0][0] = 10. If we need 30
        # units of width along the top, sideinfo[0][1] = 30. If we need
        # 50 units of height along the left side, sideinfo[3][1] = 50.
        #
        # So, the amount of space we need along an axis is either the
        # orthogonal distance away from the axis, or the bigger of
        # half of the distances along the adjacent sides, whichever is
        # biggest.
        #
        # We increment the input so that this function can be called
        # repeatedly.

        vprot = max (s[1][1], s[3][1]) / 2
        hprot = max (s[0][1], s[2][1]) / 2
        prots = [vprot, hprot, vprot, hprot]
        
        return [exteriors[i] + max (s[i][0], prots[i]) for i in range (0, 4)]

    def getMinimumSize (self, ctxt, style):
        # First, we figure out how much space our axes need. Then, we
        # add to that the amount of space that our outer painters need.
        # Then, we incorporate what the fieldpainters need.

        s = self._axisApplyHelper (0, 0, 'spaceExterior', ctxt, style)
        self.ext_axis = self._calcExteriors ([0] * 4, s)
        
        oe_true, oe_alloc = self._calcOuterExtents (ctxt, style)

        combined = [self.ext_axis[i] + oe_alloc[i] \
                    for i in range (0, 4)]

        self.ext_total = [self.ext_axis[i] + oe_true[i] \
                          for i in range (0, 4)]

        # Field painters
        fw, fh = 0, 0
        for fp in self.fpainters:
            w, h = fp.getMinimumSize (ctxt, style)
            fw, fh = max (fw, w), max (fh, h)

        return combined[1] + combined[3] + fw, \
               combined[0] + combined[2] + fh
    
    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        # First, size the field.
        
        fieldw = w - self.ext_total[1] - self.ext_total[3]
        fieldh = h - self.ext_total[0] - self.ext_total[2]

        if self.fieldAspect:
            cur = float (fieldw) / fieldh

            if cur > self.fieldAspect:
                # Wider than desired ; bump up left/right margins
                want_fieldw = fieldh * self.fieldAspect
                delta = (fieldw - want_fieldw) / 2
                self.ext_total[1] += delta
                self.ext_total[3] += delta
                fieldw = want_fieldw
            elif cur < self.fieldAspect:
                # Taller than desired ; bump up top/bottom margins
                want_fieldh = fieldw / self.fieldAspect
                delta = (fieldh - want_fieldh) / 2
                self.ext_total[0] += delta
                self.ext_total[2] += delta
                fieldh = want_fieldh
        
        self.fieldw = fieldw
        self.fieldh = fieldh
        
        ctxt.save ()
        ctxt.translate (self.ext_total[3], self.ext_total[0])

        for fp in self.fpainters:
            fp.configurePainting (ctxt, style, self.fieldw, self.fieldh)

        ctxt.restore ()
        
        # Now do the outer painters

        opad = self.outerPadding * style.smallScale
        ext_outer = [self.ext_total[i] - self.ext_axis[i] \
                     for i in range (0, 4)]
        
        for (op, side, pos) in self.opainters:
            # well this is gross
            ow, oh = op.getMinimumSize (ctxt, style)

            if side == self.SIDE_TOP:
                x = (fieldw - ow) * pos + self.ext_total[3]
                y = ext_outer[0] - oh - opad
            elif side == self.SIDE_BOTTOM:
                x = (fieldw - ow) * pos + self.ext_total[3]
                y = h - ext_outer[2] + opad
            elif side == self.SIDE_LEFT:
                x = ext_outer[3] - ow - opad
                y = (fieldh - oh) * (1 - pos) + self.ext_total[0]
            elif side == self.SIDE_RIGHT:
                x = w - ext_outer[1] + opad
                y = (fieldh - oh) * (1 - pos) + self.ext_total[0]

            #print ' -> %s, %d, %f to (%f, %f)' % (op, side, pos, x, y)
            
            ctxt.save ()
            ctxt.translate (x, y)
            op.configurePainting (ctxt, style, ow, oh)
            ctxt.restore ()

    def doPaint (self, ctxt, style):
        """Paint the rectangular plot: axes and data items."""

        # Axes
        
        ctxt.save ()
        ctxt.translate (self.ext_total[3], self.ext_total[0])
        self._axisApplyHelper (self.fieldw, self.fieldh, \
                               'paint', ctxt, style)
        ctxt.restore ()

        # Clip to the field, then paint the field items.
        
        ctxt.save ()
        ctxt.rectangle (self.ext_total[3], self.ext_total[0],
                        self.fieldw, self.fieldh)
        ctxt.clip ()
        
        for fp in self.fpainters:
            fp.paint (ctxt, style)

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
        
        self.xform = self.field.makeTransformer (self.width, self.height, True)

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

        w = self.hDrawSize * style.largeScale
        w += self.hPadding * style.smallScale
        w += self.tw

        return w, h

    def doPaint (self, ctxt, style):
        w, h = self.width, self.height
        dw = w - self.hPadding * style.smallScale - self.tw

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

        tx = w - self.tw
        ty = (h - self.th) / 2
        tc = style.getColor (self.textColor)

        self.ts.paintAt (ctxt, tx, ty, tc)

class XYKeyPainter (GenericKeyPainter):
    def _getText (self):
        return self.owner.keyText


    def _drawLine (self):
        return self.owner.lines


    def _drawStamp (self):
        return self.owner.pointStamp is not None
    

    def _applyLineStyle (self, style, ctxt):
        style.applyDataLine (ctxt, self.owner.primaryStyleNum)
        style.apply (ctxt, self.owner.lineStyle)


    def _applyStampStyle (self, style, ctxt):
        style.applyDataStamp (ctxt, self.owner.primaryStyleNum)
        style.apply (ctxt, self.owner.stampStyle)


    def _getStamp (self):
        return self.owner.pointStamp

class XYDataPainter (FieldPainter):
    lineStyle = None
    stampStyle = None
    needsPrimaryStyle = True
    primaryStyleNum = None
    lines = True
    pointStamp = None
    keyText = 'Data'
    
    def __init__ (self, lines=True, pointStamp=None, keyText=None):
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
            self.pointStamp.setData (self.data)

        if keyText is not None: self.keyText = keyText

    def getDataBounds (self):
        ign, ign, xs, ys = self.data.getAll ()

        if xs.shape[1] < 1:
            return (None, None, None, None)
        
        return xs.min (), xs.max (), ys.min (), ys.max ()

    def getKeyPainter (self):
        return XYKeyPainter (self)
    
    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

        imisc, fmisc, allx, ally = self.data.getAllMapped (self.xform)
        
        if allx.shape[1] < 1: return

        ctxt.save ()
        style.applyDataLine (ctxt, self.primaryStyleNum)
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
        style.applyDataStamp (ctxt, self.primaryStyleNum)
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
        style.applyDataLine (ctxt, self.owner.primaryStyleNum)
        style.apply (ctxt, self.owner.lineStyle)


    def _applyStampStyle (self, style, ctxt):
        style.applyDataStamp (ctxt, self.owner.primaryStyleNum)
        style.apply (ctxt, self.owner.stampStyle)


class DiscreteSteppedPainter (FieldPainter):
    lineStyle = None
    needsPrimaryStyle = True
    primaryStyleNum = None
    connectors = True
    keyText = 'Data'
    
    def __init__ (self, lineStyle=None, connectors=True, keyText=None):
        Painter.__init__ (self)

        self.lineStyle = lineStyle
        self.connectors = connectors
        
        self.data = RectDataHolder (DataHolder.AxisTypeInt,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)

        if keyText is not None: self.keyText = keyText

    def getDataBounds (self):
        ign, ign, xs, ys = self.data.getAll ()

        return xs.min (), xs.max (), ys.min (), ys.max ()
        
    def getKeyPainter (self):
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
        xpos = axis.transformIndices (axis.allIndices ()) * self.width
        ys = self.xform.mapY (ally[0])
        
        style.applyDataLine (ctxt, self.primaryStyleNum)
        style.apply (ctxt, self.lineStyle)

        for i in xrange (0, ys.size):
            idx = idxs[i]
            y = ys[i]

            if idx == 0:
                xleft = 0.0
            else:
                xleft = (xpos[idx] + xpos[idx-1]) / 2

            if idx == nidx - 1:
                xright = self.width
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
    primaryStyleNum = None
    connectors = True
    keyText = 'Data'
    
    def __init__ (self, lineStyle=None, connectors=True, keyText=None):
        Painter.__init__ (self)

        self.lineStyle = lineStyle
        self.connectors = connectors
        
        self.data = RectDataHolder (DataHolder.AxisTypeFloat,
                                    DataHolder.AxisTypeFloat)
        self.data.exportIface (self)
        self.cinfo = self.data.register (0, 0, 1, 1)

        if keyText is not None: self.keyText = keyText

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
        return LineOnlyKeyPainter (self)
    
    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)

        xs, ys = self.data.getRawXY (self.cinfo)
        finalx = self.xform.mapX (self._calcMaxX (xs))
        xs = self.xform.mapX (xs)
        ys = self.xform.mapY (ys)
        
        if xs.size < 1: return

        style.applyDataLine (ctxt, self.primaryStyleNum)
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
        hAct = self.hPadding * style.smallScale
        vAct = self.vPadding * style.smallScale

        self.chsize = self.child.getMinimumSize (ctxt, style)
        return (self.chsize[0] + hAct, self.chsize[1] + vAct)

    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        hAct = self.hPadding * style.smallScale
        vAct = self.vPadding * style.smallScale
        
        dx = hAct + self.hAlign * (w - self.chsize[0] - 2 * hAct)
        dy = vAct + self.vAlign * (h - self.chsize[1] - 2 * vAct)

        ctxt.save ()
        ctxt.translate (dx, dy)
        self.child.configurePainting (ctxt, style, self.chsize[0],
                                      self.chsize[1])
        ctxt.restore ()

    def getDataBounds (self):
        return None, None, None, None

    def getKeyPainter (self): return None
    
    def doPaint (self, ctxt, style):
        FieldPainter.doPaint (self, ctxt, style)
        self.child.paint (ctxt, style)

class XBand (FieldPainter):
    style = 'genericBand'
    needsPrimaryStyle = False
    primaryStyleNum = None
    keyText = 'Band'
    stroke = False
    fill = True
    
    def __init__ (self, xmin, xmax, stroke=False, fill=True, keyText=None):
        Painter.__init__ (self)

        self.stroke = stroke
        self.fill = fill
        
        if xmin > xmax: xmin, xmax = xmax, xmin
        self.xmin, self.xmax = xmin, xmax
        
        if keyText is not None: self.keyText = keyText

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
