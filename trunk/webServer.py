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
    os.path.join(os.path.dirname(__file__), 'templates'),
    auto_reload=True
)
 
class AdminPage(resource.Resource):
    isLeaf = 1

    def __init__(self, counter):
        resource.Resource.__init__(self)
        self.counter = counter
        self.log = RollingMemoryHandler()
        self.log.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.log.setFormatter(formatter)
        logging.getLogger("").addHandler(self.log)


    def render_GET(self, request):
        tmpl = loader.load('index.html')
        stream = tmpl.generate(log=self.log.currentLog, currentCount=self.counter.count, totalCount=self.counter.totalCount, currentLevel=logging.getLevelName(self.log.level))
        return stream.render('html', doctype='html')

    def render_POST(self, request):
        tmpl = loader.load('index.html') 
        self.log.setLevel( getattr(logging, str(request.args["logLevel"][0]).upper()) );
        stream = tmpl.generate(log=self.log.currentLog, currentCount=self.counter.count, totalCount=self.counter.totalCount, currentLevel=logging.getLevelName(self.log.level))
        return stream.render('html', doctype='html')

def createSite(counter):
    root = resource.Resource()
    root.putChild('', AdminPage(counter))
    root.putChild('default.css', static.File('templates/default.css'))
    return server.Site(root)
    
