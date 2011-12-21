## Copyright 2011 Peter Williams
##
## This file is part of omegaplot.
##
## Omegaplot is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation, either version 3 of the License,
## or (at your option) any later version.
##
## Omegaplot is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Omegaplot. If not, see <http://www.gnu.org/licenses/>.
##
## (This copyright notice is delimited with double hashes to prevent
## it from being confusingly included in Makefile.in by automake.)

dist_noinst_DATA = \
 apiref.txt \
 common.inc \
 index.txt \
 intro.txt \
 omega.txt \
 omega_util.txt

# Hack: make sure the empty 'static' directory gets created
EXTRA_DIST = static/.gitignore

SCANNEDPY = \
 $(top_srcdir)/omega/__init__.py \
 $(top_srcdir)/omega/util.py

BUILD = PYTHONPATH=$(top_srcdir):$$PYTHONPATH $(SPHINXBUILD) -d doctrees -c .

HTML_STAMP = html.sphstamp

all-local: $(HTML_STAMP)

$(HTML_STAMP): $(noinst_DATA) $(SCANNEDPY)
	$(MKDIR_P) html doctrees
	$(BUILD) -b html $(srcdir) html
	touch $@

clean-local:
	-rm -rf doctrees html $(HTML_STAMP)
