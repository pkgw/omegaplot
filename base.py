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

import cairo
import gobject
import gtk
import gtkThread
import math
import sys

class OmegaArea (gtk.DrawingArea):
    def __init__ (self, bag, style, sources):
        gtk.DrawingArea.__init__ (self)
        self.connect ("expose_event", self._expose)
        self.omegaStyle = style
        self._painter = NullPainter ()
        self.sources = sources
        self.bag = bag
        self.savedWidth = -1
        self.savedHeight = -1
        self.lastException = None

    def _expose (self, widget, event):
        ctxt = widget.window.cairo_create()
    
        # set a clip region for the expose event
        ctxt.rectangle (event.area.x, event.area.y,
                        event.area.width, event.area.height)
        ctxt.clip()

        w, h = self.allocation.width, self.allocation.height

        try:
            if w != self.savedWidth or h != self.savedHeight:
                (minw, minh) = self._painter.getMinimumSize (ctxt, self.omegaStyle)

                if w < minw or h < minh:
                    print 'Unable to paint: actual size (%f, %f) smaller than ' \
                          'minimum size (%f, %f)' % (w, h, minw, minh)
                    return False
            
                self._painter.configurePainting (ctxt, self.omegaStyle, w, h)
                self.savedWidth = w
                self.savedHeight = h

            self.bag.startFlushing (self.sources)
            self._painter.paint (ctxt, self.omegaStyle, True)

            while self.bag.startNewRound ():
                self._painter.paint (ctxt, self.omegaStyle, False)
        except:
            self.lastException = sys.exc_info ()
        
        return False

    def setPainter (self, p):
        if not isinstance (p, Painter): raise Exception ('Not a Painter: %s' % p)
        self._painter = p or NullPainter ()
        self.lastException = None
        self.forceReconfigure ()

    def forceReconfigure (self):
        self.savedWidth = self.savedHeight = -1
        
class GtkOmegaDemo (object):
    def __init__ (self, bag, style, sources):
        self.win = None
        self.oa = None
        self.sources = sources
        self.bag = bag
        self.style = style
        self.paintId = -1
        gtkThread.send (self._initWindow)
        self.autoRepaint = True

    paintInterval = 500 # milliseconds
    autoReconfigure = True # Reconfigure every repaint?
    
    def _initWindow (self):
        self.win = gtk.Window ()
        self.win.set_title ('OmegaPlot Test Window Canvas')
        self.win.set_default_size (640, 480)
        self.win.set_border_width (4)
        
        # We only hold a weak reference to 'self' here, so that 'del
        # [instance-of-gtkOmegaDemo]' will actually destroy the object
        # (and hence the window), which is a functionality that I
        # really want, for no particular reason. If we pass a
        # reference to an instance function, the reference to 'self'
        # is tracked by python/pygtk, preventing 'del [i-o-gOD]' from
        # removing the final reference to the instance, so that
        # __del__ isn't called.

        import weakref
        sref = weakref.ref (self)

        def clear (obj):
            instance = sref ()
            
            if instance != None:
                instance.win = instance.oa = None
                
        self.win.connect ('destroy', clear)
        
        self.oa = OmegaArea (self.bag, self.style, self.sources)
        self.win.add (self.oa)

        self.win.show_all ()

    def get_autoRepaint (self):
        return self.paintId >= 0

    def set_autoRepaint (self, value):
        if not value ^ (self.paintId >= 0): return #noop?

        if not value:
            # disabling?
            gobject.source_remove (self.paintId)
            self.paintId = -1
            return
        
        # enabling. Same idea as _initWindow
        import weakref
        sref = weakref.ref (self)

        def repaint ():
            instance = sref ()

            # Owner was destroyed; terminate timeout.
            if not instance: return False
                
            # Owner still going strong
            if instance.oa:
                if instance.oa.lastException:
                    # oops we blew up
                    from traceback import print_exception
                    print_exception (*instance.oa.lastException)
                    print 'Painting failed. Disabling automatic repainting.'
                    instance.oa.lastException = None
                    self.paintId = -1
                    return False

                if instance.autoReconfigure:
                    instance.oa.forceReconfigure ()
                
                instance.oa.queue_draw ()
            return True
                
        self.paintId = gobject.timeout_add (self.paintInterval, \
                                            repaint)

    autoRepaint = property (get_autoRepaint, set_autoRepaint)

    def setPainter (self, p):
        def doit ():
            if self.oa: self.oa.setPainter (p)
        gtkThread.send (doit)

    def reconfigure (self):
        def doit ():
            if self.oa: self.oa.forceReconfigure ()
        gtkThread.send (doit)
        
    def __del__ (self):
        if gobject and self.paintId >= 0:
            gobject.source_remove (self.paintId)
            self.paintId = -1

        if self.win == None: return
        if gtkThread == None: return # this can get GC'd before us!

        # The user may destroy the window via the WM
        # and then delete this object before the clear()
        # function has had a chance to run ...

        def doit ():
            if self.win != None:
                self.win.destroy ()
            
        gtkThread.send (doit)

class LinearAxis (object):
    """A class that defines a linear axis for a rectangular plot. Note
    that this class does not paint the axis; it just maps values from
    the bounds to a [0, 1] range so that the RectPlot class knows
    where to locate points."""
    
    def __init__ (self):
        self.min = 0. # XXX should be a bagprop!
        self.max = 10. # XXX should be a bagprop!

    def transform (self, value):
        """Return where the given value should reside on this axis, 0
        indicating all the way towards the physical minimum of the
        plotting area, 1 indicating all the way to the maximum."""

        return (value - self.min) / (self.max - self.min)

    def inbounds (self, value):
        """Return True if the given value is within the bounds of this axis."""
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
    numFormat = '%lg' # can be a function mapping float -> str
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

class FuncSource (object):
    def __init__ (self):
        self.xmin = 0. # XXX bagprop, should support multi-dim
        self.xmax = 10.
        self.npts = 300
        self.func = self.demofunc

    import math
    
    def demofunc (self, x):
        return FuncSource.math.sin(x) + 1.

    class pointiter:
        def __init__ (self, owner):
            self.val = owner.xmin
            self.bound = owner.xmax
            self.func = owner.func
            self.inc = (owner.xmax - owner.xmin) / owner.npts

        def __iter__ (self): return self

        def next (self):
            if self.val > self.bound: raise StopIteration ()

            try:
                r = (self.val, self.func (self.val))
            except:
                r = (self.val, 0.0) # XXX FIXME ugggh
            
            self.val += self.inc
            return r
        
    class chunkiter:
        def __init__ (self, owner):
            self.owner = owner

        def __iter__ (self): return self

        def next (self):
            if not self.owner: raise StopIteration ()
            r = FuncSource.pointiter (self.owner)
            self.owner = None
            return r
    
    def __iter__ (self): return FuncSource.chunkiter (self)

class Bag (object):
    def __init__ (self):
        self.sinks = set ()
        self.exposed = {}
        
    def registerSink (self, sink):
        self.sinks.add (sink)

    def exposeSink (self, sink, name):
        self.registerSink (sink)
        self.exposed[name] = sink

    def getChunk (self, sink):
        chunk = self.currentRound.get (sink)

        if chunk: return chunk

        raise Exception ('uh oh now what')

    def startFlushing (self, sources):
        self.currentIters = {}
        
        for (name, sink) in self.exposed.iteritems ():
            if name not in sources: raise Exception ('No such source %s!' % (name))

            self.currentIters[sink] = sources[name].__iter__ ()

        
    def startNewRound (self):
        self.currentRound = {}
        gotany = False
        
        for (sink, iter) in self.currentIters.iteritems ():
            try:
                chunk = iter.next ()
                self.currentRound[sink] = chunk
                gotany = True
            except StopIteration:
                self.currentRound[sink] = None

        return gotany
    
    def push (self, sources, *args):
        if len (sources) < len (self.exposed):
            raise Exception ('Not enough sources for all exposed sinks!')
        
        for sink in self.sinks:
            if hasattr (sink, 'streamBegin'): sink.streamBegin (*args)

        for (name, sink) in self.exposed.iteritems ():
            if name not in sources: raise Exception ('No such source %s!' % (name))

            source = sources[name]

            for chunk in source:
                sink.acceptChunk (chunk, *args)

        for sink in self.sinks:
            if hasattr (sink, 'streamEnd'): sink.streamEnd (*args)
        
class Painter (object):
    def __init__ (self):
        self.matrix = None

    def getMinimumSize (self, ctxt, style):
        #"""Should be a function of the style only."""
        # I feel like the above should be true, but we at least
        # need ctxt for measuring text, unless another way is found.
        return 0, 0

    def configurePainting (self, ctxt, style, w, h):
        self.matrix = ctxt.get_matrix ()
        self.width = w
        self.height = h

    def paint (self, ctxt, style, firstPaint):
        ctxt.save ()
        ctxt.set_matrix (self.matrix)
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

class NullPainter (Painter):
    def getMinimumSize (self, ctxt, style):
        return 0, 0

    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return
        
        ctxt.move_to (0, 0)
        ctxt.line_to (self.width, self.height)
        ctxt.stroke ()
        ctxt.move_to (0, self.height)
        ctxt.line_to (self.width, 0)
        ctxt.stroke ()

class Overlay (Painter):
    """An overlay in which multiple painters can be stacked in one
    box, with an optional border area."""

    def __init__ (self):
        Painter.__init__ (self)
        self.painters = []

    hBorderSize = 4 # in style.smallScale
    vBorderSize = 4 # in style.smallScale
    bgStyle = None # style ref
    
    def getMinimumSize (self, ctxt, style):
        w, h = 0, 0

        for p in self.painters:
            childw, childh = p.getMinimumSize (ctxt, style)
            w = max (w, childw)
            h = max (h, childh)

        return w + 2 * self.hBorderSize * style.smallScale, \
               h + 2 * self.vBorderSize * style.smallScale

    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)
        
        hreal = self.hBorderSize * style.smallScale
        vreal = self.vBorderSize * style.smallScale

        childw = w - 2 * hreal
        childh = h - 2 * vreal
        
        ctxt.save ()
        ctxt.translate (hreal, vreal)

        for p in self.painters:
            p.configurePainting (ctxt, style, childw, childh)

        ctxt.restore ()
        
    def doPaint (self, ctxt, style, firstPaint):
        if firstPaint and self.bgStyle:
            ctxt.save ()
            style.apply (ctxt, self.bgStyle)
            ctxt.rectangle (0, 0, self.width, self.height)
            ctxt.fill ()
            ctxt.restore ()
            
        for p in self.painters:
            p.paint (ctxt, style, firstPaint)

    def addPainter (self, p):
        self.painters.append (p)

    def removePainter (self, p):
        self.painters.remove (p)

class Grid (Painter):
    def __init__ (self, nw, nh):
        Painter.__init__ (self)
        self.nw = int (nw)
        self.nh = int (nh)
        self._elements = [None] * nw * nh
        
        for i in xrange (0, self.nw):
            for j in xrange (0, self.nh):
                self[i,j] = NullPainter ()

    # FIXME: when these are changed, need to indicate
    # that a reconfigure is necessary.
    hBorderSize = 2 # size of horz. border in style.smallScale
    vBorderSize = 2 # as above for vertical border
    hPadSize = 1 # size of interior horz. padding in style.smallScale
    vPadSize = 1 # as above for interior vertical padding
    
    def _mapIndex (self, idx):
        try:
            asint = int (idx)
            if self.nw == 1: idx = [0, asint]
            elif self.nh == 1: idx = [asint, 0]
        except TypeError:
            idx = list (idx)

        if len (idx) != 2:
            raise IndexError ('Bad Grid index: %s' % idx)
        if idx[0] >= self.nw:
            raise IndexError ('Grid index width out of bounds')
        if idx[1] >= self.nh:
            raise IndexError ('Grid index width out of bounds')
        
        return idx[0] * self.nh + idx[1]

    def __getitem__ (self, idx):
        return self._elements[self._mapIndex (idx)]

    def __setitem__ (self, idx, value):
        self._elements[self._mapIndex (idx)] = value

    def getMinimumSize (self, ctxt, style):
        minw = 2 * self.hBorderSize * style.smallScale
        minh = 2 * self.vBorderSize * style.smallScale

        minw += (self.nw - 1) * self.hPadSize * style.smallScale
        minh += (self.nh - 1) * self.vPadSize * style.smallScale

        dw = dh = 0

        for i in xrange (0, self.nw):
            for j in xrange (0, self.nh):
                childw, childh = self[i,j].getMinimumSize (ctxt, style)
                dw = max (childw, dw)
                dh = max (childh, dh)

        minw += dw * self.nw
        minh += dh * self.nh

        # This code calculates for a nonuniform grid:
        #dhs = [0] * self.nh
        #
        #for i in xrange (0, nw):
        #    dw = 0
        #    
        #    for j in xrange (0, nh):
        #        childw, childh = self[i,j].getMinimumSize (ctxt, style)
        #
        #        dw = max (childw, dw)
        #        dhs[j] = max (childh, dhs[j])
        #
        #    minw += dw
        #
        #for j in xrange (0, nh): minh += dhs[j]

        return minw, minh

    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        hBorderReal = self.hBorderSize * style.smallScale
        vBorderReal = self.vBorderSize * style.smallScale
        hPadReal = self.hPadSize * style.smallScale
        vPadReal = self.vPadSize * style.smallScale
        
        childw = w - 2 * hBorderReal
        childh = h - 2 * vBorderReal
        childw -= (self.nw - 1) * hPadReal
        childh -= (self.nh - 1) * vPadReal
        
        childw /= self.nw
        childh /= self.nh

        ctxt.save ()
        ctxt.translate (hBorderReal, vBorderReal)
        
        for i in xrange (0, self.nw):
            for j in xrange (0, self.nh):
                dx = i * (childw + hPadReal)
                dy = j * (childh + vPadReal)

                ctxt.translate (dx, dy)
                self[i,j].configurePainting (ctxt, style, childw, childh)
                ctxt.translate (-dx, -dy)

    def doPaint (self, ctxt, style, firstPaint):
        for i in xrange (0, self.nw):
            for j in xrange (0, self.nh):
                self[i,j].paint (ctxt, style, firstPaint)
    
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
        self.fpainters.append (fp)

        if not self.defaultXAxis and isinstance (fp, RectDataPainter):
            self.defaultXAxis = fp.xaxis
            self.defaultYAxis = fp.yaxis

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
            
        for fp in self.fpainters:
            fp.paint (ctxt, style, firstPaint)
        
class RectDataPainter (StreamSink):
    sinkSpec = 'FF' # FIXME

    def __init__ (self, bag):
        StreamSink.__init__ (self, bag)
        
        self.xaxis = LinearAxis ()
        self.yaxis = LinearAxis ()
        self.lines = True # XXX
        self.pointPainter = None # XXX

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
        
        if self.lastx == None:
            try:
                self.lastx, self.lasty = self.transform (chunk.next ())
                if self.pointPainter: points.append ((self.lastx, self.lasty))
            except StopIteration:
                return

        ctxt.move_to (self.lastx, self.lasty)
        
        for pair in chunk:
            x, y = self.transform (pair)
            ctxt.line_to (x, y)
            if self.pointPainter: points.append ((x, y))

        self.lastx, self.lasty = ctxt.get_current_point ()
        ctxt.stroke ()

        if self.pointPainter:
            for (x, y) in points: self.pointPainter.paint (ctxt, style, x, y, ())
        
class TestStyle (object):
    smallScale = 2
    largeScale = 5

    def apply (self, ctxt, style):
        if not style: return

        if hasattr (style, 'apply'):
            style.apply (ctxt)
            return

        if callable (style):
            style (ctxt)
            return

        if isinstance (style, basestring):
            fn = 'apply_' + style

            if hasattr (self, fn):
                getattr (self, fn)(ctxt)
                return

        raise Exception ('Dont know what to do with style item %s' % style)

    def apply_bgLinework (self, ctxt):
        ctxt.set_line_width (1)
        ctxt.set_source_rgb (0.3, 0.3, 0.3) # do rgba?

    def apply_bgFill (self, ctxt):
        ctxt.set_source_rgb (1, 1, 1)

class PointPainter (object):
    sinkSpec = ''

    def paint (self, ctxt, style, x, y, data):
        ctxt.save ()
        self.doPaint (ctxt, style, x, y, data)
        ctxt.restore ()

class DotPainter (PointPainter):
    size = 2 # in style.smallScale

    def doPaint (self, ctxt, style, x, y, data):
        ctxt.arc (x, y, self.size * style.smallScale, 0, 2 * math.pi)
        ctxt.fill ()

