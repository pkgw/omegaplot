# -*- mode: python; coding: utf-8 -*-
# Copyright 2012, 2014, 2015 Peter Williams
# Licensed under the MIT License.

"""omegamap [keywords]

Render an image attractively into vector or bitmap output.

map=
 Required. Path to the input image: FITS, MIRIAD, or CASA format

range=
 Required. Data values that anchor the minimum and maximum of the
 color scale. The first range value must be smaller than the second.
 If unspecified, the minimum and maximum data values are used.

out=
 Path of output image to create; image will be displayed interactively
 if unspecified. Format guessed from the file extension; legal ones
 include pdf, eps, ps, png, svg.

pangofamily=
 Font family to use in Pango.

pangosize=
 Size of the font to use in Pango.

subsuperrise=
 Amount to offset subscripts and superscripts in *builtin* text labels,
 in ten thousands of an em (default: 5000, as in Pango itself).
 User-specified labels have to do this manually by using
 <span rise="RISE" size="smaller"> rather than <sub> or <sup>.

dims=
 Width and height of the output image, in points or pixels; ignored if
 displaying interactively. If only one value is specified, it is used
 for both width and height. (default: 256,256)

margin=
 Margin width, in points or pixels (default: 2)

coloring=
 Name of the color scale to use. A list of possibilities can be seen
 by running "python -m colormaps".  (default: white_to_black)

omstyle=
 Name of the OmegaPlot style class to use (default:
 ColorOnWhiteVector)

subshape=
 Width and height of the subregion of the input map to image, in
 pixels, centered on the image center. No subregion is extracted if
 unspecified. If only one value is specified, it is used for both the
 width and height of the subregion.

logfactor=
 If specified, the data are logarithmically scaled such that
  newdata = log (data + logfactor * (1 - median(data)))
 If unspecified, linear scaling is used. The range values used
 above are taken relative to the _transformed_ data.

aspect=
 Aspect ratio of the plot field. Ratio is unconstrained if left
 unspecified.

xlabel=
 Label of the X axis. (default: "Right Ascension (J2000)")

ylabel=
 Label of the Y axis. (default: "Declination (J2000)")

ccrad=
 Radius of an overlaid circle to draw around the pointing center, in
 arcseconds. Useful for denoting the primary beam size.

locator=
 Three to five values: RA (sexagesimal hours), dec (sexagesimal
 degrees), major axis (arcseconds), minor (arcsec, defaults to major),
 PA (degrees, defaults to 0). An ellipse of the specified shape will
 be drawn at the position. Useful for identifying special sources. PA
 is east from north. Can be specified multiple times, in which case
 multiple locators will be drawn.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np, sys

try:
    import cairocffi as cairo
except ImportError:
    import cairo

from pwkit import astimage, astutil, cli, data_gui_helpers, ellipses
from pwkit.kwargv import ParseKeywords, Custom

import omega as om
import omega.astimage

try:
    import omega.pango_g3 as ompango
except ImportError:
    import omega.pango_g2 as ompango


class Config (ParseKeywords):
    map = Custom (str, required=True)

    @Custom ([float, float], required=True)
    def range (v):
        if v[0] >= v[1]:
            cli.wrong_usage (__doc__, 'data range must have min < max')
        return v

    out = str
    pangofamily = str
    pangosize = float
    subsuperrise = 5000
    coloring = 'white_to_black'
    logfactor = float
    xlabel = 'Right Ascension (J2000)'
    ylabel = 'Declination (J2000)'
    ccrad = Custom (float, scale=astutil.A2R)

    @Custom ([int, int], default=None)
    def subshape (v):
        if v[1] is None:
            v[1] = v[0]
        return v

    @Custom (float)
    def aspect (v):
        if v <= 0:
            cli.wrong_usage (__doc__, 'aspect ratio must be greater than zero')
        return v

    @Custom (2.0)
    def margin (v):
        return [v] * 4

    @Custom ([256.0, float])
    def dims (v):
        if v[1] is None:
            v[1] = v[0]
        return v

    @Custom ([str, str, float, float, 0.], minvals=3, default=None, repeatable=True)
    def locator (v):
        # switch order from ra,dec to lat,lon!
        tmp = astutil.parsehours (v[0])
        v[0] = astutil.parsedeglat (v[1])
        v[1] = tmp

        v[2] *= astutil.A2R # major axis

        if v[2] <= 0:
            die ('locator major axis must be greater than zero')

        if v[3] is None:
            v[3] = v[2]
        else:
            v[3] *= astutil.A2R # minor axis

        if v[3] <= 0:
            die ('locator minor axis must be greater than zero')

        v[4] *= astutil.D2R # PA

        if v[3] > v[2]: # try to be sensible if minor > major
            v[2], v[3] = v[3], v[2]
            v[4] += 0.5 * np.pi

        return v

    @Custom ('ColorOnWhiteVector')
    def omstyle (v):
        try:
            return getattr (om.styles, v) ()
        except:
            die ('can\'t load/instantiate OmegaPlot style "%s"', v)


def plot (config):
    im = astimage.open (config.map, 'r')
    im = im.simple ()

    if config.subshape is not None:
        # Take a subset of the image?
        nw, nh = config.subshape
        pixofs = [(im.shape[0] - nh) // 2, (im.shape[1] - nw) // 2]
        im = im.subimage (pixofs, [nh, nw])

    data = im.read (squeeze=True, flip=True)
    print ('Raw data bounds:', data.min (), data.max ())

    if config.logfactor is not None:
        # TODO: switch to using the 'stretch' keyword of data_to_argb32() or
        # something along those lines.
        q = config.logfactor * (1 - np.median (data))
        print ('Magic q:', q)
        assert data.min () > -q, 'Can\'t logify it'
        data = np.log (data + q)

    argb32 = data_gui_helpers.data_to_argb32 (data,
                                              cmin=config.range[0],
                                              cmax=config.range[1],
                                              cmap=config.coloring)

    # Draw!

    p = om.quickImage (cairo.FORMAT_ARGB32, argb32)
    coords = omega.astimage.AstimageCoordinates (im, p)
    p.paintCoordinates (coords)
    p.setLabels (config.xlabel, config.ylabel)

    if config.aspect is not None:
        p.fieldAspect = config.aspect

    if config.ccrad is not None:
        assert False, 'need to re-implement pointing center for astimage'
        pclon, pclat = None, None # IMPLEMENT ME
        lat, lon = astutil.sphofs (pclat, pclon, config.ccrad,
                                   np.linspace (0, 2 * np.pi, 200))
        cx, cy = coords.arb2lin (lon, lat)
        p.addXY (cx, cy, None, dsn=1)

    for clat, clon, maj, min, pa in config.locator:
        # lat = dec = x in astro PA convention
        dlat, dlon = ellipses.ellpoint (maj, min, pa, np.linspace (0, 2 * np.pi, 200))
        lat = clat + dlat
        lon = clon + dlon / np.cos (lat) # ignore pole issues
        ex, ey = coords.arb2lin (lon, lat)
        p.addXY (ex, ey, None, dsn=1)

    return p


def doit (config):
    fontparams = {}
    if config.pangofamily is not None:
        fontparams['family'] = config.pangofamily
    if config.pangosize is not None:
        fontparams['size'] = config.pangosize
    if len (fontparams):
        ompango.setFont (**fontparams)
    ompango.setBuiltinSubsuperRise (config.subsuperrise)

    # Plot bounds and tick marks are drawn in the "muted" color since you want
    # them to be less prominent than the data. However, when drawing a map,
    # which fills the plot field, the tick marks should be made more prominent
    # since they can easily get lost against the image. We achieve this by
    # redefining "muted".
    config.omstyle.colors.muted = config.omstyle.colors.foreground

    p = plot (config)

    if config.out is None:
        p.show (style=config.omstyle)
    else:
        p.save (config.out, style=config.omstyle, dims=config.dims,
                margins=config.margin)


def cmdline (argv=None):
    if argv is None:
        argv = sys.argv
        cli.unicode_stdio ()

    cli.check_usage (__doc__, argv, usageifnoargs='long')
    doit (Config ().parse (argv[1:]))
