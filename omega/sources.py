import math as _math

class Function (object):
    sourceSpec = 'FF'
    
    def __init__ (self, func=None):
        self.xmin = 0. # XXX bagprop, should support multi-dim
        self.xmax = 10.
        self.npts = 300
        self.func = func or self.demofunc

    def demofunc (self, x):
        return _math.sin(x) + 1.

    # FIXME If we were awesome, we could track the derivative
    # of the function, and increase the density of points as
    # the variation gets larger.

    def genPoints (self):
        iter = LinearIterator (self.xmin, self.xmax, self.npts)
        return [(x, self.func (x)) for x in iter]
    
    def __iter__ (self): return OneFuncIterator (self.genPoints)

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
        return [self.func (t) for t in iter]
    
    def __iter__ (self): return OneFuncIterator (self.genPoints)

class StoredData (object):
    def __init__ (self, sourceSpec, data):
        self.sourceSpec = sourceSpec
        self.data = data

    def __iter__ (self): return OneItemIterator (list (self.data))

# These classes will be obviated once we can count
# on generators

class LinearIterator:
    def __init__ (self, min, max, npts):
        self.val = min
        self.max = max
        self.inc = float (max - min) / npts

    def __iter__ (self): return self

    def next (self):
        if self.val > self.max: raise StopIteration ()
        r = self.val
        self.val += self.inc
        return r

class OneItemIterator:
    def __init__ (self, item):
        self.item = item

    def __iter__ (self): return self

    def next (self):
        if not self.item: raise StopIteration ()
        r = self.item
        self.item = None
        return r

class OneFuncIterator:
    def __init__ (self, func):
        self.func = func

    def __iter__ (self): return self

    def next (self):
        if not self.func: raise StopIteration ()
        f = self.func
        self.func = None
        return f()

