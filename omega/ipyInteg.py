"""IPython integration for OmegaPlot."""

# Do we have IPython? Are we being run in it?

try:
    import IPython.ipapi

    haveIPython = True
    api = IPython.ipapi.get ()
    inIPython = api is not None

    if inIPython:
        _ipsh = api.IP
except ImportError:
    haveIPython = False
    inIPython = False
    _ipsh = None

# If we're using it, are we in crazy multithreaded mode?
# If so, check that we're in GTK threading mode, since that's
# the only toolkit backend we have right now.

def _checkGTKThreads ():
    import threading
    
    for t in threading.enumerate ():
        if isinstance (t, IPython.Shell.IPShellGTK):
            return t.gtk_mainloop

    raise ImportError ('Running in multithreaded IPython but not using GTK threads.')

if inIPython:
    usingThreads = isinstance (_ipsh, IPython.Shell.MTInteractiveShell)

    if usingThreads: 
        _real_gtk_mainloop = _checkGTKThreads ()
    else:
        _real_gtk_mainloop = None


def shell ():
    if not inIPython:
        raise Exception ('Trying to get IPython shell and not even in IPython! Fix your code')

    return _ipsh

def gtkMainloopWorkaround ():
    if inIPython and usingThreads:
        _real_gtk_mainloop ()
    else:
        import gtk
        gtk.main ()
