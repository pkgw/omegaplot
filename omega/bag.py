class Bag (object):
    def __init__ (self):
        self.sinks = set ()
        self.exposed = {}
        self.exposedSpecs = {}
        self.linked = {}
        
    def registerSink (self, sink):
        self.sinks.add (sink)

    def exposeSink (self, sink, name):
        curSpec = self.exposedSpecs.get (name)

        if not curSpec:
            self.exposedSpecs[name] = sink.sinkSpec
        elif curSpec != sink.sinkSpec:
            raise Exception ('Trying to expose two sinks with different specs' \
                             'to the same name, %s' % (name))
        
        self.registerSink (sink)
        self.exposed[sink] = name
        return sink

    def linkTo (self, source, sink):
        if source.sourceSpec != sink.sinkSpec:
            raise Exception ('Trying to link disagreeing sink (%s) and source (%s)!' \
                             % (sink.sinkSpec, source.sourceSpec))
        
        self.registerSink (sink)
        self.registerSink (source)
        self.linked[sink] = source

        if not hasattr (source, 'filterChunk'):
            raise Exception ('Trying to link a source with no filterChunk member')
            
    def getChunk (self, sink):
        chunk = self.currentRound.get (sink)

        if chunk: return iter (chunk)

        source = self.linked.get (sink)

        if source:
            chunk = self.getChunk (source)
            filtered = source.filterChunk (chunk)
            self.currentRound[sink] = filtered
            return iter (filtered)
        
        raise Exception ('uh oh now what')

    def startFlushing (self, sources):
        self.currentIters = {}
        
        for (sink, name) in self.exposed.iteritems ():
            if name not in sources: raise Exception ('No such source %s!' % (name))

            src = sources[name]

            if src.sourceSpec != sink.sinkSpec:
                raise Exception ('Trying to feed sink with disagreeing source!')
                
            self.currentIters[sink] = src.__iter__ ()

        for sink in self.sinks:
            if sink in self.exposed: continue
            if sink in self.linked: continue

            raise Exception ('Sink %s is neither exposed nor linked, cannot flush' % sink)
    
    def startNewRound (self):
        self.currentRound = {}
        gotany = False
        
        for (sink, iter) in self.currentIters.iteritems ():
            try:
                chunk = iter.next ()
                self.currentRound[sink] = list (chunk)
                gotany = True
            except StopIteration:
                self.currentRound[sink] = None

        return gotany

class FunctionFilter (object):
    def __init__ (self, func, sinkSpec, sourceSpec):
        self.func = func
        self.sinkSpec = sinkSpec
        self.sourceSpec = sourceSpec

    def expose (self, bag, name):
        bag.exposeSink (self, name)
        
    def linkTo (self, bag, source):
        bag.linkTo (source, self)
    
    def filterChunk (self, chunk):
        # We return a list, not a generator, because our return value
        # might be iterated over twice, and you can only iterate over
        # a generator once (for reasons that I do not know).
        return [self.func (*x) for x in chunk]

class IndexMapFilter (object):
    """Filter an incoming stream of data by remapping its values to
    new indices (the "out indices") arbitrarily. This is done
    independent of the actual contents of the incoming data. For
    instance, if an incoming datum has the value (A, B, C), and
    the out indices are (0, 2, 1, 0), the corresponding output
    datum will have the value (A, C, B, A)."""
    
    def __init__ (self, sinkSpec, outIndices):
        self.sinkSpec = sinkSpec
        self.outIndices = outIndices

        s = ''
        
        for idx in outIndices:
            s += sinkSpec[idx]

        self.sourceSpec = s

    def expose (self, bag, name):
        bag.exposeSink (self, name)
        
    def linkTo (self, bag, source):
        bag.linkTo (source, self)

    def mapOne (self, val):
        # This could probably be made more efficient. I think it's
        # best to return a tuple since the data will be immutable,
        # but we'll be allocating and freeing a lot of arrays as
        # the code stands.
        
        r = []

        for idx in self.outIndices:
            r.append (val[idx])

        return tuple (r)
        
    def filterChunk (self, chunk):
        return [self.mapOne (x) for x in chunk]
