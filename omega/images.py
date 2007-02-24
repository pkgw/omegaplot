import cairo
import latexsnippet
import atexit

from base import *
from math import pi

globalCache = latexsnippet.SnippetCache ()

class ImagePainter (Painter):
    def __init__ (self, surf=None):
        Painter.__init__ (self)

    def getSurf (self, style):
        raise NotImplementedError ()

    ROT_NONE = 0
    ROT_CW90 = 1
    ROT_180 = 2
    ROT_CCW90 = 3

    rotation = 0
    
    def setRotation (self, value):
        self.rotation = value
        
    def getMinimumSize (self, ctxt, style):
        surf = self.getSurf (style)

        if not isinstance (surf, cairo.ImageSurface):
            raise Exception ('Need to specify an ImageSurface for ImagePainter, got %s' % surf)
        
        w, h = surf.get_width (), surf.get_height ()

        if self.rotation % 2 == 1:
            return h, w
        return w, h

    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        surf = self.getSurf (style)

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

def _colorizeLatex (surf, color):
    if color == (0, 0, 0):
        return surf

    if surf.get_format () != cairo.FORMAT_ARGB32:
        raise Exception ('FIXME: require LaTeX PNGs to be ARGB32')
    
    csurf = cairo.Surface.create_similar (surf,
                                          cairo.CONTENT_COLOR_ALPHA,
                                          surf.get_width (),
                                          surf.get_height ())
    basedata = surf.get_data ()
    cdata = csurf.get_data ()

    if len (basedata) != len (cdata):
        raise Exception ('Disagreeing image data lengths? Can\'t happen!')
        
    for i in range (0, len (basedata), 4):
        basealpha = ord (basedata[i+3])

        if basealpha == 0:
            level = 0
        else:
            level = 255 - ord (basedata[i])
            
        # I *think* we use premultiplied alpha ...
        cdata[i+0] = chr (color[0] * level)
        cdata[i+1] = chr (color[1] * level)
        cdata[i+2] = chr (color[2] * level)
        cdata[i+3] = chr (level)
        
    return csurf
    
class LatexPainter (ImagePainter):
    color = 'foreground'
    
    def __init__ (self, snippet, cache=globalCache):
        ImagePainter.__init__ (self, None)
        
        self.cache = cache
        self.handle = self.cache.addSnippet (snippet)
        self.basesurf = None

    def getSurf (self, style):
        if not self.basesurf:
            f = self.cache.getPngFile (self.handle)
            self.basesurf = cairo.ImageSurface.create_from_png (f)

        return _colorizeLatex (self.basesurf, style.getColor (self.color))
        
    def __del__ (self):
        self.cache.expire (self.handle)

class LatexStamper (object):
    def __init__ (self, snippet, cache=globalCache):
        self.cache = cache
        self.handle = self.cache.addSnippet (snippet)
        self.basesurf = None

    def getBaseSurf (self):
        if not self.basesurf:
            fname = self.cache.getPngFile (self.handle)
            self.basesurf = cairo.ImageSurface.create_from_png (fname)

        return self.basesurf

    def getColorSurf (self, color):
        return _colorizeLatex (self.getBaseSurf (), color)
        
    def getSize (self):
        surf = self.getBaseSurf ()
        return surf.get_width (), surf.get_height ()

    def stamp (self, ctxt, x, y, color):
        ctxt.save ()
        ctxt.translate (x, y)
        ctxt.set_source_surface (self.getColorSurf (color))
        ctxt.paint ()
        ctxt.restore ()
    
def _atexit ():
    globalCache.close ()

atexit.register (_atexit)
