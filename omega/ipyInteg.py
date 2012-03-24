# Copyright 2011, 2012 Peter Williams
#
# This file is part of omegaplot.
#
# Omegaplot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# Omegaplot is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Omegaplot. If not, see <http://www.gnu.org/licenses/>.

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
