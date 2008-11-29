noinst_DATA = \
 apiref.txt \
 index.txt \
 omega.txt \
 omega_util.txt

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
