# Rectangular plots.

import math
import bag
from base import *
from images import LatexPainter

class LinearAxis (object):
    """A class that defines a linear axis for a rectangular plot. Note
    that this class does not paint the axis; it just maps values from
    the bounds to a [0, 1] range so that the RectPlot class knows
    where to locate points."""

    coordSpec = 'F'
    
    def __init__ (self, min=0., max=10.):
        self.min = min # XXX should be a bagprop!
        self.max = max # XXX should be a bagprop!

    def transform (self, value):
        """Return where the given value should reside on this axis, 0
        indicating all the way towards the physical minimum of the
        plotting area, 1 indicating all the way to the maximum."""

        return float (value - self.min) / (self.max - self.min)

    def inbounds (self, value):
        """Return True if the given value is within the bounds of this axis."""
        return value >= self.min and value <= self.max
    
class DiscreteAxis (object):
    """A class that defines a discrete axis for a rectangular plot. That is,
    the abscissa values are abitrary and mapped to sequential points along
    the axis with even spacing."""

    # If true, and there are N abscissae, map values to 1 / (N + 1) to
    # N / (N + 1), so that no data points land on the left and right edges
    # of the field. If false, map them to 0 / (N - 1) to (N - 1) / (N - 1),
    # so that the first value lands on the left edge and the last value on
    # the right edge.
    
    padBoundaries = True
    
    def __init__ (self, coordSpec):
        self.coordSpec = coordSpec

    def numAbscissae (self):
        raise NotImplementedError ()

    def valueToIndex (self, value):
        raise NotImplementedError ()
        
    def indexToValue (self, index):
        raise NotImplementedError ()
        
    def inbounds (self, value):
        raise NotImplementedError ()
    
    def transform (self, value):
        try:
            idx = self.valueToIndex (value)

            if self.padBoundaries:
                return float (idx + 1) / (self.numAbscissae () + 1)
            
            return float (idx) / (self.numAbscissae () - 1)
        except ValueError:
            # What would a proper retval be here?
            return 0.

class EnumeratedDiscreteAxis (DiscreteAxis):
    """A discrete axis in which the abscissae values are stored in memory in
    an array."""
    
    def __init__ (self, coordSpec, abscissae):
        DiscreteAxis.__init__ (self, coordSpec)
        self.abscissae = list (abscissae)

    def numAbscissae (self):
        return len (self.abscissae)

    def valueToIndex (self, value):
        return self.abscissae.index (value)

    def indexToValue (self, index):
        return self.abscissae[index]

    def inbounds (self, value): 
        return value in self.abscissae
    
class DiscreteIntegerAxis (DiscreteAxis):
    """A discrete axis in which the abscissae values are integers, specified
    by a minimum, maximum, and step."""
    
    def __init__ (self, min, max, step=1):
        DiscreteAxis.__init__ (self, 'F') # proper to call it a float and not an int?
        self.min = int (min)
        self.max = int (max)
        step = int (step)
        
        if min < max and step < 0:
            self.step = -step
        elif min > max and step > 0:
            self.step = -step
        else:
            self.step = step

    def numAbscissae (self):
        return (self.max - self.min) // self.step + 1

    def valueToIndex (self, value):
        return (value - self.min) // self.step

    def indexToValue (self, index):
        return index * self.step + self.min

    def inbounds (self, value): 
        return value >= self.min and value <= self.max
    
class BlankAxisPainter (object):
    """An axisPainter for the RectPlot class. Either paints nothing at
    all, or just the line on the plot with no tick marks or labels."""
    
    drawBaseline = True # XXX bagprop
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
    majorTickScale = 2 # in largeScale
    minorTickScale = 2 # in smallScale
    minorTicks = 5
    tickStyle = 'bgLinework' # style ref.
    labelStyle = None
    avoidBounds = True # do not draw ticks at extremes of axes
    labelMinorTicks = False # draw value labels at the minor tick points?
    
    def formatLabel (self, val):
        if callable (self.numFormat): return self.numFormat (val)
        return self.numFormat % (val)

    def spaceExterior (self, helper, ctxt, style):
        test = self.formatLabel (self.axis.max)
        (tmp, tmp, textw, texth, tmp, tmp) = \
              ctxt.text_extents (test)
        return self.labelSeparation * style.smallScale \
               + helper.spaceRectOut (textw, texth), \
               helper.spaceRectAlong (textw, texth)
    
    def paint (self, helper, ctxt, style):
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        # Tick spacing variables
        
        span = self.axis.max - self.axis.min
        mip = math.floor (math.log10 (span)) # major interval power

        inc = 10. ** mip / self.minorTicks # incr. between minor ticks
        coeff = int (math.ceil (self.axis.min / inc)) # coeff. of first tick
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
            if coeff % self.minorTicks == 0: len = self.majorTickScale * style.largeScale
            else: len = self.minorTickScale * style.smallScale

            if zeroclamp and abs(val) < zeroclamp:
                val = 0.
            
            v = self.axis.transform (val)

            # If our tick would land right on the bounds of the plot field,
            # it might overplot on the baseline of the axis adjacent to ours.
            # This is ugly, so don't do it. However, this behavior can be
            # disabled by setting avoidBounds to false, so that if the adjacent
            # axes don't draw their baselines, we'll see the ticks as desired.
            
            if not self.avoidBounds or (v != 0. and v != 1.):
                helper.paintTickIn (ctxt, v, len)

            # Now print the label text with Cairo, for the time being.
            # We must be crafty to align the text appropriately
            # relative to the known location of the tick mark.
            # Cairo text extents are given in user coordinates, which
            # has implications for how the coords need to be
            # transformed, I'm pretty sure.
            #
            # FIXME: if textw > w * f, don't draw the text, to avoid
            # overlapping tick labels.
            #
            # FIXME: we need to be able to render mathematical symbols
            # correctly, for axes with labels of 5 \pi, eg. The only
            # correct way I can think to do this is to invoke latex.
            # Eeek.

            if coeff % self.minorTicks == 0 or self.labelMinorTicks:
                helper.moveToAlong (ctxt, v)
                helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)

                s = self.formatLabel (val)
                (xbear, ybear, textw, texth, xadv, yadv) = \
                        ctxt.text_extents (s)
                helper.relMoveRectOut (ctxt, textw, texth)
                ctxt.rel_move_to (-xbear, -ybear) # brings us from UL to LR

                ctxt.save ()
                style.apply (ctxt, self.labelStyle)
                ctxt.show_text (s)
                ctxt.restore ()
            
            val += inc
            coeff += 1

LinearAxis.defaultPainter = LinearAxisPainter

class DiscreteAxisPainter (BlankAxisPainter):
    """An axisPainter for the RectPlot class. Paints a tick mark and label
    for each item in the list of abscissae of the DiscreteAxis. Specialized
    subclasses of this class should be used for common discrete scenarios
    (months, days of week, etc.)"""
    
    def __init__ (self, axis, formatLabel=None):
        BlankAxisPainter.__init__ (self)

        if not isinstance (axis, DiscreteAxis):
            raise Exception ('Giving DiscreteAxisPainter a'
                             'non-DiscreteAxis axis')
        
        self.axis = axis
        self.formatLabel = formatLabel or self.genericFormat

    labelSeparation = 2 # in smallScale
    tickScale = 2 # in largeScale
    tickStyle = 'bgLinework' # style ref.
    labelStyle = None

    def genericFormat (self, v): return str(v)
    
    def spaceExterior (self, helper, ctxt, style):
        test = self.formatLabel (self.axis.indexToValue (0))
        (tmp, tmp, textw, texth, tmp, tmp) = \
              ctxt.text_extents (test)
        return self.labelSeparation * style.smallScale \
               + helper.spaceRectOut (textw, texth), \
               helper.spaceRectAlong (textw, texth)
    
    def paint (self, helper, ctxt, style):
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        n = self.axis.numAbscissae ()

        for i in range (0, n):
            val = self.axis.transform (self.axis.indexToValue (i))
            helper.paintTickIn (ctxt, val, self.tickScale * style.largeScale)

            # See discussion of label painting in LinearAxisPainter.
            # Code needs to be consolidated, for sure.

            helper.moveToAlong (ctxt, val)
            helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)

            s = self.formatLabel (self.axis.indexToValue (i))
            (xbear, ybear, textw, texth, xadv, yadv) = \
                    ctxt.text_extents (s)
            helper.relMoveRectOut (ctxt, textw, texth)
            ctxt.rel_move_to (-xbear, -ybear) # brings us from UL to LR

            ctxt.save ()
            style.apply (ctxt, self.labelStyle)
            ctxt.show_text (s)
            ctxt.restore ()

DiscreteAxis.defaultPainter = DiscreteAxisPainter

class RectField (object):
    """A rectangular field. A field is associated with X and Y axes; other objects
    use the field to map X and Y values input from the user into coordinates at which
    to paint."""

    def __init__ (self, xaxisOrField=None, yaxis=None):
        if isinstance (xaxisOrField, RectField):
            xaxis = xaxisOrField.xaxis
            yaxis = xaxisOrField.yaxis
            
        if not xaxisOrField: xaxisOrField = LinearAxis ()
        if not yaxis: yaxis = LinearAxis ()

        self.xaxis = xaxisOrField
        self.yaxis = yaxis
    
    def mapSpec (self, spec):
        """Objects which reference a field and source or sink X and Y values should
        call use this function to generate the correct 'sinkSpec'. For instance, if
        a Y error bar stamp painter might have a sink specification of 'XYYY', corresponding
        to an X/Y location, a lower Y error bound, and an upper Y error bound. This function
        might then map these values into FFFF, if the axes both take floats as inputs,
        or perhaps SFFF, if the X axis is indexed by strings."""
        
        return spec.replace ('X', self.xaxis.coordSpec).replace ('Y', self.yaxis.coordSpec)

    class Transformer (object):
        """A utility class tied to a RectField object. Has three members:

        - mapData (spec, data): Given a sink specification and a tuple or list
        of data, maps those data corresponding to 'X' or 'Y' values in the specification
        to an appropriate floating point number using the axes associated with the
        RectField

        - mapX (val): Transforms val to an X value within the field using
        the RectField's X axis.

        - mapY (val): Analogous to transformX.
        """
        
        def __init__ (self, field, width, height):
            self.field = field
            self.width = float (width)
            self.height = float (height)

        def mapX (self, val):
            return self.field.xaxis.transform (val) * self.width
        
        def mapY (self, val):
            # Mathematical Y axes have 0 on the bottom, while cairo has 0 at the
            # top. The one-minus accounts for that difference. (We transform from
            # math sense to cairo sense.)
            
            return (1. - self.field.yaxis.transform (val)) * self.height

        def mapData (self, spec, data):
            mapped = list (data)
        
            for i in range (0, len(mapped)):
                if spec[i] == 'X':
                    mapped[i] = self.mapX (data[i])
                elif spec[i] == 'Y':
                    mapped[i] = self.mapY (data[i])

            return mapped

        def mapChunk (self, spec, chunk):
            # FIXME: could probably make this a bit more efficient
            # Could maybe precompile a specific mapData function
            # somehow. That would be cute.
            
            xmaps = []
            ymaps = []

            for i in range (0, len(spec)):
                if spec[i] == 'X':
                    xmaps.append (i)
                elif spec[i] == 'Y':
                    ymaps.append (i)

            for data in chunk:
                mapped = list (data)

                for idx in xmaps:
                    mapped[idx] = self.mapX (data[idx])
                for idx in ymaps:
                    mapped[idx] = self.mapY (data[idx])

                yield mapped
                
    def makeTransformer (self, width, height):
        return self.Transformer (self, width, height)

    def setBounds (self, xmin, xmax, ymin, ymax):
        self.xaxis.min = xmin
        self.xaxis.max = xmax
        self.yaxis.min = ymin
        self.yaxis.max = ymax

class RectPlot (Painter):
    """A rectangular plot. The workhorse of omegaplot, so it better be
    good!"""
    
    fieldAspect = None # Aspect ratio of the plot field, None for free
    outerPadding = 3 # in smallScale
    
    SIDE_TOP = 0
    SIDE_RIGHT = 1
    SIDE_BOTTOM = 2
    SIDE_LEFT = 3

    def __init__ (self, emulate=None):
        Painter.__init__ (self)
        
        # we might want to plot two data sets with different logical axes,
        # but store default ones here to make life easier in the common case.

        if not emulate:
            self.defaultField = None
            self.bpainter = BlankAxisPainter () # bottom (primary x) axis painter
            self.lpainter = BlankAxisPainter () # left (primary y) axis painter
            self.rpainter = BlankAxisPainter () # right (secondary x) axis painter
            self.tpainter = BlankAxisPainter () # top (secondary y) axis painter
        else:
            self.defaultField = emulate.defaultField
            self.bpainter = emulate.bpainter
            self.lpainter = emulate.lpainter
            self.rpainter = emulate.rpainter
            self.tpainter = emulate.tpainter

        self.fpainters = [] # field painters
        self.opainters = [] # outer painters
        self.mainLabels = [None] * 4
        
    def addFieldPainter (self, fp):
        fp.setParent (self)
        self.fpainters.append (fp)
        
        if not self.defaultField and hasattr (fp, 'field') and \
               isinstance (fp.field, RectField):
            self.defaultField = fp.field

    def addOuterPainter (self, op, side, position):
        op.setParent (self)
        self.opainters.append ((op, side, position))

    def _outerPainterIndex (self, op):
        for i in xrange (0, len(self.opainters)):
            if self.opainters[i][0] == self: return 1

        raise ValueError ('%s not in list of outer painters' % (op))

    def moveOuterPainter (self, op, side, position):
        idx = self._outerPainterIndex (self, op)
        self.opainters[i] = (op, side, position)
    
    def removeChild (self, child):
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

           rdp.magicAxisPainters ('lb') will give a classical plot
           in which the left and bottom sides of the field are marked with axes.

           rdp.magicAxisPainters ('hv') will give an IDL-style plot
           in which all sides of the field are marked with axes.

           rdp.magicAxisPainters ('r') will give an unusual plot in which
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

    def addStream (self, stream, name, bag, sources):
        rdp = RectDataPainter (bag)
        bag.exposeSink (rdp, name)
        sources[name] = stream

        self.addFieldPainter (rdp)

    # X and Y axis label helpers

    def setSideLabel (self, side, val):
        if self.mainLabels[side]:
            self.removeChild (self.mainLabels[side])

        if not isinstance (val, Painter):
            val = LatexPainter (str (val))

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

            # Hack, hack hack hack... hack, hack hack hack haaack!
            # Autorotate axis labels if they appear to be text
            
            if op in self.mainLabels and side % 2 == 1 and \
                   isinstance (op, LatexPainter):
                
                aspect = float (w) / h

                if aspect > 3.:
                    if side == R:
                        op.setRotation (LatexPainter.ROT_CW90)
                    elif side == L:
                        op.setRotation (LatexPainter.ROT_CCW90)
                        
                    w, h = h, w

            # End hack.
            
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

        self.oe_true = trueoe
        self.oe_alloc = allocoe
    
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
        
        s = self._axisApplyHelper (0, 0, 'spaceExterior', ctxt, style)
        self.ext_axis = self._calcExteriors ([0] * 4, s)
        
        self._calcOuterExtents (ctxt, style)

        combined = [self.ext_axis[i] + self.oe_alloc[i] \
                    for i in range (0, 4)]

        self.ext_total = [self.ext_axis[i] + self.oe_true[i] \
                          for i in range (0, 4)]

        return combined[1] + combined[3], \
               combined[0] + combined[2]
    
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

    def doPaint (self, ctxt, style, firstPaint):
        """Paint the rectangular plot: axes and data items."""

        if firstPaint:
            ctxt.save ()
            ctxt.translate (self.ext_total[3], self.ext_total[0])
            self._axisApplyHelper (self.fieldw, self.fieldh, \
                                   'paint', ctxt, style)
            ctxt.restore ()

        ctxt.save ()
        ctxt.rectangle (self.ext_total[3], self.ext_total[0],
                        self.fieldw, self.fieldh)
        ctxt.clip ()
        
        for fp in self.fpainters:
            fp.paint (ctxt, style, firstPaint)

        ctxt.restore ()

        for (op, side, pos) in self.opainters:
            op.paint (ctxt, style, firstPaint)

class FieldPainter (StreamSink):
    rawSpec = 'XY'
    field = None
    
    def __init__ (self, bagOrFP):
        if isinstance (bagOrFP, bag.Bag):
            StreamSink.__init__ (self, bagOrFP)
            self.field = RectField ()
        else:
            StreamSink.__init__ (self, bagOrFP.getBag ())
            self.field = bagOrFP.field

    @property
    def sinkSpec (self):
        return self.field.mapSpec (self.rawSpec)
    
    def doFirstPaint (self, ctxt, style):
        self.xform = self.field.makeTransformer (self.width, self.height)

    def setBounds (self, *args):
        self.field.setBounds (*args)

class RectDataPainter (FieldPainter):
    lineStyle = 'genericLine'
    lines = True
    pointStamp = None
    
    def __init__ (self, bagOrFP):
        FieldPainter.__init__ (self, bagOrFP)

    @property
    def rawSpec (self):
        if not self.pointStamp:
            return 'XY'
        
        spec = self.pointStamp.stampSpec
        
        if spec[0:2] != 'XY':
            raise Exception ('trying to paint rect data with invalid stamp!')
        
        return spec
    
    def doFirstPaint (self, ctxt, style):
        FieldPainter.doFirstPaint (self, ctxt, style)
        self.lastx = None
        self.lasty = None

    def doChunkPaint (self, ctxt, style, chunk):
        chunk = list (self.xform.mapChunk (self.rawSpec, chunk))
        
        style.apply (ctxt, self.lineStyle)
        
        if self.lastx == None:
            try:
                self.lastx, self.lasty = chunk[0][0:2]
            except StopIteration:
                return

        ctxt.move_to (self.lastx, self.lasty)

        if self.lines:
            for data in chunk:
                ctxt.line_to (data[0], data[1])

            self.lastx, self.lasty = ctxt.get_current_point ()
            ctxt.stroke ()
        elif self.pointStamp:
            self.lastx, self.lasty = chunk[-1][0:2]

        if self.pointStamp:
            for data in chunk:
                self.pointStamp.paint (ctxt, style, data)

class BandPainter (FieldPainter):
    bandStyle = 'genericBand'
    rawSpec = 'XYY'
    
    def __init__ (self, bagOrFP):
        FieldPainter.__init__ (self, bagOrFP)

    def doFirstPaint (self, ctxt, style):
        FieldPainter.doFirstPaint (self, ctxt, style)
        self.lastx = None
        self.lastylow = None
        self.lastyhigh = None

    def doChunkPaint (self, ctxt, style, chunk):
        # FIXME this will require lots of ... fixing
        style.apply (ctxt, self.bandStyle)

        chunk = list (self.xform.mapChunk (self.rawSpec, chunk))
        l = len (chunk)
        
        ctxt.move_to (chunk[0][0], chunk[0][2])

        for i in xrange (1, l):
            ctxt.line_to (chunk[i][0], chunk[i][2])

        for i in xrange (1, l + 1):
            ctxt.line_to (chunk[l - i][0], chunk[l - i][1])

        ctxt.close_path ()
        ctxt.fill ()

class DiscreteHistogramPainter (FieldPainter):
    lineStyle = 'genericLine'
    
    def __init__ (self, bagOrFP):
        FieldPainter.__init__ (self, bagOrFP)

        if isinstance (bagOrFP, bag.Bag):
            self.field.xaxis = None # User needs to specify a DiscreteAxis

    def nextX (self, preval):
        # uuuugly
        idx = self.field.xaxis.valueToIndex (preval)
        idx += 1

        if idx >= self.field.xaxis.numAbscissae ():
            return -1

        # We should really use a Transformer returned by
        # the field somehow.
        val = self.field.xaxis.indexToValue (idx)
        return self.width * self.field.xaxis.transform (val)
    
    def doFirstPaint (self, ctxt, style):
        if not self.field.xaxis:
            raise Exception ('Need to specify an X axis for this class!')

        FieldPainter.doFirstPaint (self, ctxt, style)
        
        self.lastx = 0
        self.lasty = self.height

    def doChunkPaint (self, ctxt, style, chunk):
        # FIXME: we assume that xaxis.padBoundaries = True
        # We also assume that the data show up in order!
        # If padBoundaries = False, this code actually somehow
        # works. I have no idea why.
        #
        # This algorithm is really gross. I needed to sketch it
        # out on paper in detail to check that it worked.
        
        style.apply (ctxt, self.lineStyle)

        #try:
        #    xyvals = chunk.next ()
        #    next_ctr_x, nexty = self.transform (xyvals)
        #except StopIteration:
        #    return

        #ctxt.move_to (self.lastx, self.lasty)
        #ctxt.line_to (self.lastx, nexty)

        #lastx = (next_ctr_x + self.nextX (xyvals[0])) / 2
        #lasty = nexty
        #lastctrx = next_ctr_x

        lastx = self.lastx
        lasty = self.lasty
        lastctrx = 0
        
        for ctrx, y in self.xform.mapChunk (self.rawSpec, chunk):
            #if lastctrx < 0:
            #    rt_edge_x = self.lastx
            #else:
            rt_edge_x = (ctrx + lastctrx) / 2
            
            ctxt.line_to (lastx, lasty)
            ctxt.line_to (rt_edge_x, lasty)

            lastx = rt_edge_x
            lastctrx = ctrx
            lasty = y

        # Finish off the current bar in prep for the next
        # chunk, cause we don't know if we're the last chunk
        # or not.
        
        next_ctr_x = self.nextX (ctrx)

        if next_ctr_x < 0:
            # We just painted the last item in the list;
            # don't just draw the horizontal, drop it down to 0
            rt_edge_x = (self.width + lastctrx) / 2
            ctxt.line_to (lastx, lasty)
            ctxt.line_to (rt_edge_x, lasty)
            ctxt.line_to (rt_edge_x, self.height)
            # This is to match the left-hand side of the histogram;
            # it might be better not to draw it, but then the first-chunk
            # and beginning-of-chunk algorithm will need to be tweaked somehow.
            ctxt.line_to (self.width, self.height)
        else:
            ctxt.line_to (lastx, lasty)
            ctxt.line_to ((ctrx + next_ctr_x)/2, lasty)
        
        ctxt.stroke ()

        self.lastx = lastx
        self.lasty = lasty
    
class LinePainter (Painter):
    lineStyle = 'genericLine'
    x0 = 0
    y0 = 0
    x1 = 10
    y1 = 10
    
    def __init__ (self, field, *pts):
        Painter.__init__ (self)
        
        self.field = field or RectField ()

        if len (pts) == 4:
            self.x0, self.y0, self.x1, self.y1 = pts
        elif len (pts) == 0:
            return
        else:
            raise Exception ('Invalid argument to LinePainter(): should have 0 or 4 elements')
    
    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        style.apply (ctxt, self.lineStyle)

        xform = self.field.makeTransformer (self.width, self.height)
        ctxt.move_to (xform.mapX (self.x0), xform.mapY (self.y0))
        ctxt.line_to (xform.mapX (self.x1), xform.mapY (self.y1))
        ctxt.stroke ()
