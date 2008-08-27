import cairo
import latexsnippet
import atexit

from base import *
from base import _TextPainterBase, _TextStamperBase
import base

globalCache = latexsnippet.CairoCache ()
#latexsnippet.defaultConfig._debug = True

class LatexPainter (_TextPainterBase):
    hAlign = 0.0
    vAlign = 0.0
    style = None
    
    def __init__ (self, snippet, cache=globalCache, hAlign=0.0, vAlign=0.0):
        self.cache = cache
        self.handle = self.cache.addSnippet (snippet)
        self.hAlign = float (hAlign)
        self.vAlign = float (vAlign)

    def getMinimumSize (self, ctxt, style):
        r = self.cache.getRenderer (self.handle)
        return r.bbw, r.bbh

    def configurePainting (self, ctxt, style, w, h):
        Painter.configurePainting (self, ctxt, style, w, h)

        r = self.cache.getRenderer (self.handle)
        self.dx = self.hAlign * (w - r.bbw)
        self.dy = self.vAlign * (h - r.bbh)
        
    def doPaint (self, ctxt, style):
        ctxt.save ()
        style.apply (ctxt, self.style)
        ctxt.set_source_rgb (*style.getColor (self.color))
        ctxt.translate (self.dx, self.dy)
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

base._setTextBackend (LatexPainter, LatexStamper)

