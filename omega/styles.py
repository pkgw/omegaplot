class BitmapStyle (object):
    """This style is meant for bitmap surfaces, where one unit
    represents one pixel, and hence holding things to integral
    units is important."""
    
    smallScale = 2
    largeScale = 5
    fineLine = 1
    thickLine = 2
    
    def __init__ (self, colorscheme):
        self.colors = colorscheme

    def initContext (self, ctxt, width, height):
        ctxt.set_source_rgb (*self.colors.background)
        ctxt.paint ()

    def apply (self, ctxt, style):
        if not style: return

        if hasattr (style, 'apply'):
            style.apply (ctxt)
            return

        if callable (style):
            style (ctxt, self)
            return

        if isinstance (style, basestring):
            fn = 'apply_' + style

            if hasattr (self, fn):
                getattr (self, fn)(ctxt)
                return

        raise Exception ('Dont know what to do with style item %s' % style)

    def apply_bgLinework (self, ctxt):
        ctxt.set_line_width (self.fineLine)
        ctxt.set_source_rgb (*self.colors.faint) # do rgba?

    def apply_bgFill (self, ctxt):
        ctxt.set_source_rgb (*self.colors.background)

    def apply_genericStamp (self, ctxt):
        ctxt.set_line_width (self.fineLine)
        ctxt.set_source_rgb (*self.colors.foreground)

    def apply_genericLine (self, ctxt):
        ctxt.set_line_width (self.thickLine)
        ctxt.set_source_rgb (*self.colors.foreground)

    def apply_genericBand (self, ctxt):
        ctxt.set_source_rgba (self.colors.foreground[0],
                              self.colors.foreground[1],
                              self.colors.foreground[2],
                              0.2)

    def getColor (self, color):
        if isinstance (color, tuple): return color
        
        return getattr (self.colors, color)

    def applyPrimary (self, ctxt, stylenum):
        raise NotImplementedError ()

class BlackOnWhiteColors (object):
    background = (1, 1, 1)
    foreground = (0, 0, 0)
    faint = (0.3, 0.3, 0.3)

class WhiteOnBlackColors (object):
    background = (0, 0, 0)
    foreground = (1, 1, 1)
    faint = (0.7, 0.7, 0.7)

def _dashedPrimary (style, ctxt, stylenum):
    if stylenum is None: return
        
    u = style.largeScale
    
    if stylenum == 0:
        return
    elif stylenum == 1:
        a = [u * 2, u * 2]
    elif stylenum == 2:
        a = [u * 3, u]
    elif stylenum == 3:
        a = [u * 3, u, u, u]
    elif stylenum == 4:
        a = [u * 3, u, u, u, u, u]
    else:
        raise Exception ('Only support primary style numbers < 5!')

    ctxt.set_dash (a, 0.)
    ctxt.set_line_width (style.thickLine)
    
class BlackOnWhiteBitmap (BitmapStyle):
    def __init__ (self):
        BitmapStyle.__init__ (self, BlackOnWhiteColors ())

    applyPrimary = _dashedPrimary
        
class WhiteOnBlackBitmap (BitmapStyle):
    def __init__ (self):
        BitmapStyle.__init__ (self, WhiteOnBlackColors ())

    applyPrimary = _dashedPrimary

class ColorOnBlackBitmap (BitmapStyle):
    def __init__ (self):
        BitmapStyle.__init__ (self, WhiteOnBlackColors ())

    def applyPrimary (self, ctxt, stylenum):
        if stylenum is None: return

        if stylenum == 0:
            c = (0.9, 0.1, 0.1)
        elif stylenum == 1:
            c = (0.2, 0.4, 0.9)
        elif stylenum == 2:
            c = (0.1, 0.9, 0.4)
        elif stylenum == 3:
            c = (0.7, 0.7, 0)
        elif stylenum == 4:
            c = (0.7, 0, 0.7)
        elif stylenum == 5:
            c = (0, 0.7, 0.7)
        else:
            raise Exception ('Only support primary numbers < 6!')

        ctxt.set_source_rgb (*c)
        ctxt.set_line_width (self.thickLine)
