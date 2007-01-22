class Bag (object):
    def __init__ (self):
        self.sinks = set ()
        self.exposed = {}
        self.linked = {}
        
    def registerSink (self, sink):
        self.sinks.add (sink)

    def exposeSink (self, sink, name):
        self.registerSink (sink)
        self.exposed[name] = sink

    def linkTo (self, source, sink):
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
        
        for (name, sink) in self.exposed.iteritems ():
            if name not in sources: raise Exception ('No such source %s!' % (name))

            self.currentIters[sink] = sources[name].__iter__ ()

        for sink in self.sinks:
            if sink in self.exposed.itervalues (): continue
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
    def __init__ (self, func):
        self.func = func

    def linkTo (bag, source):
        bag.linkTo (source, self)
    
    def filterChunk (self, chunk):
        # We return a list, not a generator, because our return value
        # might be iterated over twice, and you can only iterate over
        # a generator once (for reasons that I do not know).
        return [self.func (*x) for x in chunk]
