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

import cairo, os, tempfile

from IPython.display import display, SVG

import styles, render

defaultStyle = styles.ColorOnWhiteVector
defaultDims = (400, 300) # points

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

        # TODO: Cairo 1.2 has "cairo_svg_surface_create_for_stream", which
        # should allow us to render into memory rather than use a temporary
        # file, but I haven't found a Python binding that lets us access it.

        tf = tempfile.NamedTemporaryFile (delete=False)
        tf.close ()

        surf = cairo.SVGSurface (tf.name, w, h)

        def renderfunc (prend):
            ctxt = cairo.Context (surf)
            prend (ctxt, self.style, w, h)
            ctxt.show_page ()

        painter.render (renderfunc)

        surf.finish ()
        svg = open (tf.name).read ()

        try:
            os.unlink (tf.name)
        except Exception:
            pass

        display (SVG (data=svg))

    def done (self):
        pass


render.setDisplayPagerClass (NotebookDisplayPager)
