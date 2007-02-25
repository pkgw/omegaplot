#!/usr/bin/python
#
# Obvious a lot of work needs to go into support structures to make
# it easier to create graphs, but this is just testing the
# bare functionality so far.

import omega
import gtk
from math import sin, cos, pi
from numpy import sinc

bag = omega.Bag ()
style = omega.BlackOnWhiteBitmap ()

src1 = omega.Function (lambda x: sin (pi * 7 * x) * sinc (x))
src1.xmin = -10
src1.xmax = 10
src1.npts = 1000

src2 = omega.Function (lambda x: cos (pi * 7 * x) * sinc (x))
src2.xmin = -10
src2.xmax = 10
src2.npts = 1000

sources = {'sinc1': src1, 'sinc2': src2}

rdp1 = omega.RectDataPainter (bag)
rdp1.setBounds (-10, 10, -1, 1)
rdp1.expose ('sinc1')

rdp2 = omega.RectDataPainter (rdp1)
rdp2.expose ('sinc2')

# In terms of aesthetics, I would leave the left and right
# axis painters as just the baseline, but they reveal some
# limitations in the current LinearAxisPainter code.

rp1 = omega.RectPlot ()
rp1.addFieldPainter (rdp1)
rp1.magicAxisPainters ('vb')
rp1.lpainter.numFormat = '%1.1f'
rp1.setLabels ('X Value', 'Y Value')

rp2 = omega.RectPlot (rp1)
rp2.addFieldPainter (rdp2)
rp2.setLabels ('X', 'Y')

g = omega.Grid (1, 2)
g[0] = rp1
g[1] = rp2
g.hBorderSize = 4
g.vBorderSize = 4

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, sources, g))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
