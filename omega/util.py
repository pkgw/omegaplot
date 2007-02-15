import cairo

from base import Painter, NullPainter

defaultLiveDisplay = None

def LiveDisplay (pipeline, **kwargs):
    return defaultLiveDisplay (pipeline, **kwargs)

class PaintPipeline (object):
    def __init__ (self, bag, style, sources, painter=None):
        self.bag = bag
        self.style = style
        self.sources = sources

        self.removeChild (None) # reset to NullPainter child
        self.setPainter (painter)

    def setPainter (self, painter):
        if self._painter: self._painter.setParent (None)

        if painter:
            if not isinstance (painter, Painter):
                raise Exception ('Not a Painter: %s' % painter)

            painter.setParent (self)
            self._painter = painter

    def removeChild (self, child):
        self._painter = NullPainter ()
        self._painter.setParent (self)

    savedCtxt = None
    savedWidth = -1
    savedHeight = -1
    
    def paintToContext (self, ctxt, w, h):
        if ctxt is not self.savedCtxt or w != self.savedWidth or \
           h != self.savedHeight:

            (minw, minh) = self._painter.getMinimumSize (ctxt, self.style)

            if w < minw or h < minh:
                raise ContextTooSmallError (w, h, minw, minh)

            self.savedCtxt = ctxt
            self.savedWidth = w
            self.savedHeight = h

            self._painter.configurePainting (ctxt, self.style, w, h)

        self.style.initContext (ctxt, w, h)
        self.bag.startFlushing (self.sources)
        self._painter.paint (ctxt, self.style, True)

        while self.bag.startNewRound ():
            self._painter.paint (ctxt, self.style, False)

    def forceReconfigure (self):
        self.savedWidth = -1

    def makeLiveDisplay (self):
        return defaultLiveDisplay (self)

class ContextTooSmallError (Exception):
    def __init__ (self, w, h, minw, minh):
        (self.w, self.h, self.minw, self.minh) = (w, h, minw, minh)

    def __str__ (self):
        return 'Unable to paint: context size of %fx%f smaller than ' \
               'required minimum size of %fx%f' % (self.w, self.h,
                                                   self.minw, self.minh)

# Utilities for dumping pipelines to various useful output devices.

class GenericPointSizedFile (object):
    def __init__ (self, filename, w, h, type=None):
        if type == 'ps' or filename[-3:] == '.ps':
            self.surf = cairo.PSSurface
        elif type == 'pdf' or filename[-4:] == '.pdf':
            self.surf = cairo.PDFSurface
        elif type == 'svg' or filename[-4:] == '.svg':
            self.surf = cairo.SVGSurface
        else:
            raise Exception ('Cannot guess file type and no hint given')

        self.filename = filename
        self.w = w
        self.h = h
        self.serial = 0

    def getFilename (self):
        if '%' not in self.filename: return self.filename

        f = self.filename % (self.serial)
        self.serial += 1
        return f
    
    def renderPipeline (self, pipeline):
        f = self.getFilename ()
        surf = self.surf (f, self.w, self.h)
        ctxt = cairo.Context (surf)
        
        pipeline.paintToContext (ctxt, self.w, self.h)
        
        ctxt.show_page ()
        surf.finish ()

class LetterFile (GenericPointSizedFile):
    # FIXME: I am not sure if the whole page size / orientation
    # issue is handled in the correct way. I kind of feel that
    # we ought to have w = 8.5, h = 11, rotate the context, and
    # indicate that the orientation is landscape. Reading the DSC
    # guidelines and understanding them would probably be a
    # useful thing to do here.

    def __init__ (self, filename, type=None):
        GenericPointSizedFile.__init__ (self, filename, 11.0 * 72,
                                        8.5 * 72, type)

    def createSurface (self):
        ret = GenericPointSizedFile.createSurface (self)
        surf = ret[0]
        
        if isinstance (surf, cairo.PSSurface):
            surf.dsc_begin_page_setup ()
            surf.dsc_comment ('%%IncludeFeature: *PageSize Letter')
            surf.dsc_comment ('%%PageOrientation: Landscape')
    
        return ret

class InchesFile (GenericPointSizedFile):
    def __init__ (self, filename, w, h, type=None):
        GenericPointSizedFile.__init__ (self, filename, w * 72,
                                        h * 72, type)
        
class CMFile (GenericPointSizedFile):
    def __init__ (self, filename, w, h, type=None):
        GenericPointSizedFile.__init__ (self, filename, w * 72 / 2.54,
                                        h * 72 / 2.54, type)
        
class GenericPngFile (object):
    def __init__ (self, filename, w, h):
        self.filename = filename
        self.w = w
        self.h = h
        self.serial = 0

    def getFilename (self):
        if '%' not in self.filename: return self.filename

        f = self.filename % (self.serial)
        self.serial += 1
        return f
    
    def renderPipeline (self, pipeline):
        f = self.getFilename ()
        surf = cairo.ImageSurface (cairo.FORMAT_ARGB32, self.w, self.h)
        ctxt = cairo.Context (surf)
        
        pipeline.paintToContext (ctxt, self.w, self.h)
        
        surf.write_to_png (f)

class LargePngFile (GenericPngFile):
    def __init__ (self, filename):
        GenericPngFile.__init__ (self, filename, 1024, 768)

_dumpSerial = 0
dumpName = 'omegaDump%02d.ps'
dumpSurfgen = LetterFile

def dump (painter, bag, style, sources):
    global _dumpSerial, dumpName

    _dumpSerial += 1
    f = dumpName % (_dumpSerial)

    pl = PaintPipeline (bag, style, sources, painter)
    dumpSurfgen (f).renderPipeline (pl)

def resetDumpSerial ():
    global _dumpSerial
    _dumpSerial = 0

# Generating quick-and-dirty pipelines from data

import sources, base, bag, styles, stamps

def makeQuickPipeline (xinfo, yinfo=None, lines=True):
    """Construct a PaintPipeline object that tries to represent
    the passed-in data reasonably in a plot."""
    
    if yinfo is None:
        yinfo = xinfo
        xinfo = xrange (0, len(yinfo))

    if callable (yinfo):
        raise Exception ('write this bit')

    try:
        tmp = float (xinfo[0])
        tmp = float (yinfo[0])
    except:
        raise

    b = bag.Bag ()
    style = styles.BlackOnWhiteBitmap ()
    
    src = sources.StoredData ('FF', zip (xinfo, yinfo))

    rdp = base.RectDataPainter (b)
    rdp.setBounds (min (xinfo), max (xinfo), min (yinfo), max(yinfo))
    rdp.expose ('data')

    if not lines:
        rdp.lines = False
        rdp.pointStamp = stamps.X ()
    
    rp = base.RectPlot ()
    rp.addFieldPainter (rdp)
    rp.magicAxisPainters ('lb')

    return PaintPipeline (b, style, {'data': src}, rp), rp

def makeQuickDisplay (*args, **kwargs):
    """Create a LiveDisplay object that attempts to represent the
    passed-in data passably in a plot. Just creates a pipeline using
    omega.util.makeQuickPipeline and wraps it with a LiveDisplay object.

    Returns: LiveDisplay object, PaintPipeline object, RectPlot object."""
    
    pl, rp = makeQuickPipeline (*args, **kwargs)
    return LiveDisplay (pl), pl, rp
