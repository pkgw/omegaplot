r"""
.. This docstring is read and processed by Sphinx to create the full
   OmegaPlot documentation. It should be readable as-is but the 
   processed documentation is much nicer.

.. sectionauthor:: Peter Williams <peter@newton.cx>

This is API reference documentation for the :mod:`omega` module. For a
general introduction to OmegaPlot, please see the 
:ref:`full documentation <index>`.
"""

from base import *
from rect import *

import layout, rect, render, stamps, styles, util

from layout import Overlay, Grid
from styles import BlackOnWhiteBitmap, WhiteOnBlackBitmap
from util import quickXY, quickXYErr, quickHist, quickPager, _demo
from render import makePager, makeDisplayPager

