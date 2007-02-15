#!/usr/bin/python
#
# Obvious a lot of work needs to go into support structures to make
# it easier to create graphs, but this is just testing the
# bare functionality so far.

import omega
import gtk

import random
from math import *

bag = omega.Bag ()
style = omega.BlackOnWhiteBitmap ()

# A quick little simulation that demonstrates the
# central limit theorem! Apparently in this specific
# case it is the de Moivre-Laplace limit theorem.

ntrials = 10000
nflips = 10
counts = [0] * 11

def fact (n):
    if n == 1: return 1
    return n * fact (n - 1)

expected_max = 1. * ntrials * fact (nflips) / fact (nflips / 2)**2 / 2**nflips

for i in xrange (0, ntrials):
    nheads = 0

    for i in xrange (0, nflips):
        nheads += random.randint (0, 1)

    counts[nheads] += 1

obs = zip (range (0, nflips + 1), counts)
obssrc = omega.sources.StoredData ('FF', obs)

thy = omega.sources.Function ()
thy.xmin = -1
thy.xmax = 11
thy.npts = 500
thy.func = lambda x: expected_max * exp (-(x - 5)**2 / 4 / sqrt(2))
                          
sources = { 'obs': obssrc, 'thy': thy }

dhp = omega.DiscreteHistogramPainter (bag)
dhp.field.xaxis = omega.DiscreteIntegerAxis (0, 10)
#dhp.xaxis.padBoundaries = False
dhp.field.yaxis.min = 0
dhp.field.yaxis.max = expected_max * 1.1
dhp.expose ('obs')

def hackDash (ctxt, style):
    style.apply_genericLine (ctxt)
    ctxt.set_dash ((3, 3), 0.0)

rdp = omega.RectDataPainter (bag)
rdp.field.xaxis = omega.LinearAxis (thy.xmin, thy.xmax)
rdp.field.yaxis = dhp.field.yaxis
rdp.lineStyle = hackDash
rdp.expose ('thy')

rp = omega.RectPlot ()
rp.addFieldPainter (dhp)
rp.addFieldPainter (rdp)
rp.magicAxisPainters ('vb')
rp.lpainter.numFormat = '%.0f'

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, sources, rp))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
