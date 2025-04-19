# -*- mode: python; coding: utf-8 -*-
# Copyright 2011, 2012, 2014, 2015 Peter Williams
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

"""
A few things to keep in mind:

- Properties on GObject-derived classes must be explicitly declared,
  and they revert to their default values on destruction. This means
  that GObject-derived classes are best kept simple.

- If you're in Jupyter/IPython and you do "%gui gtk3", show some plots, then
  "%gui" (-> no GUI), bad things will happen. This seems to be Jupyter's
  problem, not mine.
"""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gdk, Gtk

from .base import NullPainter, ToplevelPaintParent, ContextTooSmallError
from . import jupyter, styles, render


_base_default_style = styles.ColorOnBlackBitmap
_default_size_request = (600, 480)


def default_style(widget=None):
    if widget is None:
        screen = Gdk.Screen.get_default()
    else:
        screen = widget.get_screen()

    settings = Gtk.Settings.get_for_screen(screen)
    dpi = settings.get_property("gtk-xft-dpi") / 1024.0
    hidpi = dpi > 120

    style = _base_default_style()

    if hidpi:
        style._gtk_size_request = (
            2 * _default_size_request[0],
            2 * _default_size_request[1],
        )
        style.sizes.smallScale *= 2
        style.sizes.largeScale *= 2
        # we do NOT double fineLine
        style.sizes.normalFontSize *= 2

    return style


# A GTK widget that renders a Painter


class OmegaPainter(Gtk.DrawingArea):
    __gtype_name__ = "OmegaPainter"

    # We can't just call the style "style" since that conflicts with the Gtk
    # style property.
    omega_style = GObject.Property(type=GObject.TYPE_PYOBJECT)
    tpp = GObject.Property(type=GObject.TYPE_PYOBJECT)

    def __init__(self, painter, style, weak=False):
        super(OmegaPainter, self).__init__()

        self.omega_style = style
        self.tpp = ToplevelPaintParent(weak)
        self.tpp.setPainter(painter)

        sr = getattr(style, "_gtk_size_request", _default_size_request)
        self.set_size_request(*sr)

    def setPainter(self, painter):
        # Don't check to see if painter is the same object as our current
        # painter, since it might be the same object with different children
        # (e.g., GridPager) in which case a redraw is still merited. And it's
        # better to have an unnecessary redraw than not to redraw when
        # necessary.
        self.queue_draw()
        self.tpp.setPainter(painter)

    def setStyle(self, style):
        self.queue_draw()
        self.omega_style = style

    def do_draw(self, ctxt):
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        p = self.tpp.getPainter()

        if p is None:
            # We lost our painter, or never had one! Repaint the whole area as
            # blank. We could set our child to the new NullPainter, but if
            # we're weak-ref'ing, then it'll get deallocated when this
            # function exits ...
            p = NullPainter()
            p.setParent(self.tpp)

        try:
            p.renderBasic(ctxt, self.omega_style, w, h)
        except ContextTooSmallError as ctse:
            print(ctse)

    def do_destroy(self):
        # This function must be careful since it can be called
        # from the Python destructor.
        if self.tpp is not None:
            p = self.tpp.getPainter()
            if p is not None:
                p.setParent(None)


# Display pager implementation -- first, a custom window.


class PagerWindow(Gtk.Window):
    __gtype_name__ = "PagerWindow"
    __gsignals__ = {str("key-press-event"): str("override")}  # Py 2/3 compat

    is_fullscreen = GObject.Property(type=bool, default=False)
    op = GObject.Property(type=OmegaPainter)
    btn = GObject.Property(type=Gtk.Button)

    def __init__(self, style=None, parent=None):
        super(PagerWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)

        self.set_title("OmegaPlot Pager")
        self.set_default_size(640, 480)
        self.set_border_width(4)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        # self.set_urgency_hint(True)

        if parent is not None:
            self.set_transient_for(parent)

        if style is None:
            style = default_style(widget=self)

        self.op = op = OmegaPainter(None, style, False)
        self.btn = btn = Gtk.Button(label="Next")

        vb = Gtk.VBox()
        vb.pack_start(op, True, True, 4)
        vb.pack_end(btn, False, False, 4)

        self.add(vb)

    def set_painter(self, p):
        self.op.setPainter(p)

    def set_show_button(self, show_button):
        if show_button:
            self.btn.show()
        else:
            self.btn.hide()

    def do_key_press_event(self, event):
        if not self.is_fullscreen and event.keyval == Gdk.KEY_F11:
            self.fullscreen()
            self.is_fullscreen = True
            return True

        if self.is_fullscreen and event.keyval == Gdk.KEY_Escape:
            self.unfullscreen()
            self.is_fullscreen = False
            return True

        # There's an issue in pygobject3 where it thinks there's a type
        # mismatch between Gdk.EventKey and Gdk.Event. This is the workaround.
        n = Gdk.Event()
        n.type = event.type
        n.window = event.window
        n.send_event = event.send_event
        n.time = event.time
        n.state = event.state
        n.keyval = event.keyval
        n.length = event.length
        n.string = event.string
        n.hardware_keycode = event.hardware_keycode
        n.group = event.group
        n.is_modifier = event.is_modifier
        return self.chain(n)


class Gtk3DisplayPager(render.DisplayPager):
    """Page plots through a window. There's a wrinkle because we try to
    auto-detect when running in Jupyter/IPython with a Glib main loop running
    in the background; if so, send() returns instantly. If not, we block until
    the user hits Next.

    """

    _in_modal_loop = False

    def __init__(self, style=None, parent=None):
        self.win = PagerWindow(style, parent)
        self.win.connect(str("delete-event"), self._window_deleted)
        self.win.btn.connect(str("clicked"), self._next_clicked)

    def is_mainloop_running(self):
        # This is intended to be overridden or replaced.
        return False

    def send(self, painter):
        self.win.set_painter(painter)
        self.win.show_all()

        if self.is_mainloop_running():
            # The window will linger after this function returns.
            self.win.set_show_button(False)
        else:
            # Run the main loop manually; we'll return when the window is
            # closed.
            self.win.set_show_button(True)

            try:
                self._in_modal_loop = True
                Gtk.main()
            finally:
                self._in_modal_loop = False
                self.win.set_painter(None)

    def getLatestPainter(self):
        return self.win.op.tpp.getPainter()

    def done(self):
        if self.is_mainloop_running():
            # Leave the window around for the user to admire.
            return

        # We're in "modal" mode. Hide the window; we have to run the
        # mainloop to process the X events.
        self.win.hide()
        self.win.set_painter(None)

        while Gtk.events_pending():
            Gtk.main_iteration()

    def _window_deleted(self, win, event):
        self.win.hide()
        self.win.set_painter(None)

        if self._in_modal_loop:
            Gtk.main_quit()
            self._in_modal_loop = False

        # True -> do not destroy window.
        return True

    def _next_clicked(self, event):
        # This function shouldn't be called with _in_modal_loop = False,
        # but let's be safe.
        if self._in_modal_loop:
            Gtk.main_quit()
            self._in_modal_loop = False


class Gtk3JupyterDisplayPager(Gtk3DisplayPager):
    def is_mainloop_running(self):
        return jupyter.gtk_mainloop_running()


render.setDisplayPagerClass(Gtk3JupyterDisplayPager)
