AC_INIT(README)
AC_CANONICAL_SYSTEM
dnl AM_CONFIG_HEADER(config.h)
AM_INIT_AUTOMAKE(omegaplot,0.1)
AM_MAINTAINER_MODE

AC_SUBST(ACLOCAL_AMFLAGS, "-I .")
AM_PATH_PYTHON(2.3.5)
AM_CHECK_PYMOD(cairo,,,
  AC_MSG_ERROR(A cairo Python module is required)
)
AM_CHECK_PYMOD(gtk,,,
  AC_MSG_ERROR(A gtk Python module is required)
)

dnl Configuration checks for latexsnippet -- need to make
dnl sure that we have latex, dvipng, and the preview package
dnl installed.

AC_PATH_PROG(LATEX, latex, true, false)
if $LATEX ; then
   :
else
   AC_MSG_ERROR([The program 'latex' wasn't found on your system! It
is necessary for the creation of text labels. Set the environment
variable LATEX to the full path to the program if it is not in your
default system \$PATH.])
fi

AC_PATH_PROG(DVIPNG, dvipng, true, false)
if $DVIPNG ; then
   :
else
   AC_MSG_ERROR([The program 'dvipng' wasn't found on your system! It
is necessary for the creation of text labels. Set the environment
variable DVIPNG to the full path to the program if it is not in your
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
   AC_MSG_ERROR([Proper generation of text labels requires the LaTeX
`preview' package, which does not seem to be present on your system.
It is part of the GNU AUCTeX package, available from
http://www.gnu.org/software/auctex. It is available on Fedora Core 
systems as the `tetex-preview' RPM package.])
fi

dnl All done.

AC_OUTPUT([
Makefile
latexsnippet/Makefile
omega/Makefile
demo/Makefile
])
