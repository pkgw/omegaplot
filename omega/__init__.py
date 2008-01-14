"""OmegaPlot, the last plotting package you'll ever need.

OmegaPlot is a flexible plotting package based on the
Cairo graphics system.

Names exported in the top-level namespace are:

...
"""

from base import *
from rect import *

import layout, rect, stamps, styles, util

from layout import Overlay, Grid
from styles import BlackOnWhiteBitmap, WhiteOnBlackBitmap
from util import quickXY, quickHist
