# omegaplot

Omegaplot is an open-source Python library for creating excellent
plots. It offers:

* Drop-dead easy support for standard plotting needs with attractive
  results.
* Output of those plots to the screen, PDF, EPS, and PNG with
  optimal quality and identical rendering for each.
* Support for better-than-publication-quality, professional-level
  features such as full vectorized rendering of arbitrary equations,
  angled axis ticks on spherical projections, etc.

Here are a few of the key technical features that allow these goals
to be accomplished:

* A clean, modular, object-oriented API for creating and combining plots,
  with good separation between plot structure and styling.
* Rendering with the Cairo toolkit to allow fully vectorized drawing
  of plots to multiple backends with ideal bitmapping and performance
  and no code changes.
* Optional support for text rendering through LaTeX, with full
  vectorization of the output, and Pango, with simple high-quality
  typesetting and textual information embedded in PDF output.
* Default styling that aims to be both attractive and legible, following
  a Tuftean design aesthetic.

Omegaplot has been written by Peter Williams, peter@newton.cx. It has
been stable and useful for his purposes, but it is currently a
homebrew project: there is no manual, examples are rare, and the API
has its share of hacks and rough edges.

On the other hand, you can get personal support from Peter for just
about any question via email. If you're at all interested, please
get in touch.

## Installation

A standard `pip install .` should suffice. Omegaplot requires the following
packages:

* Python (duh)
* Numpy
* Cairo and its Python bindings

Omegaplot optionally integrates with several other modules and/or
tools to provide various features:

* GTK+ and its Python bindings -- live GUI plotting (highly recommended)
* LaTeX -- can be used to provide arbitrarily complex label rendering.
  Requires the programs "latex", "dvips", and "pstoedit" to be found
  in the path, and the "preview" LaTeX package to be available. The
  last of these is part of the GNU AUCTeX package, available from
  http://www.gnu.org/software/auctex. It is available on Fedora
  systems as the 'tetex-preview' RPM package.
* Pango and its Python bindings -- good, fast text layout without
  the complete featureset of LateX
* Jupyter/IPython -- can render plots live in the background, subject to some
  limitations; requires GTK+.
* pyrap -- can be used to draw proper labels for spherical coordinate
  systems stored in CASA images.
* pywcs -- can be used to draw proper labels for spherical coordinate
  systems stored in preexisting pywcs object.


## Licensing

Omegaplot is free software, licensed under the GNU GPL version 3 or
higher, with the exception of some insignificant files used in the
build process. See the file COPYING for more information, including a
copy of the license.


## Copyright Notice for This File

Copyright Peter Williams

This file is free documentation; the copyright holder gives unlimited
permission to copy, distribute, and modify it.
