# Basic classes of OmegaPlot.

class Painter (object):
    mainStyle = None
    parent = None
    
    def __init__ (self):
        self.matrix = None

    def setParent (self, parent):
        if self.parent:
            self.parent.removeChild (self)

        self.parent = parent
        self.matrix = None
        
    def getMinimumSize (self, ctxt, style):
        #"""Should be a function of the style only."""
        # I feel like the above should be true, but we at least
        # need ctxt for measuring text, unless another way is found.
        return 0, 0

    def configurePainting (self, ctxt, style, w, h):
        if not self.parent:
            raise Exception ('Cannot configure parentless painter')
        
        self.matrix = ctxt.get_matrix ()
        self.width = w
        self.height = h

    def paint (self, ctxt, style, firstPaint):
        ctxt.save ()
        ctxt.set_matrix (self.matrix)
        style.apply (ctxt, self.mainStyle)
        self.doPaint (ctxt, style, firstPaint)
        ctxt.restore ()

class StreamSink (Painter):
    def __init__ (self, bag):
        Painter.__init__ (self)
        bag.registerSink (self)
        self._bag = bag

    def getBag (self): return self._bag
    
    def doPaint (self, ctxt, style, firstPaint):
        if firstPaint:
            self.doFirstPaint (ctxt, style)
        else:
            chunk = self._bag.getChunk (self)
            if not chunk: return # no more chunks
            self.doChunkPaint (ctxt, style, chunk)

    def expose (self, name):
        self._bag.exposeSink (self, name)
        return self
    
    def linkTo (self, source):
        self._bag.linkTo (source, self)
        return source

    def linkExpose (self, source, name):
        self._bag.linkTo (source, self)
        self._bag.exposeSink (source, name)
        return source

class NullPainter (Painter):
    lineStyle = 'genericLine'
    
    def getMinimumSize (self, ctxt, style):
        return 0, 0

    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        style.apply (ctxt, self.lineStyle)
        
        ctxt.move_to (0, 0)
        ctxt.line_to (self.width, self.height)
        ctxt.stroke ()
        ctxt.move_to (0, self.height)
        ctxt.line_to (self.width, 0)
        ctxt.stroke ()

# Text handling routines. Possible backends are Cairo text
# support (fast) or LaTeX (inefficient but capable of rendering
# arbitrarily complex formulae). I am not fond of globals, but you
# reeeally don't want text in different parts of your graph to be
# rendered via different mechanisms (for aesthetic reasons), so here
# we are.

class _TextPainterBase (Painter):
    color = 'foreground'

class _TextStamperBase (object):
    def getSize (self, ctxt, style):
        raise NotImplementedError ()

    def stamp (self, ctxt, x, y, color):
        raise NotImplementedError ()

# Our simple default backend

import cairo

class CairoTextPainter (_TextPainterBase):
    def __init__ (self, text):
        _TextPainterBase.__init__ (self)
        self.text = text
        self.extents = None
        
    def getMinimumSize (self, ctxt, style):
        if not self.extents:
            self.extents = ctxt.text_extents (self.text)

        return self.extents[2:4]

    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        ctxt.move_to (-self.extents[0], -self.extents[1])
        ctxt.set_source_rgb (*style.getColor (self.color))
        ctxt.show_text (self.text)

class CairoTextStamper (_TextStamperBase):
    def __init__ (self, text):
        self.text = text
        self.extents = None

    def getSize (self, ctxt, style):
        if not self.extents:
            self.extents = ctxt.text_extents (self.text)

        return self.extents[2:4]

    def stamp (self, ctxt, x, y, color):
        ctxt.save ()
        ctxt.move_to (x, y)
        ctxt.rel_move_to (-self.extents[0], -self.extents[1])
        ctxt.set_source_rgb (*color)
        ctxt.show_text (self.text)
        ctxt.restore ()

_textPainterClass = CairoTextPainter
_textStamperClass = CairoTextStamper

def TextPainter (text, **kwargs):
    return _textPainterClass (text, **kwargs)

def TextStamper (text, **kwargs):
    return _textStamperClass (text, **kwargs)

def _setTextBackend (painterClass, stamperClass):
    global _textPainterClass, _textStamperClass
    
    if not issubclass (painterClass, _TextPainterBase):
        raise Exception ('Text backend class %s is not a TextPainterBase subclass' % \
                         painterClass)

    if not issubclass (stamperClass, _TextStamperBase):
        raise Exception ('Text backend class %s is not a TextStamperBase subclass' % \
                         stamperClass)

    _textPainterClass = painterClass
    _textStamperClass = stamperClass

# Generic painting of ImageSurfaces

class _ImagePainterBase (Painter):
    def getSurf (self, style):
        raise NotImplementedError ()

    def getMinimumSize (self, ctxt, style):
        surf = self.getSurf (style)

        if not isinstance (surf, cairo.ImageSurface):
            raise Exception ('Need to specify an ImageSurface for ImagePainter, got %s' % surf)
        
        return surf.get_width (), surf.get_height ()

    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        surf = self.getSurf (style)

        ctxt.set_source_surface (surf)
        # Whatever the default is, it seems to do the right thing.
        #ctxt.set_operator (cairo.OPERATOR_ATOP)

        ctxt.paint ()

class ImagePainter (_ImagePainterBase):
    def __init__ (self, surf):
        _ImagePainterBase.__init__ (self)
        self.surf = surf

    def getSurf (self, style):
        return self.surf
