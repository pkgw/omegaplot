"""style - Graphical styling classes."""

import numpy as N

class Style (object):
    def __init__ (self, sizes, colors, data, roles):
        self.sizes = sizes
        self.colors = colors
        self.data = data
        self.roles = roles

        self.normC = sizes.normC
        self.normL = sizes.normL


    def apply (self, ctxt, styleItem):
        if styleItem is None:
            return

        if hasattr (styleItem, 'apply'):
            styleItem.apply (ctxt)
            return

        if callable (styleItem):
            styleItem (ctxt, self)
            return

        if isinstance (styleItem, dict):
            self._applyDictStyle (ctxt, styleItem)
            return

        if isinstance (styleItem, basestring):
            fn = 'apply_' + styleItem

            if hasattr (self.roles, fn):
                getattr (self.roles, fn)(ctxt, self)
                return

        raise Exception ('Don\'t know what to do with '
                         'style item %s' % styleItem)


    def _applyDictStyle (self, ctxt, item):
        v = item.get ('color')
        if v is not None:
            ctxt.set_source_rgb (*self.getColor (v))

        v = item.get ('linewidth')
        if v is not None:
            ctxt.set_line_width (v * self.sizes.thickLine)

        v = item.get ('dashing')
        if v is not None:
            ctxt.set_dash (N.asarray (v) * self.sizes.smallScale, 0.)


    def getColor (self, color):
        if isinstance (color, tuple): return color
        
        return getattr (self.colors, color)


    def initContext (self, ctxt, width, height):
        # Clear the context
        ctxt.set_source_rgb (*self.colors.background)
        ctxt.paint ()

        # Font size
        ctxt.set_font_size (self.sizes.normalFontSize)


    def applyDataLine (self, ctxt, dsn):
        self.data.applyLine (self, ctxt, dsn)


    def applyDataRegion (self, ctxt, dsn):
        self.data.applyRegion (self, ctxt, dsn)


    def applyDataStamp (self, ctxt, dsn):
        self.data.applyStamp (self, ctxt, dsn)


    # Shortcut accessors for useful properties

    @property
    def smallScale (self): return self.sizes.smallScale


    @property
    def largeScale (self): return self.sizes.largeScale


# Sizes of graphical elements and coordinate transforms

class Sizes (object):
    smallScale = None
    largeScale = None
    fineLine = None
    thickLine = None
    normalFontSize = None


    def normC (self, coord):
        """Normalizes a coordinate for this sizing scheme.
        Used to round off measurements to integral pixels
        when rendering to a bitmap."""
        raise NotImplementedError ()

    def normL (self, coord):
        """Normalizes a length for this sizing scheme.
        Used to round off measurements to integral pixels
        when rendering to a bitmap."""
        raise NotImplementedError ()


class BitmapSizes (Sizes):
    smallScale = 2
    largeScale = 5
    fineLine = 1
    thickLine = 2
    normalFontSize = 12


    normC = round
    normL = round


class VectorSizes (Sizes):
    smallScale = 1.5
    largeScale = 4.5
    fineLine = 0.5
    thickLine = 1
    normalFontSize = 12


    normC = lambda x: x
    normL = normC


# Color scheme for graphical elements

class Colors (object):
    background = None
    foreground = None
    muted = None
    faint = None

    def getDataColor (self, dsn):
        raise NotImplementedError ()

    def towardBG (self, color, howfar):
        raise NotImplementedError ()


class BlackOnWhiteColors (Colors):
    background = (1, 1, 1)
    foreground = (0, 0, 0)
    muted = (0.3, 0.3, 0.3)
    faint = (0.9, 0.9, 0.9)

    _dataColors = [
        (0.9, 0.1, 0.1),
        (0, 0.1, 0.7),
        (0.1, 0.9, 0.4),
        (0.2, 0.9, 0.9),
        (0.7, 0, 0.7),
        (0.8, 0.6, 0),
        ]

    def getDataColor (self, dsn):
        dc = self._dataColors
        return dc[dsn % len (dc)]

    def towardBG (self, color, howfar):
        f = 1. - howfar
        r = howfar + f * color[0]
        g = howfar + f * color[1]
        b = howfar + f * color[2]
        return r, g, b


class WhiteOnBlackColors (Colors):
    background = (0, 0, 0)
    foreground = (1, 1, 1)
    muted = (0.7, 0.7, 0.7)
    faint = (0.15, 0.15, 0.15)

    _dataColors = [
        (0.9, 0.1, 0.1),
        (0, 0.1, 0.7),
        (0.1, 0.9, 0.4),
        (0.2, 0.9, 0.9),
        (0.7, 0, 0.7),
        (0.8, 0.6, 0),
        ]

    def getDataColor (self, dsn):
        dc = self._dataColors
        return dc[dsn % len (dc)]

    def towardBG (self, color, howfar):
        f = 1. - howfar
        r = f * color[0]
        g = f * color[1]
        b = f * color[2]
        return r, g, b


# Themes for different kinds of data in a shared plot

import stamps


class DataTheme (object):
    def applyLine (self, style, ctxt, n):
        raise NotImplementedError ()

    def applyRegion (self, style, ctxt, n):
        raise NotImplementedError ()

    def applyStamp (self, style, ctxt, n):
        raise NotImplementedError ()

    def getSymbolFunc (self, n):
        raise NotImplementedError ()
        


def _wf (func, fill):
    # "with fill"
    return lambda c, sty, sz: func (c, sty, sz, fill)


class MonochromeDataTheme (DataTheme):
    """This theme disambiguates data from different
    sources by dashing lines in different ways and
    using different plot symbols."""

    _dashLengthTuples = [
        (),
        (2, 2),
        (3, 1, 0.5, 1),
        (3, 1, 1, 1, 1, 1),
        (3, 1, 0.5, 1, 0.5, 1),
        ]

    def __init__ (self):
        from numpy import asarray
        dlas = self._dashLengthArrays = []

        for t in self._dashLengthTuples:
            dlas.append (asarray (t))


    def applyLine (self, style, ctxt, dsn):
        if dsn is None: return
        
        ctxt.set_source_rgb (*style.colors.foreground)
        ctxt.set_line_width (style.sizes.thickLine)

        dlas = self._dashLengthArrays
        dashlengths = dlas[dsn % len (dlas)]

        if len (dashlengths):
            ctxt.set_dash (dashlengths * style.smallScale, 0.)


    def applyRegion (self, style, ctxt, dsn):
        if dsn is None:
            return

        ctxt.set_source_rgb (*style.colors.muted)
        # FIXME: different fill patterns


    def applyStamp (self, style, ctxt, dsn):
        if dsn is None: return

        # No variation based on data style number here.
        ctxt.set_source_rgb (*style.colors.foreground)
        ctxt.set_line_width (style.sizes.thickLine)
        

    _symFuncs = [_wf (stamps.symCircle, True),
                 _wf (stamps.symUpTriangle, True),
                 _wf (stamps.symBox, True),
                 _wf (stamps.symDiamond, True),
                 _wf (stamps.symDownTriangle, True),
                 stamps.symX,
                 stamps.symPlus,
                 _wf (stamps.symCircle, False),
                 _wf (stamps.symUpTriangle, False),
                 _wf (stamps.symBox, False),
                 _wf (stamps.symDiamond, False),
                 _wf (stamps.symDownTriangle, False)]

    
    def getSymbolFunc (self, dsn):
        dsn = dsn % len (self._symFuncs)
        
        return self._symFuncs[dsn]
    
        
class ColorDataTheme (DataTheme):
    """This theme disambiguates data from different
    sources by drawing lines in different colors. When using
    this theme, you should keep in mind that 1) many 
    people are colorblind in various ways and 2) many
    people print out color figures on black-and-white 
    printers."""


    def applyLine (self, style, ctxt, dsn):
        if dsn is None: return

        c = style.colors.getDataColor (dsn)
        ctxt.set_source_rgb (*c)
        ctxt.set_line_width (style.sizes.thickLine)


    def applyRegion (self, style, ctxt, dsn):
        if dsn is None:
            return

        c = style.colors.getDataColor (dsn)
        c = style.colors.towardBG (c, 0.6)
        ctxt.set_source_rgb (*c)


    def applyStamp (self, style, ctxt, dsn):
        if dsn is None: return

        c = style.colors.getDataColor (dsn)
        ctxt.set_source_rgb (*c)
        ctxt.set_line_width (style.sizes.thickLine)


    def getSymbolFunc (self, dsn):
        # FIXME hardcoded hack
        symnum = (dsn // 6) % len (MonochromeDataTheme._symFuncs)
        return MonochromeDataTheme._symFuncs[symnum]


# Higher-level styling for various graphical elements based 
# on their roles. This builds upon the lower-level sizes and 
# colors that the style defines.

class Roles (object):
    pass


class DefaultRoles (Roles):
    def apply_bgLinework (self, ctxt, style):
        ctxt.set_line_width (style.sizes.fineLine)
        ctxt.set_source_rgb (*style.colors.muted)


    def apply_strongLine (self, ctxt, style):
        ctxt.set_line_width (style.sizes.thickLine)
        ctxt.set_source_rgb (*style.colors.foreground)


    def apply_genericBand (self, ctxt, style):
        # FIXME: PostScript doesn't support opacity,
        # so it would be best to avoid any use of the
        # alpha channel by default in any of our styles.

        ctxt.set_source_rgb (*style.colors.faint)

# Now put them all together

def BlackOnWhiteBitmap ():
    return Style (BitmapSizes (), BlackOnWhiteColors (),
                  MonochromeDataTheme (), DefaultRoles ())


def WhiteOnBlackBitmap ():
    return Style (BitmapSizes (), WhiteOnBlackColors (),
                  MonochromeDataTheme (), DefaultRoles ())


def ColorOnBlackBitmap ():
    return Style (BitmapSizes (), WhiteOnBlackColors (),
                  ColorDataTheme (), DefaultRoles ())


def ColorOnWhiteBitmap ():
    return Style (BitmapSizes (), BlackOnWhiteColors (),
                  ColorDataTheme (), DefaultRoles ())


def BlackOnWhiteVector ():
    return Style (VectorSizes (), BlackOnWhiteColors (),
                  MonochromeDataTheme (), DefaultRoles ())


def WhiteOnBlackVector ():
    return Style (VectorSizes (), WhiteOnBlackColors (),
                  MonochromeDataTheme (), DefaultRoles ())


def ColorOnBlackVector ():
    return Style (VectorSizes (), WhiteOnBlackColors (),
                  ColorDataTheme (), DefaultRoles ())


def ColorOnWhiteVector ():
    return Style (VectorSizes (), BlackOnWhiteColors (),
                  ColorDataTheme (), DefaultRoles ())
