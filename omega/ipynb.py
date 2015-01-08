# -*- mode: python; coding: utf-8 -*-
# Copyright 2014 Peter Williams
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

from __future__ import absolute_import, division, print_function, unicode_literals

# XXX: I'd like to use SVG graphics, but I ran into problems with corrupted
# output with multiple plots in a notebook. See the history for SVG-writing
# code.

import cairo, os, StringIO, tempfile
from IPython.display import display, Image

from . import styles, render

defaultStyle = styles.ColorOnWhiteBitmap
defaultDims = (600, 400)


class NotebookDisplayPager (render.DisplayPager):
    def __init__ (self, dims=defaultDims, style=None):
        if style is None:
            style = defaultStyle ()

        self.style = style
        self.dims = dims

    def canPage (self):
        return False

    def isReusable (self):
        return True

    def send (self, painter):
        w, h = self.dims

        surf = cairo.ImageSurface (cairo.FORMAT_ARGB32, w, h)

        def renderfunc (prend):
            ctxt = cairo.Context (surf)
            prend (ctxt, self.style, w, h)
            ctxt.show_page ()

        painter.render (renderfunc)

        buf = StringIO.StringIO ()
        surf.write_to_png (buf)
        surf.finish ()
        data = buf.getvalue ()
        buf.close ()

        display (Image (data=data))

    def done (self):
        pass


render.setDisplayPagerClass (NotebookDisplayPager)
