#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
These are common classes and functions to the whole project
"""
#Internal Modules

#Python BulitIns
import logging, ConfigParser, collections
#External Modules

class Config(ConfigParser.SafeConfigParser):

    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        self.optionxform = str #This is so we don't loose case on the key names
    
    def importDefaults(self, sectionName, configDefaults ):
        for key in configDefaults.keys():
            if not self.has_section(sectionName):
                self.add_section(sectionName)
            if not self.has_option(sectionName, key):
                self.set( sectionName, key , configDefaults[key] )

_config = Config()

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

    defaultValues = {}
    _config.importDefaults("QueueMessageCounter", defaultValues)

    def __init__(self):
        BaseMessageCounter.__init__(self)
        self.logger = logging.getLogger("QueueMessageCounter")
        self.queues = collections.defaultdict(int)

    def incrementCount(self, message):
        BaseMessageCounter.incrementCount(self, message) #increment the totals and a running count as be base class
        self.queues[message.FROM] += 1

    def clearCount(self):
        BaseMessageCounter.clearCount(self)
        for fromaddr in self.queues.keys():
            self.logger.debug( "Clearing count for queue %s (totalCount:%s)" , fromaddr , self.totalCount )
            self.queues[fromaddr] = 0

    def reachedExcessAmount(self, message):
        return self.queues[message.FROM] > _config.getint("BaseMessageCounter", "excessAmount")

    def getCounts(self):
        """Returns the counts of the queues"""
        retval = BaseMessageCounter.getCounts(self)
        retval.update( self.queues  )
        return retval

    
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
   


