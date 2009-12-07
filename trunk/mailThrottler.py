#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
The main entry point for the email throttler
"""
#Internal Modules
import mailServer, webServer, core
#Python BulitIns

#External Modules
from twisted.internet import reactor

if __name__ == '__main__':
    core.loggerSetup()
    counter = core.BaseMessageCounter()
    delivery = mailServer.LocalDelivery(counter, 5.0)
    reactor.listenTCP(8001, mailServer.SMTPFactory(delivery))    
    reactor.listenTCP(8080, webServer.createSite(counter))
    reactor.run()
