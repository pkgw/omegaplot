from math import pi
from base import Painter, NullPainter

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
        p.setParent (self)
        self.painters.append (p)

    def removeChild (self, p):
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
        midx = self._mapIndex (idx)
        prev = self._elements[midx]
        
        if prev is value: return

        # This will recurse to our own removeChild
        if prev: prev.setParent (None)

        # Do this before modifying self._elements, so that
        # if value is already in _elements and is being
        # moved to an earlier position, removeChild doesn't
        # remove the wrong entry.
        
        if value: value.setParent (self)
        
        self._elements[midx] = value

    def removeChild (self, child):
        midx = self._elements.index (child)
        self._elements[midx] = NullPainter ()
        self._elements[midx].setParent (self)
        
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
    
class RightRotationPainter (Painter):
    ROT_NONE = 0
    ROT_CW90 = 1
    ROT_180 = 2
    ROT_CCW90 = 3

    rotation = 0
    
    def __init__ (self, child):
        Painter.__init__ (self)
        self.child = None
        self.setChild (child)

    def setChild (self, child):
        if self.child:
            self.child.setParent (None)

        if child:
            child.setParent (self)
            self.child = child

    def removeChild (self, child):
        self.child = None
    
    def setRotation (self, value):
        self.rotation = value
        
    def getMinimumSize (self, ctxt, style):
        w, h = self.child.getMinimumSize (ctxt, style)

        if self.rotation % 2 == 1:
            return h, w
        return w, h

    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        if not self.child: return

        if self.rotation == self.ROT_CW90:
            ctxt.rotate (pi / 2)
            ctxt.translate (0, -w)
        elif self.rotation == self.ROT_180:
            ctxt.rotate (pi)
            ctxt.translate (-h, -w)
        elif self.rotation == self.ROT_CCW90:
            ctxt.rotate (-pi / 2)
            ctxt.translate (-h, 0)

        if self.rotation % 2 == 1:
            self.child.configurePainting (ctxt, style, h, w)
        else:
            self.child.configurePainting (ctxt, style, w, h)
        
    def doPaint (self, ctxt, style, firstPaint):
        self.child.paint (ctxt, style, firstPaint)


