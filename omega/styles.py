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
        ctxt.rectangle (0, 0, width, height)
        ctxt.set_source_rgb (*self.colors.background)
        ctxt.fill ()
    
    def apply (self, ctxt, style):
        if not style: return

        if hasattr (style, 'apply'):
            style.apply (ctxt)
            return

        if callable (style):
            style (ctxt)
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

class BlackOnWhiteColors (object):
    background = (1, 1, 1)
    foreground = (0, 0, 0)
    faint = (0.3, 0.3, 0.3)

class WhiteOnBlackColors (object):
    background = (0, 0, 0)
    foreground = (1, 1, 1)
    faint = (0.7, 0.7, 0.7)

class BlackOnWhiteBitmap (BitmapStyle):
    def __init__ (self):
        BitmapStyle.__init__ (self, BlackOnWhiteColors ())

class WhiteOnBlackBitmap (BitmapStyle):
    def __init__ (self):
        BitmapStyle.__init__ (self, WhiteOnBlackColors ())
