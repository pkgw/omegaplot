#! /bin/sh
#
# Run this to create the configure script and Makefile.in
# files.
#
# Many packages have their autogen.sh also run the configure
# script; I don't like this behavior and avoid it here.

DIE=0
PKG=omegaplot
ACLOCAL_FLAGS="-I . $ACLOCAL_FLAGS"

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.

(autoconf --version) < /dev/null > /dev/null 2>&1 || {
  echo
  echo "**Error**: You must have \`autoconf' installed to compile $PKG."
  echo "Download the appropriate package for your distribution,"
  echo "or get the source tarball at ftp://ftp.gnu.org/pub/gnu/"
  DIE=1
}

(automake --version) < /dev/null > /dev/null 2>&1 || {
  echo
  echo "**Error**: You must have \`automake' installed to compile $PKG."
  echo "Get ftp://ftp.gnu.org/pub/gnu/automake-1.10.tar.gz"
  echo "(or a newer version if it is available)"
  DIE=1
  NO_AUTOMAKE=yes
}

# if no automake, don't bother testing for aclocal
test -n "$NO_AUTOMAKE" || (aclocal --version) < /dev/null > /dev/null 2>&1 || {
  echo
  echo "**Error**: Missing \`aclocal'.  The version of \`automake'"
  echo "installed doesn't appear recent enough."
  echo "Get ftp://ftp.gnu.org/pub/gnu/automake-1.10.tar.gz"
  echo "(or a newer version if it is available)"
  DIE=1
}

if test "$DIE" -eq 1; then
  exit 1
fi

cd $srcdir

echo "Running aclocal $ACLOCAL_FLAGS ..."
aclocal $ACLOCAL_FLAGS || 
  { echo "**Error**: aclocal failed."; exit 1; }

echo "Running automake --add-missing --gnu $am_opt ..."
automake --add-missing --gnu $am_opt ||
  { echo "**Error**: automake failed."; exit 1; }

echo "Running autoconf ..."
autoconf || 
  { echo "**Error**: autoconf failed."; exit 1; }

echo "Now run \`$srcdir/configure' to configure your build and create"
echo "Makefiles."
exit 0
