# Copyright 2011 Peter Williams
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

# Support for plot axes derived from coordinates embedded in a CASA
# image access with pyrap.

# FIXME: we're hardcoding which axes are the lat/lon axes, etc etc

import numpy as N
from omega import rect, sphere


def _makeRAPainter (axis):
    return sphere.AngularAxisPainter (axis, 12./N.pi,
                                      sphere.DISPLAY_HMS, sphere.WRAP_POS)

def _makeLatPainter (axis):
    return sphere.AngularAxisPainter (axis, 180./N.pi,
                                      sphere.DISPLAY_DMS, sphere.WRAP_ZCEN)

def _makeLonPainter (axis):
    return sphere.AngularAxisPainter (axis, 180./N.pi,
                                      sphere.DISPLAY_DMS, sphere.WRAP_POS)


class PyrapImageCoordinates (rect.RectCoordinates):
    def __init__ (self, image, field_or_plot):
        """*dircoords* are direction coordinates accessed from pyrap.
If you have a pyrap image, you get these via::

  im.coordinates() ['direction']
"""

        super (PyrapImageCoordinates, self).__init__ (field_or_plot)
        self.image = image


    def makeAxis (self, side):
        axis = rect.CoordinateAxis (self, side)

        if side in (rect.RectPlot.SIDE_TOP, rect.RectPlot.SIDE_BOTTOM):
            axidx = 1
        else:
            axidx = 0

        axtype = self.image.coordinates ()['direction'].get_axes ()[axidx]

        if axtype == 'Right Ascension':
            axis.defaultPainter = _makeRAPainter
        elif axtype == 'Declination':
            axis.defaultPainter = _makeLatPainter
        elif axtype == 'Longitude':
            axis.defaultPainter = _makeLonPainter
        elif axtype == 'Latitude':
            axis.defaultPainter = _makeLatPainter
        elif axtype == 'Hour Angle':
            axis.defaultPainter = _makeRAPainter
        else:
            raise Exception ('Don\'t know what to do with axis of '
                             'type ' + axtype)

        return axis


    def lin2arb (self, linx, liny):
        linx = N.atleast_1d (linx)
        liny = N.atleast_1d (liny)

        assert linx.ndim == 1, 'can only handle 1d case right now'

        # Deal with vectorization that Numpy makes implicit:
        # e.g., arbx.size = n, arby.size = 1

        if linx.size == 1:
            linxval = linx[0]
            linx = N.empty (liny.shape, linx.dtype)
            linx.fill (linxval)

        if liny.size == 1:
            linyval = liny[0]
            liny = N.empty (linx.shape, liny.dtype)
            liny.fill (linyval)

        result = N.empty ((2, linx.size))
        coords = N.zeros (self.image.ndim ())

        for i in xrange (linx.size):
            coords[-1] = linx[i] # RA is last coord
            coords[-2] = liny[i]
            r = self.image.toworld (coords)
            result[0,i] = r[-1] # RA -> x
            result[1,i] = r[-2] # dec -> y

        return result


    def arb2lin (self, arbx, arby):
        arbx = N.atleast_1d (arbx)
        arby = N.atleast_1d (arby)

        # along with all of the other bad stuff we're assuming, this
        # function also assumes that it doesn't affect our results to
        # set the physical coordinates all to ones. The reason we're
        # using ones is that a Stokes coordinate of zero is illegal
        # ... Good times.

        assert arbx.ndim == 1, 'can only handle 1d case right now'

        # Deal with vectorization that Numpy makes implicit:
        # e.g., arbx.size = n, arby.size = 1

        if arbx.size == 1:
            arbxval = arbx[0]
            arbx = N.empty (arby.shape, arbx.dtype)
            arbx.fill (arbxval)

        if arby.size == 1:
            arbyval = arby[0]
            arby = N.empty (arbx.shape, arby.dtype)
            arby.fill (arbyval)

        result = N.empty ((2, arbx.size))
        coords = N.ones (self.image.ndim ())

        for i in xrange (arbx.size):
            coords[-1] = arbx[i] # x is last coord
            coords[-2] = arby[i]
            r = self.image.topixel (coords)
            result[0,i] = r[-1] # x -> ra
            result[1,i] = r[-2] # y -> dec

        return result
