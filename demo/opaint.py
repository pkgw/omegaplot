#!/usr/bin/python

import omega
import gtk

from math import sin
from omega.images import LatexPainter
from omega import RectPlot

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

rp.addOuterPainter (LatexPainter ('top left'), RectPlot.SIDE_TOP, 0)
rp.addOuterPainter (LatexPainter ('top mid'), RectPlot.SIDE_TOP, 0.5)
rp.addOuterPainter (LatexPainter ('top right'), RectPlot.SIDE_TOP, 1)
rp.addOuterPainter (LatexPainter ('right top'), RectPlot.SIDE_RIGHT, 1)
rp.addOuterPainter (LatexPainter ('right mid'), RectPlot.SIDE_RIGHT, 0.5)
rp.addOuterPainter (LatexPainter ('right bot'), RectPlot.SIDE_RIGHT, 0.)
rp.addOuterPainter (LatexPainter ('bottom left'), RectPlot.SIDE_BOTTOM, 0)
rp.addOuterPainter (LatexPainter ('bottom mid'), RectPlot.SIDE_BOTTOM, 0.5)
rp.addOuterPainter (LatexPainter ('bottom right'), RectPlot.SIDE_BOTTOM, 1)
rp.addOuterPainter (LatexPainter ('left top'), RectPlot.SIDE_LEFT, 1)
rp.addOuterPainter (LatexPainter ('left mid'), RectPlot.SIDE_LEFT, 0.5)
rp.addOuterPainter (LatexPainter ('left bot'), RectPlot.SIDE_LEFT, 0.)

odw = omega.gtkUtil.OmegaDemoWindow (omega.PaintPipeline (bag, style, sources, rp))
odw.connect ('destroy', gtk.main_quit)
odw.show_all ()

gtk.main ()
