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

AC_OUTPUT([
Makefile
latexsnippet/Makefile
omega/Makefile
demo/Makefile
])
