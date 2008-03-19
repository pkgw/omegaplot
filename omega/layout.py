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
        
    def doPaint (self, ctxt, style):
        if self.bgStyle:
            ctxt.save ()
            style.apply (ctxt, self.bgStyle)
            ctxt.rectangle (0, 0, self.width, self.height)
            ctxt.fill ()
            ctxt.restore ()
            
        for p in self.painters:
            p.paint (ctxt, style)

    def add (self, p):
        if p is None:
            return
        
        self.painters.append (p)

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

        if value is None: value = NullPainter ()
        
        self._elements[midx] = value

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

        ctxt.restore ()

    def doPaint (self, ctxt, style):
        for i in xrange (0, self.nw):
            for j in xrange (0, self.nh):
                self[i,j].paint (ctxt, style)
    
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
        if child is None: child = NullPainter ()
        self.child = child

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

        ctxt.save ()
        
        if self.rotation == self.ROT_CW90:
            ctxt.rotate (pi / 2)
            ctxt.translate (0, -w)
        elif self.rotation == self.ROT_180:
            ctxt.rotate (pi)
            ctxt.translate (-w, -h)
        elif self.rotation == self.ROT_CCW90:
            ctxt.rotate (-pi / 2)
            ctxt.translate (-h, 0)

        if self.rotation % 2 == 1:
            self.child.configurePainting (ctxt, style, h, w)
        else:
            self.child.configurePainting (ctxt, style, w, h)

        ctxt.restore ()
        
    def doPaint (self, ctxt, style):
        self.child.paint (ctxt, style)

class VBox (Painter):
    def __init__ (self, size):
        Painter.__init__ (self)
        self.size = int (size)

        self._elements = [None] * self.size
        
        for i in xrange (0, self.size):
            self._elements[i] = (NullPainter (), 1.0, 0.0)

    # FIXME: when these are changed, need to indicate
    # that a reconfigure is necessary.
    hBorderSize = 2 # size of horz. border in style.smallScale
    vBorderSize = 2 # as above for vertical border
    padSize = 1 # as above for interior vertical padding
    
    def __getitem__ (self, idx):
        return self._elements[idx][0]

    def __setitem__ (self, idx, value):
        prevptr, prevwt, prevmin = self._elements[idx]
        
        if prevptr is value: return

        if value is None: value = NullPainter ()
        
        self._elements[idx] = (value, prevwt, prevmin)

    def appendChild (self, child):
        if child is None: child = NullPainter ()
        
        self._elements.append ((child, 1.0, 0.0))
        self.size += 1
    
    def setWeight (self, index, wt):
        (ptr, oldwt, minh) = self._elements[index]
        self._elements[index] = (ptr, wt, minh)
    
    def getMinimumSize (self, ctxt, style):
        minw = 2 * self.hBorderSize * style.smallScale
        minh = 2 * self.vBorderSize * style.smallScale

        minh += (self.size - 1) * self.padSize * style.smallScale

        dw = 0

        for i in xrange (0, self.size):
            (ptr, wt, oldminh) = self._elements[i]
            childw, childh = ptr.getMinimumSize (ctxt, style)
            self._elements[i] = (ptr, wt, childh)
            
            dw = max (childw, dw)
            minh += childh
            #print i, childh, minh

        minw += dw
        
        return minw, minh

    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        hBorderReal = self.hBorderSize * style.smallScale
        vBorderReal = self.vBorderSize * style.smallScale
        padReal = self.padSize * style.smallScale
        
        childw = w - 2 * hBorderReal

        hspace = h - 2 * vBorderReal
        hspace -= (self.size - 1) * padReal

        totwt = 0.0
        
        for i in xrange (0, self.size): 
            totwt += self._elements[i][1]
            
        ctxt.save ()
        ctxt.translate (hBorderReal, vBorderReal)
        
        for i in xrange (0, self.size):
            ptr, wt, minh = self._elements[i]

            if totwt > 0:
                childh = hspace * wt / totwt
            else:
                childh = 0
            
            if childh < minh: childh = minh
            
            ptr.configurePainting (ctxt, style, childw, childh)
            
            ctxt.translate (0, childh + padReal)

            hspace -= childh + padReal
            totwt -= wt

        ctxt.restore ()

    def doPaint (self, ctxt, style):
        for i in xrange (0, self.size):
            self._elements[i][0].paint (ctxt, style)
