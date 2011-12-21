dnl Copyright 2011 Peter Williams
dnl
dnl This file is part of omegaplot.
dnl
dnl Omegaplot is free software: you can redistribute it and/or modify
dnl it under the terms of the GNU General Public License as published
dnl by the Free Software Foundation, either version 3 of the License,
dnl or (at your option) any later version.
dnl
dnl Omegaplot is distributed in the hope that it will be useful, but
dnl WITHOUT ANY WARRANTY; without even the implied warranty of
dnl MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
dnl General Public License for more details.
dnl
dnl You should have received a copy of the GNU General Public License
dnl along with Omegaplot. If not, see <http://www.gnu.org/licenses/>.

dnl General initialization

AC_INIT([OmegaPlot], [0.1], [peter@newton.cx])
AC_CONFIG_SRCDIR([omega/rect.py])
AM_INIT_AUTOMAKE([dist-bzip2])

AM_MAINTAINER_MODE

dnl Both of these are used in doc/conf.py.in

AC_SUBST([OMEGA_SHORTVERSION],[0.1])
AC_SUBST([OMEGA_COPYRIGHT],["2011, Peter Williams"])

dnl Python and dependent modules

AM_PATH_PYTHON([2.3.5])

AM_CHECK_PYMOD(cairo,,,[
  AC_MSG_ERROR([The 'cairo' Python module is required])
])

AM_CHECK_PYMOD(gtk,,,[
  AC_MSG_ERROR([The 'gtk' Python module is required])
])

AM_CHECK_PYMOD(numpy,,,[
  AC_MSG_ERROR([The 'numpy' Python module is required])
])

dnl Checks for building documentation

AC_PATH_PROG(SPHINXBUILD, sphinx-build, notfound)
if test x"$SPHINXBUILD" != xnotfound ; then
   BUILD_DOCS=true
else
   AC_MSG_WARN([The program 'sphinx-build' wasn't found on your
system! Documentation will not be built.])
   BUILD_DOCS=false
fi

AM_CONDITIONAL([BUILD_DOCS], $BUILD_DOCS)

if $BUILD_DOCS ; then
   AC_CONFIG_FILES([doc/conf.py])
fi

dnl We use this in the doc/ install rule. On my Fedora 10 computers this
dnl subst wasn't needed but on a SuSE 10.2 it was -- I think that older
dnl (<=1.9) automakes don't define this automatically whereas newer ones
dnl do.
AC_PROG_MKDIR_P
AC_SUBST([MKDIR_P])

dnl Configuration checks for latexsnippet -- need to make
dnl sure that we have latex, dvips, pstoedit, and the preview package
dnl installed.

AC_PATH_PROG(LATEX, latex, notfound)
if test x"$LATEX" != xnotfound ; then
   :
else
   AC_MSG_ERROR([The program 'latex' wasn't found on your system! It
is necessary for the creation of text labels. Set the environment
variable LATEX to the full path to the program if it is not in your
default system \$PATH.])
fi

AC_PATH_PROG(DVIPS, dvips, notfound)
if test x"$DVIPS" != xnotfound ; then
   :
else
   AC_MSG_ERROR([The program 'dvips' wasn't found on your system! It
is necessary for the creation of text labels. Set the environment
variable DVIPS to the full path to the program if it is not in your
default system \$PATH.])
fi

AC_PATH_PROG(PSTOEDIT, pstoedit, notfound)
if test x"$PSTOEDIT" != xnotfound ; then
   :
else
   AC_MSG_ERROR([The program 'pstoedit' wasn't found on your system! It
is necessary for the creation of text labels. Set the environment
variable PSTOEDIT to the full path to the program if it is not in your
default system \$PATH.])
fi

AC_MSG_CHECKING([for the LaTeX preview package])
cat <<EOF >previewcheck.tex
\documentclass{article}
\usepackage{preview}
\begin{document}
\end{document}
EOF

if latex previewcheck.tex </dev/null 1>/dev/null 2>&1 ; then
   rm -f previewcheck.tex previewcheck.log previewcheck.aux previewcheck.dvi
   AC_MSG_RESULT([yes])
else
   rm -f previewcheck.tex previewcheck.log previewcheck.aux previewcheck.dvi
   AC_MSG_RESULT([no])
   AC_MSG_ERROR([Proper generation of typeset text labels requires the LaTeX
`preview' package, which does not seem to be present on your system.
It is part of the GNU AUCTeX package, available from
http://www.gnu.org/software/auctex. It is available on Fedora Core 
systems as the `tetex-preview' RPM package.])
fi

dnl All done.

AC_CONFIG_FILES([
Makefile
oputil/Makefile
omega/Makefile
doc/Makefile
])

AC_OUTPUT
