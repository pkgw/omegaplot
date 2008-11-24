from base import _kwordDefaulted
    
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


# A function to easily make a demo plot to make testing of 
# rendering features quick. The purpose of these is not
# to demonstrate fancy plots, but just to give something
# quick to render.

_demoNumber = 0

def _demo ():
    global _demoNumber
    import numpy as N

    if _demoNumber == 0:
        x = N.linspace (0, 10, 100)
        p = quickXY (x, N.sin (x), 'sin(x)')
        p.addXY (x, N.cos (x), 'cos(x)')
        p.setLabels ('Radians', 'Trigginess')
    elif _demoNumber == 1:
        x = N.linspace (-5, 5, 100)
        p = quickXY (x, x**2, 'squared')
        p.addXY (x, x**3, 'cubed')
        p.setLabels ('X', 'Y')
    elif _demoNumber == 2:
        x = N.linspace (0.01, 10, 100)
        p = quickXY (x, N.log10 (x), 'base 10')
        p.addXY (x, N.log (x), 'natural')
        p.setLabels ('X', 'Log[X]')

    _demoNumber = (_demoNumber + 1) % 3
    return p


# Easy construction of pagers -- not that getting the pager
# you want is difficult, but I find that I write a lot of programs
# that I want to page either to the screen or to a file. My usual
# semantics are that argv has a filename if a file is to be used
# or is empty if the screen is to be used

def quickPager (args, **kwargs):
    import render

    if len (args) == 0:
        pg = render.makeDisplayPager (**kwargs)
    elif len (args) == 1:
        pg = render.makePager (args[0], **kwargs)
    else:
        raise ValueError ('Unexpected args to quickPager: %s' % (args, ))

    return pg


# Dumping plots -- saving them to disk conveniently.

_dumpPager = None
dumpTemplate = 'omegaDump%02d.ps'


def _makeDumpPager (**kwargs):
    from render import getFilePagerInfo, MultiFilePager, ReusingPager

    tup = getFilePagerInfo (dumpTemplate)
    if tup is None:
        raise Exception ('Unhandled dump filetype ' + dumpTemplate)

    tname, klass, dims, margins, style = tup
    p = MultiFilePager (dumpTemplate, klass, dims, margins, style)
    return ReusingPager (p)


def dumpPainter (painter, **kwargs):
    global _dumpPager
    
    if _dumpPager is None:
        _dumpPager = _makeDumpPager (**kwargs)

    painter.sendTo (_dumpPager)
    print 'Dumped to \"%s\".' % _dumpPager.spager.lastFile


def resetDumping ():
    global _dumpPager
    _dumpPager = None
