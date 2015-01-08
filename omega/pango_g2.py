# -*- mode: python; coding: utf-8 -*-
# Copyright 2011, 2012, 2014, 2015 Peter Williams
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


# This version of the pango support module is intended for use with Gtk+ 2.0;
# it imports the "pango" and "pangocairo" modules.

from __future__ import absolute_import, division, print_function, unicode_literals

import pangocairo

from . import base

# FIXME: the way we do things here is likely to be SUPER SLOW
# since we're creating new contexts willy-nilly. Should deal
# with that at some point.


X, Y, W, H = range (4)
S = 1024 # = Pango universal scale factor.


def globalLayoutMutate (layout):
    pass


def setFont (family=None, style=None, variant=None,
             weight=None, stretch=None, size=None):
    global globalLayoutMutate

    def mutate (layout):
        fd = layout.get_font_description ()
        if fd is None:
            fd = layout.get_context ().get_font_description ()

        if family is not None:
            fd.set_family (family)
        if style is not None:
            fd.set_style (style)
        if variant is not None:
            fd.set_variant (variant)
        if weight is not None:
            fd.set_weight (weight)
        if stretch is not None:
            fd.set_stretch (stretch)
        if size is not None:
            fd.set_size (int (round (size * S)))

        layout.set_font_description (fd)

    globalLayoutMutate = mutate


def _copyConstants ():
    import pango
    g = globals ()

    for pfx in 'STYLE VARIANT WEIGHT STRETCH'.split ():
        pfx += '_'

        for item in dir (pango):
            if item.startswith (pfx):
                g[item] = getattr (pango, item)

_copyConstants ()
del _copyConstants


class PangoPainter (base._TextPainterBase):
    hAlign = 0.0
    vAlign = 0.0
    style = None


    def __init__ (self, markup, hAlign=0.0, vAlign=0.0):
        self.markup = markup
        self.hAlign = float (hAlign)
        self.vAlign = float (vAlign)


    def doLayout (self, ctxt, style, isfinal, w, h, bt, br, bl, bb):
        pcr = pangocairo.CairoContext (ctxt)
        layout = pcr.create_layout ()
        globalLayoutMutate (layout)
        layout.set_markup (self.markup)
        e = layout.get_extents ()[1] # [1] -> use logical extents
        e = [v / S for v in e]
        self._extents = e

        self._dx = self.hAlign * (w - e[W]) + e[X]
        self._dy = self.vAlign * (h - e[H]) + e[Y]

        return base.LayoutInfo (minsize=(e[W], e[H]))


    def doPaint (self, ctxt, style):
        pcr = pangocairo.CairoContext (ctxt)

        layout = pcr.create_layout ()
        globalLayoutMutate (layout)
        layout.set_markup (self.markup)

        pcr.save ()
        style.apply (pcr, self.style)
        pcr.set_source_rgb (*style.getColor (self.color))
        pcr.move_to (self.border[3] + self._dx, self.border[0] + self._dy)
        pcr.show_layout (layout)
        pcr.restore ()


class PangoStamper (base._TextStamperBase):
    def __init__ (self, markup):
        self.markup = markup


    def getSize (self, ctxt, style):
        pcr = pangocairo.CairoContext (ctxt)
        layout = pcr.create_layout ()
        globalLayoutMutate (layout)
        layout.set_markup (self.markup)
        e = layout.get_extents ()[1]
        return e[W] / S, e[H] / S


    def paintAt (self, ctxt, x, y, color):
        pcr = pangocairo.CairoContext (ctxt)

        layout = pcr.create_layout ()
        globalLayoutMutate (layout)
        layout.set_markup (self.markup)
        e = layout.get_extents ()[1]

        pcr.save ()
        pcr.set_source_rgb (*color)
        pcr.move_to (x + e[X] / S, y + e[Y] / S)
        pcr.show_layout (layout)
        pcr.restore ()


_subsuperRise = 5000

def setBuiltinSubsuperRise (value):
    global _subsuperRise
    _subsuperRise = int (value)

_pangoMappings = {
    # U+22C5 = math dot operator
    '10^%d': '10<span size="smaller" rise="{R}">%d</span>',
    '%d*10^%d': u'%d\u22c510<span size="smaller" rise="{R}">%d</span>',
    'UNIT_h': 'UNIT_<span size="smaller" rise="{R}">h</span>',
    'UNIT_m': 'UNIT_<span size="smaller" rise="{R}">m</span>',
    'UNIT_s': 'UNIT_<span size="smaller" rise="{R}">s</span>',
}

def _getPangoMapping (t):
    new = _pangoMappings.get (t)
    if new is None:
        return t
    return new.replace ('{R}', str (_subsuperRise))


base._setTextBackend (PangoPainter, PangoStamper, _getPangoMapping)
