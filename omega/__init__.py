# -*- mode: python; coding: utf-8 -*-
# Copyright 2011, 2012, 2014 Peter Williams
#
# This file is part of omegaplot.
#
# Omegaplot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Omegaplot is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Omegaplot. If not, see <http://www.gnu.org/licenses/>.

r"""
.. This docstring is read and processed by Sphinx to create the full
   OmegaPlot documentation. It should be readable as-is but the
   processed documentation is much nicer.

.. sectionauthor:: Peter Williams <peter@newton.cx>

This is API reference documentation for the :mod:`omega` module. For a
general introduction to OmegaPlot, please see the
:ref:`full documentation <index>`.
"""

__version__ = "0.dev0"  # cranko project-version

from .base import *
from .rect import *
from . import layout, rect, render, stamps, styles, util

from .layout import Overlay, Grid
from .styles import BlackOnWhiteBitmap, WhiteOnBlackBitmap
from .util import (
    quickXY,
    quickXYErr,
    quickDF,
    quickHist,
    quickContours,
    quickImage,
    quickPager,
    _demo,
)
from .render import makePager, makeDisplayPager, getLatestPainter as latest
