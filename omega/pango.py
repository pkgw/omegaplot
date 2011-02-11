# needed to get right 'pango' module:
from __future__ import absolute_import
import cairo, pango, pangocairo
from omega import base

# FIXME: the way we do things here is likely to be SUPER SLOW
# since we're creating new contexts willy-nilly. Should deal
# with that at some point.


X, Y, W, H = range (4)
S = pango.SCALE


class PangoPainter (base._TextPainterBase):
    hAlign = 0.0
    vAlign = 0.0
    style = None


    def __init__ (self, markup, hAlign=0.0, vAlign=0.0):
        self.markup = markup
        self.hAlign = float (hAlign)
        self.vAlign = float (vAlign)


    def getMinimumSize (self, ctxt, style):
        pcr = pangocairo.CairoContext (ctxt)
        layout = pcr.create_layout ()
        layout.set_markup (self.markup)
        e = layout.get_extents ()[1] # [1] -> use logical extents
        e = [v / S for v in e]
        self._extents = e
        return e[W], e[H], 0, 0, 0, 0


    def configurePainting (self, ctxt, style, w, h, bt, br, bl, bb):
        super (PangoPainter, self).configurePainting (ctxt, style, w, h, bt, br, bl, bb)
        e = self._extents
        self._dx = self.hAlign * (w - e[W]) + e[X]
        self._dy = self.vAlign * (h - e[H]) + e[Y]


    def doPaint (self, ctxt, style):
        pcr = pangocairo.CairoContext (ctxt)

        layout = pcr.create_layout ()
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
        layout.set_markup (self.markup)
        e = layout.get_extents ()[1]
        return e[W] / S, e[H] / S


    def paintAt (self, ctxt, x, y, color):
        pcr = pangocairo.CairoContext (ctxt)

        layout = pcr.create_layout ()
        layout.set_markup (self.markup)
        e = layout.get_extents ()[1]

        pcr.save ()
        pcr.set_source_rgb (*color)
        pcr.move_to (x + e[X] / S, y + e[Y] / S)
        pcr.show_layout (layout)
        pcr.restore ()


base._setTextBackend (PangoPainter, PangoStamper)
