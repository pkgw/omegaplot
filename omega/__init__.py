# OmegaPlot main module

from base import *

import bag
import gtkThread
import gtkUtil
import sources
import stamps
import styles

from bag import Bag
from styles import BlackOnWhiteBitmap, WhiteOnBlackBitmap
from sources import Function
from gtkUtil import LiveDisplay # FIXME: import different class depending on what toolkit is available
