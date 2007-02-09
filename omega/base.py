# Fooling around with OmegaPlot design and stuff
#
# Huuuuuge outstanding issues:
#
# * Bag architecture: push? pull? aiigggh
#
# * Size negotiation (top-down, bottom-up? fixed aspect ratio graphs)
#
# * Interactivity
#

import math

import bag

class Painter (object):
    mainStyle = None
    parent = None
    
    def __init__ (self):
        self.matrix = None

    def setParent (self, parent):
        if self.parent:
            self.parent.removeChild (self)

        self.parent = parent
        self.matrix = None
        
    def getMinimumSize (self, ctxt, style):
        #"""Should be a function of the style only."""
        # I feel like the above should be true, but we at least
        # need ctxt for measuring text, unless another way is found.
        return 0, 0

    def configurePainting (self, ctxt, style, w, h):
        if not self.parent:
            raise Exception ('Cannot configure parentless painter')
        
        self.matrix = ctxt.get_matrix ()
        self.width = w
        self.height = h

    def paint (self, ctxt, style, firstPaint):
        ctxt.save ()
        ctxt.set_matrix (self.matrix)
        style.apply (ctxt, self.mainStyle)
        self.doPaint (ctxt, style, firstPaint)
        ctxt.restore ()

class StreamSink (Painter):
    def __init__ (self, bag):
        Painter.__init__ (self)
        bag.registerSink (self)
        self._bag = bag

    def getBag (self): return self._bag
    
    def doPaint (self, ctxt, style, firstPaint):
        if firstPaint:
            self.doFirstPaint (ctxt, style)
        else:
            chunk = self._bag.getChunk (self)
            if not chunk: return # no more chunks
            self.doChunkPaint (ctxt, style, chunk)

    def expose (self, name):
        self._bag.exposeSink (self, name)
    
    def linkTo (self, source):
        self._bag.linkTo (source, self)

class NullPainter (Painter):
    lineStyle = 'genericLine'
    
    def getMinimumSize (self, ctxt, style):
        return 0, 0

    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        style.apply (ctxt, self.lineStyle)
        
        ctxt.move_to (0, 0)
        ctxt.line_to (self.width, self.height)
        ctxt.stroke ()
        ctxt.move_to (0, self.height)
        ctxt.line_to (self.width, 0)
        ctxt.stroke ()
    
class LinearAxis (object):
    """A class that defines a linear axis for a rectangular plot. Note
    that this class does not paint the axis; it just maps values from
    the bounds to a [0, 1] range so that the RectPlot class knows
    where to locate points."""

    coordSpec = 'F'
    
    def __init__ (self):
        self.min = 0. # XXX should be a bagprop!
        self.max = 10. # XXX should be a bagprop!

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

class RectPlot (Painter):
    """A rectangular plot. The workhorse of omegaplot, so it better be
    good!"""
    
    def __init__ (self, emulate=None):
        Painter.__init__ (self)
        
        # we might want to plot two data sets with different logical axes,
        # but store default ones here to make life easier in the common case.

        if not emulate:
            self.defaultXAxis = None
            self.defaultYAxis = None
            self.bpainter = BlankAxisPainter () # bottom (primary x) axis painter
            self.lpainter = BlankAxisPainter () # left (primary y) axis painter
            self.rpainter = BlankAxisPainter () # right (secondary x) axis painter
            self.tpainter = BlankAxisPainter () # top (secondary y) axis painter
        else:
            self.defaultXAxis = emulate.defaultXAxis
            self.defaultYAxis = emulate.defaultYAxis
            self.bpainter = emulate.bpainter
            self.lpainter = emulate.lpainter
            self.rpainter = emulate.rpainter
            self.tpainter = emulate.tpainter

        self.fpainters = [] # field painters

    def addFieldPainter (self, fp):
        fp.setParent (self)
        self.fpainters.append (fp)
        
        if not self.defaultXAxis and isinstance (fp, RectDataPainter):
            self.defaultXAxis = fp.xaxis
            self.defaultYAxis = fp.yaxis

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
        is pointed to by the defaultPainter attribute of the
        defaultXAxis and defaultYAxis members of the RectPlot. This class
        is instantiated with the logical axis as the only argument to __init__.

        Examples:

           rdp.magicAxisPainters ('lb') will give a classical plot
           in which the left and bottom sides of the field are marked with axes.

           rdp.magicAxisPainters ('hv') will give an IDL-style plot
           in which all sides of the field are marked with axes.

           rdp.magicAxisPainters ('r') will give an unusual plot in which
           only the right side is labeled with axes.
        """
        
        if 'h' in spec:
            self.bpainter = self.defaultXAxis.defaultPainter (self.defaultXAxis)
            self.tpainter = self.bpainter
        else:
            if 'b' in spec:
                self.bpainter = self.defaultXAxis.defaultPainter (self.defaultXAxis)
            else:
                self.bpainter = BlankAxisPainter ()

            if 't' in spec:
                self.tpainter = self.defaultXAxis.defaultPainter (self.defaultXAxis)
            else:
                self.tpainter = BlankAxisPainter ()
                    
        if 'v' in spec:
            self.lpainter = self.defaultYAxis.defaultPainter (self.defaultYAxis)
            self.rpainter = self.lpainter
        else:
            if 'l' in spec:
                self.lpainter = self.defaultYAxis.defaultPainter (self.defaultYAxis)
            else:
                self.lpainter = BlankAxisPainter ()

            if 'r' in spec:
                self.rpainter = self.defaultYAxis.defaultPainter (self.defaultYAxis)
            else:
                self.rpainter = BlankAxisPainter ()

    def removeChild (self, child):
        self.fpainters.remove (child)
        
    def addStream (self, stream, name, bag, sources):
        rdp = RectDataPainter (bag)
        bag.exposeSink (rdp, name)
        sources[name] = stream

        self.addFieldPainter (rdp)
    
    fieldAspect = None # Aspect ratio of the plot field, None for free
    
    SIDE_TOP = 0
    SIDE_RIGHT = 1
    SIDE_BOTTOM = 2
    SIDE_LEFT = 3

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

    def getMinimumSize (self, ctxt, style):
        s = self._axisApplyHelper (0, 0, 'spaceExterior', ctxt, style)

        self.exteriors = [0] * 4

        # How much space we need along top: either the orthogonal
        # distance reported by the top sidePainter, or the bigger
        # of half of the along distances reported by the left and
        # right sidePainters; whichever is bigger.

        self.exteriors[0] = max (s[0][0], max (s[1][1], s[3][1]) / 2)

        # And so on.
        
        self.exteriors[1] = max (s[1][0], max (s[0][1], s[2][1]) / 2)
        self.exteriors[2] = max (s[2][0], max (s[1][1], s[3][1]) / 2)
        self.exteriors[3] = max (s[3][0], max (s[0][1], s[2][1]) / 2)

        return self.exteriors[1] + self.exteriors[3], self.exteriors[0] + self.exteriors[2]
    
    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        fieldw = w - self.exteriors[1] - self.exteriors[3]
        fieldh = h - self.exteriors[0] - self.exteriors[2]

        if self.fieldAspect:
            cur = float (fieldw) / fieldh

            if cur > self.fieldAspect:
                # Wider than desired ; bump up left/right margins
                want_fieldw = fieldh * self.fieldAspect
                delta = (fieldw - want_fieldw) / 2
                self.exteriors[1] += delta
                self.exteriors[3] += delta
                fieldw = want_fieldw
            elif cur < self.fieldAspect:
                # Taller than desired ; bump up top/bottom margins
                want_fieldh = fieldw / self.fieldAspect
                delta = (fieldh - want_fieldh) / 2
                self.exteriors[0] += delta
                self.exteriors[2] += delta
                fieldh = want_fieldh
        
        self.fieldw = fieldw
        self.fieldh = fieldh
        
        ctxt.save ()
        ctxt.translate (self.exteriors[3], self.exteriors[0])

        for fp in self.fpainters:
            fp.configurePainting (ctxt, style, self.fieldw, self.fieldh)

        ctxt.restore ()
    
    def doPaint (self, ctxt, style, firstPaint):
        """Paint the rectangular plot: axes and data items."""

        if firstPaint:
            ctxt.save ()
            ctxt.translate (self.exteriors[3], self.exteriors[0])
            self._axisApplyHelper (self.fieldw, self.fieldh, \
                                   'paint', ctxt, style)
            ctxt.restore ()

        ctxt.save ()
        ctxt.rectangle (self.exteriors[3], self.exteriors[2],
                        self.fieldw, self.fieldh)
        ctxt.clip ()
        
        for fp in self.fpainters:
            fp.paint (ctxt, style, firstPaint)

        ctxt.restore ()

class StampPaintHelper (object):
    def __init__ (self, xformfn):
        self.transform = xformfn

class RectDataPainter (StreamSink):
    lineStyle = 'genericLine'
    lines = True
    pointStamp = None
    
    def __init__ (self, bagOrRDP):
        if isinstance (bagOrRDP, bag.Bag):
            StreamSink.__init__ (self, bagOrRDP)
            self.xaxis = LinearAxis ()
            self.yaxis = LinearAxis ()
        else:
            StreamSink.__init__ (self, bagOrRDP.getBag ())
            self.xaxis = bagOrRDP.xaxis
            self.yaxis = bagOrRDP.yaxis

    @property
    def sinkSpec (self):
        if self.pointStamp:
            return self.xaxis.coordSpec + self.yaxis.coordSpec + \
                   self.pointStamp.sinkSpec
        return self.xaxis.coordSpec + self.yaxis.coordSpec
    
    def transform (self, x, y):
        # the 1-f(y) deals with the opposite senses of math and
        # cairo coordinate systems.
        return self.width * self.xaxis.transform (x), \
               self.height * (1. - self.yaxis.transform (y))
    
    def doFirstPaint (self, ctxt, style):
        self.lastx = None
        self.lasty = None

    def doChunkPaint (self, ctxt, style, chunk):
        # FIXME this will require lots of ... fixing
        points = []

        style.apply (ctxt, self.lineStyle)
        
        if self.lastx == None:
            try:
                data = chunk.next ()
                self.lastx, self.lasty = self.transform (data[0], data[1])
                if self.pointStamp: points.append ((self.lastx, self.lasty) + data[2:])
            except StopIteration:
                return

        ctxt.move_to (self.lastx, self.lasty)

        if self.lines:
            for data in chunk:
                x, y = self.transform (data[0], data[1])
                ctxt.line_to (x, y)
                if self.pointStamp: points.append ((x, y) + data[2:])

            self.lastx, self.lasty = ctxt.get_current_point ()
            ctxt.stroke ()
        elif self.pointStamp:
            for data in chunk:
                xy = self.transform (data[0], data[1])
                points.append (xy + data[2:])

            self.lastx, self.lasty = points[len (points) - 1][0:2]

        if self.pointStamp:
            helper = StampPaintHelper (self.transform)
            
            for xdata in points:
                self.pointStamp.paint (ctxt, style, helper, xdata[0], xdata[1], xdata[2:])

    def setBounds (self, xmin, xmax, ymin, ymax):
        self.xaxis.min = xmin
        self.xaxis.max = xmax
        self.yaxis.min = ymin
        self.yaxis.max = ymax
        
class BandPainter (StreamSink):
    bandStyle = 'genericBand'
    
    def __init__ (self, bag):
        StreamSink.__init__ (self, bag)
        
        self.xaxis = LinearAxis ()
        self.yaxis = LinearAxis ()

    @property
    def sinkSpec (self):
        return self.xaxis.coordSpec + self.yaxis.coordSpec * 2
    
    def transform (self, pts):
        return (self.width * self.xaxis.transform (pts[0]),
                self.height * (1. - self.yaxis.transform (pts[1])),
                self.height * (1. - self.yaxis.transform (pts[2])))
    
    def doFirstPaint (self, ctxt, style):
        self.lastx = None
        self.lastylow = None
        self.lastyhigh = None

    def doChunkPaint (self, ctxt, style, chunk):
        # FIXME this will require lots of ... fixing
        style.apply (ctxt, self.bandStyle)

        points = [self.transform (pts) for pts in chunk]
        l = len (points)
        
        ctxt.move_to (points[0][0], points[0][2])

        for i in xrange (1, l):
            ctxt.line_to (points[i][0], points[i][2])

        for i in xrange (1, l + 1):
            ctxt.line_to (points[l - i][0], points[l - i][1])

        ctxt.close_path ()
        ctxt.fill ()

class DiscreteHistogramPainter (StreamSink):
    lineStyle = 'genericLine'
    
    def __init__ (self, bag):
        StreamSink.__init__ (self, bag)
        self.xaxis = None
        self.yaxis = LinearAxis ()

    @property
    def sinkSpec (self):
        return self.xaxis.coordSpec + self.yaxis.coordSpec
    
    def transform (self, x, y):
        # the 1-f(y) deals with the opposite senses of math and
        # cairo coordinate systems.
        return self.width * self.xaxis.transform (x), \
               self.height * (1. - self.yaxis.transform (y))

    def nextX (self, preval):
        # uuuugly
        idx = self.xaxis.valueToIndex (preval)
        idx += 1

        if idx >= self.xaxis.numAbscissae ():
            return -1
        
        val = self.xaxis.indexToValue (idx)
        return self.width * self.xaxis.transform (val)
    
    def doFirstPaint (self, ctxt, style):
        if not self.xaxis:
            raise Exception ('Need to specify an X axis for this class!')
        
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
        
        for pair in chunk:
            ctrx, y = self.transform (*pair)

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
        
        next_ctr_x = self.nextX (pair[0])

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
    
    def setBounds (self, xmin, xmax, ymin, ymax):
        self.xaxis.min = xmin
        self.xaxis.max = xmax
        self.yaxis.min = ymin
        self.yaxis.max = ymax
