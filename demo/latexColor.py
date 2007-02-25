#!/usr/bin/python

import omega, omega.latex
from omega.stamps import *
from omega.images import *

import gtk

bag = omega.Bag ()

style = omega.BlackOnWhiteBitmap ()
#style.smallScale *= 2

g = omega.Grid (2, 2)
g[0,0] = omega.TextPainter ('2+2')
g[0,1] = omega.TextPainter ('2+2')
g[1,0] = omega.TextPainter ('2+2')
g[1,1] = omega.TextPainter ('2+2')

g[0,1].color = (1, 0, 0)
g[1,0].color = (0, 1, 0)
g[1,1].color = (0, 0, 1)

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, {}, g))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
