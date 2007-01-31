# OmegaPlot main module

from base import *

import bag
import gtkThread
import gtkUtil
import layout
import sources
import stamps
import styles

from bag import Bag
from layout import Overlay, Grid
from styles import BlackOnWhiteBitmap, WhiteOnBlackBitmap
from sources import Function

# FIXME: we might want to import a different
# class depending on what toolkit is available (eg,
# if there is ever a qtUtil).

from gtkUtil import LiveDisplay
