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

import os, os.path 
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
      '-T tight -D 120 -z 9 -bg Transparent'.

    shutup -- Flags appended to a command-line to suppress program output.
      Defaults to '>/dev/null'.

    noinput -- Flags appended to a command-line to prevent a program from
      accepting input. Defaults to '</dev/null'.
    
    preamble -- The very first text written to the LaTeX file that is
      processed. Defaults to some sensible \usepackage commands.

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

def renderSnippets (snips, texbase, pngbase, header=None, cfg=defaultConfig):
    """Render a list of LaTeX fragments into a sequence of PNG files.
    Arguments:

    snips -- An enumerable of fragments of LaTeX source. Note that equations
      must be enclosed in $$ or \\[\\] to be processed as such.

    texbase -- The base string filename used for the .tex file. Note that
      LaTeX outputs into the current directory regardless of any path
      components in the input filename, so processing will fail if there
      are any path components in this variable.

    pngbase -- The base string used for the output .png files. If more than
      one snippet is being processed, this argument should contain a
      printf-style integer argument of the form %d, %01d, .. %09d. The
      generated files will have sequential numbers formatted into their
      names, started with 1. A suffix of '.png' is appended to this argument
      as well. So passing in 'test%02dfile' and three snippets will create
      files named 'test01file.png', 'test02file.png', and 'test03file.png'.

    header (optional) -- An optional set of header commands to insert
      into the preamble of the generated LaTeX file. Should include
      \usepackage{} commands and the like. This header is output
      before the \begin{document} statement.

    config (optional, defaults to defaultConfig) -- A RendererConfig object
      whose fields are used to control how this function interacts with
      its environment.
    
    Returns: None.

    This runs the latex and dvipng programs using os.system (). Exceptions
    are not handled. Intermediate files are removed and program output to
    standard output are suppressed, unless the _debug variable of the module
    is True.
    """
    
    texfile = texbase + '.tex'

    if cfg._debug: shutflag = ''
    else: shutflag = cfg.shutup
    
    # Write out a TeX file
    
    f = file (texfile, 'w')
    f.write (cfg.preamble)
    if header: f.write (header)
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

    # Now run LaTeX

    os.system ('%s %s %s %s %s' % (cfg.texprogram, cfg.texflags, texfile,
                                   shutflag, cfg.noinput))

    if not cfg._debug:
        os.remove (texfile)
        os.remove (texbase + '.aux')
        os.remove (texbase + '.log')

    # Now pngify that shit

    dvifile = texbase + '.dvi'
    pngfile = pngbase + '.png'
    
    os.system ('%s %s -o \'%s\' %s %s' % (cfg.pngprogram, cfg.pngflags, pngfile,
                                          dvifile, shutflag))

    if not cfg._debug:
        os.remove (dvifile)

class SnippetCache (object):
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

    getPngFile -- Return the name of the PNG file that contains the
      rendered form of the snippet.

    close -- Delete all of the snippets and the temporary directory.

    __del__ -- Calls close() if possible.

    Properties:

    texbase -- The texbase parameter passed to renderSnippets. Should
      not be needed outside of the class implementation.

    pngbase -- The pngbase parameter passed to renderSnippets. Should
      not be needed outside of the class implementation.
    """
    
    texbase = 'tex'
    pngbase = 'png%04d'
    
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
            return self.snips.index (snip)
        except ValueError:
            pass
        
        self.snips.append (snip)
        return len (self.snips) - 1

    def renderAll (self):
        """Render all of the registered snippets in one pass.
        Merely farms out the work to renderSnippets.

        Arguments: None
        Returns: None
        """
        
        pwd = os.path.abspath (os.curdir)
        
        try:
            os.chdir (self.cdir)
            renderSnippets (self.snips, self.texbase, self.pngbase, self.header, self.cfg)
        finally:
            os.chdir (pwd)

    def renderOne (self, handle):
        """Render the specified snippet only. This may involve
        less work than rerendering all of the snippets, but it will
        be faster to render all of the snippets at once rather than
        call this function once for each snippet. The actual rendering
        is done in a call to renderSnippets ().

        Arguments:

        handle -- The handle of the snippet to render. This should be a
          value returned by addSnippet.

        Returns: None
        """
        
        pwd = os.path.abspath (os.curdir)

        snips = [self.snips[handle]]
        pngbase = self.pngbase % (handle)
        
        try:
            os.chdir (self.cdir)
            renderSnippets (snips, self.texbase, pngbase, self.header, self.cfg)
        finally:
            os.chdir (pwd)

    def _pngName (self, handle):
        return os.path.join (self.cdir, self.pngbase % (handle + 1) + '.png')

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
        
        # Just delete the file for now and don't waste time regenerating the snippet
        f = self._pngName (handle)

        try:
            os.remove (f)
        except:
            pass

        self.snips[handle] = 'X'

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
    
    def getPngFile (self, handle, regenAll=True):
        """Returns the absolute path of a PNG file containing the
        rendered form of the snippet associated with the handle. If the
        snippet has not yet been rendered, that is done so first.

        Arguments:

        handle -- The handle of the snippet to retrieve. This
          should be a value returned by addSnippet.

        regenAll (optional, defaults True) -- If True, and the PNG file
          of the specified snippet does not exist, regenerate all snippets,
          not just the one requested. Otherwise, if the associated PNG file
          does not exist, only that file is regenerated. The default behavior
          is intended so that a bunch of snippets can be added to a cache,
          and individual calls to getPngFile can be made with the first one
          generating all of the snippets at once, which is more efficient
          than generating them piecemeal.
          
        Returns: The absolute path name of a PNG file containing the
        rendered form of the snippet.
        """
        f = self._pngName (handle)

        if os.path.exists (f): return f

        if regenAll:
            self.renderAll ()
        else:
            self.renderOne (handle)

        if not os.path.exists (f):
            raise Exception ('Couldn\'t get file %s for snippet %d: \'%s\'?' % \
                             (f, handle, self.snips[handle]))

        return f

    def close (self):
        """Deletes every file in the cache's temporary directory, then
        deletes the directory itself. The cache will be unusuable after
        a call to this function.

        Arguments: None
        Returns: None
        """
        
        for f in os.listdir (self.cdir):
            os.remove (os.path.join (self.cdir, f))
        os.rmdir (self.cdir)

    def __del__ (self):
        """Calls close() if possible."""
        
        if hasattr (self, 'cdir') and os and hasattr (os, 'path'):
            self.close ()

if __name__ == '__main__':
    import sys

    if len (sys.argv) != 3:
        print 'Usage: %s \'snippet\' filename-base' % (sys.argv[0])
        sys.exit (1)

    renderSnippets ([sys.argv[1]], sys.argv[2], sys.argv[2])
    sys.exit (0)
