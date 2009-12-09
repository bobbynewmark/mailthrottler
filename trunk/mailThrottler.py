#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
The main entry point for the email throttler
"""
#Internal Modules
import mailServer, webServer, core
from core import _config
#Python BulitIns
import sys
#External Modules
from twisted.internet import reactor

if __name__ == '__main__':
    _config.importDefaults("Main", { "mailPort" : "8001", "webPort" : "8080" } )
    if len(sys.argv) > 1:
        core.loadConfig(sys.argv[1])
    core.loggerSetup()
    counter = core.BaseMessageCounter()
    delivery = mailServer.LocalDelivery(counter)
    mailPort = _config.getint("Main", "mailPort")
    webPort = _config.getint("Main", "webPort")
    reactor.listenTCP(mailPort, mailServer.SMTPFactory(delivery))    
    reactor.listenTCP(webPort, webServer.createSite(counter))
    reactor.run()
