#! /usr/bin/env python

import omega, numpy as N, sys
latex = False #or True

if latex:
    import omega.latex
    kt = 'Some data (\LaTeX)'
    xl = '$x$'
    yl = '$\sin x$'
else:
    kt = 'Some data'
    xl = 'x'
    yl = 'sin x'
    
x = N.linspace (0, 10, 200)
y = N.sin (x)

#p = omega.quickXY (x, y, kt)
#p.setLabels (xl, yl)

#if len (sys.argv) == 1:
#    p.showBlocking ()
#else:
#    p.save (sys.argv[1])

pg = omega.quickPager (sys.argv[1:], nw=2, nh=2)

for i in xrange (0, 6):
    p = omega.quickXY (x, y * (i + 1), kt)
    p.setLabels (xl, yl)
    pg.send (p)

pg.done ()
