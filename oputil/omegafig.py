# -*- mode: python; coding: utf-8 -*-
# Copyright 2013-2014 Peter Williams
# Licensed under the MIT License.

"""omegafig [Python file] [keywords...]

Make a plot with omegaplot, either interactively or to hard copy. The Python
file should provide a function called plot() that returns an omegaplot
painter.

out=
 Path of output image to create; image will be displayed interactively if
 unspecified. Format guessed from the file extension; legal ones include pdf,
 eps, ps, png, svg.

dims=
 Width and height of the output image, in points or pixels; ignored if
 displaying interactively. If only one value is specified, it is used for both
 width and height. (default: 256,256; nonintegers not allowed)

margin=
 Margin width, in points or pixels (default: 2)

omstyle=
 Name of the OmegaPlot style class to use (default: ColorOnWhiteVector)

pango=[bool]
 Whether to use Pango for text rendering (default: true)

pangofamily=[str]
 The name of the font family to use for text; passed to Pango

pangosize=[int]
 The size of the font to use for text; passed to Pango

Set OMEGAFIG_BACKTRACE to a nonempty environment value to get full backtraces
when the figure-creating code crashes.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, types

from pwkit import cli
from pwkit.kwargv import ParseKeywords, Custom

import omega as om


class Config(ParseKeywords):
    out = str
    pango = True
    pangofamily = str
    pangosize = int

    @Custom(2.0)
    def margin(v):
        return [v] * 4

    @Custom([256, int])
    def dims(v):
        if v[1] is None:
            v[1] = v[0]
        return v

    @Custom("ColorOnWhiteVector")
    def omstyle(v):
        try:
            return getattr(om.styles, v)()
        except:
            cli.die('can\'t load/instantiate OmegaPlot style "%s"', v)


def doit(driver, args):
    # Load up the driver code

    try:
        text = open(driver).read()
    except Exception as e:
        cli.die('cannot read driver file "%s": %s', driver, e)

    try:
        code = compile(text, driver, "exec")
    except Exception as e:
        if "OMEGAFIG_BACKTRACE" in os.environ:
            raise
        cli.die('cannot compile driver file "%s": %s', driver, e)

    ns = {"__file__": driver, "__name__": "__omegafig__"}

    try:
        exec(code, ns)
    except Exception as e:
        if "OMEGAFIG_BACKTRACE" in os.environ:
            raise
        cli.die('cannot execute driver file "%s": %s', driver, e)

    pfunc = ns.get("plot")
    if pfunc is None:
        cli.die('driver file "%s" does not provide a function called "plot"', driver)
    if not callable(pfunc):
        cli.die(
            'driver file "%s" provides something called "plot", but it\'s '
            "not a function",
            driver,
        )

    # Deal with args

    try:
        code = pfunc.__code__
    except AttributeError:
        code = pfunc.func_code

    nargs = code.co_argcount
    argnames = code.co_varnames

    keywords = []
    nonkeywords = []

    for arg in args:
        if "=" in arg:
            keywords.append(arg)
        else:
            nonkeywords.append(arg)

    if len(nonkeywords) != nargs:
        cli.die(
            "expected %d non-keyword arguments to driver, but got %d",
            nargs,
            len(nonkeywords),
        )

    config = Config()
    defaults = ns.get("figdefaults")

    if defaults is not None:
        for key in defaults:
            setattr(config, key, defaults[key])

    config.parse(keywords)

    # Set up omegaplot globals as appropriate

    if config.pango:
        import omega.pango_g3 as ompango

        fontparams = {}
        if config.pangofamily is not None:
            fontparams["family"] = config.pangofamily
        if config.pangosize is not None:
            fontparams["size"] = config.pangosize
        if len(fontparams):
            ompango.setFont(**fontparams)

    # Execute.

    p = pfunc(*nonkeywords)

    if config.out is None:
        p.show(style=config.omstyle)
    else:
        p.save(
            config.out, style=config.omstyle, dims=config.dims, margins=config.margin
        )


def cmdline(argv=None):
    if argv is None:
        argv = sys.argv
        cli.unicode_stdio()

    cli.check_usage(__doc__, argv, usageifnoargs="long")
    doit(argv[1], argv[2:])
