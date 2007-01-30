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

    # FIXME all unnecessary, chunk should be lists because
    # it must be possible to iterate over them twice.

    def genPoints (self):
        iter = LinearIterator (self.xmin, self.xmax, self.npts)
        return [(x, self.func (x)) for x in iter]
    
    class chunkiter:
        def __init__ (self, owner):
            self.owner = owner

        def __iter__ (self): return self

        def next (self):
            if not self.owner: raise StopIteration ()
            r = self.owner.genPoints ()
            self.owner = None
            return r
    
    def __iter__ (self): return Function.chunkiter (self)

class ParametricFunction (object):
    def __init__ (self, func=None, sourceSpec='FF'):
        self.tmin = 0. # XXX bagprop, should support multi-dim
        self.tmax = 10.
        self.npts = 300
        self.func = func or self.demofunc
        self.sourceSpec = sourceSpec

    def demofunc (self, t):
        return (_math.sin(2*t), _math.cos (5*t))

    # FIXME all unnecessary, chunk should be lists because
    # it must be possible to iterate over them twice.

    def genPoints (self):
        iter = LinearIterator (self.tmin, self.tmax, self.npts)
        return [self.func (t) for t in iter]
    
    class chunkiter:
        def __init__ (self, owner):
            self.owner = owner

        def __iter__ (self): return self

        def next (self):
            if not self.owner: raise StopIteration ()
            r = self.owner.genPoints ()
            self.owner = None
            return r
    
    def __iter__ (self): return ParametricFunction.chunkiter (self)

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

