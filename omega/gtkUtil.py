import gobject
import gtk
import gtkThread

import sys #exc_info

from base import NullPainter, Painter
import styles

class OmegaArea (gtk.DrawingArea):
    def __init__ (self, painter, style, autoRepaint, weak=False):
        gtk.DrawingArea.__init__ (self)

        self.weakRef = weak
        self.omegaStyle = style
        self.setPainter (painter)

        self.lastException = None
        self.paintId = -1
        self.autoRepaint = autoRepaint

        self.connect ('expose_event', self._expose)
        self.connect ('destroy', self._destroyed)

    # Painting

    def _expose (self, widget, event):
        if self.lastException is not None:
            # oops we blew up
            from traceback import print_exception
            print 'Unprocessed exception from last painting:'
            print_exception (*self.lastException)
            return False

        # Figure out if we still have our painter

        if not self.weakRef:
            p = self.painter
        else:
            p = self.pRef ()

            if p is None:
                p = NullPainter ()
            
        ctxt = widget.window.cairo_create()
        style = self.omegaStyle
        
        # set a clip region for the expose event
        ctxt.rectangle (event.area.x, event.area.y,
                        event.area.width, event.area.height)
        ctxt.clip()

        w, h = self.allocation.width, self.allocation.height

        try:
            p.renderBasic (ctxt, style, w, h)
        #except ContextTooSmallError, ctse:
        #    print ctse
        except:
            self.lastException = sys.exc_info ()
        
        return False

    # automatic repaint control
    
    paintInterval = 500 # milliseconds
    autoReconfigure = True # Reconfigure every repaint?
    
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
        if self.lastException:
            # oops we blew up
            from traceback import print_exception
            print_exception (*self.lastException)
            print 'Painting failed. Disabling automatic repainting.'
            self.lastException = None
            self.paintId = -1
            return False

        #if self.autoReconfigure:
        #    self.forceReconfigure ()
                
        self.queue_draw ()
        return True

    # Python interface
    
    def setPainter (self, p):
        if not self.weakRef:
            self.painter = p
        else:
            import weakref
            self.pRef = weakref.ref (p)
        
        self.queue_draw ()
    
    #def forceReconfigure (self):
    #    self.pipeline.forceReconfigure ()

    # Cleanup
    
    def _destroyed (self, unused):
        self.autoRepaint = False # remove the timeout
        
    def __del__ (self):
        self._destroyed (self)

_slowMode = False

def slowMode (value=True):
    global _slowMode
    _slowMode = value

class OmegaDemoWindow (gtk.Window):
    isFullscreen = False

    __gsignals__ = { 'key-press-event' : 'override' }
    
    def __init__ (self, painter, style, parent=None, weak=False):
        gtk.Window.__init__ (self, gtk.WINDOW_TOPLEVEL)
        
        self.set_title ('OmegaPlot Test Window Canvas')
        self.set_default_size (640, 480)
        self.set_border_width (4)
        self.set_position (gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_type_hint (gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        #self.set_urgency_hint (True)

        if parent is not None: self.set_transient_for (parent)
        
        # window_position GtkWindowPosition, type_hint GdkWindowTypeHint
        # urgency_hint, GdkGravity gravity, 
        self.oa = OmegaArea (painter, style, True, weak=weak)
        self.add (self.oa)

        if _slowMode:
            self.oa.autoRepaint = False
            self.oa.autoReconfigure = False
    
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
    
    # Emulate the OmegaArea interface for convenience.

    def get_paintInterval (self):
        return self.oa.paintInterval

    def set_paintInterval (self, value):
        self.oa.paintInterval = value

    paintInterval = property (get_paintInterval, set_paintInterval)
    
    def get_autoReconfigure (self):
        return self.oa.autoReconfigure

    def set_autoReconfigure (self, value):
        self.oa.autoReconfigure = value

    autoReconfigure = property (get_autoReconfigure, set_autoReconfigure)
    
    def get_autoRepaint (self):
        return self.oa.autoRepaint

    def set_autoRepaint (self, value):
        self.oa.autoRepaint = value

    autoRepaint = property (get_autoRepaint, set_autoRepaint)
    
    def setPainter (self, p):
        self.oa.setPainter (p)

    #def forceReconfigure (self):
    #    self.oa.forceReconfigure ()

def showBlocking (painter, style=None):
    if style is None: 
            style = styles.WhiteOnBlackBitmap ()
            
    win = OmegaDemoWindow (painter, style)
    win.connect ('destroy', gtk.main_quit)
    win.show_all ()
    
    gtk.main ()

class LiveDisplay (object):
    def __init__ (self, painter, style):
        self.win = None

        if painter is not None:
            self.setPainter (painter, style)

    def setPainter (self, painter, style=None, winTrack=True):
        # Note that we do not honor @style if the window already
        # exists. Should add a setStyle () function at some point.
        
        if style is None:
            style = styles.WhiteOnBlackBitmap ()
        
        def f ():
            if self.win is not None:
                self.win.setPainter (painter)

                if winTrack:
                    if painter is not None: self.win.present ()
                    else: self.win.hide ()
            else:
                self.win = OmegaDemoWindow (painter, style, weak=True)

                if winTrack:
                    if painter is not None:
                        self.win.show_all ()
                        self.win.present ()
                    #else: self.win.hide () # redundant
            
        gtkThread.send (f)

    # More OmegaArea interface emulation, with the added wrinkle
    # of doing everything cross-thread. Don't even bother providing
    # read access to the attributes.

    def set_paintInterval (self, value):
        def doit ():
            if self.win != None:
                self.win.paintInterval = value
        gtkThread.send (doit)
        
    paintInterval = property (None, set_paintInterval)
    
    def set_autoReconfigure (self, value):
        def doit ():
            if self.win != None:
                self.win.autoReconfigure = value
        gtkThread.send (doit)

    autoReconfigure = property (None, set_autoReconfigure)
    
    def set_autoRepaint (self, value):
        def doit ():
            if self.win != None:
                self.win.autoRepaint = value
        gtkThread.send (doit)

    autoRepaint = property (None, set_autoRepaint)
    
    #def forceReconfigure (self):
    #    def doit ():
    #        if self.win: self.win.forceReconfigure ()
    #    gtkThread.send (doit)

    def queueRedraw (self):
        def doit ():
            if self.win: self.win.queue_draw ()
        gtkThread.send (doit)
        
    lingerInterval = 250
    
    def linger (self):
        """Block the caller until the LiveDisplay window has been closed
        by the user. Useful for semi-interactive programs to pause while
        the user examines a plot. You may avoid using threads altogether
        with the showBlocking () in module gtkUtil."""
        
        from Queue import Queue, Empty

        q = Queue ()

        def check_done ():
            if self.win is not None:
                return True
            q.put (True)
            return False
        
        def doit ():
            gobject.timeout_add (self.lingerInterval,
                                 check_done)

        gtkThread.send (doit)
        q.get ()
    
import util
util.defaultLiveDisplay = LiveDisplay
util.defaultShowBlocking = showBlocking
util.slowMode = slowMode
