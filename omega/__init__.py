# OmegaPlot main module

from base import *
from rect import *

import bag, gtkThread, gtkUtil, layout, rect, \
       sources, stamps, styles, util

from bag import Bag
from layout import Overlay, Grid
from styles import BlackOnWhiteBitmap, WhiteOnBlackBitmap
from sources import Function, StoredData
from util import dump, LiveDisplay, PaintPipeline, LetterFile, InchesFile, LargePngFile

QP = util.makeQuickPipeline
QD = util.makeQuickDisplay
RSP = util.makeRectSkeletonPipeline

def MQD (*args, **kwargs):
    if len (args) < 1: raise Exception ('dumbass')
    
    xmin = kwargs.get ('xmin')
    xmax = kwargs.get ('xmax')
    ymin = kwargs.get ('ymin')
    ymax = kwargs.get ('ymax')

    for s in ('xmin', 'xmax', 'ymin', 'ymax'):
        if s in kwargs: del kwargs[s]
    
    (pl, rp) = RSP ()
    tmpl = None
    
    for a in args:
        if isinstance (a, tuple):
            if len (a) != 2: raise Exception ('dumbass2')
            tmpl = util.addQuickRectDataPainter (pl, rp, a[0], yinfo=a[1],
                                                 tmpl=tmpl, **kwargs)
        else:
            tmpl = util.addQuickRectDataPainter (pl, rp, a, tmpl=tmpl, **kwargs)

    if xmin is not None:
        rp.defaultField.xaxis.min = xmin
    if xmax is not None:
        rp.defaultField.xaxis.max = xmax
    if ymin is not None:
        rp.defaultField.yaxis.min = ymin
    if ymax is not None:
        rp.defaultField.yaxis.max = ymax
        
    rp.magicAxisPainters ('lb')
    return (pl.makeLiveDisplay (), pl, rp)
