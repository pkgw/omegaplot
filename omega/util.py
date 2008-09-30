import cairo

from base import _kwordDefaulted
from numpy import pi

defaultLiveDisplay = None
defaultShowBlocking = None

def _loadLiveBackend ():
    # Once we have multiple backends, we should try them
    # sequentially, etc.
    
    import omega, gtkThread, gtkUtil
    omega.gtkThread = gtkThread
    omega.gtkUtil = gtkUtil

def LiveDisplay (painter, style=None, **kwargs):
    if defaultLiveDisplay is None: _loadLiveBackend ()

    return defaultLiveDisplay (painter, style, **kwargs)

def showBlocking (painter, style=None, **kwargs):
    if defaultShowBlocking is None: _loadLiveBackend ()

    defaultShowBlocking (painter, style, **kwargs)
    
# Quick display of plots

import rect

def quickXY (*args, **kwargs):
    xmin = _kwordDefaulted (kwargs, 'xmin', float, None)
    xmax = _kwordDefaulted (kwargs, 'xmax', float, None)
    ymin = _kwordDefaulted (kwargs, 'ymin', float, None)
    ymax = _kwordDefaulted (kwargs, 'ymax', float, None)
    
    rp = rect.RectPlot ()
    rp.addXY (*args, **kwargs)
    rp.setBounds (xmin, xmax, ymin, ymax)
    return rp

def quickXYErr (*args, **kwargs):
    xmin = _kwordDefaulted (kwargs, 'xmin', float, None)
    xmax = _kwordDefaulted (kwargs, 'xmax', float, None)
    ymin = _kwordDefaulted (kwargs, 'ymin', float, None)
    ymax = _kwordDefaulted (kwargs, 'ymax', float, None)
    
    rp = rect.RectPlot ()
    rp.addXYErr (*args, **kwargs)
    rp.setBounds (xmin, xmax, ymin, ymax)
    return rp

def quickHist (data, bins=10, range=None, normed=False, **kwargs):
    from numpy import histogram

    xmin = _kwordDefaulted (kwargs, 'xmin', float, None)
    xmax = _kwordDefaulted (kwargs, 'xmax', float, None)
    ymin = _kwordDefaulted (kwargs, 'ymin', float, 0.0)
    ymax = _kwordDefaulted (kwargs, 'ymax', float, None)

    values, edges = histogram (data, bins, range, normed)

    fp = rect.ContinuousSteppedPainter (**kwargs)
    fp.setFloats (edges, values)
    
    rp = rect.RectPlot ()
    rp.add (fp)
    rp.setBounds (xmin, xmax, ymin, ymax)
    return rp

# Utilities for dumping to various useful output devices.

import styles

LetterDims = (11.0 * 72, 8.5 * 72)
BigImageSize = (1024, 768)

def PostScript (filename, pagedims, style=None):
    """Return a render function that will render a painter to a
    PostScript file with the specified filename and page dimensions
    (in points), with an optionally specified style (which defaults to
    BlackOnWhiteBitmap). This function should be passed to
    Painter.render () to actually create the file.

    A suggested default for pagedims is omega.util.LetterDims."""
    
    w, h = pagedims

    landscape = w > h
    if landscape:
        w, h = (h, w)
        
    if style is None: style = styles.BlackOnWhiteBitmap ()
    
    def f (painter):
        surf = cairo.PSSurface (filename, w, h)
        surf.dsc_begin_page_setup ()
        # surf.dsc_comment ('%%IncludeFeature: *PageSize Letter')

        if landscape:
            surf.dsc_comment ('%%PageOrientation: Landscape')

        ctxt = cairo.Context (surf)

        if not landscape:
            painter.renderBasic (ctxt, style, w, h)
        else:
            ctxt.translate (w/2, h/2)
            ctxt.rotate (-pi/2)
            ctxt.translate (-h/2, -w/2)
            painter.renderBasic (ctxt, style, h, w)

        ctxt.show_page ()
        surf.finish ()

    return f

def PDF (filename, pagedims, style=None):
    """Return a render function that will render a painter to
    a PDF file with the specified filename and page
    dimensions (in points), with an optionally specified style (which defaults
    to BlackOnWhiteBitmap). This function should be passed to
    Painter.render () to actually create the file.

    A suggested default for pagedims is omega.util.LetterDims."""

    w, h = pagedims

    if style is None: style = styles.BlackOnWhiteBitmap ()
    
    def f (painter):
        surf = cairo.PDFSurface (filename, w, h)
        ctxt = cairo.Context (surf)
        painter.renderBasic (ctxt, style, w, h)
        ctxt.show_page ()
        surf.finish ()

    return f

def PNG (filename, imgsize, style=None):
    """Return a render function that will render a painter to a PNG
    file with the specified filename and image dimensions (in pixels),
    with an optionally specified style (which defaults to
    BlackOnWhiteBitmap). This function should be passed to
    Painter.render () to actually create the file.

    A suggested default for imgsize is omega.util.BigImageSize."""

    w, h = imgsize

    if style is None: style = styles.BlackOnWhiteBitmap ()
    
    def f (painter):
        surf = cairo.ImageSurface (cairo.FORMAT_ARGB32, w, h)
        ctxt = cairo.Context (surf)
        painter.renderBasic (ctxt, style, w, h)
        ctxt.show_page ()
        surf.write_to_png (filename)
        surf.finish ()
        
    return f

def SVG (filename, imgsize, style=None):
    """Return a render function that will render a painter to an SVG
    file with the specified filename and image dimensions (in points),
    with an optionally specified style (which defaults to
    BlackOnWhiteBitmap). This function should be passed to
    Painter.render () to actually create the file.

    A suggested default for imgsize is omega.util.LetterDims."""

    w, h = imgsize

    if style is None: style = styles.BlackOnWhiteBitmap ()
    
    def f (painter):
        surf = cairo.SVGSurface (filename, w, h)
        ctxt = cairo.Context (surf)
        painter.renderBasic (ctxt, style, w, h)
        ctxt.show_page ()
        surf.finish ()
        
    return f

def savePainter (painter, filename, type=None, dims=None, **kwargs):
    """Save the specified painter to a file.

    The rendering method is chosen based on either the filename extension
    or the optional 'type' argument. Valid values of the latter are:
    ps, pdf, or png. These correspond to the recognized filename extensions.

    If the 'dims' argument is supplied, the default page size or image
    dimensions are overridded. Note that the units of this argument
    depend on the file type. For types 'ps' and 'pdf', 'dims' is measured in
    points; for 'png', it is measured in pixels. The default for the former
    file types is omega.util.LetterDims while for the latter is is
    omega.util.BigImageSize.

    Any extra keyword arguments are passed to the appropriate render-function
    constructor function.
    """
    
    if type == 'ps' or filename[-3:] == '.ps':
        if dims is None: dims = LetterDims
        f = PostScript (filename, dims, **kwargs)
    elif type == 'pdf' or filename[-4:] == '.pdf':
        if dims is None: dims = LetterDims
        f = PDF (filename, dims, **kwargs)
    elif type == 'svg' or filename[-4:] == '.svg':
        if dims is None: dims = LetterDims
        f = SVG (filename, dims, **kwargs)
    elif type == 'png' or filename[-4:] == '.png':
        if dims is None: dims = BigImageSize
        f = PNG (filename, dims, **kwargs)
    else:
        raise Exception ('Cannot guess file type and no hint given')

    painter.render (f)

_dumpSerial = 0
dumpName = 'omegaDump%02d.ps'

def dumpPainter (painter, **kwargs):
    global _dumpSerial, dumpName

    _dumpSerial += 1
    fn = dumpName % (_dumpSerial)

    savePainter (painter, fn, **kwargs)

def resetDumpSerial ():
    global _dumpSerial
    _dumpSerial = 0

#import sources, base, bag, styles, stamps
#from rect import XYDataPainter, RectPlot, FieldPainter

class Template (object):
    def add (self, x, y):
        raise NotImplementedException ()

    def show (self, **kwargs):
        self.painter.show (**kwargs)

    def showNew (self, **kwargs):
        self.painter.showNew (**kwargs)

    def renderBasic (self, ctxt, style, w, h):
        self.painter.renderBasic (self, ctxt, style, w, h)

    def render (self, func):
        self.painter.render (func)

    def save (self, filename, **kwargs):
        self.painter.save (filename, **kwargs)

    def dump (self, **kwargs):
        self.painter.dump (**kwargs)
