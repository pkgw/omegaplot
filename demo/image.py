#!/usr/bin/python

import omega
from omega.stamps import *

import gtk

bag = omega.Bag ()

style = omega.BlackOnWhiteBitmap ()
#style.smallScale *= 2

class StampPainter (omega.Painter):
    def __init__ (self, stamp):
        self.stamp = stamp
    
    def doPaint (self, ctxt, style, firstPaint):
        if not firstPaint: return

        data = (self.width / 2, self.height / 2)
        self.stamp.paint (ctxt, style, data)

g = omega.Grid (3, 2)
g[0,0] = StampPainter (Dot ())
g[0,1] = omega.images.LatexPainter (r'$2+2=4$')
g[1,0] = omega.images.LatexPainter (r'$\frac{2 + \pi}{e^{\pi i} + 1}$')
g[1,1] = StampPainter (UpTriangle ())
g[2,0] = StampPainter (X ())
g[2,1] = omega.images.LatexPainter (r'$\sum_0^{100}x^2 - \cos x$')

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, {}, g))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
