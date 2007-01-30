import math as _math

class Function (object):
    def __init__ (self, func=None):
        self.xmin = 0. # XXX bagprop, should support multi-dim
        self.xmax = 10.
        self.npts = 300
        self.func = func or self.demofunc

    def demofunc (self, x):
        return _math.sin(x) + 1.

    # FIXME all unnecessary, chunk should be lists because
    # it must be possible to iterate over them twice.
    
    class pointiter:
        def __init__ (self, owner):
            self.val = owner.xmin
            self.bound = owner.xmax
            self.func = owner.func
            self.inc = float (owner.xmax - owner.xmin) / owner.npts

        def __iter__ (self): return self

        def next (self):
            if self.val > self.bound: raise StopIteration ()

            try:
                r = (self.val, self.func (self.val))
            except:
                r = (self.val, 0.0) # XXX FIXME ugggh
            
            self.val += self.inc
            return r
        
    class chunkiter:
        def __init__ (self, owner):
            self.owner = owner

        def __iter__ (self): return self

        def next (self):
            if not self.owner: raise StopIteration ()
            r = Function.pointiter (self.owner)
            self.owner = None
            return r
    
    def __iter__ (self): return Function.chunkiter (self)

class ParametricFunction (object):
    def __init__ (self, func=None):
        self.tmin = 0. # XXX bagprop, should support multi-dim
        self.tmax = 10.
        self.npts = 300
        self.func = func or self.demofunc

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

