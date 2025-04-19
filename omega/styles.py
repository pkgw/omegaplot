# -*- mode: python; coding: utf-8 -*-
# Copyright 2011, 2012, 2014, 2015 Peter Williams
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

"""
Graphical styling classes.
"""

import numpy as np


def apply_color(ctxt, c):
    if len(c) == 4:
        ctxt.set_source_rgba(*c)
    else:
        ctxt.set_source_rgb(*c)


class Style(object):
    def __init__(self, sizes, colors, data, roles):
        self.sizes = sizes
        self.colors = colors
        self.data = data
        self.roles = roles

        self.normC = sizes.normC
        self.normL = sizes.normL

    def apply(self, ctxt, styleItem):
        if styleItem is None:
            return

        if hasattr(styleItem, "apply"):
            styleItem.apply(ctxt)
            return

        if callable(styleItem):
            styleItem(ctxt, self)
            return

        if isinstance(styleItem, dict):
            self._applyDictStyle(ctxt, styleItem)
            return

        if isinstance(styleItem, str):
            fn = "apply_" + styleItem

            if hasattr(self.roles, fn):
                getattr(self.roles, fn)(ctxt, self)
                return

        raise Exception("Don't know what to do with " "style item %s" % styleItem)

    def _applyDictStyle(self, ctxt, item):
        v = item.get("dsline")
        if v is not None:
            self.applyDataLine(ctxt, v, item)

        v = item.get("dsregion")
        if v is not None:
            self.applyDataRegion(ctxt, v, item)

        v = item.get("dsstamp")
        if v is not None:
            self.applyDataStamp(ctxt, v, item)

        v = item.get("color")
        if v is not None:
            apply_color(ctxt, self.getColor(v))

        v = item.get("linewidth")
        if v is not None:
            ctxt.set_line_width(v * self.sizes.fineLine)

        v = item.get("dashing")
        if v is not None:
            ctxt.set_dash(np.asarray(v) * self.sizes.smallScale, 0.0)

    def getColor(self, color):
        if isinstance(color, tuple):
            return color
        return getattr(self.colors, color)

    def initContext(self, ctxt, width, height):
        apply_color(ctxt, self.colors.background)
        ctxt.paint()

        ctxt.set_font_size(self.sizes.normalFontSize)
        ctxt.set_line_width(self.sizes.fineLine)

    def applyDataLine(self, ctxt, dsn, modifiers={}):
        self.data.applyLine(self, ctxt, dsn, modifiers)

    def applyDataRegion(self, ctxt, dsn, modifiers={}):
        self.data.applyRegion(self, ctxt, dsn, modifiers)

    def applyDataStamp(self, ctxt, dsn, modifiers={}):
        self.data.applyStamp(self, ctxt, dsn, modifiers)

    # Shortcut accessors for useful properties

    @property
    def smallScale(self):
        return self.sizes.smallScale

    @property
    def largeScale(self):
        return self.sizes.largeScale


# Sizes of graphical elements and coordinate transforms


class Sizes(object):
    smallScale = None
    largeScale = None
    fineLine = None
    normalFontSize = None

    def normC(self, coord):
        """Normalizes a coordinate for this sizing scheme.
        Used to round off measurements to integral pixels
        when rendering to a bitmap."""
        raise NotImplementedError()

    def normL(self, coord):
        """Normalizes a length for this sizing scheme.
        Used to round off measurements to integral pixels
        when rendering to a bitmap."""
        raise NotImplementedError()


class BitmapSizes(Sizes):
    smallScale = 2
    largeScale = 5
    fineLine = 1
    normalFontSize = 12

    normC = round
    normL = round


class VectorSizes(Sizes):
    smallScale = 1.5
    largeScale = 4.5
    fineLine = 2.0
    normalFontSize = 12

    normC = lambda x: x
    normL = normC


# Color scheme for graphical elements


class Colors(object):
    background = None
    foreground = None
    muted = None
    faint = None

    def getDataColor(self, dsn):
        raise NotImplementedError()

    def towardBG(self, color, howfar):
        raise NotImplementedError()


class BlackOnWhiteColors(Colors):
    background = (1, 1, 1)
    foreground = (0, 0, 0)
    muted = (0.3, 0.3, 0.3)
    faint = (0.9, 0.9, 0.9)

    # This is the 6-class "Dark2" qualitative color palette from
    # ColorBrewer2.org. Unfortunately it's not colorblind- or photocopy-
    # friendly, but it seems like the best available option. I've reordered
    # them to line up better with the warmth of my previous palette.

    _dataColors = [
        (0.85, 0.37, 0.01),
        (0.11, 0.62, 0.47),
        (0.46, 0.44, 0.70),
        (0.91, 0.16, 0.54),
        (0.40, 0.65, 0.12),
        (0.90, 0.67, 0.01),
    ]

    def getDataColor(self, dsn):
        dc = self._dataColors
        return dc[dsn % len(dc)]

    def towardBG(self, color, howfar):
        f = 1.0 - howfar
        r = howfar + f * color[0]
        g = howfar + f * color[1]
        b = howfar + f * color[2]
        return r, g, b


class WhiteOnBlackColors(Colors):
    background = (0, 0, 0)
    foreground = (1, 1, 1)
    muted = (0.7, 0.7, 0.7)
    faint = (0.15, 0.15, 0.15)

    # This is the 6-class "Set2" qualitative color palette from
    # ColorBrewer2.org. Unfortunately it's not photocopy-friendly and is only
    # ranked as moderately colorblind-friendly.

    _dataColors = [
        (0.89, 0.10, 0.11),
        (0.22, 0.49, 0.72),
        (0.30, 0.69, 0.29),
        (0.60, 0.31, 0.64),
        (1.00, 0.50, 0.00),
        (1.00, 1.00, 0.20),
    ]

    def getDataColor(self, dsn):
        dc = self._dataColors
        return dc[dsn % len(dc)]

    def towardBG(self, color, howfar):
        f = 1.0 - howfar
        r = f * color[0]
        g = f * color[1]
        b = f * color[2]
        return r, g, b


# Themes for different kinds of data in a shared plot

from . import stamps


class DataTheme(object):
    def applyLine(self, style, ctxt, n, modifiers={}):
        raise NotImplementedError()

    def applyRegion(self, style, ctxt, n, modifiers={}):
        raise NotImplementedError()

    def applyStamp(self, style, ctxt, n, modifiers={}):
        raise NotImplementedError()

    def getSymbolFunc(self, n):
        raise NotImplementedError()

    def getStrictSymbolFunc(self, n):
        """In "strict" mode, don't iterate through colors, and avoid stamps
        that may be confused with limit arrows, and return functions for
        which the fill mode is a parameter."""
        raise NotImplementedError()


def _wfa(func):
    # "with fill argument"
    from .stamps import PathPainter

    return lambda c, sty, sz, fill: func(c, sty, sz, PathPainter(fill=fill))


def _wff(func, fill):
    # "with fixed fill"
    from .stamps import PathPainter

    return lambda c, sty, sz: func(c, sty, sz, PathPainter(fill=fill))


class MonochromeDataTheme(DataTheme):
    """This theme disambiguates data from different
    sources by dashing lines in different ways and
    using different plot symbols."""

    _dashLengthTuples = [
        (),
        (2, 2),
        (0.5, 1),
        (3, 1, 0.5, 1),
        (3, 1, 1, 1, 1, 1),
        (3, 1, 0.5, 1, 0.5, 1),
    ]

    def __init__(self):
        from numpy import asarray

        dlas = self._dashLengthArrays = []

        for t in self._dashLengthTuples:
            dlas.append(asarray(t))

    def applyLine(self, style, ctxt, dsn, modifiers={}):
        if dsn is None:
            return

        apply_color(ctxt, style.colors.foreground)

        dlas = self._dashLengthArrays
        dashlengths = dlas[dsn % len(dlas)]

        if len(dashlengths):
            ctxt.set_dash(dashlengths * style.smallScale, 0.0)

    def applyRegion(self, style, ctxt, dsn, modifiers={}):
        if dsn is None:
            return

        apply_color(ctxt, style.colors.muted)
        # FIXME: different fill patterns

    def applyStamp(self, style, ctxt, dsn, modifiers={}):
        if dsn is None:
            return

        # No variation based on data style number here.
        apply_color(ctxt, style.colors.foreground)

    _symFuncs = [
        _wff(stamps.symCircle, True),
        _wff(stamps.symUpTriangle, True),
        _wff(stamps.symBox, True),
        _wff(stamps.symDiamond, True),
        _wff(stamps.symDownTriangle, True),
        stamps.symX,
        stamps.symPlus,
        _wff(stamps.symCircle, False),
        _wff(stamps.symUpTriangle, False),
        _wff(stamps.symBox, False),
        _wff(stamps.symDiamond, False),
        _wff(stamps.symDownTriangle, False),
    ]

    def getSymbolFunc(self, dsn):
        return self._symFuncs[dsn % len(self._symFuncs)]

    _strictSymFuncs = [
        _wfa(stamps.symCircle),
        _wfa(stamps.symBox),
        _wfa(stamps.symDiamond),
        _wfa(stamps.symX),
        _wfa(stamps.symPlus),
    ]

    def getStrictSymbolFunc(self, dsn):
        return self._strictSymFuncs[dsn % len(self._strictSymFuncs)]


class ColorDataTheme(DataTheme):
    """This theme disambiguates data from different
    sources by drawing lines in different colors. When using
    this theme, you should keep in mind that 1) many
    people are colorblind in various ways and 2) many
    people print out color figures on black-and-white
    printers."""

    def applyLine(self, style, ctxt, dsn, modifiers={}):
        if dsn is None:
            return

        c = style.colors.getDataColor(dsn)
        if "towardbg" in modifiers:
            c = style.colors.towardBG(c, modifiers["towardbg"])
        if "alpha" in modifiers:
            # This gives us robustness if c already has an alpha:
            c = (c[0], c[1], c[2], modifiers["alpha"])

        apply_color(ctxt, c)

    def applyRegion(self, style, ctxt, dsn, modifiers={}):
        if dsn is None:
            return

        c = style.colors.getDataColor(dsn)
        tbg = modifiers.get("towardbg", 0.6)
        c = style.colors.towardBG(c, tbg)
        if "alpha" in modifiers:
            c = (c[0], c[1], c[2], modifiers["alpha"])

        apply_color(ctxt, c)

    def applyStamp(self, style, ctxt, dsn, modifiers={}):
        if dsn is None:
            return

        c = style.colors.getDataColor(dsn)
        if "towardbg" in modifiers:
            c = style.colors.towardBG(c, modifiers["towardbg"])
        if "alpha" in modifiers:
            # This gives us robustness if c already has an alpha:
            c = (c[0], c[1], c[2], modifiers["alpha"])

        apply_color(ctxt, c)

    def getSymbolFunc(self, dsn):
        # FIXME hardcoded hack
        symnum = (dsn // 6) % len(MonochromeDataTheme._symFuncs)
        return MonochromeDataTheme._symFuncs[symnum]

    def getStrictSymbolFunc(self, dsn):
        ssf = MonochromeDataTheme._strictSymFuncs
        return ssf[dsn % len(ssf)]


# Higher-level styling for various graphical elements based
# on their roles. This builds upon the lower-level sizes and
# colors that the style defines.


class Roles(object):
    pass


class DefaultRoles(Roles):
    def apply_bgLinework(self, ctxt, style):
        ctxt.set_line_width(style.sizes.fineLine)
        apply_color(ctxt, style.colors.muted)

    def apply_strongLine(self, ctxt, style):
        ctxt.set_line_width(2 * style.sizes.fineLine)
        apply_color(ctxt, style.colors.foreground)

    def apply_genericBand(self, ctxt, style):
        # FIXME: PostScript doesn't support opacity,
        # so it would be best to avoid any use of the
        # alpha channel by default in any of our styles.
        apply_color(ctxt, style.colors.faint)


# Now put them all together


def BlackOnWhiteBitmap():
    return Style(
        BitmapSizes(), BlackOnWhiteColors(), MonochromeDataTheme(), DefaultRoles()
    )


def WhiteOnBlackBitmap():
    return Style(
        BitmapSizes(), WhiteOnBlackColors(), MonochromeDataTheme(), DefaultRoles()
    )


def ColorOnBlackBitmap():
    return Style(BitmapSizes(), WhiteOnBlackColors(), ColorDataTheme(), DefaultRoles())


def ColorOnWhiteBitmap():
    return Style(BitmapSizes(), BlackOnWhiteColors(), ColorDataTheme(), DefaultRoles())


def BlackOnWhiteVector():
    return Style(
        VectorSizes(), BlackOnWhiteColors(), MonochromeDataTheme(), DefaultRoles()
    )


def WhiteOnBlackVector():
    return Style(
        VectorSizes(), WhiteOnBlackColors(), MonochromeDataTheme(), DefaultRoles()
    )


def ColorOnBlackVector():
    return Style(VectorSizes(), WhiteOnBlackColors(), ColorDataTheme(), DefaultRoles())


def ColorOnWhiteVector():
    return Style(VectorSizes(), BlackOnWhiteColors(), ColorDataTheme(), DefaultRoles())
