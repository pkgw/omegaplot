"""style - Graphical styling classes."""

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

        if isinstance (styleItem, basestring):
            fn = 'apply_' + styleItem

            if hasattr (self.roles, fn):
                getattr (self.roles, fn)(ctxt, self)
                return

        raise Exception ('Don\'t know what to do with '
                         'style item %s' % styleItem)


    def getColor (self, color):
        if isinstance (color, tuple): return color
        
        return getattr (self.colors, color)


    def initContext (self, ctxt, width, height):
        # Clear the context
        ctxt.set_source_rgb (*self.colors.background)
        ctxt.paint ()

        # Font size
        ctxt.set_font_size (self.sizes.normalFontSize)


    def applyDataLine (self, ctxt, stylenum):
        self.data.applyLine (self, ctxt, stylenum)


    def applyDataStamp (self, ctxt, stylenum):
        self.data.applyStamp (self, ctxt, stylenum)


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


    def getDataColor (self, stylenum):
        raise NotImplementedError ()
    

class BlackOnWhiteColors (Colors):
    background = (1, 1, 1)
    foreground = (0, 0, 0)
    muted = (0.3, 0.3, 0.3)
    faint = (0.9, 0.9, 0.9)


    def getDataColor (self, stylenum):
        stylenum = stylenum % 6

        if stylenum == 0:
            c = (0.9, 0.1, 0.1)
        elif stylenum == 1:
            c = (0, 0.1, 0.7)
        elif stylenum == 2:
            c = (0.1, 0.9, 0.4)
        elif stylenum == 3:
            c = (0.2, 0.9, 0.9)
        elif stylenum == 4:
            c = (0.7, 0, 0.7)
        elif stylenum == 5:
            c = (0.8, 0.6, 0)

        return c


class WhiteOnBlackColors (Colors):
    background = (0, 0, 0)
    foreground = (1, 1, 1)
    muted = (0.7, 0.7, 0.7)
    faint = (0.15, 0.15, 0.15)


    def getDataColor (self, stylenum):
        stylenum = stylenum % 6

        if stylenum == 0:
            c = (0.9, 0.1, 0.1)
        elif stylenum == 1:
            c = (0, 0.1, 0.7)
        elif stylenum == 2:
            c = (0.1, 0.9, 0.4)
        elif stylenum == 3:
            c = (0.2, 0.9, 0.9)
        elif stylenum == 4:
            c = (0.7, 0, 0.7)
        elif stylenum == 5:
            c = (0.8, 0.6, 0)

        return c


# Themes for different kinds of data in a shared plot

import stamps


class DataTheme (object):
    def applyLine (self, style, ctxt, n):
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

    def applyLine (self, style, ctxt, stylenum):
        if stylenum is None: return
        
        ctxt.set_source_rgb (*style.colors.foreground)
        ctxt.set_line_width (style.sizes.thickLine)

        u = style.smallScale
        stylenum = stylenum % 5

        if stylenum == 0:
            return
        elif stylenum == 1:
            a = [u * 2, u * 2]
        elif stylenum == 2:
            a = [u * 3, u, u / 2, u]
        elif stylenum == 3:
            a = [u * 3, u, u, u, u, u]
        elif stylenum == 4:
            a = [u * 3, u, u / 2, u, u / 2, u]

        ctxt.set_dash (a, 0.)


    def applyStamp (self, style, ctxt, stylenum):
        if stylenum is None: return

        # No variation based on stylenum here.
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

    
    def getSymbolFunc (self, stylenum):
        stylenum = stylenum % len (self._symFuncs)
        
        return self._symFuncs[stylenum]
    
        
class ColorDataTheme (DataTheme):
    """This theme disambiguates data from different
    sources by drawing lines in different colors. When using
    this theme, you should keep in mind that 1) many 
    people are colorblind in various ways and 2) many
    people print out color figures on black-and-white 
    printers."""


    def applyLine (self, style, ctxt, stylenum):
        if stylenum is None: return

        c = style.colors.getDataColor (stylenum)
        ctxt.set_source_rgb (*c)
        ctxt.set_line_width (style.sizes.thickLine)


    def applyStamp (self, style, ctxt, stylenum):
        if stylenum is None: return

        c = style.colors.getDataColor (stylenum)
        ctxt.set_source_rgb (*c)
        ctxt.set_line_width (style.sizes.thickLine)


    def getSymbolFunc (self, stylenum):
        # FIXME hardcoded hack
        symnum = (stylenum // 6) % len (MonochromeDataTheme._symFuncs)
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


