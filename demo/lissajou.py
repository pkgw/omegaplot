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

sources = {'data': src}

rdp1 = omega.RectDataPainter (bag)
rdp1.setBounds (-2, 2, -2, 2)
rdp1.expose ('data')

rdp2 = omega.RectDataPainter (rdp1)
rdp2.linkExpose (omega.bag.IndexMapFilter ('FF', (1, 0)), 'data')

def tempstyle (ctxt, style):
    style.apply_genericLine (ctxt)
    ctxt.set_source_rgb (0.9, 0.3, 0.3)

rdp2.lineStyle = tempstyle

# In terms of aesthetics, I would leave the left and right
# axis painters as just the baseline, but they reveal some
# limitations in the current LinearAxisPainter code.

rp = omega.RectPlot ()
rp.fieldAspect = 1.0
rp.addFieldPainter (rdp1)
rp.addFieldPainter (rdp2)
rp.magicAxisPainters ('hv')
rp.setLabels (r'$\int_0^\infty e^x', r'\sin (\pi x) + \sum_0^10 n')

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, sources, rp))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
