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

from __future__ import absolute_import, division, print_function, unicode_literals

import gobject
import gtk

import sys #exc_info

from .base import NullPainter, Painter, ToplevelPaintParent, ContextTooSmallError
from . import styles, render

_defaultStyle = styles.ColorOnBlackBitmap


# This is needed to know what to do about mainloop integration with the pager
# (XXX: should have a generic architecture, blah blah).
from . import ipython


interactiveAutoRepaint = False

def autoRepaint (repaint):
    global interactiveAutoRepaint
    interactiveAutoRepaint = repaint


# A GTK widget that renders a Painter

class OmegaPainter (gtk.DrawingArea,ToplevelPaintParent):
    def __init__ (self, painter, style, autoRepaint, weak=False):
        gtk.DrawingArea.__init__ (self)
        ToplevelPaintParent.__init__ (self, weak)

        self.omegaStyle = style
        ToplevelPaintParent.setPainter (self, painter)

        self.paintId = -1
        self.autoRepaint = autoRepaint

        self.connect (b'expose_event', self._expose)
        self.connect (b'destroy', self._destroyed)


    def setStyle (self, style):
        if self.omegaStyle is not style:
            self.queue_draw ()

        self.omegaStyle = style


    def setPainter (self, painter):
        # Don't check to see if painter is the same object
        # as our current painter, since it might be the same
        # object with different children (e.g., GridPager)
        # in which case a redraw is still merited. And it's
        # better to have an unnecessary redraw than not to
        # redraw when necessary.

        self.queue_draw ()
        ToplevelPaintParent.setPainter (self, painter)


    # The rendering magic

    def _expose (self, widget, event):
        ctxt = widget.window.cairo_create()
        style = self.omegaStyle

        w, h = self.allocation.width, self.allocation.height

        p = self.getPainter ()

        if p is None:
            # We lost our painter, or never had one! Repaint
            # the whole area as blank. We could set our child
            # to the new NullPainter, but if we're weak-ref'ing,
            # then it'll get deallocated when this function
            # exits ...
            p = NullPainter ()
            p.setParent (self)
        else:
            # set a clip region for the expose event
            ctxt.rectangle (event.area.x, event.area.y,
                            event.area.width, event.area.height)
            ctxt.clip()

        try:
            p.renderBasic (ctxt, style, w, h)
        except ContextTooSmallError, ctse:
            print (ctse)

        return False

    # automatic repaint control


    paintInterval = 500 # milliseconds


    def get_autoRepaint (self):
        return self.paintId >= 0


    def set_autoRepaint (self, value):
        if not value ^ (self.paintId >= 0): return # noop?

        if value:
            self.paintId = gobject.timeout_add (self.paintInterval, \
                                                self._repaint)
        else:
            gobject.source_remove (self.paintId)
            self.paintId = -1


    autoRepaint = property (get_autoRepaint, set_autoRepaint)


    def _repaint (self):
        self.queue_draw ()
        return True


    # Cleanup

    def _destroyed (self, unused):
        self.autoRepaint = False # remove the timeout

        p = self.getPainter ()

        if p is not None:
            p.setParent (None)


    def __del__ (self):
        self._destroyed (self)


# Display pager implementation -- first, a custom window.

class PagerWindow (gtk.Window):
    isFullscreen = False

    __gsignals__ = { b'key-press-event' : b'override' }


    def __init__ (self, blocking, autoRepaint, style=None, parent=None):
        gtk.Window.__init__ (self, gtk.WINDOW_TOPLEVEL)

        self.set_title ('OmegaPlot Pager')
        self.set_default_size (640, 480)
        self.set_border_width (4)
        self.set_position (gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        #self.set_urgency_hint (True)

        if parent is not None: self.set_transient_for (parent)
        if style is None: style = _defaultStyle ()

        # Construct simple widget heirarchy.
        # We don't create the OmegaPainter until we have something
        # to paint.

        self.vb = vb = gtk.VBox ()
        self.add (vb)

        self.op = op = OmegaPainter (None, style, autoRepaint, False)
        self.vb.pack_start (op, True, True, 4)

        if not blocking:
            self.btn = None
        else:
            self.btn = btn = gtk.Button ('Next')
            vb.pack_end (btn, False, False, 4)


    def setPainter (self, p):
        self.op.setPainter (p)


    # Fun

    def do_key_press_event (self, event):
        if not self.isFullscreen and event.keyval == gtk.keysyms.F11:
            self.fullscreen ()
            self.isFullscreen = True
            return True
        elif self.isFullscreen and event.keyval == gtk.keysyms.Escape:
            self.unfullscreen ()
            self.isFullscreen = False
            return True

        return gtk.Window.do_key_press_event (self, event)


class NoLoopDisplayPager (render.DisplayPager):
    # A pager for displaying plots if there is no GTK mainloop
    # running. We start and stop the mainloop as needed to
    # show the plots briefly.

    def __init__ (self, style=None, parent=None):
        self.win = None
        self.style = style
        self.parent = parent


    def send (self, painter):
        if self.win is None:
            self.win = self._makeWin ()

        self.win.setPainter (painter)
        self.win.show_all ()
        self._inModalLoop = True

        try:
            gtk.main ()
        except:
            self._inModalLoop = False
            raise

        assert self._inModalLoop == False, 'Weird mainloop interactions??'


    def done (self):
        self._killWin ()


    def getLatestPainter (self):
        return self.win.op.getPainter ()


    def _makeWin (self):
        win = PagerWindow (True, False, self.style, self.parent)
        win.connect (b'destroy', self._winDestroyed)
        win.btn.connect (b'clicked', self._nextClicked)
        return win


    def _killWin (self):
        if self.win is None: return

        self.win.destroy ()

        # Actually run the mainloop to get rid of the window
        while gtk.events_pending ():
            gtk.main_iteration ()

        self.win = None


    def _winDestroyed (self, event):
        if self._inModalLoop:
            gtk.main_quit ()
            self._inModalLoop = False

        self.win = None


    def _nextClicked (self, event):
        if self._inModalLoop:
            # Not sure how this function could get called
            # with _inModalLoop = False, but let's be safe.
            gtk.main_quit ()
            self._inModalLoop = False


class YesLoopDisplayPager (render.DisplayPager):
    # A display pager for use if there is a GTK mainloop
    # running in the background. This is taken to imply that
    # we're running interactively.

    def __init__ (self, style=None, parent=None):
        self.win = None
        self.style = style
        self.parent = parent


    def send (self, painter):
        if self.win is None:
            self.win = self._makeWin ()

        self.win.setPainter (painter)
        self.win.show_all ()


    def getLatestPainter (self):
        return self.win.op.getPainter ()


    def done (self):
        pass


    def _makeWin (self):
        win = PagerWindow (False, interactiveAutoRepaint, self.style, self.parent)
        win.connect (b'destroy', self._winDestroyed)
        return win


    def _winDestroyed (self, event):
        self.win = None


def makeGtkPager (**kwargs):
    if ipython.gtk_mainloop_running ():
        return YesLoopDisplayPager (**kwargs)
    return NoLoopDisplayPager (**kwargs)

render.setDisplayPagerClass (makeGtkPager)
