class Bag (object):
    def __init__ (self):
        self.sinks = set ()
        self.exposed = {}
        
    def registerSink (self, sink):
        self.sinks.add (sink)

    def exposeSink (self, sink, name):
        self.registerSink (sink)
        self.exposed[name] = sink

    def getChunk (self, sink):
        chunk = self.currentRound.get (sink)

        if chunk: return chunk

        raise Exception ('uh oh now what')

    def startFlushing (self, sources):
        self.currentIters = {}
        
        for (name, sink) in self.exposed.iteritems ():
            if name not in sources: raise Exception ('No such source %s!' % (name))

            self.currentIters[sink] = sources[name].__iter__ ()

        
    def startNewRound (self):
        self.currentRound = {}
        gotany = False
        
        for (sink, iter) in self.currentIters.iteritems ():
            try:
                chunk = iter.next ()
                self.currentRound[sink] = chunk
                gotany = True
            except StopIteration:
                self.currentRound[sink] = None

        return gotany
    
    def push (self, sources, *args):
        if len (sources) < len (self.exposed):
            raise Exception ('Not enough sources for all exposed sinks!')
        
        for sink in self.sinks:
            if hasattr (sink, 'streamBegin'): sink.streamBegin (*args)

        for (name, sink) in self.exposed.iteritems ():
            if name not in sources: raise Exception ('No such source %s!' % (name))

            source = sources[name]

            for chunk in source:
                sink.acceptChunk (chunk, *args)

        for sink in self.sinks:
            if hasattr (sink, 'streamEnd'): sink.streamEnd (*args)
