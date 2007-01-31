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
    
    def __init__ (self, coordSpec, abscissae):
        self.coordSpec = coordSpec
        self.abscissae = list (abscissae)

    def transform (self, value):
        try:
            idx = self.abscissae.index (value)
            return float (idx + 1) / (len (self.abscissae) + 1)
        except ValueError:
            # What would a proper retval be here?
            return 0.

    def inbounds (self, value):
        return value in self.abscissae
    
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
        
        span = self.axis.max - self.axis.min
        mip = math.floor (math.log10 (span)) # major interval power

        inc = 10. ** mip / self.minorTicks # incr. between minor ticks
        coeff = int (math.ceil (self.axis.min / inc)) # coeff. of first tick
        val = coeff * inc # location of first tick

        while self.axis.inbounds (val):
            if coeff % self.minorTicks == 0: len = self.majorTickScale * style.largeScale
            else: len = self.minorTickScale * style.smallScale

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

            if coeff % self.minorTicks == 0:
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
        test = self.formatLabel (self.axis.abscissae[0])
        (tmp, tmp, textw, texth, tmp, tmp) = \
              ctxt.text_extents (test)
        return self.labelSeparation * style.smallScale \
               + helper.spaceRectOut (textw, texth), \
               helper.spaceRectAlong (textw, texth)
    
    def paint (self, helper, ctxt, style):
        BlankAxisPainter.paint (self, helper, ctxt, style)

        style.apply (ctxt, self.tickStyle)

        abscissae = self.axis.abscissae
        inc = 1.0 / (len (abscissae) + 1)
        val = inc

        for i in range (0, len (abscissae)):
            helper.paintTickIn (ctxt, val, self.tickScale * style.largeScale)

            # See discussion of label painting in LinearAxisPainter.
            # Code needs to be consolidated, for sure.

            helper.moveToAlong (ctxt, val)
            helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)

            s = self.formatLabel (abscissae[i])
            (xbear, ybear, textw, texth, xadv, yadv) = \
                    ctxt.text_extents (s)
            helper.relMoveRectOut (ctxt, textw, texth)
            ctxt.rel_move_to (-xbear, -ybear) # brings us from UL to LR

            ctxt.save ()
            style.apply (ctxt, self.labelStyle)
            ctxt.show_text (s)
            ctxt.restore ()
            
            val += inc

class RectPlot (Painter):
    """A rectangular plot. The workhorse of omegaplot, so it better be
    good!"""
    
    def __init__ (self):
        Painter.__init__ (self)
        
        # we might want to plot two data sets with different logical axes,
        # but store default ones here to make life easier in the common case.
        
        self.defaultXAxis = None
        self.defaultYAxis = None
        self.bpainter = BlankAxisPainter () # bottom (primary x) axis painter
        self.lpainter = BlankAxisPainter () # left (primary y) axis painter
        self.rpainter = BlankAxisPainter () # right (secondary x) axis painter
        self.tpainter = BlankAxisPainter () # top (secondary y) axis painter
        self.fpainters = [] # field painters

    def addFieldPainter (self, fp):
        fp.setParent (self)
        self.fpainters.append (fp)
        
        if not self.defaultXAxis and isinstance (fp, RectDataPainter):
            self.defaultXAxis = fp.xaxis
            self.defaultYAxis = fp.yaxis

    def removeChild (self, child):
        self.fpainters.remove (child)
        
    def addStream (self, stream, name, bag, sources):
        rdp = RectDataPainter (bag)
        bag.exposeSink (rdp, name)
        sources[name] = stream

        self.addFieldPainter (rdp)
    
    field_aspect = None # Aspect ratio of the plot field, None for free
    
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

        self.fieldw = w - self.exteriors[1] - self.exteriors[3]
        self.fieldh = h - self.exteriors[0] - self.exteriors[2]

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
        
class RectDataPainter (StreamSink):
    lineStyle = 'genericLine'
    lines = True
    pointStamp = None
    
    def __init__ (self, bag):
        StreamSink.__init__ (self, bag)
        
        self.xaxis = LinearAxis ()
        self.yaxis = LinearAxis ()

    @property
    def sinkSpec (self):
        if self.pointStamp:
            return self.xaxis.coordSpec + self.yaxis.coordSpec + \
                   self.pointStamp.sinkSpec
        return self.xaxis.coordSpec + self.yaxis.coordSpec
    
    def transform (self, pair):
        # the 1-f(y) deals with the opposite senses of math and
        # cairo coordinate systems.
        return self.width * self.xaxis.transform (pair[0]), \
               self.height * (1. - self.yaxis.transform (pair[1]))
    
    def doFirstPaint (self, ctxt, style):
        self.lastx = None
        self.lasty = None

    def doChunkPaint (self, ctxt, style, chunk):
        # FIXME this will require lots of ... fixing
        points = []

        style.apply (ctxt, self.lineStyle)
        
        if self.lastx == None:
            try:
                self.lastx, self.lasty = self.transform (chunk.next ())
                if self.pointStamp: points.append ((self.lastx, self.lasty))
            except StopIteration:
                return

        ctxt.move_to (self.lastx, self.lasty)

        if self.lines:
            for pair in chunk:
                x, y = self.transform (pair)
                ctxt.line_to (x, y)
                if self.pointStamp: points.append ((x, y))

            self.lastx, self.lasty = ctxt.get_current_point ()
            ctxt.stroke ()
        elif self.pointStamp:
            for pair in chunk:
                points.append (self.transform (pair))

            self.lastx, self.lasty = points[len (points) - 1]

        if self.pointStamp:
            for (x, y) in points: self.pointStamp.paint (ctxt, style, x, y, ())

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


