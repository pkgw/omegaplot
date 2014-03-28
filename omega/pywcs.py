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

# Support for plot axes derived from WCS coordinate transforms
# using the pywcs binding to wcslib.

# TODO: allow "paper 4" or "SIP" transforms if desired. Whatever
# they are.

from __future__ import absolute_import, division, print_function, unicode_literals

import pywcs, numpy as np

from . import rect, sphere


def _makeRAPainter (axis):
    return sphere.AngularAxisPainter (axis, 1./15,
                                      sphere.DISPLAY_HMS, sphere.WRAP_POS_HR)

def _makeLatPainter (axis):
    return sphere.AngularAxisPainter (axis, 1,
                                      sphere.DISPLAY_DMS, sphere.WRAP_LAT)

def _makeLonPainter (axis):
    return sphere.AngularAxisPainter (axis, 1,
                                      sphere.DISPLAY_DMS, sphere.WRAP_POS_DEG)


class WCSCoordinates (rect.RectCoordinates):
    def __init__ (self, wcs, field_or_plot):
        super (WCSCoordinates, self).__init__ (field_or_plot)
        self.wcs = wcs


    def makeAxis (self, side):
        axis = rect.CoordinateAxis (self, side)

        if side in (rect.RectPlot.SIDE_TOP, rect.RectPlot.SIDE_BOTTOM):
            axidx = 0
        else:
            axidx = 1

        if self.wcs.wcs.ctype[axidx].startswith ('RA--'):
            axis.defaultPainter = _makeRAPainter
        elif self.wcs.wcs.ctype[axidx][1:].startswith ('LAT'):
            axis.defaultPainter = _makeLatPainter
        else:
            axis.defaultPainter = _makeLonPainter

        return axis


    def lin2arb (self, linx, liny):
        linx = np.atleast_1d (linx)
        liny = np.atleast_1d (liny)

        if linx.size == 1:
            linxval = linx[0]
            linx = np.empty (liny.shape, linx.dtype)
            linx.fill (linxval)

        if liny.size == 1:
            linyval = liny[0]
            liny = np.empty (linx.shape, liny.dtype)
            liny.fill (linyval)

        return self.wcs.wcs_pix2sky (linx, liny, 0)


    def arb2lin (self, arbx, arby):
        arbx = np.atleast_1d (arbx)
        arby = np.atleast_1d (arby)

        if arbx.size == 1:
            arbxval = arbx[0]
            arbx = np.empty (arby.shape, arbx.dtype)
            arbx.fill (arbxval)

        if arby.size == 1:
            arbyval = arby[0]
            arby = np.empty (arbx.shape, arby.dtype)
            arby.fill (arbyval)

        return self.wcs.wcs_sky2pix (arbx, arby, 0)
