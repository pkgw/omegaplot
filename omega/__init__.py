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
