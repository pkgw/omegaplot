#!/usr/bin/env python

"""Render snippets of LaTeX code into small PNG files.

Derived from htmlatex.py (http://www.meangrape.com/htmlatex/) by
Jay Edwards, which in turn is "based on mt-math by A.M. Kuchling
(http://www.amk.ca/python/code/mt-math) which is based on eqhtml.py by
Kjell Magne Fauske (http://fauskes.net/nb/htmleqII/eqhtml.py)."

Modified from all of these for non-web-server use. Importantly, all
the sanitization code has been removed, so you don't want to hook this
back up to a web server.

If this module is run as a program, it will expect an argument of
a LaTeX snippet and a filename base, and it will render the snippet
into the specified file with a .png extension.

Methods:

renderSnippets -- Renders a set of latex snippets into a sequence
  of PNG-format files.

Classes:

RenderConfig -- Structure containing parameters configuring how the
  rendering code interacts with the OS environment.

SnippetCache -- Maintains a list of snippets to be generated and
  renders them in chunks, and allows retrieval of already-rendered
  snippets without rerunning latex

Variables:

defaultConfig -- An instance of RenderConfig that has sensible defaults.

"""

import sys, os
import cairo, gtk
from os.path import basename, splitext, join, abspath, exists
import tempfile
import md5

class RenderConfig (object):
    """A simple structure containing parameters used by the
    renderSnippets function.
    
    Variables:

    texprogram -- The tex program to run; defaults to 'latex'. It is NOT
      checked whether the program is present.

    texflags -- Flags to pass to texprogram. Defaults to
      '-interaction scrollmode' to not have LaTeX pause for input if there
      are any issues with the input.

    pngprogram -- The program to convert DVI files to PNG. Defaults to
      'dvipng'. It is NOT checked whether this program is present.
  
    pngflags -- Flags to pass to pngprogram. Defaults to
      '-T tight -D 100 -z 9 -bg Transparent'.

    shutup -- Flags appended to a command-line to suppress program output.
      Defaults to '>/dev/null'.

    noinput -- Flags appended to a command-line to prevent a program from
      accepting input. Defaults to '</dev/null'.
    
    preamble -- The very first text written to the LaTeX file that is
      processed. Defaults to some sensible \usepackage commands.

    pstoedit -- FIXME

    dvips -- FIXME

    multiext -- FIXME

    supershutup -- FIXME

    midamble -- The text that is written after the user header and before
      the snippets. Sets the pagestyle to empty, a \usepackage{preview},
      and a \begin{document}.
    """

    # FIXME: the -D 100 parameter sets the DPI used by dvipng, sort of.
    # (There are a lot of words in the manpage about that argument.)
    # We shouldn't just make up a value or it will come back to bite us
    # in the ass.

    texprogram = 'latex'
    texflags = '-interaction scrollmode'
    pngprogram = 'dvipng'
    pngflags = '-T tight -D 100 -z 9 -bg Transparent'
    shutup = '>/dev/null'
    noinput = '</dev/null'
    dvips = 'dvips'
    dvipsflags = '-q -f -E -D 600 -y 1500'
    pstoedit = 'pstoedit'
    multiext = '_%03d'
    supershutup = '2>&1'

    _debug = False

    # From original source:
    # "Include your favourite LaTeX packages and commands here
    # ------ NOTE: please leave \usepackage{preview} as the last package
    # ------       it plays a role with dvipng in generating to correct
    # ------       offset for inline equations"
    #
    # I have looked into this a little. The preview package is part of
    # the GNU AUCTeX extensions to LaTeX which are mainly aimed at
    # integrating LaTeX and Emacs. It's used here because one thing that
    # the preview package does is add some more information into DVI files
    # that helps with the computation of bounding boxes. Specifically,
    # it seems that the bounding box of an equation, say, normally has to
    # be computed from the bounding boxes of the PostScript characters that
    # go into it. However, this bounding box may be far too small if some
    # of the characters (eg, integral sign) aren't known, and software like
    # DVIPNG will then give bad results. The preview package adds fake 0-size
    # images in the corners of such LaTeX groups, so that the correct bounding
    # boxes will be calculated by DVI processing programs.
    
    preamble = r'''
\documentclass[12pt]{article} 
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{mathrsfs}
\usepackage{gensymb}
'''

    midamble = r'''
\usepackage{preview}
\pagestyle{empty} 
\begin{document} 
'''

defaultConfig = RenderConfig ()

# Functions to perform various rendering steps

def _run (shellcmd, cfg):
    if cfg._debug:
        print >>sys.stderr, 'Running:', shellcmd

    ret = os.system (shellcmd)

    assert ret == 0, ('Command returned %d: ' % ret) + shellcmd
    
def _recklessUnlink (name, cfg):
    if cfg._debug: return

    try: os.unlink (name)
    except: pass

def _recklessMultiUnlink (count, tmpl, cfg):
    if cfg._debug: return

    if count == 1: 
        _recklessUnlink (tmpl)
    else:
        for i in xrange (0, count):
            _recklessUnlink (tmpl % i)

def _makeDvi (snips, texbase, header, cfg):
    if cfg._debug: shutflag = ''
    else: shutflag = cfg.shutup
    
    texfile = texbase + '.tex'

    # Write out the TeX file
    
    f = file (texfile, 'w')
    f.write (cfg.preamble)
    if header is not None: f.write (header)
    f.write (cfg.midamble)

    first = True
    
    for snip in snips:
        f.write ('\n')
        if not first: f.write ('\\newpage\n')
        else: first = False
        f.write (snip)
        f.write ('\n')

    f.write ('\\end{document}\n')
    f.close ()
    del f

    # Run LaTeX

    _run ('%s %s \'%s\' %s %s' % (cfg.texprogram, cfg.texflags, texfile,
                                  shutflag, cfg.noinput), cfg)

    if not cfg._debug:
        os.unlink (texfile)
        os.unlink (texbase + '.aux')
        os.unlink (texbase + '.log')

    return texbase + '.dvi'

def _makePngs (dvifile, pngtmpl, count, cfg):
    if cfg._debug: shutflag = ''
    else: shutflag = cfg.shutup

    _run ('%s %s -o \'%s\' %s %s' % (cfg.pngprogram, cfg.pngflags, pngtmpl,
                                     dvifile, shutflag), cfg)

    if '%' in pngtmpl:
        return [pngtmpl % i for i in xrange (0, count)]
    assert count == 1
    return [pngtmpl]


def _makeEpss (dvifile, epsbase, count, cfg):
    if cfg._debug: shutflag = ''
    else: shutflag = cfg.shutup

    if count > 1: iflag = '-i'
    else: iflag = ''

    _run ('%s %s %s -o \'%s.eps\' %s %s' % (cfg.dvips, cfg.dvipsflags, iflag, epsbase,
                                            dvifile, shutflag), cfg)

    if count == 1:
        return [epsbase + '.eps']
    else:
        return ['%s.%03d' % (epsbase, i+1) for i in xrange (0, count)]

def _makeSvgs (dvifile, epsbase, svgtmpl, count, cfg):
    if cfg._debug: shutflag = ''
    else: shutflag = cfg.shutup + ' ' + cfg.supershutup

    epsfiles = _makeEpss (dvifile, epsbase, count, cfg)

    if count == 1:
        _run ('%s -f svg \'%s\' \'%s\' %s' % (cfg.pstoedit, epsfiles[0], svgtmpl, shutflag), cfg)
        svgfiles = [svgtmpl]
    else:
        svgfiles = []
        for i in xrange (0, count):
            fout = svgtmpl % i
            _run ('%s -f svg \'%s\' \'%s\' %s' % (cfg.pstoedit, epsfiles[i], fout, shutflag), cfg)
            svgfiles.append (fout)

    return epsfiles, svgfiles

def _getBBox (epsfile):
    f = file (epsfile, 'r')
    first = True

    x1 = None

    for l in f:
        if first:
            assert l.startswith ('%!PS')
            first = False
        else:
            if not l.startswith ('%%'): break

            if l.startswith ('%%BoundingBox:'):
                x1, y1, x2, y2 = (int (x) for x in l.split ()[1:])

    assert x1 is not None, 'Couldn\'t find EPS file bounding box'
    return x1, y2, x2 - x1, y2 - y1
    
def _makeSks (dvifile, epsbase, sktmpl, count, checkExists, cfg):
    if cfg._debug: shutflag = ''
    else: shutflag = cfg.shutup + ' ' + cfg.supershutup

    epsfiles = _makeEpss (dvifile, epsbase, count, cfg)

    # We want bounding boxes for Cairo rendering

    if count == 1:
        if not checkExists or not exists (sktmpl):
            _run ('%s -f sk -dt -ssp \'%s\' \'%s\' %s' % (cfg.pstoedit, epsfiles[0], 
                                                          sktmpl, shutflag), cfg)
        skfiles = [sktmpl]
        bboxes = [_getBBox (epstmpl)]
    else:
        skfiles = []
        bboxes = []
        for i in xrange (0, count):
            fout = sktmpl % i
            if not checkExists or not exists (fout):
                _run ('%s -f sk -dt -ssp \'%s\' \'%s\' %s' % (cfg.pstoedit, epsfiles[i], 
                                                              fout, shutflag), cfg)
            skfiles.append (fout)
            bboxes.append (_getBBox (epsfiles[i]))

    return epsfiles, skfiles, bboxes

# End-to-end renderers
#
# Return convention: single string means output
# is a multipage format with all of the snippets
#
# list means output is a one-file-per-snippet format

def _render_dvi (snips, outbase, header, cfg):
    return _makeDvi (snips, outbase, header, cfg)

def _render_eps (snips, outbase, header, cfg):
    dvifile = _makeDvi (snips, outbase, header, cfg)

    try:
        return _makeEpss (dvifile, outbase, len (snips), cfg)
    finally:
        _recklessUnlink (dvifile, cfg)

    
def _render_png (snips, outbase, header, cfg):
    count = len (snips)

    if count > 1: pngtmpl = outbase + cfg.multiext + '.png'
    else: pngtmpl = outbase + '.png'

    dvifile = _makeDvi (snips, outbase, header, cfg)

    try:
        return _makePngs (dvifile, pngtmpl, count, cfg)
    finally:
        _recklessUnlink (dvifile, cfg)

def _render_svg (snips, outbase, header, cfg):
    count = len (snips)

    if count > 1: svgtmpl = outbase + cfg.multiext + '.svg'
    else: svgtmpl = outbase + '.svg'

    dvifile = _makeDvi (snips, outbase, header, cfg)
    
    try:
        epss = [] # in case makesvgs dies
        epss, svgs = _makeSvgs (dvifile, outbase, svgtmpl, count, cfg)
    finally:
        _recklessUnlink (dvifile, cfg)
        for f in epss: _recklessUnlink (f, cfg)

    return svgs

def _render_sk (snips, outbase, header, cfg, getbbs=False, checkExists=False):
    count = len (snips)

    if count > 1: sktmpl = outbase + cfg.multiext + '.sk'
    else: sktmpl = outbase + '.sk'

    dvifile = _makeDvi (snips, outbase, header, cfg)

    try:
        epss = []
        epss, sks, bbs = _makeSks (dvifile, outbase, sktmpl, count, checkExists, cfg)
    finally:
        _recklessUnlink (dvifile, cfg)
        for f in epss: _recklessUnlink (f, cfg)

    if getbbs: return sks, bbs
    return sks

_renderMap = {}

def _makeRenderMap ():
    for (name, val) in globals ().iteritems ():
        if not name.startswith ('_render_'): continue
        _renderMap[name[8:]] = val

_makeRenderMap ()

# High-level rendering functions

def renderSnippet (snip, outbase, fmt, header=None, cfg=defaultConfig, **kwargs):
    return _renderMap[fmt] ([snip], outbase, header, cfg, **kwargs)

def renderSnippets (snips, outbase, fmt, header=None, cfg=defaultConfig, **kwargs):
    return _renderMap[fmt] (snips, outbase, header, cfg, **kwargs)

def _guessFmt (outfile):
    base, ext = splitext (outfile)
    ext = ext[1:]

    assert ext in _renderMap, 'Unknown output format "%s"' % ext

    return base, ext

def renderToFile (snip, outfile, header=None, cfg=defaultConfig, **kwargs):
    base, fmt = _guessFmt (outfile)
    return renderSnippet (snip, base, fmt, header, cfg, **kwargs)

# No renderToFiles since interpolating the image number into the
# middle of the filename would be a bit weird

# Utility: class to render a Skencil file in a Cairo context.
# Only supports enough to render pstoedit'ed LaTeX documents...

# SCR global functions - no ctxt

def _scrg_document ():
    #print 'document'
    pass

def _scrg_layer (name, visible, printable, locked, outlined, *rest):
    #print 'layer', visible, printable, locked, outlined, rest
    pass

def _scrg_guess_cont ():
    #print 'guess_cont'
    pass

# SCR local functions -- need ctxt

def _scrl_fp (ctxt, color):
    # fill pattern
    #print 'fp', color
    ctxt.set_source_rgb (*color)

def _scr_nullfp (color): pass

def _scrl_le (ctxt):
    # line pattern empty
    #print 'le'
    ctxt.set_dash ([])

def _scrl_b (ctxt):
    # begin bezier
    #print 'b'
    ctxt.new_path ()

def _scrl_bs (ctxt, x, y, cont):
    # bezier straightline
    #print 'bs', x, y, cont
    ctxt.line_to (x, y)

def _scrl_bc (ctxt, x1, y1, x2, y2, x, y, cont):
    # bezier curve?
    #print 'bc', x1, y1, x2, y2, x, y, cont
    ctxt.curve_to (x1, y1, x2, y2, x, y)

def _scrl_bC (ctxt):
    # bezier close
    #print 'bC'
    ctxt.fill ()

def _scr_makeDoer (func, ctxt):
    def f (*args):
        func (ctxt, *args)
    return f

_scrGlobals = {}

def _populateScrGlobals ():
    for (name, val) in globals ().iteritems ():
        if not name.startswith ('_scrg_'): continue
        rest = name[6:]
        _scrGlobals[rest] = val

_populateScrGlobals ()

def _makeScrLocals (ctxt):
    d = {}

    for (name, val) in globals ().iteritems ():
        if not name.startswith ('_scrl_'): continue
        rest = name[6:]
        d[rest] = _scr_makeDoer (val, ctxt)

    return d
    
class SkencilCairoRenderer (object):
    def __init__ (self, filename, bbx, bby, bbw, bbh):
        self.bbx = bbx
        self.bby = bby
        self.bbw = bbw
        self.bbh = bbh

        source = file (filename, 'r').read ()
        self.compiled = compile (source, filename, 'exec')

    def render (self, ctxt, ignoreColor=False):
        l = _makeScrLocals (ctxt)

        if ignoreColor:
            l['fp'] = _scr_nullfp

        ctxt.save ()
        #ctxt.translate (0, -self.bbh)
        ctxt.scale (1, -1)
        ctxt.translate (-self.bbx, -self.bby)
        eval (self.compiled, _scrGlobals, l)
        ctxt.restore ()

# Now, a cache for rendering multiple snippets with Cairo ...

_expiredString = 'dontevertrytorenderthis'

class CairoCache (object):
    """Generates a set of snippets at once and caches the results in a
    temporary directory. This class can be used to manage a whole set of
    snippets, generating and retrieving them efficiently.

    All the work of rendering the snippets is farmed out to the
    renderSnippets routine.
    
    Methods:

    __init__ -- Creates the object; optional arguments of the directory
      in which to cache the files and the preamble header to insert into
      the generated LaTeX file.

    addSnippet -- Request that a snippet be rendered. Returns a handle
      which can be used to retrieve it after rendering.

    renderAll -- Render all of the registered snippets.

    renderOne -- Render one specified snippet.

    expire -- Request that the specified snippet no longer be rendered.

    getSnippet -- Return the snippet text associated with a handle.

    getOutfile -- Return the name of the output file that contains the
      rendered form of the snippet.

    close -- Delete all of the snippets and the temporary directory.

    __del__ -- Calls close() if possible.

    Properties:

    texbase -- The texbase parameter passed to renderSnippets. Should
      not be needed outside of the class implementation.

    outbase -- The outbase parameter passed to renderSnippets. Should
      not be needed outside of the class implementation.
    """
    
    texbase = 'tex'
    outbase = 'out'
    
    def __init__ (self, cdir=None, header=None, cfg=defaultConfig):
        """Create a SnippetCache object.
        Arguments:

        cdir (optional) -- The directory in which the temporary
          files are stored. Defaults to a value returned by
          tempfile.mkdtemp

        header (optional) -- Passed verbatim as the header
          parameter of the renderSnippets routine.

        cfg (optional, defaults to defaultConfig) -- A RendererConfig
          instance that is handed off to renderSnippets.
        
        """
        
        if not cdir:
            cdir = tempfile.mkdtemp ('latexsnippetcache')

        self.cdir = cdir
        self.header = header
        self.cfg = cfg
        self.snips = [] # list of snippet strings
        self.refcounts = []
        self.outputs = None
        self.renderers = []

    def addSnippet (self, snip):
        """Tell the cache to render the specified snippet. Returns
        a handle object which can be used to retrieve the snippet
        later. If a snippet with the same text has already been
        added, the handle of that snippet is returned.

        Arguments:

        snip -- The snippet text. It is converted into a string and
          stripped before processing. Note that equations must be
          surrounded by $$ or \[\] in order to be processed as such.

        Returns: A handle object. Current implementation makes that
        object an integer, but this should not be relied upon.
        """
        
        # A much simpler hash might be better. I dunno. And the
        # lookup in the flat array is definitely not going to be
        # fast. But this will work for the time being.
        
        snip = str (snip).strip ()

        try:
            idx = self.snips.index (snip)
            self.refcounts[idx] += 1
            return idx
        except ValueError:
            pass
        
        self.snips.append (snip)
        self.refcounts.append (1)
        return len (self.snips) - 1

    def renderAll (self):
        """Render all of the registered snippets in one pass.
        Merely farms out the work to renderSnippets.

        Arguments: None
        Returns: None
        """
        
        pwd = abspath (os.curdir)
        
        try:
            os.chdir (self.cdir)
            sks, self.bbs = renderSnippets (self.snips, self.outbase, 'sk',
                                            self.header, self.cfg, getbbs=True,
                                            checkExists=True)
        finally:
            os.chdir (pwd)

        assert isinstance (sks, list)

        self.outputs = [join (self.cdir, x) for x in sks]

        #print 'post-render', len (self.renderers), len (self.snips)
        #print self.renderers

        # for all new snippets ...
        for i in xrange (len (self.renderers), len (self.snips)):
            self.renderers.append (SkencilCairoRenderer (self.outputs[i], *self.bbs[i]))

    def expire (self, handle):
        """Request that the specified snippet no longer be rendered.
        After calling this function, use of the handle object will
        result in undefined behavior. (Ideally this behavior would be
        an exception but I am too lazy to implement checking.) The files
        associated with the snippet are deleted when this function is called.

        Arguments:

        handle -- The handle of the snippet to expire from the cache. This
          should be a value returned by addSnippet.

        Returns: None
        """

        self.refcounts[handle] -= 1

        if self.refcounts[handle] > 0:
            return
        
        if handle >= len (self.outputs):
            # Was the snippet ever actually rendered?
            # Just delete the file for now and don't waste time regenerating the snippet
            try:
                os.remove (self.outputs[handle])
            except:
                pass
            
            self.renderers[handle] = None

        self.snips[handle] = _expiredString

    def getSnippet (self, handle):
        """Retrieve the equation text associated with a snippet handle.
        This text may not be identical to the value passed to addSnippet,
        since that object is stringified and stripped before being stored.

        Arguments:

        handle -- The handle of the snippet to retrieve. This
          should be a value returned by addSnippet.

        Returns: The text associated with that handle
        """
        
        return self.snips[handle]
    
    def getRenderer (self, handle):
        """Returns the absolute path of the output file containing the
        rendered form of the snippet associated with the handle. If the
        snippet has not yet been rendered, that is done so first.

        Arguments:

        handle -- The handle of the snippet to retrieve. This
          should be a value returned by addSnippet.

        Returns: The absolute path name of the output file containing the
        rendered form of the snippet.
        """

        if len (self.renderers) <= handle:
            self.renderAll ()

        if self.renderers[handle] is None:
            print 'oh no!'
            print 'h', handle
            print 's', self.snips[handle]
            print 'o', self.outputs[handle]
            raise Exception ()
        
        return self.renderers[handle]

    def close (self):
        """Deletes every file in the cache's temporary directory, then
        deletes the directory itself. The cache will be unusuable after
        a call to this function.

        Arguments: None
        Returns: None
        """

        if self.cfg._debug: return
        
        for f in os.listdir (self.cdir):
            os.remove (join (self.cdir, f))
        os.rmdir (self.cdir)

    def __del__ (self):
        """Calls close() if possible."""
        
        if hasattr (self, 'cdir') and os and hasattr (os, 'path'):
            self.close ()

if __name__ == '__main__':
    import sys

    if len (sys.argv) != 3:
        print 'Usage: %s \'snippet\' outfile' % (sys.argv[0])
        sys.exit (1)

    renderToFile (sys.argv[1], sys.argv[2])
    sys.exit (0)
