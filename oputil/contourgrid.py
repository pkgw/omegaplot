"""Compute contours on gridded data.

Derived from the algorithm in PGPLOT 5.2, available at:

http://www.astro.caltech.edu/~tjp/pgplot/

The relevant files are src/pgcnsc.f and src/pgcn01.f.

FIXME: more docs.
"""

import numpy as N

# ArrayGrower class copy&pasted from miriad-python.

class _ArrayGrower (object):
    __slots__ = ['dtype', 'ncols', 'chunkSize', '_nextIdx', '_arr']

    def __init__ (self, ncols, dtype=N.float, chunkSize=128):
        self.dtype = dtype
        self.ncols = ncols
        self.chunkSize = chunkSize
        self.clear ()


    def clear (self):
        self._nextIdx = 0
        self._arr = None


    def addLine (self, line):
        line = N.asarray (line, dtype=self.dtype)
        assert (line.size == self.ncols)

        if self._arr is None:
            self._arr = N.ndarray ((self.chunkSize, self.ncols), dtype=self.dtype)
        elif self._arr.shape[0] <= self._nextIdx:
            self._arr.resize ((self._arr.shape[0] + self.chunkSize, self.ncols))

        self._arr[self._nextIdx] = line
        self._nextIdx += 1


    def add (self, *args):
        self.addLine (args)


    def __len__ (self): return self._nextIdx


    def finish (self, trans=False):
        if self._arr is None:
            ret = N.ndarray ((0, self.ncols), dtype=self.dtype)
        else:
            self._arr.resize ((self._nextIdx, self.ncols))
            ret = self._arr

        self.clear ()

        if trans: ret = ret.T

        return ret


def contourValue (data, rowcoords, colcoords, value):
    """Compute contours of 2D array 'data', which describes data
    points living on a regular grid. 'rowcoords' and 'colcoords' are
    1D arrays giving the coordinate values of the first and second
    indices of 'data', respectively. 'value' is the value to contour
    for.

    Returns a list of 2D arrays. The first dimension of each array is
    of size 2. The second dimension is of variable size, depending on
    how many points are needed to trace out the contour. array[0,:]
    gives the *column* coordinates of the row points while array[1,:]
    gives the *row* coordinates. This maps on to the usual sense of
    [row,col] mapping to [y,x].

    Contours are traced out clockwise around maxima that they contain,
    or analogously counterclockwise around contained minima.

    This may or may not be the "marching squares" algorithm.
    """

    # We visualize data as a rectangular box. The coordinates of data
    # are [row,col].  The top-left corner is data[0,0]. data[0,ncol-1]
    # is the top-right corner and data[nrow-1,0] is the bottom left
    # corner. This leads to the familiar and annoying fact that
    # data[row,col] is essentially data[y,x].

    UP, RT, DN, LF = 0, 1, 2, 3

    # Check args

    data = N.asarray (data)
    rowcoords = N.asarray (rowcoords)
    colcoords = N.asarray (colcoords)
    value = float (value)

    if data.ndim != 2: raise ValueError ('Data must be 2D')
    if data.shape[0] < 2: raise ValueError ('Data must have >1 row')
    if data.shape[1] < 2: raise ValueError ('Data must have >1 col')
    if rowcoords.ndim != 1: raise ValueError ('rowcoords must be 1D')
    if rowcoords.size != data.shape[0]:
        raise ValueError ('rowcoords.size must = data.shape[0]')
    if colcoords.ndim != 1: raise ValueError ('colcoords must be 1D')
    if colcoords.size != data.shape[1]:
        raise ValueError ('colcoords.size must = data.shape[1]')

    NR = data.shape[0]
    NC = data.shape[1]

    # Utility: Mapping row & column numbers to x/y values with
    # interpolation to the contour value.

    def rinterp_dn_to_y (r, c):
        dv = value - data[r,c]
        return rowcoords[r] + (rowcoords[r+1] - rowcoords[r]) / (data[r+1,c] - data[r,c]) * dv

    def cinterp_rt_to_x (r, c):
        dv = value - data[r,c]
        return colcoords[c] + (colcoords[c+1] - colcoords[c]) / (data[r,c+1] - data[r,c]) * dv

    # Utility: the workhorse function that actually follows a contour
    # and generates a list of points.

    contours = []
    pg = _ArrayGrower (2)

    def follow (rstart, cstart, dirstart):
        i = rstart
        j = cstart
        d = dirstart

        if dirstart == LF or dirstart == RT:
            x0 = colcoords[j]
            y0 = rinterp_dn_to_y (i, j)
        else:
            x0 = cinterp_rt_to_x (i, j)
            y0 = rowcoords[i]

        pg.add (x0, y0)

        hitEdge = False

        while True:
            if d == DN:
                vflags[i,j] = False

                if i == NR - 1:
                    hitEdge = True
                    break
                elif hflags[i,j]:
                    #print 'DN -> LF'
                    d = LF
                elif hflags[i,j+1]:
                    #print 'DN -> RT'
                    j += 1
                    d = RT
                elif vflags[i+1,j]:
                    #print 'DN -> DN'
                    i += 1
                    d = DN
                else:
                    #print 'DN -> EOC'
                    break
            elif d == UP:
                vflags[i,j] = False

                if i == 0:
                    hitEdge = True
                    break
                elif hflags[i-1,j+1]:
                    #print 'UP -> RT'
                    d = RT
                    i -= 1
                    j += 1
                elif hflags[i-1,j]:
                    #print 'UP -> LF'
                    i -= 1
                    d = LF
                elif vflags[i-1,j]:
                    #print 'UP -> UP'
                    i -= 1
                    d = UP
                else:
                    #print 'UP -> EOC'
                    break
            elif d == LF:
                hflags[i,j] = False

                if j == 0:
                    hitEdge = True
                    break
                elif vflags[i,j-1]:
                    #print 'LF -> UP'
                    d = UP
                    j -= 1
                elif vflags[i+1,j-1]:
                    #print 'LF -> DN'
                    d = DN
                    i += 1
                    j -= 1
                elif hflags[i,j-1]:
                    #print 'LF -> LF'
                    d = LF
                    j -= 1
                else:
                    #print 'LF -> EOC'
                    break
            elif d == RT:
                hflags[i,j] = False

                if j == NC - 1:
                    hitEdge = True
                    break
                elif vflags[i+1,j]:
                    #print 'RT -> DN'
                    d = DN
                    i += 1
                elif vflags[i,j]:
                    #print 'RT -> UP'
                    d = UP
                elif hflags[i,j+1]:
                    #print 'RT -> RT'
                    d = RT
                    j += 1
                else:
                    #print 'RT -> EOC'
                    break

            # Actually record the point for this

            if d == RT or d == LF:
                x = colcoords[j]
                y = rinterp_dn_to_y (i, j)
            else:
                x = cinterp_rt_to_x (i, j)
                y = rowcoords[i]

            pg.add (x, y)

        # Done tracing this contour

        if not hitEdge:
            pg.add (x0, y0)

        contours.append (pg.finish ().T)

    # Init tables.

    hflags = N.empty ((NR-1, NC), dtype=N.bool)
    vflags = N.empty ((NR, NC-1), dtype=N.bool)

    transition = lambda z1, z2: (value > min (z1, z2) and
                                 value <= max (z1, z2) and
                                 z1 != z2)

    for i in xrange (NR):
        for j in xrange (NC):
            z0 = data[i,j]

            if i < NR-1:
                # A transition from this cell to the one below?
                hflags[i,j] = transition (z0, data[i+1,j])

            if j < NC-1:
                # A transition from this cell to the one at right?
                vflags[i,j] = transition (z0, data[i,j+1])

    # Search for contour starts on edges. As noted in pgplot, make
    # sure that the higher value is on the left, as seen on the edge
    # looking away from the matrix. Alternatively, we proceed
    # clockwise along the contour as seen from its interior of if it
    # contains a maximum, or counterclocks along it as seen from its
    # interior if it contains a minimum.

    for j in xrange (NC-1):
        # Top
        if vflags[0,j] and data[0,j] > data[0,j+1]:
            #print 'follow from top:', 0, j
            follow (0, j, DN)

    for i in xrange (NR-1):
        # Right
        if hflags[i,NC-1] and data[i,NC-1] > data[i+1,NC-1]:
            #print 'follow from right:', i, NC-1
            follow (i, NC-1, LF)

    for j in xrange (NC-1):
        # Bottom
        if vflags[NR-1,j] and data[NR-1,j] < data[NR-1,j+1]:
            #print 'follow from bot:', NR-1, j
            follow (NR-1, j, UP)

    for i in xrange (NR-1):
        # Left
        if hflags[i,0] and data[i,0] < data[i+1,0]:
            #print 'follow from left:', i, 0
            follow (i, 0, RT)

    # Now search for interior contours.

    for i in xrange (NR-1):
        for j in xrange (NC):
            if hflags[i,j]:
                #print 'follow interior:', i, j, '=>', colcoords[j], rinterp_dn_to_y (i, j)
                if data[i,j] > data[i+1,j]:
                    # Higher value is farther up,
                    # so this obeys the clockwise rule.
                    follow (i, j, LF)
                else:
                    follow (i, j, RT)

    # All done.
    return contours


def contourValues (data, rowcoords, colcoords, values):
    """Compute contours of the 2D array 'data' at multiple
    values. See documentation for the function 'contourValue' for
    documentation of arguments. 'values' is an iterable of values
    that are contoured.

    Returns a dictionary mapping from each distinct value in 'values'
    into a list of 2D arrays as returned by 'contourValue'. If a value
    is listed repeatedly in 'values', it is contoured only once.
    """

    retval = {}

    for v in values:
        if v in retval: continue

        retval[v] = contourValue (data, rowcoords, colcoords, v)

    return retval


__all__ = ['contourValue', 'contourValues']


# Functions for generating helpful 'values' arrays.

_defaultN = 10

def valsLinRange (lower, upper, pad=False, n=_defaultN):
    n = int (n)

    if pad:
        d = float (upper - lower) / (n + 1)
    else:
        d = 0

    return N.linspace (lower + d, upper - d, n)


def valsLogRange (lower, upper, pad=False, n=_defaultN):
    return N.exp (valsLinRange (N.log (lower), N.log (upper), pad, n))


def rangeBounds (data):
    data = N.asarray (data)
    return data.min (), data.max ()


def valsLinBounds (data, n=_defaultN):
    mn, mx = rangeBounds (data)
    return valsLinRange (mn, mx, True, n)


def valsLogBounds (data, n=_defaultN):
    mn, mx = rangeBounds (data)
    return valsLogRange (mn, mx, True, n)


def rangeRMSMax (data, frms, fmax):
    data = N.asarray (data)
    return frms * N.sqrt ((data**2).mean ()), fmax * data.max ()


def valsLinRMSMax (data, frms, fmax, n=_defaultN):
    mn, mx = rangeRMSMax (data, frms, fmax)
    return valsLinRange (mn, mx, False, n)


def valsLogRMSMax (data, frms, fmax, n=_defaultN):
    mn, mx = rangeRMSMax (data, frms, fmax)
    return valsLogRange (mn, mx, False, n)


def contourAuto (data, rowcoords, colcoords, range='b', space='lin',
                 n=_defaultN, values=None, frms=3, fmax=0.75):
    """Compute contours of the 2D array 'data', which describes data
    points living on a regular grid. 'rowcoords' and 'colcoords' are
    1D arrays giving the coordinate values of the first and second
    indices of 'data', respectively. The values to contour can be
    determined automatically or specified by the user.

    'range': 'b' for dataset bounds, 'rm' for RMS/Max bounds, or
      a 2-element indexable for user-specified bounds

    'space': 'lin' for linear, 'log' for logarithmic

    'n': the number of values between the bounds

    'values': just use the values specified in this arraylike

    'frms': use frms * RMS(data) for the lower bound in RMS/Max

    'fmax': use fmax * max(data) for the upper bound in RMS/Max

    Returns a dict of lists of arrays, {value: [contour1,
    ...contourN]}

    Oh god this documentation is so poor.

    """
    if values is not None:
        values = N.asarray (values)
    else:
        if range == 'b':
            r = rangeBounds (data)
            pad = True
        elif range == 'rm':
            r = rangeRMSMax (data, frms, fmax)
            pad = False
        elif len (range) == 2:
            r = range
            pad = False
        else:
            raise ValueError ('Unhandled range value %s' % range)

        if space == 'lin':
            values = valsLinRange (r[0], r[1], pad, n)
        elif space == 'log':
            values = valsLogRange (r[0], r[1], pad, n)

    return contourValues (data, rowcoords, colcoords, values)


__all__ += ['valsLinRange', 'valsLogRange', 'rangeBounds',
            'valsLinBounds', 'valsLogBounds', 'rangeRMSMax',
            'valsLinRMSMax', 'valsLogRMSMax', 'contourAuto']
