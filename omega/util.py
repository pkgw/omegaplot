# -*- mode: python; coding: utf-8 -*-
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

r"""
.. moduleauthor:: Peter Williams <peter@newton.cx>
.. sectionauthor:: Peter Williams <peter@newton.cx>

Various functions that don't fit in other modules particularly
well. This is not to imply that these functions aren't important --
:func:`quickXY`, for instance, is quite useful.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from six.moves import range as xrange
import numpy as np

from .base import _kwordDefaulted

# Quick display of plots


def quickXY(*args, **kwargs):
    r"""Create a :class:`omega.rect.RectPlot` displaying some data.

    :type y_or_x: 1D array-like
    :param y_or_x: If *opt_y* is specified, the X coordinate data. Otherwise, the
                   Y coordinate data. In the latter case, the X coordinates
                   are defaulted to 0, 1, 2, *etc.* Must be one-dimensional.
                   This is converted to an array via :func:`numpy.asarray`,
                   so any sequence is acceptable, not just a
                   :class:`numpy.ndarray`.
    :type opt_y: 1D array-like
    :param opt_y: The Y coordinate data. Defaults to :const:`None`, which
                  indicates that *y_or_x* actually specifies the Y coordinate
                  data. Must be one-dimensional and the same size as *y_or_x*.
                  Same processing semantics as *y_or_x*.
    :type label: string
    :param label: The text used in the key of the newly-created plot. Defaults
                  to 'Data'.
    :type xmin: float
    :param xmin: The lower X bound of the plot. Defaults to :const:`None`,
                 which
                 indicates that the lower X bound should be chosen
                 automatically. See XXXFIXME for a description of the
                 automatic range-finding algorithm.
    :type xmax: float
    :param xmax: The upper X bound of the plot. Analogous semantics to
                 *xin*.
    :type ymin: float
    :param ymin: The lower Y bound of the plot. Analogous semantics to
                 *xmin*.
    :type ymax: float
    :param ymax: The upper Y bound of the plot. Analogous semantics to
                 *xmin*.
    :type xlog: bool
    :param xlog: Whether the X axis should be rendered logarithmically.
                 Defaults to :const:`False`.
    :type ylog: bool
    :param ylog: Whether the Y axis should be rendered logarithmically.
                 Defaults to :const:`False`.
    :type lines: bool
    :param lines: Whether to connect the data points with lines. If
                  :const:`False`, the data points are instead marked
                  with circles. Defaults to :const:`True`. (This argument
                  is handled in :meth:`omega.rect.RectPlot.addXY`)
    :type lineStyle: style item
    :param lineStyle: Extra styling to be applied to the lines connecting
                      the data points. Defaults to :const:`None`, which
                      indicates no extra styling. (This argument
                      is handled in :meth:`omega.rect.RectPlot.addXY`)
    :type pointStamp: :class:`omega.Stamp`
    :param pointStamp: A :class:`omega.Stamp` used to draw the data points.
                       Defaults to :const:`None`, which indicates that
                       no stamp will be used, unless *lines* is
                       :const:`False`, in which case a default stamp is chosen.
                       (This argument is handled in
                       :meth:`omega.rect.RectPlot.addXY`)
    :type autokey: bool
    :param autokey: If :const:`True`, automatically add an item to the
                    new plot's key containing the text in *label*. Defaults to
                    :const:`True`. (This argument is handled in
                    :meth:`omega.rect.RectPlot.add`)
    :type rebound: bool
    :param rebound: If :const:`True`, recompute the bounds of the plot
                    after adding the data to it with
                    :meth:`omega.rect.RectPlot.rebound`. Otherwise,
                    use the default plot bounds. Defaults to :const:`True`.
                    (This argument is handled in
                    :meth:`omega.rect.RectPlot.add`)
    :type nudgex: bool
    :param nudgex: If :const:`True` and *rebound* is :const:`True`, nudge the
                   X bounds of the plot to rounded numbers appropriate to,
                   and larger than, the range of the data. (This argument is
                   handled in :meth:`omega.rect.RectPlot.add`)
    :type nudgey: bool
    :param nudgey: Analogous to *nudgex* for the Y bounds. (This argument is
                   handled in :meth:`omega.rect.RectPlot.add`)
    :rtype: :class:`omega.rect.RectPlot`
    :return: A rectangular plot object with sensible defaults containing
             a single :class:`omega.rect.XYDataPainter` showing the
             input data.

    The returned plot object is a newly-created :class:`omega.plot.RectPlot`
    object that has its :meth:`omega.plot.RectPlot.addXY` procedure
    called to add a :class:`omega.rectXYDataPainter` displaying the
    specified data. With the exception of *xmin*, *xmax*, *ymin*, and *ymax*,
    all arguments to this function are passed verbatim to
    :meth:`omega.plot.RectPlot.addXY`, so any argument accepted by that
    function is accepted by this function.

    This function can be used to very quickly display some data. For instance,
    if you're working at an interactive prompt, the following code will create
    and display a plot object::

      >>> p = omega.quickXY (x, sin(x), 'Sin').show ()

    """

    xmin = _kwordDefaulted(kwargs, "xmin", float, None)
    xmax = _kwordDefaulted(kwargs, "xmax", float, None)
    ymin = _kwordDefaulted(kwargs, "ymin", float, None)
    ymax = _kwordDefaulted(kwargs, "ymax", float, None)
    xlog = _kwordDefaulted(kwargs, "xlog", bool, False)
    ylog = _kwordDefaulted(kwargs, "ylog", bool, False)

    from .rect import RectPlot

    rp = RectPlot()
    rp.addXY(*args, **kwargs)
    rp.setBounds(xmin, xmax, ymin, ymax)
    rp.setLinLogAxes(xlog, ylog)

    if xlog or ylog:
        rp.rebound()

    return rp


def quickXYErr(*args, **kwargs):
    xmin = _kwordDefaulted(kwargs, "xmin", float, None)
    xmax = _kwordDefaulted(kwargs, "xmax", float, None)
    ymin = _kwordDefaulted(kwargs, "ymin", float, None)
    ymax = _kwordDefaulted(kwargs, "ymax", float, None)
    xlog = _kwordDefaulted(kwargs, "xlog", bool, False)
    ylog = _kwordDefaulted(kwargs, "ylog", bool, False)

    from .rect import RectPlot

    rp = RectPlot()
    rp.addXYErr(*args, **kwargs)
    rp.setBounds(xmin, xmax, ymin, ymax)
    rp.setLinLogAxes(xlog, ylog)

    if xlog or ylog:
        rp.rebound()

    return rp


def quickDF(*args, **kwargs):
    xmin = _kwordDefaulted(kwargs, "xmin", float, None)
    xmax = _kwordDefaulted(kwargs, "xmax", float, None)
    ymin = _kwordDefaulted(kwargs, "ymin", float, None)
    ymax = _kwordDefaulted(kwargs, "ymax", float, None)
    xlog = _kwordDefaulted(kwargs, "xlog", bool, False)
    ylog = _kwordDefaulted(kwargs, "ylog", bool, False)

    from .rect import RectPlot

    rp = RectPlot()
    rp.addDF(*args, **kwargs)
    rp.setBounds(xmin, xmax, ymin, ymax)
    rp.setLinLogAxes(xlog, ylog)

    if xlog or ylog:
        rp.rebound()

    return rp


def quickHist(
    data, bins=10, range=None, weights=None, density=None, filled=False, **kwargs
):
    from numpy import concatenate, histogram

    xmin = _kwordDefaulted(kwargs, "xmin", float, None)
    xmax = _kwordDefaulted(kwargs, "xmax", float, None)
    ymin = _kwordDefaulted(kwargs, "ymin", float, 0.0)
    ymax = _kwordDefaulted(kwargs, "ymax", float, None)

    values, edges = histogram(data, bins, range, weights=weights, density=density)
    if edges.size != values.size + 1:
        raise RuntimeError("using too-old numpy? got weird histogram result")

    from . import rect

    if filled:
        dp = rect.FilledHistogram(**kwargs)
    else:
        dp = rect.ContinuousSteppedPainter(**kwargs)
    dp.setDataHist(edges, values)

    rp = rect.RectPlot()
    rp.add(dp)
    rp.setBounds(xmin, xmax, ymin, ymax)
    return rp


def quickContours(
    data,
    rowcoords,
    colcoords,
    keyText="Contours",
    xmin=None,
    xmax=None,
    ymin=None,
    ymax=None,
    xlog=False,
    ylog=False,
    **kwargs
):
    from .rect import RectPlot

    rp = RectPlot()
    rp.addContours(data, rowcoords, colcoords, keyText, **kwargs)
    rp.setBounds(xmin, xmax, ymin, ymax)
    rp.setLinLogAxes(xlog, ylog)

    if xlog or ylog:
        rp.rebound()

    return rp


def quickImage(format, data):
    from .rect import RectPlot, ImagePainter

    p = RectPlot()
    ip = ImagePainter().wrap(format, data)
    # take advantage of any futzing of data done by wrap():
    width = ip.surface.get_width()
    height = ip.surface.get_height()
    # anchor coordinate system to pixel centers:
    ip.setLocation(-0.5, width - 0.5, height - 0.5, -0.5)
    p.add(ip, nudgex=False, nudgey=False)
    # TODO: square up axes
    return p


# A function to easily make a demo plot to make testing of
# rendering features quick. The purpose of these is not
# to demonstrate fancy plots, but just to give something
# quick to render.

_demoNumber = 0


def _demo():
    global _demoNumber
    import numpy as np

    if _demoNumber == 0:
        x = np.linspace(0, 10, 100)
        p = quickXY(x, np.sin(x), "sin(x)")
        p.addXY(x, np.cos(x), "cos(x)")
        p.setLabels("Radians", "Trigginess")
    elif _demoNumber == 1:
        x = np.linspace(-5, 5, 100)
        p = quickXY(x, x**2, "squared")
        p.addXY(x, x**3, "cubed")
        p.setLabels("X", "Y")
    elif _demoNumber == 2:
        x = np.linspace(0.01, 10, 100)
        p = quickXY(x, np.log10(x), "base 10")
        p.addXY(x, np.log(x), "natural")
        p.setLabels("X", "Log[X]")

    _demoNumber = (_demoNumber + 1) % 3
    return p


# Easy construction of pagers -- not that getting the pager
# you want is difficult, but I find that I write a lot of programs
# that I want to page either to the screen or to a file. My usual
# semantics are that argv has a filename if a file is to be used
# or is empty if the screen is to be used


def quickPager(args, **kwargs):
    from . import render

    if len(args) == 0:
        pg = render.makeDisplayPager(**kwargs)
    elif len(args) == 1:
        pg = render.makePager(args[0], **kwargs)
    else:
        raise ValueError("Unexpected args to quickPager: %s" % (args,))

    return pg


# Dumping plots -- saving them to disk conveniently.

_dumpPager = None
dumpTemplate = "omegaDump%02d.ps"


def _makeDumpPager(**kwargs):
    from .render import getFilePagerInfo, MultiFilePager, ReusingPager

    tup = getFilePagerInfo(dumpTemplate)
    if tup is None:
        raise Exception("Unhandled dump filetype " + dumpTemplate)

    tname, klass, dims, margins, style = tup
    p = MultiFilePager(dumpTemplate, klass, dims, margins, style)
    return ReusingPager(p)


def dumpPainter(painter, **kwargs):
    global _dumpPager

    if _dumpPager is None:
        _dumpPager = _makeDumpPager(**kwargs)

    painter.sendTo(_dumpPager)
    print('Dumped to "%s".' % _dumpPager.spager.lastFile)


def resetDumping():
    global _dumpPager
    _dumpPager = None


# Geometry stuff


def doublearray(a, b):
    return np.asarray([a, b, a, b])


def shrinkAspect(aspect, w, h):
    if aspect is not None:
        # We don't short-circuit so aggressively here to make sure our
        # sanity checks get run.
        aspect = float(aspect)

    w, h = float(w), float(h)

    if aspect is not None and aspect <= 0.0:
        raise ValueError("illegal aspect ratio %f" % aspect)

    if w < 0.0:
        raise ValueError("illegal width %f" % w)

    if h < 0.0:
        raise ValueError("illegal height %f" % h)

    if aspect is None:
        return w, h

    if w == 0.0 or h == 0.0:
        return 0.0, 0.0

    if w > h * aspect:  # Too wide
        return h * aspect, h

    return w, w / aspect


def expandAspect(aspect, w, h):
    if aspect is not None:
        # We don't short-circuit so aggressively here to make sure our
        # sanity checks get run.
        aspect = float(aspect)

    w, h = float(w), float(h)

    if aspect is not None and aspect <= 0.0:
        raise ValueError("illegal aspect ratio %f" % aspect)

    if w < 0.0:
        raise ValueError("illegal width %f" % w)

    if h < 0.0:
        raise ValueError("illegal height %f" % h)

    if aspect is None:
        return w, h

    if w < h * aspect:  # Not wide enough
        return h * aspect, h

    return w, w / aspect


def nudgeMargins(current, minima):
    """Given some space allocated to margins and their minimum sizes, reallocate
    the space to make the margins as even as possible."""

    result = np.array(current)
    minima = np.asarray(minima)

    if result[0] + result[2] + 1e-4 < minima[0] + minima[2]:
        raise ValueError(
            "not enough vertical space to redistribute (%s, %s)" % (result, minima)
        )
    if result[1] + result[3] + 1e-4 < minima[1] + minima[3]:
        raise ValueError(
            "not enough horizontal space to redistribute (%s, %s)" % (result, minima)
        )
    if np.any(minima < 0):
        raise ValueError("some margin minima were negative (%s, %s)" % (result, minima))
    if np.any(result < 0):
        raise ValueError("some margin sizes were negative (%s, %s)" % (result, minima))

    for i in xrange(4):
        if result[i] < minima[i]:
            delta = minima[i] - result[i]
            result[i] += delta
            result[(i + 2) % 4] -= delta

    return result
