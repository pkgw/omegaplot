from math import pi
from base import Painter, NullPainter
import numpy as N


class Overlay (Painter):
    """An overlay in which multiple painters can be stacked in one
    box, with an optional border area."""

    def __init__ (self):
        super (Overlay, self).__init__ ()
        self.painters = []

    hBorderSize = 4 # in style.smallScale
    vBorderSize = 4 # in style.smallScale
    bgStyle = None # style ref

    def getMinimumSize (self, ctxt, style):
        sz = N.zeros (6)

        for p in self.painters:
            sz = N.maximum (sz, p.getMinimumSize (ctxt, style))

        sz[3:6:2] += self.hBorderSize * style.smallScale
        sz[2:6:2] += self.vBorderSize * style.smallScale

        return sz

    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (Overlay, self).configurePainting (ctxt, style, w, h, bt, br, bb, bl)

        bh = self.hBorderSize * style.smallScale
        bv = self.vBorderSize * style.smallScale

        ctxt.save ()
        ctxt.translate (bh, bv)

        for p in self.painters:
            p.configurePainting (ctxt, style, w, h, bt - bv, br - bh, bb - bv, bl - bh)

        ctxt.restore ()
        
    def doPaint (self, ctxt, style):
        if self.bgStyle:
            ctxt.save ()
            style.apply (ctxt, self.bgStyle)
            ctxt.rectangle (0, 0, self.fullw, self.fullh)
            ctxt.fill ()
            ctxt.restore ()
            
        for p in self.painters:
            p.paint (ctxt, style)

    def addPainter (self, p):
        p.setParent (self)
        self.painters.append (p)

    def _lostChild (self, p):
        self.painters.remove (p)


class Grid (Painter):
    def __init__ (self, nw, nh):
        super (Grid, self).__init__ ()
        self.nw = int (nw)
        self.nh = int (nh)
        self._elements = N.empty ((nh, nw), N.object)
        
        for r in xrange (self.nh):
            for c in xrange (self.nw):
                self[r,c] = NullPainter ()
                self[r,c].setParent (self)


    # FIXME: when these are changed, need to indicate
    # that a reconfigure is necessary.
    hBorderSize = 2 # size of horz. border in style.smallScale
    vBorderSize = 2 # as above for vertical border
    hPadSize = 1 # size of interior horz. padding in style.smallScale
    vPadSize = 1 # as above for interior vertical padding

    
    def _mapIndex (self, idx):
        try:
            asint = int (idx)
            if self.nw == 1: idx = (asint, 0)
            elif self.nh == 1: idx = (0, asint)
        except TypeError:
            pass

        return idx


    def __getitem__ (self, idx):
        return self._elements[self._mapIndex (idx)]


    def __setitem__ (self, idx, value):
        midx = self._mapIndex (idx)
        prev = self._elements[midx]
        
        if prev is value: return

        # HACK: check that 'value' isn't already in us, somewhere.
        # That can cause MultiPager to fall down in a common use-case.
        # This is probably not the best fix for that problem.

        if value is not None and value in self._elements:
            raise ValueError ('Moving child within a grid disallowed. Remove it first.')

        # This will recurse to our own _lostChild
        if prev is not None: prev.setParent (None)

        # Do this before modifying self._elements, so that
        # if value is already in _elements and is being
        # moved to an earlier position, _lostChild doesn't
        # remove the wrong entry.
        
        if value is None: value = NullPainter ()
        value.setParent (self)
        
        self._elements[midx] = value


    def _lostChild (self, child):
        wh = N.where (self._elements == child)
        p = NullPainter ()
        self._elements[wh] = p
        p.setParent (self)


    def getMinimumSize (self, ctxt, style):
        v = N.empty ((self.nh, self.nw, 6))

        for r in xrange (self.nh):
            for c in xrange (self.nw):
                v[r,c] = self._elements[r,c].getMinimumSize (ctxt, style)

        # Simple, totally uniform borders and sizes.
        
        self.maxes = maxes = v.max (0).max (0)
        
        minw = self.nw * maxes[0]
        minw += (self.nw - 1) * (maxes[3] + maxes[5] + self.hPadSize * style.smallScale)
        minh = self.nh * maxes[1]
        minh += (self.nh - 1) * (maxes[2] + maxes[4] + self.vPadSize * style.smallScale)

        hb = self.hBorderSize * style.smallScale
        vb = self.vBorderSize * style.smallScale

        return (minw, minh, maxes[2] + vb, maxes[3] + hb,
                maxes[4] + vb, maxes[5] + hb)


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (Grid, self).configurePainting (ctxt, style, w, h, bt, br, bb, bl)

        hPadReal = self.hPadSize * style.smallScale
        vPadReal = self.vPadSize * style.smallScale
        hb = self.hBorderSize * style.smallScale
        vb = self.vBorderSize * style.smallScale

        bt -= vb
        br -= hb
        bb -= vb
        bl -= hb

        childw = (w - (self.nw - 1) * (hPadReal + bl + br)) / self.nw
        childh = (h - (self.nh - 1) * (vPadReal + bt + bb)) / self.nh

        fullcw = childw + hPadReal + bl + br
        fullch = childh + vPadReal + bt + bb

        ctxt.save ()
        ctxt.translate (hb, vb)
        
        for r in xrange (self.nh):
            for c in xrange (self.nw):
                dx = c * fullcw
                dy = r * fullch

                ctxt.translate (dx, dy)
                self._elements[r,c].configurePainting (ctxt, style, childw, childh,
                                                       bt, br, bb, bl)
                ctxt.translate (-dx, -dy)

        ctxt.restore ()


    def doPaint (self, ctxt, style):
        for r in xrange (self.nh):
            for c in xrange (self.nw):
                self._elements[r,c].paint (ctxt, style)


class RightRotationPainter (Painter):
    ROT_NONE = 0
    ROT_CW90 = 1
    ROT_180 = 2
    ROT_CCW90 = 3

    rotation = 0
    child = None
    
    def __init__ (self, child):
        Painter.__init__ (self)
        self.setChild (child)

    def setChild (self, child):
        if self.child is not None:
            self.child.setParent (None)

        if child is None: child = NullPainter ()
        
        child.setParent (self)
        self.child = child

    def _lostChild (self, child):
        self.child = NullPainter ()
        self.child.setParent (self)
    
    def setRotation (self, value):
        self.rotation = value
        
    def _rotateSize (self, rot, w, h, bt, br, bb, bl):
        if rot == self.ROT_NONE:
            return w, h, bt, br, bb, bl
        elif rot == self.ROT_CW90:
            return h, w, bl, bt, br, bb
        elif rot == self.ROT_180:
            return w, h, bb, bl, bt, br
        elif rot == self.ROT_CCW90:
            return h, w, br, bb, bl, bt
        else:
            raise ValueError ('rot')

    def getMinimumSize (self, ctxt, style):
        sz = self.child.getMinimumSize (ctxt, style)
        return self._rotateSize (self.rotation, *sz)

    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (RightRotationPainter, self).configurePainting (ctxt, style, w, h,
                                                              bt, br, bb, bl)

        ctxt.save ()

        fw, fh = self.fullw, self.fullh

        if self.rotation == self.ROT_CW90:
            ctxt.rotate (pi / 2)
            ctxt.translate (0, -fw)
        elif self.rotation == self.ROT_180:
            ctxt.rotate (pi)
            ctxt.translate (-fw, -fh)
        elif self.rotation == self.ROT_CCW90:
            ctxt.rotate (-pi / 2)
            ctxt.translate (-fh, 0)

        # Reverse the effects of the rotation on the boundaries
        rot = self.rotation
        if rot == self.ROT_CW90:
            rot = self.ROT_CCW90
        elif rot == self.ROT_CCW90:
            rot = self.ROT_CW90
        sz = self._rotateSize (rot, w, h, bt, br, bb, bl)

        self.child.configurePainting (ctxt, style, *sz)

        ctxt.restore ()
        
    def doPaint (self, ctxt, style):
        self.child.paint (ctxt, style)


class LinearBox (Painter):
    # The "major axis" is the direction in which the box extends
    # as children are added, while the "minor axis" is always
    # one painter tall.

    def __init__ (self, size):
        super (LinearBox, self).__init__ ()
        self.size = int (size)

        self._elements = [None] * self.size
        
        for i in xrange (0, self.size):
            np = NullPainter ()
            self._elements[i] = (np, 1.0, 0.0, 0.0, 0.0)
            np.setParent (self)

    # FIXME: when these are changed, need to indicate
    # that a reconfigure is necessary.
    majBorderSize = 2 # size of major axis border in style.smallScale
    minBorderSize = 2 # as above for minor axis border
    padSize = 1 # as above for interior padding along major axis
    
    def __getitem__ (self, idx):
        return self._elements[idx][0]

    def __setitem__ (self, idx, value):
        prevptr, prevwt, prevb1, prevmaj, prevb2 = self._elements[idx]
        
        if prevptr is value: return

        # This will recurse to our own _lostChild
        if prevptr is not None: prevptr.setParent (None)

        # Do this before modifying self._elements, so that
        # if value is already in _elements and is being
        # moved to an earlier position, _lostChild doesn't
        # remove the wrong entry.
        
        if value is None: value = NullPainter ()
        value.setParent (self)
        
        self._elements[idx] = (value, prevwt, prevb1, prevmaj, prevb2)

    def appendChild (self, child, weight=1.0):
        if child is None: child = NullPainter ()
        child.setParent (self)
        
        self._elements.append ((None, weight, 0.0, 0.0, 0.0))
        self.size += 1
        self[self.size - 1] = child
    
    def _lostChild (self, child):
        for i in xrange (0, self.size):
            (ptr, wt, tmp, tmp, tmp) = self._elements[i]

            if ptr is child:
                newptr = NullPainter ()
                self._elements[i] = (newptr, wt, 0.0, 0.0, 0.0)
                newptr.setParent (self)


    def setWeight (self, index, wt):
        (ptr, oldwt, bmaj1, majsz, bmaj2) = self._elements[index]
        self._elements[index] = (ptr, wt, bmaj1, majsz, bmaj2)


    def _getChildMinSize (self, child, ctxt, style):
        raise NotImplementedError ()


    def _boxGetMinimumSize (self, ctxt, style):
        majb = self.majBorderSize * style.smallScale
        minb = self.minBorderSize * style.smallScale

        minmaj = (self.size - 1) * self.padSize * style.smallScale

        maxSPW = 0 # max size per weight
        totwt = 0
        maxbmin1 = maxbmin2 = maxcmin = 0

        for i in xrange (self.size):
            (ptr, wt, tmp, tmp, tmp) = self._elements[i]
            cmaj, cmin, cbmaj1, cbmin1, cbmaj2, cbmin2 = self._getChildMinSize (ptr, ctxt, style)

            # Along the major direction, we don't equalize borders at all, so the
            # effective size of each child includes its borders...
            
            cfull = cbmaj1 + cmaj + cbmaj2
            cbmaj1eff = cbmaj1
            cbmaj2eff = cbmaj2

            # ... except that the borders of the first and last children are
            # incorporated to the borders of the box as a whole.

            if i == 0:
                bmaj1 = cbmaj1
                cfull -= cbmaj1
                cbmaj1eff = 0
            if i == self.size - 1:
                bmaj2 = cbmaj2
                cfull -= cbmaj2
                cbmaj2eff = 0

            maxcmin = max (maxcmin, cmin)
            maxbmin1 = max (maxbmin1, cbmin1)
            maxbmin2 = max (maxbmin2, cbmin2)

            self._elements[i] = (ptr, wt, cbmaj1eff, cmaj, cbmaj2eff)

            if wt == 0:
                minmaj += cfull
            else:
                maxSPW = max (maxSPW, 1. * cfull / wt)
                totwt += wt

            #print i, childh, minh

        minmaj += maxSPW * totwt

        return (minmaj, maxcmin, bmaj1 + majb, maxbmin1 + minb,
                bmaj2 + majb, maxbmin2 + minb)


    def _boxTranslate (self, ctxt, major, minor):
        raise NotImplementedError ()


    def _boxConfigureChild (self, child, ctxt, style, major, minor, bmaj1, bmin1,
                            bmaj2, bmin2):
        raise NotImplementedError ()


    def _boxConfigurePainting (self, ctxt, style, major, minor, bmaj1, bmin1, bmaj2, bmin2):
        bmaj = self.majBorderSize * style.smallScale
        bmin = self.minBorderSize * style.smallScale
        pad = self.padSize * style.smallScale

        # Compensate for our whitespace border.
        bmin1 -= bmin
        bmin2 -= bmin

        # How much major-axis space do we have to allocate for the
        # painters that have nonzero weights? It's the total major
        # axis space including borders except for our whitespace
        # border, minus the internal padding, minus the size of the
        # painters with zero weights.

        majspace = major - (self.size - 1) * pad + bmaj1 + bmaj2 - 2 * bmaj
        totwt = 0.0
        
        for i in xrange (self.size):
            e = self._elements[i]
            wt = e[1]
            totwt += wt

            if wt == 0:
                majspace -= e[2] + e[3] + e[4]

        # Allocate space to the painters

        ctxt.save ()
        self._boxTranslate (ctxt, bmaj, bmin)
        
        for i in xrange (self.size):
            ptr, wt, cbmaj1, cmaj, cbmaj2 = self._elements[i]

            if wt == 0:
                cfullmaj = cbmaj1 + cmaj + cbmaj2
            else:
                if totwt > 0:
                    cfullmaj = majspace * wt / totwt
                else:
                    cfullmaj = 0
            
                cfullmaj = max (cfullmaj, cbmaj1 + cmaj + cbmaj2)
                assert cfullmaj <= majspace, 'Not enough room in vbox!'

            if i == 0:
                cbmaj1 = bmaj1 - bmaj
            if i == self.size - 1:
                cbmaj2 = bmaj2 - bmaj

            cmaj = cfullmaj - cbmaj1 - cbmaj2

            self._boxConfigureChild (ptr, ctxt, style, cmaj, minor,
                                     cbmaj1, bmin1, cbmaj2, bmin2)
            self._boxTranslate (ctxt, cfullmaj + pad, 0)

            if wt != 0:
                majspace -= cfullmaj
                totwt -= wt

        ctxt.restore ()

    def doPaint (self, ctxt, style):
        for i in xrange (self.size):
            self._elements[i][0].paint (ctxt, style)


class VBox (LinearBox):
    def _setHBorderSize (self, val):
        self.minBorderSize = val

    def _getHBorderSize (self):
        return self.minBorderSize

    hBorderSize = property (_getHBorderSize, _setHBorderSize)


    def _setVBorderSize (self, val):
        self.majBorderSize = val

    def _getVBorderSize (self):
        return self.majBorderSize

    vBorderSize = property (_getVBorderSize, _setVBorderSize)


    def _getChildMinSize (self, child, ctxt, style):
        t = child.getMinimumSize (ctxt, style)
        return t[1], t[0], t[2], t[3], t[4], t[5]


    def getMinimumSize (self, ctxt, style):
        t = self._boxGetMinimumSize (ctxt, style)
        return t[1], t[0], t[2], t[3], t[4], t[5]


    def _boxTranslate (self, ctxt, major, minor):
        ctxt.translate (minor, major)


    def _boxConfigureChild (self, child, ctxt, style, major, minor, bmaj1, bmin1,
                            bmaj2, bmin2):
        child.configurePainting (ctxt, style, minor, major, bmaj1, bmin1, bmaj2, bmin2)


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (VBox, self).configurePainting (ctxt, style, w, h, bt, br, bb, bl)
        self._boxConfigurePainting (ctxt, style, h, w, bt, br, bb, bl)


class HBox (LinearBox):
    def _setHBorderSize (self, val):
        self.majBorderSize = val

    def _getHBorderSize (self):
        return self.majBorderSize

    hBorderSize = property (_getHBorderSize, _setHBorderSize)


    def _setVBorderSize (self, val):
        self.minBorderSize = val

    def _getVBorderSize (self):
        return self.minBorderSize

    vBorderSize = property (_getVBorderSize, _setVBorderSize)


    def _getChildMinSize (self, child, ctxt, style):
        t = child.getMinimumSize (ctxt, style)
        return t[0], t[1], t[5], t[2], t[3], t[4]


    def _boxTranslate (self, ctxt, major, minor):
        ctxt.translate (major, minor)


    def getMinimumSize (self, ctxt, style):
        t = self._boxGetMinimumSize (ctxt, style)
        return t[0], t[1], t[3], t[4], t[5], t[2]


    def _boxConfigureChild (self, child, ctxt, style, major, minor, bmaj1, bmin1,
                            bmaj2, bmin2):
        child.configurePainting (ctxt, style, major, minor, bmin1, bmaj2, bmin2, bmaj1)


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (HBox, self).configurePainting (ctxt, style, w, h, bt, br, bb, bl)
        self._boxConfigurePainting (ctxt, style, w, h, bl, bt, br, bb)
