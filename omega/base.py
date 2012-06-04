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

# Basic classes of OmegaPlot.

import numpy as np

class DataHolder (object):
    """Stores a set of data inputs.

    A DataHolder stores data that will (most likely) be used to render
    a single plot element. The data are two-dimensional: there are
    columns with a specific meaning (e.g., X, Y, line width) and some
    number of rows, each of which represents one item to plot in some
    way or another.

    There are two types of columns: integer and floating-point.  (The
    latter should really be storable as doubles if desired, but that's
    a FIXME right now). Certain data are truly discrete and hence
    should really be stored as integers, while most numerical data
    will be stored as floats. Internally, DataHolder stores the data
    grouped in one 2D array of integers and one 2D array of
    floats. When data, the appropriate columns are selected and
    returned in the manner described below.

    The exact number of columns needed may vary depending on options
    that can be set. For instance, an XYDataPainter may only need two
    columns, for X and Y points, but it could need as many as seven
    columns, if each point is being plotted with X and Y error bars
    and the stamp size is variable.

    DataHolder has a concept of \"consumers\" to manage this
    flexibility. Upon creation, one or more consumers are registered
    with the DataHolder; each lists a set of columns that it expects
    the DataHolder to store for it.  In the above example, the
    XYDataPainter itself registers that it wants two columns, X and Y
    data, while its pointStamp registers that it wants five columns: X
    and Y error bars and a size parameter. If the latter is
    registered, the DataHolder is 7 coulumns wide; if not, it is only
    two wide.

    Further complicating matters is the fact that sometimes you don't
    know whether the data that you're dealing with is of integer or
    float type.  For instance, a 2D plot may have discrete axes, so a
    stamp with X error bars can't assume that those values are of
    float type. To accomodate this uncertainty, DataHolders have
    logical \"axes\" that are associated with a type. Instead of
    directly requesting columns of integer or float type, consumers
    request columns of the type associated with a given axis.

    Upon creation, a DataHolder has a fixed number of axes of fixed
    types. One or more consumers are then registered with the
    DataHolder, setting the number of columns allocated to each axis
    (its \"width\") and hence the total number of allocated
    columns. At some later point, the data are actually filled in with
    calles to setInts() and/or setFloats(). Finally, the consumers can
    retrieve the data associated with them with a call to get().

    Every DataHolder has two default axes: the first is \"MiscInt\",
    for storing miscellaneous data that is sure to be
    integer-typed. The second is \"MiscFloat\", the analogue for
    float-typed data. As a more complicated example, DataHolders for
    rectangular plots have four axes: MiscInt, MiscFloat, X, and Y.
    The types of the X and Y axes depend on the kind of plot.

    This model is convoluted, but it's important to distinguish
    between int and float data, and if that's going to happen, there
    needs to be some abstraction for things like X and Y data so that
    they can be stored via both means. And it's important to be able
    to use the same API for plotting simple XY data as well as more
    complicated 7D data as exemplified above. In practice, using a
    DataHolder shouldn't be too confusing, because there are no more
    than two function calls necessary to populate the data, and they
    slice the data the way it absolutely must be sliced: into an
    ndarray of ints and one of floats.
    """

    AxisTypeInt = 0
    AxisTypeFloat = 1

    AxisMiscInt = 0
    AxisMiscFloat = 1

    axistypes = (AxisTypeInt, AxisTypeFloat) # tuple of AxisType* values

    allocations = None
    intdata = None
    fltdata = None
    dlen = 0


    def register (self, *widths):
        """Register a consumer with this DataHolder.

        Arguments:

        *widths - A list of n integers, where n is the number of axes
          this DataHolder has. Each integer is the number of columns
          this particular consumer requests in the given axis.

        Returns: an opaque \"consumer info\" handle to be passed to get().

        Registers a consumer with the DataHolder, allocating column space
        that the user must fill up when populating this object's data.
        Consumers must be registered in a predictable order to give
        predictable user behavior.

        register() must not be called once the DataHolder's data contents
        have been set.
        """

        if self.intdata is not None or self.fltdata is not None:
            raise Exception ("Can't register new consumer now.")

        if self.allocations is None:
            self.allocations = [0] * len (self.axistypes)

        if len (widths) != len (self.axistypes):
            raise Exception ("Consumer expects different number of axes")

        offsets = ()

        for i in xrange (0, len (widths)):
            offsets += (self.allocations[i], )
            self.allocations[i] += widths[i]

        return (offsets, widths)


    def _checkLengths (self):
        if self.intdata is None and self.fltdata is None:
            raise Exception ('No data yet!')

        if self.intdata is not None and \
           self.intdata.shape[1] != self.dlen:
            raise Exception ('Disagreeing int and float data lengths')

        if self.fltdata is not None and \
           self.fltdata.shape[1] != self.dlen:
            raise Exception ('Disagreeing int and float data lengths')


    def get (self, cinfo):
        """Retrieve the data requested by a particular consumer.

        Arguments:

        cinfo - The opaque \"consumer info\" handle returned by
          register ()

        Returns: a tuple of n ndarrays, where n is the number of axes
          in this DataHolder. Each ndarray is 2D, with its first axis
          having a size equal to that specified in the call to register(),
          and with the second having an unpredictable size based on the
          amount of data given by the user. All arrays will have a second
          dimension of the same size, though. The type of each ndarray
          is the type associated with its axis: N.int or N.float.
        """

        offsets, widths = cinfo
        intofs = fltofs = 0
        ret = ()

        self._checkLengths ()

        for i in xrange (0, len (widths)):
            type, ofs, w = self.axistypes[i], offsets[i], widths[i]

            if w == 0:
                ret += (np.ndarray ((0,self.dlen)), )
            elif type == self.AxisTypeInt:
                ret += (self.intdata[intofs+ofs:intofs+ofs+w,:], )
            elif type == self.AxisTypeFloat:
                ret += (self.fltdata[fltofs+ofs:fltofs+ofs+w,:], )

            if type == self.AxisTypeInt:
                intofs += self.allocations[i]
            elif type == self.AxisTypeFloat:
                fltofs += self.allocations[i]

        return ret


    def getAll (self):
        """Retrieve all data stored in this DataHolder.

        Arguments: None.

        Returns: a tuple of n ndarrays, where n is the number of axes
          in this DataHolder. Each ndarray is of the same kind described
          in the documentation to get(), but containing the data for all
          registered consumers.
        """

        intofs = fltofs = 0
        ret = ()

        self._checkLengths ()

        for i in xrange (0, len (self.allocations)):
            type, w = self.axistypes[i], self.allocations[i]

            if w == 0:
                ret += (np.ndarray ((0,self.dlen)), )
            elif type == self.AxisTypeInt:
                ret += (self.intdata[intofs:intofs+w,:], )
            elif type == self.AxisTypeFloat:
                ret += (self.fltdata[fltofs:fltofs+w,:], )

            if type == self.AxisTypeInt:
                intofs += w
            elif type == self.AxisTypeFloat:
                fltofs += w

        return ret


    def totalWidth (self):
        """Get the total number of columns in this DataHolder.

        Arguments: None.

        Returns: The total number of columns in this DataHolder.
        """

        return reduce (lambda x, y: x + y, self.allocations)


    def _allocMerged (self, type, dtype, len):
        totw = 0

        for atype, w in zip (self.axistypes, self.allocations):
            if atype == type: totw += w

        return np.ndarray ((totw, len), dtype=dtype)


    def _setGeneric (self, type, dtype, arrays):
        arrays = [np.asarray (x) for x in arrays]
        mergedofs = 0
        l = -1
        naxes = len (self.axistypes)

        for i in xrange (0, len (arrays)):
            a = arrays[i]

            if a.ndim == 1:
                a = a[np.newaxis,:]
            elif a.ndim != 2:
                raise Exception ('Expect 1- or 2-D arrays only')

            if type == self.AxisTypeInt and a.dtype.kind != 'i':
                raise Exception ('Need to pass ints to for int data')

            w = a.shape[0]
            dataofs = 0

            if l < 0:
                l = a.shape[1]
                merged = self._allocMerged (type, dtype, l)
                totw = merged.shape[0]
            elif a.shape[1] != l:
                raise Exception ('Expect same-length arrays')

            if mergedofs + w > totw:
                raise Exception ('More input data than expected')

            merged[mergedofs:mergedofs+w,:] = a
            mergedofs += w

        if mergedofs != totw:
            raise Exception ('Less input data than required')

        self.dlen = l
        return merged


    def setInts (self, *args):
        """Set the integer data of this DataHolder.

        Arguments:

        *args - An arbitrary number of ndarrays, handled as described
          below.

        Returns: self

        Sets the integer data of this DataHolder. Once the DataHolder has
        been created, the types of its axes have been fixed, and all of its
        consumers have been registered. Thus the total number of needed
        integer axes (and float axes) is known. This function populates the
        data associated with those axes.

        Each element of @args is a 1- or 2-dimensional ndarray. A 1D argument
        of size k is treated as a 2D array of shape (1, k). Each element
        is considered in sequence. If the first element has shape (w1, k), then
        the first w1 integer columns are set to the values stored in the
        first element. If the second element has shape (w2, k), the next w2
        integer columns are set to those values. And so on. Thus, the sum
        w1 + w2 + ... wX must be equal to the total number of integer columns
        in this DataHolder. However, the particular widths of the argument
        arrays need not agree with the widths of the axes or of the consumers
        in any particular way. Naturally, the value of k must be the same
        in all of the arguments.

        The datatypes of the argument ndarrays need not be exactly N.int, but
        they must be integer-type and compatible with N.int.
        """

        self.intdata = self._setGeneric (self.AxisTypeInt, np.int, args)
        return self


    def setFloats (self, *args):
        """Set the float data of this DataHolder.

        Arguments:

        *args - An arbitrary number of ndarrays, handled as described
          in the documentation to setInts ().

        Returns: self

        Sets the float data of this DataHolder. See the documentation
        for setInts() for a description of how this process works in general.
        This function is exactly analogous, with floating-point rather than
        integer data.

        Integer arrays passed to this function will be upcast to
        floating-point arrays.
        """

        self.fltdata = self._setGeneric (self.AxisTypeFloat, np.float, args)
        return self


    def exportIface (self, other):
        """Export the data-setting interface of this object to another.

        Arguments:

        other - An object that will have new data-management methods
          added to it.

        Returns: self

        Sets new attributes on @other pointing to the data-management
        methods of this object. For the base DataHolder, those methods
        are setInts() and setFloats().

        This routine is meant to allow an object that has a DataHolder
        member to act as if it were a DataHolder itself for the purposes
        of callers. Painter objects that take data will have a DataHolder
        member, but it would be inconvenient to have to write
        \"painter.data.setInts ()\" all the time. This function helps
        that problem a bit.
        """

        other.setInts = self.setInts
        other.setFloats = self.setFloats
        return self


# Painting and useful utilities for painting

class ToplevelPaintParent (object):
    _painter = None
    _painterRef = None

    from weakref import ref as _ref

    def __init__ (self, weakRef):
        self._weakRef = bool (weakRef)


    def getPainter (self):
        if not self._weakRef:
            return self._painter

        if self._painterRef is None: return None

        p = self._painterRef ()

        if p is None:
            self._painterRef = None
            return None

        return p


    def setPainter (self, painter):
        pCur = self.getPainter ()

        if pCur is not None:
            pCur.setParent (None)

        if painter is not None:
            painter.setParent (self)

        if not self._weakRef:
            self._painter = painter
        elif painter is not None:
            self._painterRef = self._ref (painter)
        else:
            self._painterRef = None


    def _lostChild (self, child):
        if not self._weakRef:
            self._painter = None
        else:
            self._painterRef = None


class ContextTooSmallError (StandardError):
    pass


class Painter (object):
    mainStyle = None
    parentRef = None
    _toplevel_render_aspect = None

    from weakref import ref as _ref


    def __init__ (self):
        self.matrix = None


    def _getParent (self):
        if self.parentRef is None: return None

        p = self.parentRef ()

        if p is None:
            self.parentRef = None
            return None

        return p


    def setParent (self, parent):
        p = self._getParent ()

        if p is not None:
                p._lostChild (self)

        if parent is None:
            self.parentRef = None
        else:
            self.parentRef = self._ref (parent)

        self.matrix = None


    def getMinimumSize (self, ctxt, style):
        #"""Should be a function of the style only."""
        # I feel like the above should be true, but we at least
        # need ctxt for measuring text, unless another way is found.
        # Return min_interior_width, min_interior_height, min_top_border,
        # min_right_border, min_bot_border, min_left_border
        return 0, 0, 0, 0, 0, 0


    def configurePainting (self, ctxt, style, w, h, btop, brt, bbot, bleft):
        p = self._getParent ()

        if p is None:
            raise Exception ('Cannot configure parentless painter')

        self.matrix = ctxt.get_matrix ()
        self.width = w
        self.height = h
        self.border = (btop, brt, bbot, bleft)
        self.fullw = w + brt + bleft
        self.fullh = h + btop + bbot


    def paint (self, ctxt, style):
        if self.matrix is None:
            raise RuntimeError ('Attempting to paint without having called configurePainting')

        ctxt.save ()
        ctxt.set_matrix (self.matrix)
        style.apply (ctxt, self.mainStyle)
        self.doPaint (ctxt, style)
        ctxt.restore ()


    def doPaint (self, ctxt, style):
        raise NotImplementedError ()


    def renderBasic (self, ctxt, style, w, h):
        # Must init the context before calling getMinimumSize
        # in case we're using the Cairo text backend -- we need
        # the font size to be set correctly. Hacky; should go away
        # with better support for multiple text backends.

        style.initContext (ctxt, w, h)

        szinfo = self.getMinimumSize (ctxt, style)
        mainw = max (w - szinfo[3] - szinfo[5], 0) # fill as much as possible
        mainh = max (h - szinfo[2] - szinfo[4], 0) # by default

        if self._toplevel_render_aspect is not None:
            # possibly shrink if trying to fix the main region aspect ratio
            if mainh <= 0:
                mainh = mainw / self._toplevel_render_aspect
            else:
                aspect = mainw / mainh

                if aspect > self._toplevel_render_aspect:
                    # Too wide
                    mainw = mainh * self._toplevel_render_aspect
                else:
                    mainh = mainw / self._toplevel_render_aspect

        needw = mainw + szinfo[3] + szinfo[5]
        needh = mainh + szinfo[2] + szinfo[4]

        if w < needw or h < needh:
            raise ContextTooSmallError ('Context too small: got (%s, %s);'
                                        ' need (%s, %s)' % \
                                            (w, h, needw, needh))

        # spend extra space on margins, trying to center the main plot
        # area as much as possible. We've checked that there's enough
        # space overall, so our tweaks should never cause any problems.

        marginw = 0.5 * (w - mainw)
        marginh = 0.5 * (h - mainh)
        margins = [marginh, marginw, marginh, marginw]
        minfo = szinfo[2:]

        for i in xrange (4):
            if margins[i] < minfo[i]:
                delta = minfo[i] - margins[i]
                margins[i] += delta
                margins[(i + 2) % 4] -= delta

        self.configurePainting (ctxt, style, mainw, mainh, *margins)
        self.paint (ctxt, style)


    def render (self, func):
        p = self._getParent ()

        if p is not None:
            raise Exception ("Can't render in-use Painter")

        # We have to hold a ref to tpp in this function because setParent
        # only references it weakly! That shit is bananas.

        tpp = ToplevelPaintParent (False)
        self.setParent (tpp)
        func (self.renderBasic)
        self.setParent (None)


    def sendTo (self, pager):
        pager.send (self)
        return self


    def show (self, ident=None, **kwargs):
        from render import showPainter
        showPainter (self, ident, **kwargs)
        return self


    def save (self, filename, **kwargs):
        from render import savePainter
        savePainter (self, filename, **kwargs)
        return self


    def dump (self, **kwargs):
        from util import dumpPainter
        dumpPainter (self, **kwargs)
        return self


class NullPainter (Painter):
    def doPaint (self, ctxt, style):
        pass


class DebugPainter (Painter):
    lineStyle = 'strongLine'

    minWidth = 0
    minHeight = 0
    bTop = 0
    bRight = 0
    bBottom = 0
    bLeft = 0


    def getMinimumSize (self, ctxt, style):
        s = style.smallScale
        return (self.minWidth * s, self.minHeight * s, self.bTop * s, self.bRight * s,
                self.bBottom * s, self.bLeft * s)


    def doPaint (self, ctxt, style):
        style.apply (ctxt, self.lineStyle)

        ctxt.move_to (0, 0)
        ctxt.line_to (self.fullw, self.fullh)
        ctxt.stroke ()
        ctxt.move_to (0, self.fullh)
        ctxt.line_to (self.fullw, 0)
        ctxt.stroke ()

        ctxt.rectangle (self.border[3], self.border[0], self.width, self.height)
        ctxt.stroke ()


# Stamps -- things that draw some shape but are
# not full-fledged space-allocating painters.
# Stamps do not have access to a style; they use
# whatever values the current context has.

class Stamp (object):
    def paintAt (self, ctxt, x, y):
        raise NotImplementedError ()

    def paintHere (self, ctxt):
        x, y = ctxt.get_current_point ()
        self.paintAt (ctxt, x, y)


# Text handling routines. Possible backends are Cairo text
# support (fast) or LaTeX (inefficient but capable of rendering
# arbitrarily complex formulae). I am not fond of globals, but you
# reeeally don't want text in different parts of your graph to be
# rendered via different mechanisms (for aesthetic reasons), so here
# we are.

class _TextPainterBase (Painter):
    color = 'foreground'


class _TextStamperBase (object):
    def getSize (self, ctxt, style):
        raise NotImplementedError ()

    def paintAt (self, ctxt, x, y, color):
        raise NotImplementedError ()

    def paintHere (self, ctxt, color):
        x, y = ctxt.get_current_point ()
        self.paintAt (ctxt, x, y, color)


# Our simple default backend

import cairo

class CairoTextPainter (_TextPainterBase):
    hAlign = 0.5
    vAlign = 0.5

    def __init__ (self, text, hAlign=None, vAlign=None):
        _TextPainterBase.__init__ (self)
        self.text = text
        self.extents = None

        if hAlign is not None: self.hAlign = hAlign
        if vAlign is not None: self.vAlign = vAlign


    def getMinimumSize (self, ctxt, style):
        if not self.extents:
            self.extents = ctxt.text_extents (self.text)

        return self.extents[2], self.extents[3], 0, 0, 0, 0


    def doPaint (self, ctxt, style):
        dx = self.border[3] + (self.width - self.extents[2]) * self.hAlign
        dy = self.border[0] + (self.height - self.extents[3]) * self.vAlign

        ctxt.move_to (dx - self.extents[0], dy - self.extents[1])
        ctxt.set_source_rgb (*style.getColor (self.color))
        ctxt.show_text (self.text)


class CairoTextStamper (_TextStamperBase):
    def __init__ (self, text):
        self.text = text
        self.extents = None


    def getSize (self, ctxt, style):
        if not self.extents:
            self.extents = ctxt.text_extents (self.text)

        return self.extents[2:4]


    def paintAt (self, ctxt, x, y, color):
        ctxt.save ()
        ctxt.move_to (x, y)
        ctxt.rel_move_to (-self.extents[0], -self.extents[1])
        ctxt.set_source_rgb (*color)
        ctxt.show_text (self.text)
        ctxt.restore ()


_textPainterClass = CairoTextPainter
_textStamperClass = CairoTextStamper
_textMarkupFunc = lambda t: t


def TextPainter (text, **kwargs):
    return _textPainterClass (text, **kwargs)


def TextStamper (text, **kwargs):
    return _textStamperClass (text, **kwargs)


def textMarkup (text, **kwargs):
    # This is a little silly-seeming, but it lets code import the
    # textMarkup name and still see changes to the text markup
    # function if a new text backend is subsequently imported.
    return _textMarkupFunc (text, **kwargs)


def _setTextBackend (painterClass, stamperClass, markupFunc):
    global _textPainterClass, _textStamperClass, _textMarkupFunc

    if not issubclass (painterClass, _TextPainterBase):
        raise ValueError ('Text backend class %s is not a TextPainterBase subclass' %
                          painterClass)
    if not issubclass (stamperClass, _TextStamperBase):
        raise ValueError ('Text backend class %s is not a TextStamperBase subclass' %
                          stamperClass)
    if not callable (markupFunc):
        raise ValueError ('text markup function %r is not callable' % markupFunc)

    _textPainterClass = painterClass
    _textStamperClass = stamperClass
    _textMarkupFunc = markupFunc


# Generic painting of ImageSurfaces

class _ImagePainterBase (Painter):
    def getSurf (self, style):
        raise NotImplementedError ()


    def getMinimumSize (self, ctxt, style):
        surf = self.getSurf (style)

        if not isinstance (surf, cairo.ImageSurface):
            raise Exception ('Need to specify an ImageSurface for ImagePainter, got %s' % surf)

        return surf.get_width (), surf.get_height (), 0, 0, 0, 0


    def doPaint (self, ctxt, style):
        surf = self.getSurf (style)

        ctxt.set_source_surface (surf)
        # Whatever the default is, it seems to do the right thing.
        #ctxt.set_operator (cairo.OPERATOR_ATOP)
        ctxt.translate (self.border[3], self.border[0])
        ctxt.paint ()

class ImagePainter (_ImagePainterBase):
    def __init__ (self, surf):
        _ImagePainterBase.__init__ (self)
        self.surf = surf


    def getSurf (self, style):
        return self.surf


# Expandable keyword arg handling

def _kwordDefaulted (kwargs, name, coerce, default):
    # This routine is useful if we want our routine to
    # accept keyword arguments, but we also want to take
    # *args arguments, which preclude standard keyword
    # arguments.

    if name not in kwargs:
        return default

    if coerce is not None:
        val = coerce (kwargs[name])
    else:
        val = kwargs[name]

    del kwargs[name]
    return val


def _kwordExtract (kwargs, *names):
    # This routine is useful if we want to pass parts
    # of **kwargs on to different subroutines. It will
    # extract the named keywords into a separate dictionary
    # that can be used as a **kwargs in a function call
    # and remove them from our **kwargs.

    retval = {}

    for n in names:
        if n in kwargs:
            retval[n] = kwargs[n]
            del kwargs[n]

    return retval


def _checkKwordsConsumed (kwargs):
    if len (kwargs) == 0:
        return

    args = ', '.join ('%s=%s' % tup for tup in kwargs.iteritems ())
    raise TypeError ('Unconsumed keyword arguments: ' + args)
