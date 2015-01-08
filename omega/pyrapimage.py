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

# Support for plot axes derived from coordinates embedded in a CASA
# image access with pyrap.

# FIXME: we're hardcoding which axes are the lat/lon axes, etc etc

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np

from . import rect, sphere


def _makeRAPainter (axis):
    return sphere.AngularAxisPainter (axis, 12./np.pi,
                                      sphere.DISPLAY_HMS, sphere.WRAP_POS_HR)

def _makeLatPainter (axis):
    return sphere.AngularAxisPainter (axis, 180./np.pi,
                                      sphere.DISPLAY_DMS, sphere.WRAP_LAT)

def _makeLonPainter (axis):
    return sphere.AngularAxisPainter (axis, 180./np.pi,
                                      sphere.DISPLAY_DMS, sphere.WRAP_POS_DEG)


class PyrapImageCoordinates (rect.RectCoordinates):
    def __init__ (self, image, field_or_plot):
        """*dircoords* are direction coordinates accessed from pyrap.
If you have a pyrap image, you get these via::

  im.coordinates() ['direction']
"""

        super (PyrapImageCoordinates, self).__init__ (field_or_plot)
        self.image = image
        self.refworld = self.image.toworld (np.zeros (self.image.ndim ()))
        self._sniff_discontinuities ()


    def _sniff_discontinuities (self):
        """Check for discontinuities in the world coordinates as a
function of pixel coordinates in the image area. We must postprocess
the world coordinates to hide these so that all the code above us can
keep on making assumptions that ought to be totally reasonable.

The "inspiration" for this is the fact that WCSLIB wraps longitudes to
be within [0, 360], so there's a discontinuity if your image crosses
zero longitude. In order to be able to check this we enforce that the
X axis must be mostly aligned with the longitude axis.

There will also be problems if you try to image latitudes that hit +/-
90 degrees. The generalization of that issue is the world coordinates
must vary monotonically with the pixel coordinates. But for now I'm
just dealing with the particular longitude wraparound issue.
"""
        s = np.asarray (self.image.shape ())
        p = np.zeros (s.size)
        delta = 1e-6
        toworld = self.image.toworld

        # For now, all we do is check for discontinuities along the
        # x/longitude axes. We run along both the top and the bottom
        # of the image in case the coordinate systems behave
        # substantially differently there.

        delta_w = 0

        for ypix in 0, s[-2] - 1:
            if delta_w != 0:
                break # found a discontinuity the first time

            p[-2] = ypix
            p[-1] = 0
            expected_w = None

            while p[-1] < s[-1]: # make our way across the image ...
                w1 = toworld (p)
                w1[-1] += delta_w

                if expected_w is not None and \
                        abs ((w1[-1] - expected_w) / w1[-1]) > 0.5:
                    # The world coordinate changed a LOT more than
                    # it should have. Looks like we found a discontinuity.
                    if abs (abs (w1[-1] - expected_w) - 6.28) > 0.1:
                        raise Exception ('expected a 2pi delta at discontinuity')
                    if delta_w != 0:
                        raise Exception ('can\'t handle more than one discontinuity')

                    if w1[-1] - expected_w > 0:
                        delta_w = -2 * np.pi
                    else:
                        delta_w = 2 * np.pi

                    w1[-1] += delta_w # correct for next set of checks

                # How many pixels should we move to get a "smallish"
                # fractional change in the longitude coordinate? But
                # clamp the move to be between 1 and 50 pixels, and
                # make sure that we're mostly moving along the
                # longitude axis (because we're not checking for
                # latitude discontinuities, under the assumption that
                # latitude doesn't change much).

                p[-1] += delta
                w2 = toworld (p)
                w2[-1] += delta_w
                dlondp = (w2[-1] - w1[-1]) / delta
                dlatdp = (w2[-2] - w1[-2]) / delta

                if abs (dlatdp) > 0.3 * abs (dlondp):
                    raise Exception ('X axis does not (always) track the '
                                     'longitude axis closely')

                dp = min (max (abs (0.05 * w1[-1] / dlondp), 1), 50)
                expected_w = w2[-1] + dp * dlondp
                p[-1] += dp

        if delta_w == 0:
            lon_correct = lambda x: x
        else:
            # We found a discontinuity. Set up to correct it. We need
            # to leave a little guard band around w1 (the world coordinate
            # in question at pixel 0) to allow the coordinate routines to
            # sensibly explore the areas just beyond the defined image.
            # That's the half pi offset below.

            p[-1] = 0
            w1 = toworld (p)[-1]
            p[-1] = s[-1] - 1
            w2 = toworld (p)[-1] + delta_w

            if w1 > w2:
                # Usual astronomical convention: world coordinate
                # decreases as pixel coord increases.
                def lon_correct (x):
                    if x > w1 + 0.5 * np.pi:
                        return x + delta_w
                    return x
            else:
                def lon_correct (x):
                    if x < w1 - 0.5 * np.pi:
                        return x + delta_w
                    return x

        self._lon_correct = lon_correct


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

        result = np.empty ((2, linx.size))
        coords = np.zeros (self.image.ndim ())

        for i in xrange (linx.size):
            coords[-1] = linx[i] # longitude is last coord
            coords[-2] = liny[i]
            r = self.image.toworld (coords)
            result[0,i] = self._lon_correct (r[-1]) # longitude -> x
            result[1,i] = r[-2] # latitude -> y

        return result


    def arb2lin (self, arbx, arby):
        arbx = np.atleast_1d (arbx)
        arby = np.atleast_1d (arby)

        assert arbx.ndim == 1, 'can only handle 1d case right now'

        if arbx.size == 1:
            arbxval = arbx[0]
            arbx = np.empty (arby.shape, arbx.dtype)
            arbx.fill (arbxval)

        if arby.size == 1:
            arbyval = arby[0]
            arby = np.empty (arbx.shape, arby.dtype)
            arby.fill (arbyval)

        result = np.empty ((2, arbx.size))
        coords = np.array (self.refworld)

        for i in xrange (arbx.size):
            coords[-1] = arbx[i] # x is last coord
            coords[-2] = arby[i]
            r = self.image.topixel (coords)
            result[0,i] = r[-1] # x -> longitude
            result[1,i] = r[-2] # y -> latitude

        return result
