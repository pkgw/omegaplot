# Copyright 2011, 2012 Peter Williams
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

from base import LayoutInfo, Painter, NullPainter
from util import expandAspect, shrinkAspect, nudgeMargins
import numpy as np


class Overlay (Painter):
    """An overlay in which multiple painters can be stacked in one
    box, with an optional border area."""

    def __init__ (self):
        super (Overlay, self).__init__ ()
        self.painters = []

    hBorderSize = 4 # in style.smallScale
    vBorderSize = 4 # in style.smallScale
    bgStyle = None # style ref

    def getLayoutInfo (self, ctxt, style):
        sz = np.zeros (6)
        aspect = None

        for p in self.painters:
            li = p.getLayoutInfo (ctxt, style)
            sz = np.maximum (sz, li.asBoxInfo ())

            if aspect is None:
                aspect = li.aspect
            elif li.aspect is not None and li.aspect != aspect:
                raise RuntimeError ('cannot overlay painters with disageeing aspect '
                                    'ratios (%f, %f)' % (aspect, li.aspect))

        sz[:2] = expandAspect (aspect, *sz[:2])
        sz[3:6:2] += self.hBorderSize * style.smallScale
        sz[2:6:2] += self.vBorderSize * style.smallScale

        return LayoutInfo (minsize=sz[:2], minborders=sz[2:], aspect=li.aspect)

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
        self._elements = np.empty ((nh, nw), np.object)

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
        wh = np.where (self._elements == child)
        p = NullPainter ()
        self._elements[wh] = p
        p.setParent (self)


    def getLayoutInfo (self, ctxt, style):
        v = np.empty ((self.nh, self.nw, 6))
        aspect = None

        for r in xrange (self.nh):
            for c in xrange (self.nw):
                li = self._elements[r,c].getLayoutInfo (ctxt, style)
                v[r,c] = li.asBoxInfo ()

                if aspect is None:
                    aspect = li.aspect
                elif li.aspect is not None and li.aspect != aspect:
                    raise RuntimeError ('cannot grid painters with disagreeing aspect '
                                        'ratios (%f, %f)' % (aspect, li.aspect))

        # Simple, totally uniform borders and sizes.

        self.maxes = maxes = v.max (0).max (0)
        self._childaspect = aspect
        maxes[:2] = expandAspect (aspect, *maxes[:2])

        minw = self.nw * maxes[0]
        minw += (self.nw - 1) * (maxes[3] + maxes[5] + self.hPadSize * style.smallScale)
        minh = self.nh * maxes[1]
        minh += (self.nh - 1) * (maxes[2] + maxes[4] + self.vPadSize * style.smallScale)

        hb = self.hBorderSize * style.smallScale
        vb = self.vBorderSize * style.smallScale

        return LayoutInfo (minsize=(minw, minh),
                           minborders=(maxes[2] + vb, maxes[3] + hb,
                                       maxes[4] + vb, maxes[5] + hb))


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (Grid, self).configurePainting (ctxt, style, w, h, bt, br, bb, bl)

        hPadReal = self.hPadSize * style.smallScale
        vPadReal = self.vPadSize * style.smallScale
        hb = self.hBorderSize * style.smallScale
        vb = self.vBorderSize * style.smallScale

        # Figure out borders and such. Children get shrunk to provide
        # the right aspect ratio, with extra space redistributed into
        # their margins. All the while we account for our extra border
        # around the whole thing.

        bt -= vb
        br -= hb
        bb -= vb
        bl -= hb

        childw = (w - (self.nw - 1) * (hPadReal + bl + br)) / self.nw
        childh = (h - (self.nh - 1) * (vPadReal + bt + bb)) / self.nh
        childw, childh = shrinkAspect (self._childaspect, childw, childh)

        if self.nw == 1:
            bhextra = w - childw
        else:
            bhextra = (w - self.nw * childw) / (self.nw - 1) - (hPadReal + bl + br)
            bhextra /= self.nw

        if self.nh == 1:
            bvextra = h - childh
        else:
            bvextra = (h - self.nh * childh) / (self.nh - 1) - (vPadReal + bt + bb)
            bvextra /= self.nw

        bt, br, bb, bl = nudgeMargins ((bt + 0.5 * bvextra, br + 0.5 * bhextra,
                                        bb + 0.5 * bvextra, bl + 0.5 * bhextra),
                                       self.maxes[2:])

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

    def getLayoutInfo (self, ctxt, style):
        li = self.child.getLayoutInfo (ctxt, style)
        sz = self._rotateSize (self.rotation, *li.asBoxInfo ())

        if li.aspect is None:
            aspect = None
        elif self.rotation in (self.ROT_NONE, self.ROT_180):
            aspect = li.aspect
        else:
            aspect = 1. / li.aspect

        minsize = expandAspect (aspect, *sz[:2])

        return LayoutInfo (minsize=minsize, minborders=sz[2:], aspect=aspect)

    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (RightRotationPainter, self).configurePainting (ctxt, style, w, h,
                                                              bt, br, bb, bl)

        ctxt.save ()

        # TODO: we should do the best we can to give our child the
        # aspect ratio it wants, if it wants one.

        fw, fh = self.fullw, self.fullh

        if self.rotation == self.ROT_CW90:
            ctxt.rotate (np.pi / 2)
            ctxt.translate (0, -fw)
        elif self.rotation == self.ROT_180:
            ctxt.rotate (np.pi)
            ctxt.translate (-fw, -fh)
        elif self.rotation == self.ROT_CCW90:
            ctxt.rotate (-np.pi / 2)
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
            self._elements[i] = (np, 1.0, 0.0, 0.0, 0.0, None)
            np.setParent (self)

    # FIXME: when these are changed, need to indicate
    # that a reconfigure is necessary.
    majBorderSize = 2 # size of major axis border in style.smallScale
    minBorderSize = 2 # as above for minor axis border
    padSize = 1 # as above for interior padding along major axis

    def __getitem__ (self, idx):
        return self._elements[idx][0]

    def __setitem__ (self, idx, value):
        prevptr, prevwt, prevb1, prevmaj, prevb2, prevaspect = self._elements[idx]

        if prevptr is value:
            return

        # This will recurse to our own _lostChild
        if prevptr is not None:
            prevptr.setParent (None)

        # Do this before modifying self._elements, so that
        # if value is already in _elements and is being
        # moved to an earlier position, _lostChild doesn't
        # remove the wrong entry.

        if value is None:
            value = NullPainter ()
        value.setParent (self)

        self._elements[idx] = (value, prevwt, prevb1, prevmaj, prevb2, prevaspect)

    def appendChild (self, child, weight=1.0):
        if child is None:
            child = NullPainter ()
        child.setParent (self)

        self._elements.append ((None, weight, 0.0, 0.0, 0.0, None))
        self.size += 1
        self[self.size - 1] = child

    def _lostChild (self, child):
        for i in xrange (0, self.size):
            ptr, wt, tmp, tmp, tmp, tmp = self._elements[i]

            if ptr is child:
                newptr = NullPainter ()
                self._elements[i] = (newptr, wt, 0.0, 0.0, 0.0, None)
                newptr.setParent (self)


    def setWeight (self, index, wt):
        ptr, oldwt, bmaj1, majsz, bmaj2, aspect = self._elements[index]
        self._elements[index] = ptr, wt, bmaj1, majsz, bmaj2, aspect


    def _getChildMinSize (self, child, ctxt, style):
        raise NotImplementedError ()


    def _boxGetLayoutInfo (self, ctxt, style):
        majb = self.majBorderSize * style.smallScale
        minb = self.minBorderSize * style.smallScale

        minmaj = (self.size - 1) * self.padSize * style.smallScale

        maxSPW = 0 # max size per weight
        totwt = 0
        maxbmin1 = maxbmin2 = maxcmin = 0

        for i in xrange (self.size):
            ptr, wt, tmp, tmp, tmp, tmp = self._elements[i]
            cmaj, cmin, cbmaj1, cbmin1, cbmaj2, cbmin2, caspect = \
                self._getChildMinSize (ptr, ctxt, style)

            cmaj, cmin = expandAspect (caspect, cmaj, cmin)

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

            self._elements[i] = (ptr, wt, cbmaj1eff, cmaj, cbmaj2eff, caspect)

            if wt == 0:
                minmaj += cfull
            else:
                maxSPW = max (maxSPW, 1. * cfull / wt)
                totwt += wt

            #print i, childh, minh

        minmaj += maxSPW * totwt

        return LayoutInfo (minsize=(minmaj, maxcmin),
                           minborders=(bmaj1 + majb, maxbmin1 + minb,
                                       bmaj2 + majb, maxbmin2 + minb))


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
            ptr, wt, cbmaj1, cmaj, cbmaj2, caspect = self._elements[i]

            if wt == 0:
                cfullmaj = cbmaj1 + cmaj + cbmaj2
            else:
                if totwt > 0:
                    cfullmaj = majspace * wt / totwt
                else:
                    cfullmaj = 0

                cfullmaj = max (cfullmaj, cbmaj1 + cmaj + cbmaj2)
                assert cfullmaj <= majspace, 'Not enough room in linear box!'

            if i == 0:
                cbmaj1 = bmaj1 - bmaj
            if i == self.size - 1:
                cbmaj2 = bmaj2 - bmaj

            cmaj = cfullmaj - cbmaj1 - cbmaj2
            cmin, cbmin1, cbmin2 = minor, bmin1, bmin2

            if caspect is not None:
                delta = cmaj - caspect * minor

                if delta > 0:
                    # FIXME: this can be uneven or possibly break minimum sizing
                    cmaj -= delta
                    cbmaj1 += 0.5 * delta
                    cbmaj2 += 0.5 * delta
                elif delta < 0:
                    # This is going to look gross but we need to try as hard as
                    # we can to honor aspect ratios
                    delta = minor - cmaj / caspect
                    cmin -= delta
                    cbmin1 += 0.5 * delta
                    cbmin2 += 0.5 * delta

            self._boxConfigureChild (ptr, ctxt, style, cmaj, cmin,
                                     cbmaj1, cbmin1, cbmaj2, cbmin2)
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
        li = child.getLayoutInfo (ctxt, style)
        if li.aspect is None:
            aspect = None
        else:
            aspect = 1. / li.aspect # box aspect is major/minor = h/w
        return (li.minsize[1], li.minsize[0]) + tuple (li.minborders) + (aspect, )


    def getLayoutInfo (self, ctxt, style):
        li = self._boxGetLayoutInfo (ctxt, style)
        return LayoutInfo (minsize=(li.minsize[1], li.minsize[0]),
                           minborders=li.minborders)


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
        li = child.getLayoutInfo (ctxt, style)
        mb = li.minborders
        return tuple (li.minsize) + (mb[3], mb[0], mb[1], mb[2], li.aspect)


    def _boxTranslate (self, ctxt, major, minor):
        ctxt.translate (major, minor)


    def getLayoutInfo (self, ctxt, style):
        li = self._boxGetLayoutInfo (ctxt, style)
        mb = li.minborders
        return LayoutInfo (minsize=li.minsize,
                           minborders=(mb[1], mb[2], mb[3], mb[0]))


    def _boxConfigureChild (self, child, ctxt, style, major, minor, bmaj1, bmin1,
                            bmaj2, bmin2):
        child.configurePainting (ctxt, style, major, minor, bmin1, bmaj2, bmin2, bmaj1)


    def configurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
        super (HBox, self).configurePainting (ctxt, style, w, h, bt, br, bb, bl)
        self._boxConfigurePainting (ctxt, style, w, h, bl, bt, br, bb)
