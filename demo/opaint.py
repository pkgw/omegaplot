#!/usr/bin/python

import omega
import gtk

from math import sin
from omega import RectPlot, TextPainter

bag = omega.Bag ()
style = omega.BlackOnWhiteBitmap ()
src = omega.Function (lambda x: sin (x) + 2)

sources = {'data': src}

rdp = omega.RectDataPainter (bag)
rdp.expose ('data')

rp = RectPlot ()
rp.fieldAspect = 1.0
rp.addFieldPainter (rdp)
rp.magicAxisPainters ('btlr')
rp.lpainter.numFormat = '%1.3f'
rp.tpainter.numFormat = '%1.5f'

rp.addOuterPainter (TextPainter ('top left'), RectPlot.SIDE_TOP, 0)
rp.addOuterPainter (TextPainter ('top mid'), RectPlot.SIDE_TOP, 0.5)
rp.addOuterPainter (TextPainter ('top right'), RectPlot.SIDE_TOP, 1)
rp.addOuterPainter (TextPainter ('right top'), RectPlot.SIDE_RIGHT, 1)
rp.addOuterPainter (TextPainter ('right mid'), RectPlot.SIDE_RIGHT, 0.5)
rp.addOuterPainter (TextPainter ('right bot'), RectPlot.SIDE_RIGHT, 0.)
rp.addOuterPainter (TextPainter ('bottom left'), RectPlot.SIDE_BOTTOM, 0)
rp.addOuterPainter (TextPainter ('bottom mid'), RectPlot.SIDE_BOTTOM, 0.5)
rp.addOuterPainter (TextPainter ('bottom right'), RectPlot.SIDE_BOTTOM, 1)
rp.addOuterPainter (TextPainter ('left top'), RectPlot.SIDE_LEFT, 1)
rp.addOuterPainter (TextPainter ('left mid'), RectPlot.SIDE_LEFT, 0.5)
rp.addOuterPainter (TextPainter ('left bot'), RectPlot.SIDE_LEFT, 0.)

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, sources, rp))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
