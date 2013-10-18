#Internal Modules
import mailServer, webServer, core, logging
from core import _config
#Python BulitIns
import sys
#External Modules
from twisted.application import service, internet

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
        self.initalise()
  
    def loadConfig(self, filepath):
        """Loads a configuration file into the config object
        - `filepath`: filepath to the config file (in INI format)
        """
        if filepath:
            self.logger.debug("Loading Config @ %s", filepath)
            core.loadConfig(filepath)

    def initalise(self):
        """initalises the reactor with the mail and web servers
        """
        self.logger.debug("initalise")
        self.mailPort = _config.getint("MTDaemon", "mailPort")
        self.mailInterface = _config.get("MTDaemon", "mailInterface")
        self.webPort = _config.getint("MTDaemon", "webPort")
        self.webInterface = _config.get("MTDaemon", "webInterface")



application = service.Application("mailThrottler")
filepath = ""
daemon = MTDaemon(filepath)

mailService = internet.TCPServer(daemon.mailPort,
                                 daemon.mailFactory,
                                 interface=daemon.mailInterface)
mailService.setName("mailService")
mailService.setServiceParent(application)

webService = internet.TCPServer(daemon.webPort,
                                 daemon.adminSite,
                                 interface=daemon.webInterface)
webService.setName("webService")
webService.setServiceParent(application)
