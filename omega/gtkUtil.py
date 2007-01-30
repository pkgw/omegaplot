import gobject
import gtk
import gtkThread

import sys #exc_info

from base import NullPainter, Painter

class OmegaArea (gtk.DrawingArea):
    def __init__ (self, bag, style, sources, autoRepaint):
        gtk.DrawingArea.__init__ (self)

        self._painter = NullPainter ()

        self.bag = bag
        self.omegaStyle = style
        self.sources = sources

        self.savedWidth = -1
        self.savedHeight = -1
        self.lastException = None

        self.paintId = -1
        self.autoRepaint = autoRepaint

        self.connect ('expose_event', self._expose)
        self.connect ('destroy', self._destroyed)

    # Painting
    
    def _expose (self, widget, event):
        ctxt = widget.window.cairo_create()
    
        # set a clip region for the expose event
        ctxt.rectangle (event.area.x, event.area.y,
                        event.area.width, event.area.height)
        ctxt.clip()

        w, h = self.allocation.width, self.allocation.height

        try:
            if w != self.savedWidth or h != self.savedHeight:
                (minw, minh) = self._painter.getMinimumSize (ctxt, self.omegaStyle)

                if w < minw or h < minh:
                    print 'Unable to paint: actual size (%f, %f) smaller than ' \
                          'minimum size (%f, %f)' % (w, h, minw, minh)
                    return False
            
                self._painter.configurePainting (ctxt, self.omegaStyle, w, h)
                self.savedWidth = w
                self.savedHeight = h

            self.omegaStyle.initContext (ctxt, w, h)
            self.bag.startFlushing (self.sources)
            self._painter.paint (ctxt, self.omegaStyle, True)

            while self.bag.startNewRound ():
                self._painter.paint (ctxt, self.omegaStyle, False)
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

        if self.autoReconfigure:
            self.forceReconfigure ()
                
        self.queue_draw ()
        return True

    # Python interface
    
    def setPainter (self, p):
        if p and not isinstance (p, Painter): raise Exception ('Not a Painter: %s' % p)
        self._painter = p or NullPainter ()
        self._painter.setParent (self)
        self.lastException = None
        self.forceReconfigure ()

    def forceReconfigure (self):
        self.savedWidth = self.savedHeight = -1

    def removeChild (self, child): # For self._painter
        pass
    
    # Cleanup
    
    def _destroyed (self, unused):
        self.autoRepaint = False # remove the timeout
        
    def __del__ (self):
        self._destroyed (self)

class OmegaDemoWindow (gtk.Window):
    def __init__ (self, bag, style, sources):
        gtk.Window.__init__ (self)
        
        self.set_title ('OmegaPlot Test Window Canvas')
        self.set_default_size (640, 480)
        self.set_border_width (4)
        
        self.oa = OmegaArea (bag, style, sources, True)
        self.add (self.oa)

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

    def forceReconfigure (self):
        self.oa.forceReconfigure ()

class LiveDisplay (object):
    def __init__ (self, bag, style, sources, painter):
        self.win = None

        # Here we set up a destroy function that the window will use.
        # We only hold a weak reference to 'self' here, so that 'del
        # [instance-of-LiveDisplay]' will actually destroy the object
        # (and hence the window), which is a functionality that I
        # really like, for no particular reason. If we pass a
        # reference to an instance function, the reference to 'self'
        # is tracked by python/pygtk, preventing 'del [i-o-LD]' from
        # removing the final reference to the instance, so that
        # __del__ (below) isn't called.

        import weakref
        sref = weakref.ref (self)

        def clear (obj):
            instance = sref ()
            
            if instance != None:
                instance.win = None
                
        # End of wacky code.
        
        def init ():
            self.win = OmegaDemoWindow (bag, style, sources)
            self.win.setPainter (painter)
            self.win.connect ('destroy', clear)
            self.win.show_all ()
            
        gtkThread.send (init)

    def __del__ (self):
        if self.win == None: return
        if gtkThread == None: return # this can get GC'd before us!

        # The user may destroy the window via the WM
        # and then delete this object before the clear()
        # function has had a chance to run ...

        def doit ():
            if self.win != None:
                self.win.destroy ()
                self.win = None
            
        gtkThread.send (doit)

    # More OmegaArea interface emulation, with the added wrinkle
    # of doing everything cross-thread. Don't even bother providing
    # write access to the attributes.

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
    
    def setPainter (self, p):
        def doit ():
            if self.win: self.win.setPainter (p)
        gtkThread.send (doit)

    def forceReconfigure (self):
        def doit ():
            if self.win: self.win.forceReconfigure ()
        gtkThread.send (doit)
