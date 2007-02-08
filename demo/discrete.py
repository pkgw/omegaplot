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

# These are my made-up average temperature data for
# Boston, MA over the course of a year. The data
# are plausible, I think.

months = ('Jan', 'Feb', 'Mar', 'Apr',
          'May', 'Jun', 'Jul', 'Aug',
          'Sep', 'Oct', 'Nov', 'Dec')
data = (25, 23, 35, 51, 67, 71,
        74, 69, 45, 44, 41, 22)

pts = zip (months, data)

src = omega.sources.StoredData ('SF', pts)

sources = {'temps': src, 'errs': src}

rdp = omega.RectDataPainter (bag)
rdp.xaxis = omega.EnumeratedDiscreteAxis ('S', months)
rdp.yaxis.min = 0
rdp.yaxis.max = 100
rdp.pointStamp = omega.stamps.UpTriangle ()
rdp.lines = False
rdp.expose ('temps')

def errfilter (mon, val):
    return (mon, val - 5 * (val % 3 + 1),
            val + 5 * (val % 3 + 1))
ff = omega.bag.FunctionFilter (errfilter, 'SFF', 'SF')
ff.expose (bag, 'errs')

rdp2 = omega.BandPainter (bag)
rdp2.xaxis = rdp.xaxis
rdp2.yaxis = rdp.yaxis
rdp2.linkTo (ff)

rp = omega.RectPlot ()
rp.bpainter = omega.DiscreteAxisPainter (rdp.xaxis)
rp.lpainter = omega.LinearAxisPainter (rdp.yaxis)
rp.lpainter.numFormat = '%.0f'
rp.rpainter = rp.lpainter
rp.addFieldPainter (rdp)
rp.addFieldPainter (rdp2)

odw = omega.gtkUtil.OmegaDemoWindow (bag, style, sources)
odw.setPainter (rp)
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
