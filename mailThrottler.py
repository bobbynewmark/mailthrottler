#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
The main entry point for the email throttler
"""
#Internal Modules
import mailServer, webServer, core, logging
from core import _config
#Python BulitIns
import sys
#External Modules
from twisted.internet import reactor

class MTDaemon(object):
    
    defaultValues = { "mailInterface": "", "webInterface" : "", "mailPort" : "8001", "webPort" : "8080" }
    _config.importDefaults("MTDaemon", defaultValues)

    def __init__(self, configPath = ""):
        core.loggerSetup()
        self.logger = logging.getLogger("MTDaemon")
        self.loadConfig(configPath)
        
        self.counter = core.QueueMessageCounter()
        self.mailDelivery = mailServer.LocalDelivery(self.counter)
        self.mailFactory = mailServer.SMTPFactory(self.mailDelivery)
        self.adminSite = webServer.createSite(self.mailDelivery)        
        self.initaliseReactor()

    def loadConfig(self, filepath):
        """Loads a configuration file into the config object
        - `filepath`: filepath to the config file (in INI format)
        """
        if filepath:
            self.logger.debug("Loading Config @ %s", filepath)
            core.loadConfig(filepath)
    
    def initaliseReactor(self):
        """initalises the reactor with the mail and web servers
        """
        self.logger.debug("initalise reactor")
        mailPort = _config.getint("MTDaemon", "mailPort")
        mailInterface = _config.get("MTDaemon", "mailInterface")
        reactor.listenTCP(mailPort, self.mailFactory ,interface=mailInterface)
        
        webPort = _config.getint("MTDaemon", "webPort")
        webInterface = _config.get("MTDaemon", "webInterface")
        reactor.listenTCP(webPort, self.adminSite,interface=webInterface)

    def start(self):
        self.logger.info("Starting Reactor")
        reactor.run()

    def stop(self):
        self.logger.info("Stoping Reactor")
        reactor.stop()
        


if __name__ == '__main__':
    filepath = ""
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    daemon = MTDaemon(filepath)
    daemon.start()
