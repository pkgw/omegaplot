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
