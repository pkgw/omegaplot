dnl Copyright 2011, 2012, 2014 Peter Williams
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

AC_INIT([omegaplot], [0.2], [peter@newton.cx])
AC_CONFIG_SRCDIR([omega/rect.py])
AM_INIT_AUTOMAKE([dist-bzip2])

AM_MAINTAINER_MODE

dnl Both of these are used in doc/conf.py.in

AC_SUBST([OMEGA_SHORTVERSION],[0.2])
AC_SUBST([OMEGA_COPYRIGHT],["2011-2014 Peter Williams"])

dnl Python and dependent modules

AM_PATH_PYTHON([2.6])

AM_CHECK_PYMOD(cairo,,,[
  AC_MSG_ERROR([The 'cairo' Python module is required])
])

AM_CHECK_PYMOD(gtk,,[gtkmsg=yes],[
  gtkmsg="no; the 'gtk' Python module was not found"
])

AM_CHECK_PYMOD(numpy,,,[
  AC_MSG_ERROR([The 'numpy' Python module is required])
])

dnl Checks for building documentation

AC_PATH_PROG(SPHINXBUILD, sphinx-build, :)
if test x"$SPHINXBUILD" != x: ; then
   BUILD_DOCS=true
   docmsg=yes
else
   BUILD_DOCS=false
   docmsg="no; the program 'sphinx-build' was not found"
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
dnl TODO: should we embed these paths in latexsnippet.py?

latexmsg=no

AC_PATH_PROG(LATEX, latex, :)
if test x"$LATEX" != x: ; then
   :
else
   latexmsg="$latexmsg; no 'latex' in \$PATH"
fi

AC_PATH_PROG(DVIPS, dvips, :)
if test x"$DVIPS" != x: ; then
   :
else
   latexmsg="$latexmsg; no 'dvips' in \$PATH"
fi

AC_PATH_PROG(PSTOEDIT, pstoedit, :)
if test x"$PSTOEDIT" != x: ; then
   :
else
   latexmsg="$latexmsg; no 'dvips' in \$PATH"
fi

if test x"$LATEX" != x: ; then
  AC_MSG_CHECKING([for the LaTeX preview package])
  cat <<EOF >previewcheck.tex
\documentclass{article}
\usepackage{preview}
\begin{document}
\end{document}
EOF

  if $LATEX previewcheck.tex </dev/null 1>/dev/null 2>&1 ; then
    AC_MSG_RESULT([yes])
  else
    AC_MSG_RESULT([no])
    latexmsg="$latexmsg; no 'preview' package found"
  fi
  rm -f previewcheck.tex previewcheck.log previewcheck.aux previewcheck.dvi
fi

if test x"$latexmsg" = xno ; then
  latexmsg=yes
fi

dnl All done.

AC_CONFIG_FILES([
Makefile
oputil/Makefile
omega/Makefile
doc/Makefile
])

AC_OUTPUT

dnl Summary

echo
echo "Interactive display with GTK backend?:" $gtkmsg
echo "Building documentation?              :" $docmsg
echo "Support for LaTeX text labels?       :" $latexmsg
