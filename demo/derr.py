#! /usr/bin/env python

import sys, numpy as N, omega

# These are my made-up average temperature data for
# Boston, MA over the course of a year. The data
# are plausible, I think.
#
# TODO: axis labels of month names, not numbers

months = ('Jan', 'Feb', 'Mar', 'Apr',
          'May', 'Jun', 'Jul', 'Aug',
          'Sep', 'Oct', 'Nov', 'Dec')
data = N.asarray ((25, 23, 35, 51, 67, 71,
                   74, 69, 45, 44, 41, 22))

# Plot it with errors.

p = omega.RectPlot ()

ps = omega.stamps.WithYErrorBars (omega.stamps.Dot ())
dp = omega.XYDataPainter (lines=False, pointStamp=ps, keyText='Fake Boston Data')
p.add (dp, rebound=False)

dp.field.xaxis = omega.rect.DiscreteAxis (0, 11)
p.magicAxisPainters ('lb') # to get correct axis painter class on bottom
dp.data.setFloats (range (0, 12), data, data + 5, data - 5)
dp.setBounds (0, 11, 0, 100)

p.lpainter.numFormat = '%.0f'
p.bpainter.formatLabel = lambda n: months[n]
p.setLabels (None, 'Temperature (F)')

if len (sys.argv) == 1:
    p.showBlocking ()
else:
    p.save (sys.argv[1])
