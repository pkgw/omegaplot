import cairo
from numpy import pi

import styles


# The abstract Pager class

class Pager (object):
    def canPage (self):
        # Can you call send() more than once before you
        # have to call done?
        raise NotImplementedError ()


    def isReusable (self):
        # Can you do anything with this instance after
        # you call done() ?
        raise NotImplementedError ()


    def send (self, painter):
        raise NotImplementedError ()


    def sendMany (self, piter):
        for p in piter:
            self.send (p)


    def done (self):
        raise NotImplementedError ()


class DisplayPager (Pager):
    # This has to be able to page and to be reused
    def canPage (self): return True
    def isReusable (self): return True


# Builtin pagers for various Cairo-supported output formats

NoMargins = (0, 0, 0, 0)
LetterDims = (11.0 * 72, 8.5 * 72)
LetterMargins = (36, 36, 36, 36)
BigImageSize = (800, 600)
BigImageMargins = (4, 4, 4, 4)
EPSDims = (384, 4 * 72) # 4:3 aspect ratio, 4 in tall
EPSMargins = (8, 8, 8, 8)


class PSPager (Pager):
    def __init__ (self, filename, pagedims_in_points, margins, style, smartOrient=True,
                  useEPS=False):
        w, h = pagedims_in_points
        landscape = w > h and smartOrient

        if landscape:
            surf = cairo.PSSurface (filename, h, w)
        else:
            surf = cairo.PSSurface (filename, w, h)

        if useEPS:
            # Cairo < 1.8 (?) doesn't support this
            surf.set_eps (True)

        self.surf = surf

        def f (prend):
            surf.dsc_begin_page_setup ()
            # surf.dsc_comment ('%%IncludeFeature: *PageSize Letter')
            # FIXME: is there some DSC comment to indicate the page
            # margins?
            
            if landscape:
                surf.dsc_comment ('%%PageOrientation: Landscape')

            ctxt = cairo.Context (surf)

            if landscape:
                ctxt.translate (h/2, w/2)
                ctxt.rotate (-pi/2)
                ctxt.translate (-w/2, -h/2)
            
            ctxt.translate (margins[3], margins[0])

            weff = w - (margins[1] + margins[3])
            heff = h - (margins[0] + margins[2])
            assert weff > 0
            assert heff > 0
            prend (ctxt, style, weff, heff)
            ctxt.show_page ()

        self._rfunc = f


    def canPage (self): return True
    def isReusable (self): return False


    def send (self, painter):
        if self.surf is None:
            raise Exception ('Cannot reuse a PostScript pager')

        painter.render (self._rfunc)


    def done (self):
        self.surf.finish ()
        self.surf = None
        self._rfunc = None


def EPSPager (*args, **kwargs):
    # This is probably not the recommended way of doing this.
    kwargs['useEPS'] = True
    return PSPager (*args, **kwargs)


class PDFPager (Pager):
    # FIXME: it's not at all clear to me how to best
    # specify page sizes and margins in a PDF.

    def __init__ (self, filename, pagedims_in_points, margins, style):
        w, h = pagedims_in_points
        self.surf = surf = cairo.PDFSurface (filename, w, h)

        def f (prend):
            ctxt = cairo.Context (surf)
            ctxt.translate (margins[3], margins[0])
            weff = w - (margins[1] + margins[3])
            heff = h - (margins[0] + margins[2])
            assert weff > 0
            assert heff > 0
            prend (ctxt, style, weff, heff)
            ctxt.show_page ()

        self._rfunc = f


    def canPage (self): return True
    def isReusable (self): return False


    def send (self, painter):
        if self.surf is None:
            raise Exception ('Cannot reuse a PDF pager')

        painter.render (self._rfunc)


    def done (self):
        self.surf.finish ()
        self.surf = None
        self._rfunc = None


# FIXME: add an EPS pager when pycairo wraps PSSurface.set_eps ().
# Use a different default size than Letter paper and use no 
# margins. And use a filename extension of '.eps'.


class SVGPager (Pager):
    def __init__ (self, filename, imgsize_in_points, margins, style):
        w, h = imgsize_in_points

        self.surf = surf = cairo.SVGSurface (filename, w, h)

        def f (prend):
            ctxt = cairo.Context (surf)
            ctxt.translate (margins[3], margins[0])
            weff = w - (margins[1] + margins[3])
            heff = h - (margins[0] + margins[2])
            assert weff > 0
            assert heff > 0
            prend (ctxt, style, weff, heff)
            ctxt.show_page ()

        self._rfunc = f


    def canPage (self): return False
    def isReusable (self): return False


    def send (self, painter):
        if self._rfunc is None:
            raise Exception ('Cannot send multiple plots into SVG format')

        painter.render (self._rfunc)
        self._rfunc = None


    def done (self):
        self.surf.finish ()
        self.surf = None


class PNGPager (Pager):
    def __init__ (self, filename, imgsize_in_pixels, margins, style):
        w, h = imgsize_in_pixels

        self.filename = filename
        self.surf = surf = cairo.ImageSurface (cairo.FORMAT_ARGB32, w, h)

        def f (prend):
            ctxt = cairo.Context (surf)
            ctxt.translate (margins[3], margins[0])
            weff = w - (margins[1] + margins[3])
            heff = h - (margins[0] + margins[2])
            assert weff > 0
            assert heff > 0
            prend (ctxt, style, weff, heff)
            ctxt.show_page ()

        self._rfunc = f


    def canPage (self): return False
    def isReusable (self): return False


    def send (self, painter):
        if self._rfunc is None:
            raise Exception ('Cannot send multiple plots into PNG format')

        painter.render (self._rfunc)
        self._rfunc = None

    def done (self):
        self.surf.write_to_png (self.filename)
        self.surf.finish ()
        self.surf = None


class GridPager (Pager):
    # This accumulates multiple plots into a grid and sends
    # them to a sub-pager in batches.
    
    def __init__ (self, spager, nw, nh, nper=0):
        from layout import Grid

        nw = int (nw)
        nh = int (nh)

        if not isinstance (spager, Pager):
            raise ValueError ('Parent pager is not an instance of Pager')

        if nw < 1:
            raise ValueError ('Need grid to be at least 1 plot wide')

        if nh < 1:
            raise ValueError ('Need grid to be at least 1 plot high')

        if nper > nw * nh:
            raise ValueError ('Inconsistent value for nper')

        self.spager = spager
        self.nw = nw
        self.nh = nh
        self.nper = nper
        self.grid = Grid (nw, nh)

        self._initPage ()


    def _initPage (self):
        self.row = self.col = 0

        for r in xrange (0, self.nh):
            for c in xrange (0, self.nw):
                self.grid[c,r] = None


    def canPage (self):
        if self.nw == 1 and self.nh == 1 and not self.spager.canPage ():
            return False

        return True


    def isReusable (self):
        return self.spager.isReusable ()


    def send (self, painter):
        self.grid[self.col,self.row] = painter

        self.col += 1

        if self.nper > 0 and self.row * self.nw + self.col == self.nper:
            # We may not have filled up the grid, but we've put down
            # the requested $nper plots on this page, so finish it.
            self.finishPage ()
            return

        if self.col < self.nw:
            return

        self.col = 0
        self.row += 1

        if self.row < self.nh:
            return

        self.row = 0
        self.finishPage ()


    def finishPage (self):
        self.spager.send (self.grid)
        self._initPage ()


    def done (self):
        if self.row > 0 or self.col > 0:
            self.finishPage ()
        self.spager.done ()


class MultiFilePager (Pager):
    # Turns some sub-pager, that writes to a file, into a
    # reusable pager that writes to a new file on each
    # reuse. The new filename is varied by a simple 
    # sequence number.
    #
    # This makes the most sense to use with a subpager
    # that can't actually page. But it is not an error
    # to use this with a subpager that can page.

    def __init__ (self, filetmpl, subclass, size, margins, style, 
                  n0=1, incr=None, format=None):
        if not issubclass (subclass, Pager):
            raise ValueError ('subclass')

        self.filetmpl = filetmpl
        self.subclass = subclass
        self.size = size
        self.margins = margins
        self.style = style
        self.n = n0
        self.spager = None

        if incr is None:
            self._incr = lambda n: n + 1
        else:
            self._incr = incr

        if format is None:
            self._format = lambda t, n: t % (n, )
        else:
            self._format = format


    def _ensureSubPager (self):
        if self.spager is not None: return

        self.lastFile = self._format (self.filetmpl, self.n)
        self.spager = self.subclass (self.lastFile, self.size, self.margins, self.style)
        self.n = self._incr (self.n)


    def canPage (self):
        self._ensureSubPager ()
        return self.spager.canPage ()


    def isReusable (self):
        return True


    def send (self, painter):
        self._ensureSubPager ()
        self.spager.send (painter)


    def done (self):
        self._ensureSubPager ()
        self.spager.done ()
        self.spager = None


class ReusingPager (Pager):    
    # Turns a sub-pager that's reusable into a pager that can page.
    # This makes the most sense to use with a sub-pager that can't
    # page. But it is not an error to use this with a subpager that
    # can page.
    #
    # This pager is not classified as reusable, because the
    # difference between sending a new plot to this pager and
    # reusing it would be unclear

    def __init__ (self, spager):
        if not isinstance (spager, Pager):
            raise ValueError ('Subpager isn\'t a Pager')
        if not spager.isReusable ():
            raise ValueError ('Subpager isn\'t reusable')

        self.spager = spager


    def canPage (self): return True
    def isReusable (self): return False


    def send (self, painter):
        if self.spager is None:
            raise Exception ('Can\'t reuse a ReusingPager!')

        self.spager.send (painter)
        self.spager.done ()


    def done (self):
        self.spager = None


pagerInfo = [
 ('ps', PSPager, LetterDims, LetterMargins, styles.BlackOnWhiteVector),
 ('eps', EPSPager, EPSDims, EPSMargins, styles.BlackOnWhiteVector),
 ('pdf', PDFPager, LetterDims, LetterMargins, styles.BlackOnWhiteVector),
 ('svg', SVGPager, LetterDims, LetterMargins, styles.BlackOnWhiteVector),
 ('png', PNGPager, BigImageSize, BigImageMargins, styles.BlackOnWhiteBitmap)
]


def getFilePagerInfo (filename, type=None, dims=None, margins=None, style=None):
    for tname, klass, defdims, defmargins, defstyleclass in pagerInfo:
        if type != tname and not filename.endswith ('.' + tname):
            continue

        if dims is None: dims = defdims
        if margins is None: margins = defmargins
        if style is None: style = defstyleclass ()

        return tname, klass, dims, margins, style

    return None


def makePager (filename, type=None, dims=None, margins=None, 
               style=None, mustPage=False, nw=1, nh=1, nper=0, **kwargs):
    """Create a Pager object for rendering painters.

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
 
    doGrid = nw > 1 or nh > 1

    tup = getFilePagerInfo (filename, type, dims, margins, style)
    if tup is None:
        raise ValueError ('Cannot guess file type and no hint given')

    tname, klass, dims, margins, style = tup
    pager = klass (filename, dims, margins, style, **kwargs)

    if mustPage and not pager.canPage ():
        # We must return something that can actually page, but what we
        # got can't. Go to Plan B: layer in multifile and reusable
        # shims. This means that the output filenames are not what
        # was asked for, but that's part of the contract of 
        # mustPage=True
        from os.path import splitext
        base, ext = splitext (filename)
        tmpl = base + '%03d' + ext
        pager = MultiFilePager (tmpl, klass, dims, margins, style)
        pager = ReusingPager (pager)
    
    if doGrid:
        pager = GridPager (pager, nw, nh, nper)

    return pager



def savePainter (painter, filename, type=None, dims=None, margins=None, **kwargs):
    pager = makePager (filename, type, dims= margins, **kwargs)
    pager.send (painter)
    pager.done ()


# Display pagers -- pagers used for showing plots onscreen to a user
# There are special non-gridded "show" pagers used for Painter.show
# calls.

_displayPagerClass = None
_showPagers = {}
_lastUsedIdent = 0


def setDisplayPagerClass (klass):
    global _displayPagerClass

    assert issubclass (klass, DisplayPager)
    assert len (_showPagers) == 0

    _displayPagerClass = klass


def _loadDisplayBackend ():
    # If we ever have multiple backends, we should try them
    # sequentially, etc.
    
    import gtkInteg
    import omega

    omega.gtkInteg = gtkInteg


def makeDisplayPager (nw=1, nh=1, nper=0, mustPage=True, **kwargs):
    # We ignore mustPage, since that's always true for
    # the display pager.
    
    if _displayPagerClass is None:
        _loadDisplayBackend ()

        if _displayPagerClass is None:
            raise Exception ('Can\'t get a display backend!')

    dp = _displayPagerClass (**kwargs)

    if nw > 1 or nh > 1:
        dp = GridPager (dp, nw, nh, nper)

    return dp


def getShowPager (ident=None, **kwargs):
    # "show" pagers cannot be gridded, because
    # Painter.show () has to be guaranteed to put
    # something up on the screen, and it wouldn't know
    # when would be the right time to call the "done"
    # method.
    
    global _lastUsedIdent

    if ident is None:
        ident = _lastUsedIdent
    else:
        _lastUsedIdent = ident

    if ident in _showPagers:
        sp = _showPagers[ident]
    else:
        sp = makeDisplayPager (nw=1, nh=1, nper=0, **kwargs)
        _showPagers[ident] = sp

    return sp


def showPainter (painter, ident, **kwargs):
    pager = getShowPager (ident, **kwargs)
    pager.send (painter)
    pager.done ()
    return pager
