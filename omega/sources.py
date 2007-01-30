import math as _math

class Function (object):
    def __init__ (self, func=None, funcSpec='F'):
        self.xmin = 0. # XXX bagprop, should support multi-dim
        self.xmax = 10.
        self.npts = 300
        self.func = func or self.demofunc
        self.sourceSpec = 'F' + funcSpec

    def demofunc (self, x):
        return _math.sin(x) + 1.

    # FIXME If we were awesome, we could track the derivative
    # of the function, and increase the density of points as
    # the variation gets larger.

    def genPoints (self):
        iter = LinearIterator (self.xmin, self.xmax, self.npts)
        return ((x, self.func (x)) for x in iter)
    
    def __iter__ (self):
        yield self.genPoints ()

class ParametricFunction (object):
    def __init__ (self, func=None, sourceSpec='FF'):
        self.tmin = 0. # XXX bagprop, should support multi-dim
        self.tmax = 10.
        self.npts = 300
        self.func = func or self.demofunc
        self.sourceSpec = sourceSpec

    def demofunc (self, t):
        return (_math.sin(2*t), _math.cos (5*t))

    # FIXME See note in Function.

    def genPoints (self):
        iter = LinearIterator (self.tmin, self.tmax, self.npts)
        return (self.func (t) for t in iter)
    
    def __iter__ (self):
        yield self.genPoints ()

class StoredData (object):
    def __init__ (self, sourceSpec, data):
        self.sourceSpec = sourceSpec
        self.data = data

    def __iter__ (self):
        yield list (self.data)

# Dum de dum.

def LinearIterator (min, max, npts):
    inc = float (max - min) / npts
    val = min

    while val <= max:
        yield val
        val += inc
