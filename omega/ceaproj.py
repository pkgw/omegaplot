# -*- mode: python; coding: utf-8 -*-
# Copyright 2012, 2014 Peter Williams
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

# Simple Lambert cylindrical equal-area (CEA) projection of the sphere.

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np

from . import rect, sphere


_makeLatPainter = lambda ax: sphere.AngularAxisPainter (ax, 180./np.pi,
                                                        sphere.DISPLAY_DMS, sphere.WRAP_LAT)

_lonstyles = {
    'lon': lambda ax: sphere.AngularAxisPainter (ax, 180./np.pi,
                                                 sphere.DISPLAY_DMS, sphere.WRAP_POS_DEG),
    'ra': lambda ax: sphere.AngularAxisPainter (ax, 12./np.pi,
                                                sphere.DISPLAY_HMS, sphere.WRAP_POS_HR),
    'ha': lambda ax: sphere.AngularAxisPainter (ax, 12./np.pi,
                                                sphere.DISPLAY_HMS, sphere.WRAP_ZCEN_HR),
}


class SphereCEAProjection (rect.RectCoordinates):
    def __init__ (self, lon0, field_or_plot=None, negatex=False, lonstyle='lon'):
        super (SphereCEAProjection, self).__init__ (field_or_plot)

        if lonstyle not in _lonstyles:
            raise ValueError ('unknown longitude axis style "%s"' % lonstyle)

        self.lon0 = lon0
        self.negatex = negatex
        self.lonstyle = lonstyle


    def makeAxis (self, side):
        axis = rect.CoordinateAxis (self, side)

        if side in (rect.RectPlot.SIDE_LEFT, rect.RectPlot.SIDE_RIGHT):
            axis.defaultPainter = _makeLatPainter
        else:
            axis.defaultPainter = _lonstyles[self.lonstyle]

        return axis


    def lin2arb (self, linx, liny):
        linx = np.atleast_1d (linx)
        liny = np.atleast_1d (liny)

        assert linx.ndim == 1, 'can only handle 1d case right now'

        # Deal with vectorization that Numpy makes implicit:
        # e.g., arbx.size = n, arby.size = 1

        if linx.size == 1:
            linxval = linx[0]
            linx = np.empty (liny.shape, linx.dtype)
            linx.fill (linxval)

        if liny.size == 1:
            linyval = liny[0]
            liny = np.empty (linx.shape, liny.dtype)
            liny.fill (linyval)

        if self.negatex:
            linx = -linx

        # result[0] = arbx = longitude = lambda,
        # result[1] = arby = latitude = phi
        # TODO: not sure if this (-pi)-to-pi normalization is what we should
        # be doing in the reverse mapping here.

        result = np.empty ((2, linx.size))
        result[0] = ((self.lon0 + linx + np.pi) % (2 * np.pi)) - np.pi
        result[1] = np.arcsin (liny)
        return result


    def arb2lin (self, arbx, arby):
        # arbx = longitude = lambda, arby = latitude = phi
        lon = np.atleast_1d (arbx)
        lat = np.atleast_1d (arby)

        assert lon.ndim == 1, 'can only handle 1d case right now'

        if lon.size == 1:
            lonval = lon[0]
            lon = np.empty (lat.shape, lon.dtype)
            lon.fill (lonval)

        if lat.size == 1:
            latval = lat[0]
            lat = np.empty (lon.shape, lat.dtype)
            lat.fill (latval)

        result = np.empty ((2, lon.size))
        result[0] = ((lon - self.lon0 + np.pi) % (2 * np.pi)) - np.pi
        result[1] = np.sin (lat)

        if self.negatex:
            result[0] *= -1

        return result
