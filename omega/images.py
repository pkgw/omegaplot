import cairo
import latexsnippet
import atexit

from base import *
from math import pi

globalCache = latexsnippet.SnippetCache ()

class ImagePainter (Painter):
    def __init__ (self, surf=None):
        Painter.__init__ (self)

        self._surf = surf

    def getSurf (self):
        if not self._surf: 
            self._surf = self.createSurf ()
        
        return self._surf

    def createSurf (self):
        raise NotImplementedError ()

    ROT_NONE = 0
    ROT_CW90 = 1
    ROT_180 = 2
    ROT_CCW90 = 3

    rotation = 0
    
    def setRotation (self, value):
        self.rotation = value
        
    def getMinimumSize (self, ctxt, style):
        surf = self.getSurf ()

        if not isinstance (surf, cairo.ImageSurface):
            raise Exception ('Need to specify an ImageSurface for ImagePainter, got %s' % surf)
        
        w, h = surf.get_width (), surf.get_height ()

        if self.rotation % 2 == 1:
            return h, w
        return w, h
    
    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        surf = self.getSurf ()

        if self.rotation == self.ROT_CW90:
            ctxt.rotate (pi / 2)
            ctxt.translate (0, -surf.get_height())
        elif self.rotation == self.ROT_180:
            ctxt.rotate (pi)
            ctxt.translate (-surf.get_width(), -surf.get_height ())
        elif self.rotation == self.ROT_CCW90:
            ctxt.rotate (-pi / 2)
            ctxt.translate (-surf.get_width (), 0)

        ctxt.set_source_surface (surf)
        # Whatever the default is, it seems to do the right thing.
        #ctxt.set_operator (cairo.OPERATOR_ATOP)

        ctxt.paint ()

class LatexPainter (ImagePainter):
    def __init__ (self, snippet, cache=globalCache):
        ImagePainter.__init__ (self, None)
        self.handle = cache.addSnippet (snippet)
        self.cache = cache

    def createSurf (self):
        f = self.cache.getPngFile (self.handle)
        return cairo.ImageSurface.create_from_png (f)

    def __del__ (self):
        self.cache.expire (self.handle)

def _atexit ():
    globalCache.close ()

atexit.register (_atexit)
