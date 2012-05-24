# Copyright 2011, 2012 Peter Williams
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

# Simple sine/SIN/orthographic spherical coordinate system, for when
# you want to plot spherical things but don't have a wcslib object set
# up.

import numpy as np
from omega import rect, sphere


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


class SphereSinProjection (rect.RectCoordinates):
    def __init__ (self, lon0, lat0, field_or_plot=None, negatex=False, lonstyle='lon'):
        """Note that arguments are (lon, lat) ~ (x, y) ~ (RA, dec)
        since that's the standard practice everywhere else in
        omegaplot. In other places I try to do things consistent as
        lat, lon since that's consistent with 2D array indexing in
        Python."""
        super (SphereSinProjection, self).__init__ (field_or_plot)

        if lonstyle not in _lonstyles:
            raise ValueError ('unknown longitude axis style "%s"' % lonstyle)

        self.lon0 = lon0
        self.lat0 = lat0
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

        result = np.empty ((2, linx.size))
        cl0 = np.cos (self.lat0)
        sl0 = np.sin (self.lat0)
        rho = sinc = np.sqrt (linx**2 + liny**2)
        c = np.arcsin (rho)
        cosc = np.cos (c) # = np.sqrt (1 - rho**2)
        result[0] = self.lon0 + np.arctan2 (linx * sinc, rho * cl0 * cosc - liny * sl0 * sinc)
        w = np.where (rho == 0)
        result[1,w] = self.lat0
        w = np.where (rho != 0)
        result[1,w] = np.arcsin (cosc * sl0 + liny * sinc * cl0 / rho[w])
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
        cl0 = np.cos (self.lat0)
        sl0 = np.sin (self.lat0)
        result[0] = np.cos (lat) * np.sin (lon - self.lon0)
        result[1] = cl0 * np.sin (lat) - sl0 * np.cos (lat) * np.cos (lon - self.lon0)

        if self.negatex:
            result[0] *= -1

        return result
