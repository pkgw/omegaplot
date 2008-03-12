"""gtkThread provides simple functions for running a GTK+
main loop in an alternative thread. This allows Python code
to create GTK+ windows and interact with them without blocking
the main Python interpreter.

gtkThread exports one function, send(fn), which runs its argument
in a timeout inside a GLib main loop in the GTK+ thread. The GTK+
thread is started upon the first call to send(); at that time, a
new thread is launched that enters a gtk.main() mainloop.

gtkThread also exports a variable, interval, which specifies how
frequently in milliseconds the GTK+ thread will check for tasks
sent to it using send(). Changes to this variable will only take
effect before the first call to send().

Code using this module must be carefully designed so that Python
objects referenced in the GTK+ thread are locked and managed
correctly. In particular, all GTK+ functions should be called only
from the GTK+ thread, and it should be remembered that signal
handlers, timeouts, and idle functions will be called from the GTK+
thread. If you write code referencing GTK+ objects or functions that
is meant to be called from the main interpreter thread, you should
do the real work in functions that are sent to the GTK+ thread.
In these situations, however, you must be vigilant against race
conditions.

The GTK+ thread is terminated when the interpreter quits via an
atexit handler. This is done by causing the thread to call
gtk.main_quit(), then joining on the thread; if the GTK+ thread is
in a state where registering a gtk.main_quit timeout will not cause
the main loop to exit, the interpreter will hang upon exit."""

from threading import Thread
from Queue import Queue, Empty
import sys, atexit

import gobject, gtk

__all__ = [ 'send', 'interval' ]

interval = 100

# Referenced from both threads
_queue = Queue ()

# Referenced from the main thread
_thread = None

class _gtkThread (Thread):
    """A utility class for running gtk functions in an alternate
    thread. Has a message queue for controlling the thread from the
    main python thread."""
    
    def run (self):
        gtk.gdk.threads_init ()
        # making this an idle causes it to chew up CPU on the locks
        id = gobject.timeout_add (interval, self._checkqueue)
        gtk.main ()
        gobject.source_remove (id)
        #print 'Quitting Gtk thread.'

    def _checkqueue (self):
        try:
            func = _queue.get_nowait ()
            func ()
        except Empty: pass
        except Exception, e:
            print >>sys.stderr, 'Exception in queue callback:', e
        return True
    
def send (func):
    """Run the argument, a function, in the gtk thread,
    inside a GLib main loop timeout callback. See the module
    documentation for more information."""
    
    global _thread, _queue

    _queue.put (func)

    if _thread == None or not _thread.isAlive ():
        _thread = _gtkThread ()
        _thread.start ()

def _atexit ():
    global _thread, _queue

    if _thread is not None:
        send (gtk.main_quit)
        _thread.join ()
        _thread = None
        _queue = None

atexit.register (_atexit)
