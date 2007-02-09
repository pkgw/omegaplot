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
style = omega.WhiteOnBlackBitmap ()

src = omega.sources.ParametricFunction ()
src.tmin = 0
src.tmax = 2 * pi
src.npts = 1000

sources = {'sink1': src, 'sink2': src}

imf = omega.bag.IndexMapFilter ('FF', (1, 0))
imf.expose (bag, 'sink2')

rdp1 = omega.RectDataPainter (bag)
rdp1.xaxis.min = -2
rdp1.xaxis.max = 2
rdp1.yaxis.min = -2
rdp1.yaxis.max = 2
rdp1.expose ('sink1')

rdp2 = omega.RectDataPainter (bag)
rdp2.xaxis = rdp1.xaxis
rdp2.yaxis = rdp1.yaxis
rdp2.linkTo (imf)

def tempstyle (ctxt, style):
    style.apply_genericLine (ctxt)
    ctxt.set_source_rgb (0.9, 0.3, 0.3)

rdp2.lineStyle = tempstyle

# In terms of aesthetics, I would leave the left and right
# axis painters as just the baseline, but they reveal some
# limitations in the current LinearAxisPainter code.

rp = omega.RectPlot ()
rp.bpainter = omega.LinearAxisPainter (rdp1.xaxis)
#rp1.tpainter = omega.LinearAxisPainter (rdp1.xaxis)
rp.lpainter = omega.LinearAxisPainter (rdp1.yaxis)
rp.rpainter = rp.lpainter
rp.fieldAspect = 1.0
rp.addFieldPainter (rdp1)
rp.addFieldPainter (rdp2)

odw = omega.gtkUtil.OmegaDemoWindow (bag, style, sources)
odw.setPainter (rp)
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
