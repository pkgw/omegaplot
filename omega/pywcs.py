# Support for plot axes derived from WCS coordinate transforms
# using the pywcs binding to wcslib.

# TODO: allow "paper 4" or "SIP" transforms if desired. Whatever
# they are.

import pywcs, numpy as N
from omega import rect, sphere


def _makeRAPainter (axis):
    return sphere.AngularAxisPainter (axis, 1./15,
                                      sphere.DISPLAY_HMS, sphere.WRAP_POS)

def _makeLatPainter (axis):
    return sphere.AngularAxisPainter (axis, 1,
                                      sphere.DISPLAY_DMS, sphere.WRAP_ZCEN)

def _makeLonPainter (axis):
    return sphere.AngularAxisPainter (axis, 1,
                                      sphere.DISPLAY_DMS, sphere.WRAP_POS)


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
        linx = N.atleast_1d (linx)
        liny = N.atleast_1d (liny)

        if linx.size == 1:
            linxval = linx[0]
            linx = N.empty (liny.shape, linx.dtype)
            linx.fill (linxval)

        if liny.size == 1:
            linyval = liny[0]
            liny = N.empty (linx.shape, liny.dtype)
            liny.fill (linyval)

        return self.wcs.wcs_pix2sky (linx, liny, 0)


    def arb2lin (self, arbx, arby):
        arbx = N.atleast_1d (arbx)
        arby = N.atleast_1d (arby)

        if arbx.size == 1:
            arbxval = arbx[0]
            arbx = N.empty (arby.shape, arbx.dtype)
            arbx.fill (arbxval)

        if arby.size == 1:
            arbyval = arby[0]
            arby = N.empty (arbx.shape, arby.dtype)
            arby.fill (arbyval)

        return self.wcs.wcs_sky2pix (arbx, arby, 0)
