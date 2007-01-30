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

        self.stamp.paint (ctxt, style, self.width / 2, self.height / 2, ())

g = omega.Grid (3, 3)
g[0,0] = StampPainter (Dot ())
g[0,1] = StampPainter (Circle ())
g[0,2] = StampPainter (UpTriangle ())
g[1,0] = StampPainter (DownTriangle ())
g[1,1] = StampPainter (X ())
g[1,2] = StampPainter (Plus ())
g[2,0] = StampPainter (Box ())
g[2,1] = StampPainter (Diamond ())

odw = omega.gtkUtil.OmegaDemoWindow (bag, style, {})
odw.setPainter (g)
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
