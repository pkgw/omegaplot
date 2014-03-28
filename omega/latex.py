# -*- mode: python ; coding: utf-8 -*-

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

import cairo
from oputil import latexsnippet
import atexit

from .base import *
from .base import _TextPainterBase, _TextStamperBase
from . import base

setZoom = latexsnippet.setZoom

def setDebug (debug):
    latexsnippet.defaultConfig._debug = debug

globalCache = latexsnippet.CairoCache ()


class LatexPainter (_TextPainterBase):
    hAlign = 0.0
    vAlign = 0.0
    style = None

    def __init__ (self, snippet, cache=globalCache, hAlign=0.0, vAlign=0.0):
        self.cache = cache
        self.handle = self.cache.addSnippet (snippet)
        self.hAlign = float (hAlign)
        self.vAlign = float (vAlign)

    def getLayoutInfo (self, ctxt, style):
        r = self.cache.getRenderer (self.handle)
        return LayoutInfo (minsize=(r.bbw, r.bbh))

    def configurePainting (self, ctxt, style, w, h, bt, br, bl, bb):
        super (LatexPainter, self).configurePainting (ctxt, style, w, h, bt, br, bl, bb)

        r = self.cache.getRenderer (self.handle)
        self.dx = self.hAlign * (w - r.bbw)
        self.dy = self.vAlign * (h - r.bbh)

    def doPaint (self, ctxt, style):
        ctxt.save ()
        style.apply (ctxt, self.style)
        ctxt.set_source_rgb (*style.getColor (self.color))
        ctxt.translate (self.border[3] + self.dx, self.border[0] + self.dy)
        self.cache.getRenderer (self.handle).render (ctxt, True)
        ctxt.restore ()

    def __del__ (self):
        self.cache.expire (self.handle)

class LatexStamper (_TextStamperBase):
    def __init__ (self, snippet, cache=globalCache):
        self.cache = cache
        self.handle = self.cache.addSnippet (snippet)

    def getSize (self, ctxt, style):
        r = self.cache.getRenderer (self.handle)
        return r.bbw, r.bbh

    def paintAt (self, ctxt, x, y, color):
        ctxt.save ()
        ctxt.translate (x, y)
        ctxt.set_source_rgb (*color)
        self.cache.getRenderer (self.handle).render (ctxt, True)
        ctxt.restore ()


def _atexit ():
    globalCache.close ()

atexit.register (_atexit)


_latexMappings = {
    '%.0f': '$%.0f$',
    '%.*f': '$%.*f$',
    '10^%d': '$10^{%d}$',
    '%d*10^%d': r'$%d\cdot\!10^{%d}$',
    'UNIT_°': r'UNIT_$^\circ$',
    'UNIT_′': r'UNIT_$\'$',
    'UNIT_″': r'UNIT_$\'\'$',
    'UNIT_h': r'UNIT_$^\textrm{h}$',
    'UNIT_m': r'UNIT_\vphantom{$^\textrm{h}$}$^\textrm{m}$',
    'UNIT_s': r'UNIT_$^\textrm{s}$',
}


base._setTextBackend (LatexPainter, LatexStamper,
                      lambda t: _latexMappings.get (t, t))
