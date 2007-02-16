import cairo
import latexsnippet
import atexit

from base import *

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
    
    def getMinimumSize (self, ctxt, style):
        surf = self.getSurf ()

        if not isinstance (surf, cairo.ImageSurface):
            raise Exception ('Need to specify an ImageSurface for ImagePainter, got %s' % surf)
        
        return surf.get_width (), surf.get_height ()
    
    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        ctxt.set_source_surface (self.getSurf ())
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

def _atexit ():
    globalCache.close ()

atexit.register (_atexit)
