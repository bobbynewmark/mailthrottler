#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
The Admin Frontend to the mail server
"""
#Internal Modules
from core import RollingMemoryHandler, _config, loader
#Python BulitIns
import logging, cgi, os, json
#External Modules
from twisted.web import server, resource, static
from genshi.template import TemplateLoader
 
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
        retval = {"log" : [] }
        for txt, logitem in self.log.currentLog:
            retval["log"].append( 
                { 'asctime' : logitem.asctime, 
                  'name' : logitem.name, 
                  'levelname' : logitem.levelname, 
                  'message': logitem.message 
                  }
                )   
        
        return json.dumps(retval)

class ForceClear(resource.Resource):
    isLeaf = 1

    def __init__(self, delivery):
        resource.Resource.__init__(self)
        self.delivery = delivery
    
    def render_GET(self, request):
        self.delivery.resetClearCall()
        return "OK"

def createSite(delivery):
    counter = delivery.counter
    log = RollingMemoryHandler()
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log.setFormatter(formatter)
    logging.getLogger("").addHandler(log)
    root = resource.Resource()
    root.putChild('', AdminPage(counter, log))
    root.putChild('ajax', Ajax(log))
    root.putChild('config', ConfigPage())
    root.putChild('forceclear', ForceClear(delivery))
    root.putChild('default.css', static.File(os.path.join( _config.get("Core", "templatePath") , "default.css" )))
    root.putChild('jquery-1.3.2.min.js', static.File(os.path.join( _config.get("Core", "templatePath") , "jquery-1.3.2.min.js" )))
    return server.Site(root)
    
