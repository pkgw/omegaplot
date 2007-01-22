class Function (object):
    def __init__ (self, func=None):
        self.xmin = 0. # XXX bagprop, should support multi-dim
        self.xmax = 10.
        self.npts = 300
        self.func = func or self.demofunc

    import math
    
    def demofunc (self, x):
        return Function.math.sin(x) + 1.

    # FIXME all unnecessary, chunk should be lists because
    # it must be possible to iterate over them twice.
    
    class pointiter:
        def __init__ (self, owner):
            self.val = owner.xmin
            self.bound = owner.xmax
            self.func = owner.func
            self.inc = (owner.xmax - owner.xmin) / owner.npts

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
