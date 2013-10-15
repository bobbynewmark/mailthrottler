#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009-10
# See LICENCE for details
"""
These are common classes and functions to the whole project
"""
#Internal Modules

#Python BulitIns
import logging, ConfigParser, collections, uuid, os
from datetime import datetime, timedelta
#External Modules
from genshi.template import TemplateLoader, NewTextTemplate

class Config(ConfigParser.SafeConfigParser):

    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        self.optionxform = str #This is so we don't loose case on the key names
    
    def importDefaults(self, sectionName, configDefaults ):
        for key in configDefaults.keys():
            if not self.has_section(sectionName):
                self.add_section(sectionName)
            if not self.has_option(sectionName, key):
                #Check enviroment for vars
                default = os.environ.get(".".join((sectionName,key)),configDefaults[key]) 
                self.set( sectionName, key , default)

_config = Config()
#Some base config settings
_config.importDefaults("Core", {"saveFilePath": "maildrop" , "templatePath":"templates"})

class BaseMessageCounter(object):
    """This is the prototype for all Counters
    TODO: Check for thread safety, may have to return defereds if need to lock / unlock resource
    """

    defaultValues = {"excessAmount": "20"}
    _config.importDefaults("BaseMessageCounter", defaultValues)

    def __init__(self):
        self.logger = logging.getLogger("BaseMessageCounter")
        self.count = 0
        self.totalCount = 0  
        self.starttime = datetime.utcnow()

    def incrementCount(self, message):
        self.count += 1
        self.totalCount += 1

    def clearCount(self):
        self.count = 0
        self.logger.debug( "Clearing count (totalCount:%s)" ,self.totalCount )

    def reachedExcessAmount(self, message):
        return self.count > _config.getint("BaseMessageCounter", "excessAmount")

    def getCounts(self):
        """Returns a dictionary of counts from the counter. 
        Override to provide more than just the total and current (which should always be there)"""
        return { "total" : self.totalCount, "current": self.count }

class QueueMessageCounter(BaseMessageCounter):
    """Creates counts based on the FROM address of the message.
    Keeps these in a dictionary which it clears on clear count
    """

    defaultValues = {"sendExcessEmailMinTimeDelta_s": "60",
                     "excessMailFrom": "mailThrottler@localhost",
                     "excessMailTo": "root@localhost"
                     }
    _config.importDefaults("QueueMessageCounter", defaultValues)

    def __init__(self):
        BaseMessageCounter.__init__(self)
        self.logger = logging.getLogger("QueueMessageCounter")
        self.queues = collections.defaultdict(int)
        self.queuetotals = collections.defaultdict(int)
        self.mailQueues = collections.defaultdict(list)
        self.lastExcessEmailSent = datetime.min

    def incrementCount(self, message):
        BaseMessageCounter.incrementCount(self, message) #increment the totals and a running count as be base class
        self.queues[message.FROM] += 1
        self.queuetotals[message.FROM] += 1

    def clearCount(self): #Maybe here we should copy then clear the active ones as fast as possible
        excessQueues = []
        for fromaddr in self.queues.keys():
            self.logger.debug( "Clearing count for queue %s (totalCount:%s)" , fromaddr , self.queuetotals[fromaddr] )
            if self.queues[fromaddr] < _config.getint("BaseMessageCounter", "excessAmount"):
                self.sendMailQueue(fromaddr)
                self.queues[fromaddr] = len(self.mailQueues[fromaddr])
            else:
                excessQueues.append(fromaddr)

        self.sendExcessEmail(excessQueues)
        for excessQueue in excessQueues:
            self.clearMailQueue(excessQueue) 
            self.queues[excessQueue] = 0

        BaseMessageCounter.clearCount(self)
            
    def reachedExcessAmount(self, message):
        return self.queues[message.FROM] > _config.getint("BaseMessageCounter", "excessAmount")

    def getCounts(self):
        """Returns the counts of the queues"""
        retval = BaseMessageCounter.getCounts(self)
        for key in self.queuetotals.keys():
            retval[key] = { "current" : self.queues[key], "total" : self.queuetotals[key] }
        return retval

    def saveMsgLater(self, message, filepath, msgContent):
        self.mailQueues[message.FROM].append( (filepath, msgContent) )

    def sendMailQueue(self, fromaddr):
        errors = []
        while len(self.mailQueues[fromaddr]) > 0:
            filepath, msgContent = self.mailQueues[fromaddr].pop()
            try:
                self.writeMsgToDisk(filepath, msgContent)
                self.logger.info("Saved Message as %s" , filepath)
            except IOError:
                self.logger.error("Failed to save Message as %s" , filepath)
                errors.append((filepath, msgContent))
        self.mailQueues[fromaddr].extend(errors) #push the errors back onto the queue

    def clearMailQueue(self, fromaddr):
        while len(self.mailQueues[fromaddr]) > 0:
            filepath, msgContent = self.mailQueues[fromaddr].pop()
            self.logger.info("Cleared Message instead of saving %s" , filepath)

    def sendExcessEmail(self, excessQueues):
        emailSent = False
        if len(excessQueues) > 0:
            self.logger.info("In excess state")            
            if self.notWithinExcessEmailTimeDelta():
                fromaddr = _config.get("QueueMessageCounter", "excessMailFrom")
                toaddr = _config.get("QueueMessageCounter", "excessMailTo")
                msgContent = self.createExcessEmail(fromaddr, toaddr, excessQueues)
                filepath = createMsgFilePath()
                try:
                    self.writeMsgToDisk(filepath, msgContent)
                    self.logger.info("Saved ExcessEmail as %s" , filepath)
                    self.lastExcessEmailSent = datetime.today()
                    emailSent = True
                except IOError:
                    self.logger.error("Failed to save ExcessEmail as %s" , filepath) 
            else:
                self.logger.info("Did not send ExcessEmail as last one was sent %s ago", datetime.today() - self.lastExcessEmailSent)
        else:
            self.logger.debug("No need to send ExcessEmail as there are no excess queues")
        return emailSent

    def notWithinExcessEmailTimeDelta(self):
        timeSinceLastEmail = datetime.today() - self.lastExcessEmailSent
        return timeSinceLastEmail > timedelta(seconds=_config.getint("QueueMessageCounter", "sendExcessEmailMinTimeDelta_s"))

    def createExcessEmail(self, fromaddr, toaddr, excessQueues):
        tmpl = loader.load('excessMsg.txt', cls=NewTextTemplate)
        stream = tmpl.generate(mailQueues=self.mailQueues, excessQueues=excessQueues, fromaddr=fromaddr, toaddr=toaddr, counts=self.getCounts())
        return stream.render("text")

    def writeMsgToDisk(self, filepath, msgContent):
         f = open(filepath, "w")
         f.write(msgContent)
         f.close()

    
class RollingMemoryHandler(logging.Handler):

    defaultValues = {"logSize": "20"}
    _config.importDefaults("RollingMemoryHandler", defaultValues)

    def __init__(self):
        logging.Handler.__init__(self)        
        self.currentLog = []
        self.logSize = _config.getint("RollingMemoryHandler", "logSize")
    
    def emit(self,record):
        #have to apply the format to the text of the log or something!
        if len(self.currentLog) >= self.logSize:
            self.currentLog.pop()
        self.currentLog.insert(0, (self.format(record), record))

    def setLevel(self, lvl):
        logging.Handler.setLevel(self, lvl)
        self.currentLog = [record for record in self.currentLog if record[1].levelno >= lvl]

    def addSelfToLogging(self, initalLevel):
        self.setLevel(initalLevel)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.setFormatter(formatter)
        logging.getLogger("").addHandler(self)

def createMsgFilePath():
    return os.path.join(_config.get("Core", "saveFilePath"), str(uuid.uuid4()) + ".msg" )

def loggerSetup():
    #Sets up the Root Logger
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG) 
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def loadConfig(filename):
    _config.readfp(open(filename))

#Set up template loader
loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), _config.get("Core", "templatePath")),
    auto_reload=True
)

