# Copyright 2011, 2012, 2014 Peter Williams
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

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np

from .base import LayoutInfo, Painter, NullPainter
from .util import expandAspect, shrinkAspect, nudgeMargins


class Overlay (Painter):
    """An overlay in which multiple painters can be stacked in one
    box, with an optional border area."""

    def __init__ (self):
        super (Overlay, self).__init__ ()
        self.painters = []

    hBorderSize = 4 # in style.smallScale
    vBorderSize = 4 # in style.smallScale
    bgStyle = None # style ref

    ## def XXXgetLayoutInfo (self, ctxt, style):
    ##     sz = np.zeros (6)
    ##     aspect = None
    ##
    ##     for p in self.painters:
    ##         li = p.XXXgetLayoutInfo (ctxt, style)
    ##         sz = np.maximum (sz, li.asBoxInfo ())
    ##
    ##         if aspect is None:
    ##             aspect = li.aspect
    ##         elif li.aspect is not None and li.aspect != aspect:
    ##             raise RuntimeError ('cannot overlay painters with disageeing aspect '
    ##                                 'ratios (%f, %f)' % (aspect, li.aspect))
    ##
    ##     sz[:2] = expandAspect (aspect, *sz[:2])
    ##     sz[3:6:2] += self.hBorderSize * style.smallScale
    ##     sz[2:6:2] += self.vBorderSize * style.smallScale
    ##
    ##     return LayoutInfo (minsize=sz[:2], minborders=sz[2:], aspect=li.aspect)
    ##
    ## def XXXconfigurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
    ##     bh = self.hBorderSize * style.smallScale
    ##     bv = self.vBorderSize * style.smallScale
    ##
    ##     ctxt.save ()
    ##     ctxt.translate (bh, bv)
    ##
    ##     for p in self.painters:
    ##         p.XXXconfigurePainting (ctxt, style, w, h, bt - bv, br - bh, bb - bv, bl - bh)
    ##
    ##     ctxt.restore ()

    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        raise NotImplementedError ('omega.layout.Overlay')

    def doPaint (self, ctxt, style):
        if self.bgStyle is not None:
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


    ## def XXXgetLayoutInfo (self, ctxt, style):
    ##     v = np.empty ((self.nh, self.nw, 6))
    ##     aspect = None
    ##
    ##     for r in xrange (self.nh):
    ##         for c in xrange (self.nw):
    ##             li = self._elements[r,c].XXXgetLayoutInfo (ctxt, style)
    ##             v[r,c] = li.asBoxInfo ()
    ##
    ##             if aspect is None:
    ##                 aspect = li.aspect
    ##             elif li.aspect is not None and li.aspect != aspect:
    ##                 raise RuntimeError ('cannot grid painters with disagreeing aspect '
    ##                                     'ratios (%f, %f)' % (aspect, li.aspect))
    ##
    ##     # Simple, totally uniform borders and sizes.
    ##
    ##     self.maxes = maxes = v.max (0).max (0)
    ##     self._childaspect = aspect
    ##     maxes[:2] = expandAspect (aspect, *maxes[:2])
    ##
    ##     minw = self.nw * maxes[0]
    ##     minw += (self.nw - 1) * (maxes[3] + maxes[5] + self.hPadSize * style.smallScale)
    ##     minh = self.nh * maxes[1]
    ##     minh += (self.nh - 1) * (maxes[2] + maxes[4] + self.vPadSize * style.smallScale)
    ##
    ##     hb = self.hBorderSize * style.smallScale
    ##     vb = self.vBorderSize * style.smallScale
    ##
    ##     return LayoutInfo (minsize=(minw, minh),
    ##                        minborders=(maxes[2] + vb, maxes[3] + hb,
    ##                                    maxes[4] + vb, maxes[5] + hb))
    ##
    ##
    ## def XXXconfigurePainting (self, ctxt, style, w, h, bt, br, bb, bl):
    ##     super (Grid, self).XXXconfigurePainting (ctxt, style, w, h, bt, br, bb, bl)
    ##
    ##     hPadReal = self.hPadSize * style.smallScale
    ##     vPadReal = self.vPadSize * style.smallScale
    ##     hb = self.hBorderSize * style.smallScale
    ##     vb = self.vBorderSize * style.smallScale
    ##
    ##     # Figure out borders and such. Children get shrunk to provide
    ##     # the right aspect ratio, with extra space redistributed into
    ##     # their margins. All the while we account for our extra border
    ##     # around the whole thing.
    ##
    ##     bt -= vb
    ##     br -= hb
    ##     bb -= vb
    ##     bl -= hb
    ##
    ##     childw = (w - (self.nw - 1) * (hPadReal + bl + br)) / self.nw
    ##     childh = (h - (self.nh - 1) * (vPadReal + bt + bb)) / self.nh
    ##     childw, childh = shrinkAspect (self._childaspect, childw, childh)
    ##
    ##     if self.nw == 1:
    ##         bhextra = w - childw
    ##     else:
    ##         bhextra = (w - self.nw * childw) / (self.nw - 1) - (hPadReal + bl + br)
    ##         bhextra /= self.nw
    ##
    ##     if self.nh == 1:
    ##         bvextra = h - childh
    ##     else:
    ##         bvextra = (h - self.nh * childh) / (self.nh - 1) - (vPadReal + bt + bb)
    ##         bvextra /= self.nw
    ##
    ##     bt, br, bb, bl = nudgeMargins ((bt + 0.5 * bvextra, br + 0.5 * bhextra,
    ##                                     bb + 0.5 * bvextra, bl + 0.5 * bhextra),
    ##                                    self.maxes[2:])
    ##
    ##     fullcw = childw + hPadReal + bl + br
    ##     fullch = childh + vPadReal + bt + bb
    ##
    ##     ctxt.save ()
    ##     ctxt.translate (hb, vb)
    ##
    ##     for r in xrange (self.nh):
    ##         for c in xrange (self.nw):
    ##             dx = c * fullcw
    ##             dy = r * fullch
    ##
    ##             ctxt.translate (dx, dy)
    ##             self._elements[r,c].XXXconfigurePainting (ctxt, style, childw, childh,
    ##                                                    bt, br, bb, bl)
    ##             ctxt.translate (-dx, -dy)
    ##
    ##     ctxt.restore ()


    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        raise NotImplementedError ('omega.layout.Grid')

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

    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        fw, fh = self.fullw, self.fullh

        if isfinal:
            ctxt.save ()

            if self.rotation == self.ROT_CW90:
                ctxt.rotate (np.pi / 2)
                ctxt.translate (0, -fw)
            elif self.rotation == self.ROT_180:
                ctxt.rotate (np.pi)
                ctxt.translate (-fw, -fh)
            elif self.rotation == self.ROT_CCW90:
                ctxt.rotate (-np.pi / 2)
                ctxt.translate (-fh, 0)

        # Here we need to transform in the reverse sense of how we store
        # `self.rotation`. If self.rotation is CW90, then what the child sees
        # for `bt` should be our `br`.

        rot = self.rotation
        if rot == self.ROT_CW90:
            rot = self.ROT_CCW90
        elif rot == self.ROT_CCW90:
            rot = self.ROT_CW90
        sz = self._rotateSize (rot, w, h, bt, br, bb, bl)
        li = self.child.layout (ctxt, style, isfinal, *sz)

        if isfinal:
            ctxt.restore ()

        # Here we do the rotation in the forward sense. If self.rotation is
        # CW90, what the child reports as `bt` should become our `br`.

        sz = self._rotateSize (self.rotation, *li.asBoxInfo ())

        if li.aspect is None:
            aspect = None
        elif self.rotation in (self.ROT_NONE, self.ROT_180):
            aspect = li.aspect
        else:
            aspect = 1. / li.aspect

        minsize = expandAspect (aspect, sz[0], sz[1])
        return LayoutInfo (minsize=minsize, minborders=sz[2:], aspect=aspect)


    def doPaint (self, ctxt, style):
        self.child.paint (ctxt, style)


class _BoxChild (object):
    painter = None
    weight = 1.0 # weight in space allocation.
    majsz = 0.0 # main area size along major axis
    minsz = 0.0 # ... along minor axis.
    bmaj1 = 0.0 # border size along major axis, closer to box front
    bmaj2 = 0.0 # border size along major axis, closer to end of box
    bmin1 = 0.0 # border size along minor axis, clockwise from box front on major axis
    bmin2 = 0.0 # ... counterclockwise from box front on major axis
    aspect = None # desired aspect ratio as **major/minor**.

    def __init__ (self, painter):
        self.painter = painter


class LinearBox (Painter):
    # The "major axis" is the direction in which the box extends
    # as children are added, while the "minor axis" is always
    # one painter tall.

    bgStyle = None # style ref

    def __init__ (self, size):
        super (LinearBox, self).__init__ ()
        self.size = int (size)

        self._elements = [None] * self.size

        for i in xrange (0, self.size):
            np = NullPainter ()
            self._elements[i] = _BoxChild (np)
            np.setParent (self)

    # FIXME: when these are changed, need to indicate
    # that a reconfigure is necessary.
    majBorderSize = 2 # size of major axis border in style.smallScale
    minBorderSize = 2 # as above for minor axis border
    padSize = 1 # as above for interior padding along major axis

    def __getitem__ (self, idx):
        return self._elements[idx].painter

    def __setitem__ (self, idx, value):
        info = self._elements[idx]

        if info.painter is value:
            return

        # This will recurse to our own _lostChild
        if info.painter is not None:
            info.painter.setParent (None)

        # Setting the parent of `value` may also recurse into _lostChild, if
        # it's coming from another location in the box. Doing this before
        # adjusting `info` makes sure we modify the right list entry.

        if value is None:
            value = NullPainter ()
        value.setParent (self)

        info.painter = value
        info.majsz = info.minsz = info.bmaj1 = info.bmaj2 = info.bmin1 = info.bmin2 = 0.
        info.aspect = None


    def appendChild (self, child, weight=1.0):
        if child is None:
            child = NullPainter ()
        child.setParent (self)

        self._elements.append (_BoxChild (child))
        self._elements[-1].weight = weight
        self.size += 1


    def _lostChild (self, child):
        for e in self._elements:
            if e.painter is child:
                e.painter = NullPainter ().setParent (self)


    def setWeight (self, index, wt):
        self._elements[index].weight = wt


    # ########################################

    def _boxTranslate (self, ctxt, major, minor):
        raise NotImplementedError ()


    def _boxDoChildLayout (self, info, ctxt, style, isfinal, major, minor, bmaj1, bmin1,
                         bmaj2, bmin2):
        raise NotImplementedError ()


    def _boxDoLayout (self, ctxt, style, isfinal, major, minor, bmaj1, bmin1, bmaj2, bmin2):
        ##XXX ignoring these for now.
        ##want_bmaj = self.majBorderSize * style.smallScale
        ##want_bmin = self.minBorderSize * style.smallScale
        pad = self.padSize * style.smallScale

        # We set our requested bmaj1 and bmaj2 (the "outer" values) to be the
        # bmaj1 and bmaj2 of our first and last children, respectively (the
        # "inner" values). Processing is simplified if we just pretend that
        # the "outer" bmaj1/bmaj2 are zero, and fix up the LayoutInfo at the
        # end.

        major += bmaj1 + bmaj2

        # Compute some key parameters. We need to make an extra call to
        # doLayout on zero-weight children, since we need to know their sizes
        # before we can allocate leftover space to the non-zero-weight
        # children.

        totwt = 0.0
        tot_zerowt_major_size = 0.0

        for e in self._elements:
            if e.weight != 0:
                totwt += e.weight
            else:
                self._boxDoChildLayout (e, ctxt, style, False, 0., minor,
                                        e.bmaj2, bmin1, e.bmaj2, bmin2)

                if e.aspect is not None:
                    e.major = e.minor * e.aspect
                # otherwise, e.major is the requested minimum size.

                tot_zerowt_major_size += e.major + e.bmaj1 + e.bmaj2

        # Now we can compute the amount of major-axis space that's available
        # to allocate to the non-zero-weight children.

        majspace = major - (self.size - 1) * pad - tot_zerowt_major_size
        maxSPW = 0. # maximum size per weight.
        max_minor = max_bmin1 = max_bmin2 = 0.

        # With this, we can attempt a final layout. Information from the
        # previous layout attempt is reused, so that multiple calls should
        # iterate us to the right breakdown of the total child size into
        # bmaj1/main/bmaj2.

        if isfinal:
            ctxt.save ()

        for e in self._elements:
            if e.weight == 0:
                c_major = e.major
            else:
                c_major = e.weight * majspace / totwt - e.bmaj1 - e.bmaj2

            self._boxDoChildLayout (e, ctxt, style, isfinal, c_major, minor,
                                    e.bmaj1, bmin1, e.bmaj2, bmin2)

            if isfinal:
                self._boxTranslate (ctxt, e.bmaj1 + c_major + e.bmaj2 + pad, 0)

            if e.weight != 0:
                if e.aspect is not None:
                    raise RuntimeError ('box items with fixed aspect ratios must have zero weights')
                fullreq = e.bmaj1 + e.bmaj2 + e.major
                maxSPW = max (maxSPW, 1. * fullreq / e.weight)

            max_minor = max (max_minor, e.minor)
            max_bmin1 = max (max_bmin1, e.bmin1)
            max_bmin2 = max (max_bmin2, e.bmin2)

        # Report back results

        if isfinal:
            ctxt.restore ()

        major = maxSPW * totwt - self._elements[0].bmaj1 - self._elements[-1].bmaj2
        return LayoutInfo (minsize=(major, max_minor),
                           minborders=(self._elements[0].bmaj1, max_bmin1,
                                       self._elements[0].bmaj2, max_bmin2))


    def doPaint (self, ctxt, style):
        if self.bgStyle is not None:
            ctxt.save ()
            style.apply (ctxt, self.bgStyle)
            ctxt.rectangle (0, 0, self.fullw, self.fullh)
            ctxt.fill ()
            ctxt.restore ()

        for e in self._elements:
            e.painter.paint (ctxt, style)


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


    def _boxDoChildLayout (self, info, ctxt, style, isfinal, major, minor,
                           bmaj1, bmin1, bmaj2, bmin2):
        li = info.painter.layout (ctxt, style, isfinal,
                                  minor, major, # w = minor, h = major
                                  bmaj1, bmin1, bmaj2, bmin2) # top, right, bottom, left

        info.minor, info.major = li.minsize

        info.bmaj1 = li.minborders[0]
        info.bmin1 = li.minborders[1]
        info.bmaj2 = li.minborders[2]
        info.bmin2 = li.minborders[3]

        if li.aspect is None:
            info.aspect = None
        else:
            info.aspect = 1. / li.aspect # box aspect is major/minor = h/w

    def _boxTranslate (self, ctxt, major, minor):
        ctxt.translate (minor, major)

    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        return self._boxDoLayout (ctxt, style, isfinal, h, w, bt, br, bb, bl)


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


    def _boxDoChildLayout (self, info, ctxt, style, isfinal, major, minor,
                           bmaj1, bmin1, bmaj2, bmin2):
        li = info.painter.layout (ctxt, style, isfinal,
                                  major, minor, # w = major, h = minor
                                  bmin1, bmaj2, bmin2, bmaj1) # top, right, bottom, left
        info.major, info.minor = li.minsize
        info.bmaj1 = li.minborders[3]
        info.bmin1 = li.minborders[0]
        info.bmaj2 = li.minborders[1]
        info.bmin2 = li.minborders[2]
        info.aspect = li.aspect

    def _boxTranslate (self, ctxt, major, minor):
        ctxt.translate (major, minor)

    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bb, bl):
        return self._boxDoLayout (ctxt, style, isfinal, w, h, bl, bt, br, bb)
