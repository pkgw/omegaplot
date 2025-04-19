# -*- mode: python; coding: utf-8 -*-
# Copyright 2011-2016 Peter Williams
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

"""Jupyter/IPython integration for OmegaPlot.

For simplicity we try to maintain compatibility with pre-split IPython, later
versions of IPython, and the Jupyter consoe mode, when possible. The current
code should work for Jupyter around 4.0 and IPython works for versions >=0.11,
I think.

Note that for a while I assumed that the "ipython" command was deprecated
after the Jupyter split. That is not in fact the case. The focus of
development is just a bit different.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

try:
    __IPYTHON__
    inIPython = True
except NameError:
    inIPython = False


def shell():
    if not inIPython:
        return None
    return get_ipython()


def gtk_mainloop_running():
    sh = shell()
    if sh is None:
        return False

    try:
        eventloop = sh.kernel.eventloop
        # If we didn't crash, then we must be in Jupyter.

        if eventloop is None:
            return False
        return "gtk" in eventloop.func_name
    except AttributeError:
        try:
            curhook = sh._inputhook
            # If we didn't crash, we seem to be in IPython >= 5.0 ... I think?
            # I'm not sure if older versions of IPython have this attribute.

            if curhook is None:
                return False
            return "gtk" in curhook.__module__
        except AttributeError:
            # We must be in an older IPython.
            import IPython.lib.inputhook

            gui = IPython.lib.inputhook.inputhook_manager.current_gui()
            return gui in ("gtk", "gtk3")
