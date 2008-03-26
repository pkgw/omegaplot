#! /usr/bin/env python

import numpy as N
import omega

xs = N.asarray ([1, 2, 4, 8, 16])

rp = omega.RectPlot ()
rp.defaultField.xaxis = omega.rect.EnumeratedDiscreteAxis (xs)
rp.magicAxisPainters ('lb')
rp.bpainter.ticksBetween = True

fp = omega.rect.DiscreteSteppedPainter ()
fp.setInts (xs)
fp.setFloats (xs**2)
rp.add (fp)

rp.showBlocking ()

