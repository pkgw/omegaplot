#!/usr/bin/python

import omega, omega.latex
from omega.stamps import *
from omega.layout import RightRotationPainter as RRP
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
g[0,0] = omega.TextPainter (r'$\frac{2 + \pi}{e^{\pi i} + 1}$')
g[0,1] = omega.TextPainter (r'$2+2=4$')
g[1,0] = omega.TextPainter (r'$\sum_0^{100}x^2 - \cos x$')
g[1,1] = RRP (omega.TextPainter (r'$\sum_0^{100}x^2 - \cos x$'))
g[2,0] = RRP (omega.TextPainter (r'$\sum_0^{100}x^2 - \cos x$'))
g[2,1] = RRP (omega.TextPainter (r'$\sum_0^{100}x^2 - \cos x$'))
g[1,1].setRotation (RRP.ROT_CCW90)
g[2,0].setRotation (RRP.ROT_CW90)
g[2,1].setRotation (RRP.ROT_180)

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, {}, g))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
