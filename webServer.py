#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
The Admin Frontend to the mail server
"""
#Internal Modules
from core import RollingMemoryHandler, _config
#Python BulitIns
import logging, cgi, os
#External Modules
from twisted.web import server, resource, static
from genshi.template import TemplateLoader

#Set up template loader
loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'templates'), #TODO: Config?
    auto_reload=True
)
 
class AdminPage(resource.Resource):
    isLeaf = 1

    def __init__(self, counter, log):
        resource.Resource.__init__(self)
        self.counter = counter
        self.log = log

    def render_GET(self, request):
        tmpl = loader.load('index.html')
        stream = tmpl.generate(log=self.log.currentLog, counts=self.counter.getCounts(), currentLevel=logging.getLevelName(self.log.level))
        return stream.render('html', doctype='html')

    def render_POST(self, request):
        tmpl = loader.load('index.html') 
        self.log.setLevel( getattr(logging, str(request.args["logLevel"][0]).upper()) );
        stream = tmpl.generate(log=self.log.currentLog, counts=self.counter.getCounts(), currentLevel=logging.getLevelName(self.log.level))
        return stream.render('html', doctype='html')

class ConfigPage(resource.Resource):
    isLeaf = 1

    def __init__(self):
        resource.Resource.__init__(self)

    def render_GET(self, request):
        tmpl = loader.load('config.html')
        stream = tmpl.generate(config=_config)
        return stream.render('html', doctype='html')

class Ajax(resource.Resource):
    isLeaf = 1

    def __init__(self, log):
        resource.Resource.__init__(self)
        self.log = log
    
    def render_GET(self, request):
        retval = '{log : ['
        
        items = []
        for txt, logitem in self.log.currentLog:
            items.append('{asctime:"%s", name : "%s", levelname: "%s", message: "%s"}' % (logitem.asctime, logitem.name, logitem.levelname, logitem.message) )

        retval += ",".join(items)
        retval += ']}'
        
        return retval #'{log : [ {asctime:"abc", name : "def", levelname: "ghi", message: "jkl"} ]}'

def createSite(counter):
    log = RollingMemoryHandler()
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log.setFormatter(formatter)
    logging.getLogger("").addHandler(log)
    root = resource.Resource()
    root.putChild('', AdminPage(counter, log))
    root.putChild('ajax', Ajax(log))
    root.putChild('config', ConfigPage())
    root.putChild('default.css', static.File('templates/default.css'))
    root.putChild('jquery-1.3.2.min.js', static.File('templates/jquery-1.3.2.min.js'))
    return server.Site(root)
    
