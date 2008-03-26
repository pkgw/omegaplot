#!/usr/bin/python
#
# Obvious a lot of work needs to go into support structures to make
# it easier to create graphs, but this is just testing the
# bare functionality so far.

import omega
import numpy as N

npts = 1000

rnd = N.random.normal (size=npts)
counts, left_edges = N.histogram (rnd, 11, (-5, 5))

x = N.linspace (-5, 5, 500)
y = npts / N.sqrt (2 * N.pi) * N.exp (-x**2/2)

rp = omega.RectPlot ()

fp = omega.rect.ContinuousSteppedPainter ()
fp.setFloats (left_edges, counts)
rp.add (fp)

rp.addXY (x, y, 'Model')

rp.showBlocking ()
