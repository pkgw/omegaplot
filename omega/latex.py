import cairo
import latexsnippet
import atexit

from base import *
from base import _ImagePainterBase, _TextPainterBase, _TextStamperBase
import base

globalCache = latexsnippet.SnippetCache ()

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

    # I must confess that I do not understand why this algorithm
    # works, but it does. Also it is not exactly efficient. I would like to
    # find a way to have Cairo do this effect efficiently, but we basically
    # need to multiply the basedata image values by the color values,
    # which doesn't seem to fit into the Porter-Duff compositing model.
    # Fortunately, LaTeX snippet images are probably going to be small, so
    # this chunk of the code ought not be too much of a bottleneck.
    # (If we could somehow get the LaTeX PNG to carry all of the brightness
    # information into the alpha channel, we could fill the csurf with the
    # color and then somehow snarf the LaTeX alpha information into it,
    # I think ...)
    
    for i in range (0, len (basedata), 4):
        basealpha = ord (basedata[i+3])

        if basealpha == 0:
            level = 0
        else:
            level = 255 - ord (basedata[i])
            
        cdata[i+0] = chr (color[0] * level)
        cdata[i+1] = chr (color[1] * level)
        cdata[i+2] = chr (color[2] * level)
        cdata[i+3] = chr (level)
        
    return csurf
    
class LatexPainter (_ImagePainterBase, _TextPainterBase):
    def __init__ (self, snippet, cache=globalCache):
        _ImagePainterBase.__init__ (self)
        
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

class LatexStamper (_TextStamperBase):
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
        
    def getSize (self, ctxt, style):
        surf = self.getBaseSurf ()
        return surf.get_width (), surf.get_height ()

    def paintAt (self, ctxt, x, y, color):
        ctxt.save ()
        ctxt.translate (x, y)
        ctxt.set_source_surface (self.getColorSurf (color))
        ctxt.paint ()
        ctxt.restore ()
    
def _atexit ():
    globalCache.close ()

atexit.register (_atexit)

base._setTextBackend (LatexPainter, LatexStamper)

