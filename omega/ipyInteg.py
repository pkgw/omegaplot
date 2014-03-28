# Copyright 2011, 2012, 2014 Peter Williams
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

"""IPython integration for OmegaPlot.

This only works for versions >=0.11, I think.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Are we being run inside IPython?

try:
    __IPYTHON__
    inIPython = True
except NameError:
    inIPython = False


def shell ():
    if not inIPython:
        return None
    return get_ipython ()


def gtk_mainloop_running ():
    if not inIPython:
        return False

    import IPython.lib.inputhook
    return IPython.lib.inputhook.inputhook_manager.current_gui () == 'gtk'
