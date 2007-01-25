class TestStyle (object):
    smallScale = 2
    largeScale = 5

    def initContext (self, ctxt, width, height):
        ctxt.rectangle (0, 0, width, height)
        ctxt.set_source_rgb (1, 1, 1)
        ctxt.fill ()
    
    def apply (self, ctxt, style):
        if not style: return

        if hasattr (style, 'apply'):
            style.apply (ctxt)
            return

        if callable (style):
            style (ctxt)
            return

        if isinstance (style, basestring):
            fn = 'apply_' + style

            if hasattr (self, fn):
                getattr (self, fn)(ctxt)
                return

        raise Exception ('Dont know what to do with style item %s' % style)

    def apply_bgLinework (self, ctxt):
        ctxt.set_line_width (1)
        ctxt.set_source_rgb (0.3, 0.3, 0.3) # do rgba?

    def apply_bgFill (self, ctxt):
        ctxt.set_source_rgb (1, 1, 1)

    def apply_genericStamp (self, ctxt):
        ctxt.set_line_width (1)

    def apply_genericLine (self, ctxt):
        ctxt.set_line_width (1)
        ctxt.set_source_rgb (0, 0, 0)

