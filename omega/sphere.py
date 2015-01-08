# -*- mode: python ; coding: utf-8 -*-
# Copyright 2011, 2012, 2014 Peter Williams
#
# This file is part of omegaplot.
#
# Omegaplot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Omegaplot is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Omegaplot. If not, see <http://www.gnu.org/licenses/>.

# Axis painters for spherical projections, and potentially
# other spherical helpers

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np

from . import rect, TextStamper, textMarkup as TM

DISPLAY_DMS = 0
DISPLAY_HMS = 1

WRAP_POS_DEG = 0 # range 0 to 360
WRAP_POS_HR = 1 # range 0 to 24
WRAP_ZCEN_DEG = 2 # range -180 to 180
WRAP_ZCEN_HR = 3 # range -12 to 12
WRAP_LAT = 4 # wrap like a latitude should

LEVEL_UNIT = 0
LEVEL_MIN = 2
LEVEL_SEC = 4

_increments = [
# minor tick incr in seconds, major per minor, label detail level
(3600, 5, LEVEL_UNIT), # whole hour / degree
(1800, 4, LEVEL_UNIT), # 30 minutes, major every 2 hrs/degs
(1800, 2, LEVEL_UNIT), # 30 minutes
(900, 4, LEVEL_UNIT), # 15 minutes
(600, 6, LEVEL_UNIT), # 10 minutes
(300, 12, LEVEL_UNIT), # 5 minutes, major every unit
(300, 3, LEVEL_MIN), # 5 minutes, major every 15
(60, 5, LEVEL_MIN), # 1 minute
(60, 2, LEVEL_MIN), # 1 minute
(30, 2, LEVEL_MIN), # 30 s
(15, 4, LEVEL_MIN), # 15 s
(10, 6, LEVEL_MIN), # 10 s
(5, 12, LEVEL_MIN), # 5 s
(1, 5, LEVEL_SEC), # 1 s
]

_separators = {
    # It may not be obvious, but the ' and " below are Unicode prime
    # and double-prime characters, not typewriter quotes.
    DISPLAY_DMS: ('UNIT_°', 'UNIT_′', 'UNIT_″'),
    DISPLAY_HMS: ('UNIT_h', 'UNIT_m', 'UNIT_s'),
}

def _wrap_pos_deg (sec):
    while sec >= 1296000: # 360 * 3600
        sec -= 1296000
    while sec < 0:
        sec += 1296000
    return sec


def _wrap_pos_hr (sec):
    while sec >= 86400: # 24 * 3600
        sec -= 86400
    while sec < 0:
        sec += 86400
    return sec


def _wrap_zcen_deg (sec):
    while sec < -648000: # 180 * 3600
        sec += 1296000
    while sec > 648000:
        sec -= 1296000
    return sec


def _wrap_zcen_hr (sec):
    while sec < -43200: # 12 * 3600
        sec += 86400
    while sec > 43200:
        sec -= 86400
    return sec


def _wrap_lat (sec):
    while abs (sec) > 324000: # 90 * 3600
        if sec > 0:
            sec = 324000 - sec
        else:
            sec = -324000 + sec
    return sec


_wrappers = {
    WRAP_POS_DEG: _wrap_pos_deg,
    WRAP_POS_HR: _wrap_pos_hr,
    WRAP_ZCEN_DEG: _wrap_zcen_deg,
    WRAP_ZCEN_HR: _wrap_zcen_hr,
    WRAP_LAT: _wrap_lat,
}


class AxisInfoHolder (object):
    # xformed, isMajor, labelw, labelh, labelts
    pass

class AngularAxisPainter (rect.BlankAxisPainter):
    def __init__ (self, axis, vscale, disptype, wraptype):
        super (AngularAxisPainter, self).__init__ ()
        self.axis = axis
        self.vscale = vscale
        self.disptype = disptype
        self.wraptype = wraptype

    majorTickScale = 2.5 # in largeScale
    minorTickScale = 2.5 # in smallScale
    tickStyle = 'bgLinework'
    textColor = 'foreground'
    labelStyle = None
    avoidBounds = True
    paintLabels = True
    labelSeparation = 2 # in smallScale
    labelMinorTicks = False
    angleLabels = False

    def nudgeBounds (self):
        self.axis.normalize ()
        # TODO: implement something clever

    def _info (self, ctxt, style):
        # TODO: make sure matched top/bottom painters have the same
        # minincr/majorperminor setup.  we work in two simultaneous
        # unit systems: the "axis" units that the underlying axis
        # knows, and (arc)seconds. they are related by seconds = 3600
        # * axis * self.vscale. axis coordinates are used for layout
        # via axis.transform. seconds are used for computing labels.

        self.axis.normalize ()
        axmin = self.axis.min
        axmax = self.axis.max
        axspan = axmax - axmin

        if axspan == 0:
            return []

        for secincr, majorperminor, detaillev in _increments:
            axincr = secincr / self.vscale / 3600
            if axspan / axincr > max (8, 3 * majorperminor):
                break
        else:
            raise Exception ('TODO: fraction-of-arcsec labels')

        coeff = int (np.ceil (axmin / axincr))
        axval = coeff * axincr
        if axval < axmin:
            axval = axmin # roundoff insurance
        secval = axval * self.vscale * 3600
        secmajincr = majorperminor * secincr

        infos = []
        axvalues = []

        lastunit = lastmin = lastsec = None

        while self.axis.inbounds (axval):
            axvalues.append (axval)
            info = AxisInfoHolder ()
            infos.append (info)
            info.labelts = None
            info.isMajor = (coeff % majorperminor == 0)
            info._label = info.isMajor or self.labelMinorTicks
            info._secval = secval

            # compute label info. This includes how much detail to
            # give in the labeling, assuming left-to-right reading on
            # a non-reversed axis

            if info._label:
                sign = ''

                # Wrap and round. TODO: if we implement sub-second
                # precision, making the rounding level configurable
                # from _increments, and honor it below with a %.*d.

                effsecval = _wrappers[self.wraptype] (secval)
                effsecval = round (effsecval, 0)

                if effsecval < 0:
                    sign = '-'
                    effsecval = -effsecval

                unit = int (np.floor (effsecval / 3600))
                mnt = int (np.floor (effsecval / 60 - unit * 60.))
                sec = max (effsecval - unit * 3600 - mnt * 60, 0)
                info._breakdown = [sign, unit, mnt, sec]

                if lastunit is None or unit != lastunit:
                    start = LEVEL_UNIT
                elif lastmin is None or mnt != lastmin:
                    start = LEVEL_MIN
                else:
                    start = LEVEL_SEC

                info._lstart = min (start, detaillev)

                lastunit = unit
                lastmin = mnt
                lastsec = sec

            axval += axincr
            secval += secincr
            coeff += 1

        # now adjust label info for right-to-left reading or
        # reversed axes, and create textstampers

        lastunit = lastmin = lastsec = None
        seps = [TM (x)[5:] for x in _separators[self.disptype]]

        for i in xrange (len (infos) - 1, -1, -1):
            info = infos[i]
            if not info._label:
                continue

            sign, unit, mnt, sec = info._breakdown

            if lastunit is None or unit != lastunit:
                start = LEVEL_UNIT
            elif lastmin is None or mnt != lastmin:
                start = LEVEL_MIN
            else:
                start = LEVEL_SEC

            start = min (start, info._lstart)
            items = ['%s%d' % (sign, unit), seps[0],
                     '%02d' % mnt, seps[1],
                     '%02.0f' % sec, seps[2]]

            text = ''.join (items[start:detaillev+2])
            info.labelts = TextStamper (text)
            lastunit = unit
            lastmin = mnt
            lastsec = sec

        # now get transformed coords and textstamper sizes. Both
        # of these operations are sometimes much faster when done
        # in batch.

        xformed, nangles = self.axis.transformWithDirection (np.asarray (axvalues))
        for info, xf, nangle in zip (infos, xformed, nangles):
            info.xformed = xf
            info.nangle = nangle

            if info.labelts is not None:
                info.labelw, info.labelh = info.labelts.getSize (ctxt, style)

        return infos


    def spaceExterior (self, helper, ctxt, style):
        forward = outside = backward = 0

        for info in self._info (ctxt, style):
            if info.labelts is None:
                continue

            outside = max (outside, helper.spaceRectOut (info.labelw, info.labelh,
                                                         angle=self.angleLabels))
            fw, bw = helper.spaceRectPos (info.xformed, info.labelw, info.labelh,
                                          angle=self.angleLabels)
            forward = max (forward, fw)
            backward = max (backward, bw)

        if outside > 0:
            outside += self.labelSeparation * style.smallScale

        return forward, outside, backward


    def paint (self, helper, ctxt, style):
        infos = self._info (ctxt, style)

        super (AngularAxisPainter, self).paint (helper, ctxt, style)
        style.apply (ctxt, self.tickStyle)

        for info in infos:
            if info.isMajor:
                length = self.majorTickScale * style.largeScale
            else:
                length = self.minorTickScale * style.smallScale

            if not self.avoidBounds or (info.xformed != 0. and info.xformed != 1.):
                helper.paintNormalTickIn (ctxt, info.xformed, info.nangle, length)

        if not self.paintLabels:
            return

        style.apply (ctxt, self.labelStyle)
        tc = style.getColor (self.textColor)

        for info in infos:
            if info.labelts is None:
                continue

            helper.moveToAlong (ctxt, info.xformed)
            helper.relMoveOut (ctxt, self.labelSeparation * style.smallScale)

            if self.angleLabels:
                ctxt.save ()
                helper.setupAngledRect (ctxt, info.labelw, info.labelh)
                info.labelts.paintHere (ctxt, tc)
                ctxt.restore ()
            else:
                helper.relMoveRectOut (ctxt, info.labelw, info.labelh)
                info.labelts.paintHere (ctxt, tc)
