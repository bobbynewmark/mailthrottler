#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009-10
# See LICENCE for details
"""
The mail server itself
"""
#Internal Modules
from core import _config , BaseMessageCounter, RollingMemoryHandler, loggerSetup, createMsgFilePath
import webServer 

#Python BulitIns
import os, time, logging
from email.Header import Header

#External Modules
from twisted.mail import smtp, maildir
from twisted.web import server
from zope.interface import implements
from twisted.internet import protocol, reactor, defer, task

class BaseMessage(object): 
    implements(smtp.IMessage)

    defaultValues = {}
    _config.importDefaults("BaseMessage", defaultValues)

    def __init__(self, counter):
        self.logger = logging.getLogger("BaseMessage")
        self.lines = []
        self.FROM = ""
        self.counter = counter        
                    
    def lineReceived(self, line):
        self.logger.debug("lineRecieved")
        if line.lower().startswith("from:"):
            self.FROM = line.lower().replace("from:", "").strip()
        self.lines.append(line)

    def eomReceived(self):
        self.logger.debug("eomReceived")  
        self.logger.debug("self.FROM=%s" % self.FROM)  
        self.counter.incrementCount(self)
        self.lines.append("")
        d = defer.Deferred()
        if not self.counter.reachedExcessAmount(self):
            self.standardProcess(d)
        else:
            self.excessProcess(d)
        return d

    def standardProcess(self, d):
        return d.callback("finished")

    def excessProcess(self, d):
        return d.callback("finished")

    def connectionLost(self):
        self.logger.debug("connectionLost")
        del(self.lines)
        self.FROM = ""

class PrintMessage(BaseMessage):
    def standardProcess(self, d):
        self.logger.info("recieved into standard process msg %s" , self.counter.count)
        d.callback("standardProcess")
    
    def excessProcess(self, d):
        self.logger.info("recieved into excess process msg %s" , self.counter.count)
        d.callback("execessProcess")

class SaveMessage(BaseMessage):

    defaultValues = { }
    _config.importDefaults("SaveMessage", defaultValues)

    def __init__(self, counter):
        BaseMessage.__init__(self,counter)        

    def standardProcess(self, d):
        self.writeMsgToDisk()
        d.callback("File Saved")

    def writeMsgToDisk(self):
        filepath = createMsgFilePath()
        try:
            f = open(filepath, "w")
            f.write( self.assembleMsg()  )
            f.close()
            self.logger.info("Saved Message as %s" , filepath)
        except IOError:
            #TODO: This is bad.  Should we alert calling code so that it can do something about this?
            self.logger.error("Failed to save message as %s" , filepath) 
    
    def assembleMsg(self):
        return "\n".join(self.lines)

    def excessProcess(self, d):
        d.callback("File not saved")

class QueuedSaveMessage(SaveMessage):
    
    def __init__(self, counter):
        SaveMessage.__init__(self,counter)

    def standardProcess(self, d):
        try:
            self.counter.saveMsgLater(self, createMsgFilePath(), self.assembleMsg())
            d.callback("Msg Queued")
        except AttributeError:
            self.logger.error("Counter for QueuedSaveMessage does not have a saveMsgLater function")
            SaveMessage.standardProcess(self,d)       

class LocalDelivery(object): 
    implements(smtp.IMessageDelivery)

    defaultValues = {"clearAfter": "1.0" }
    _config.importDefaults("LocalDelivery", defaultValues)

    def __init__(self, counter):
        self.logger = logging.getLogger("LocalDelivery")
        self.counter = counter
        self.clearCall = task.LoopingCall(self.counter.clearCount)
        self.clearCall.start(_config.getfloat("LocalDelivery","clearAfter"))

    def receivedHeader(self, helo, orgin, recipents):
        myHostname, clientIP = helo
        headerValue = "by %s from %s with ESMTP; %s" % (
            myHostname, clientIP, smtp.rfc822date())
        retval = "Recieved: %s" % Header(headerValue)
        #retval = ""
        self.logger.debug("receivedHeader: helo:%s orgin:%s recipents:%s", helo, orgin, [r.dest for r in recipents] )
        return retval

    def validateTo(self, user):
        self.logger.debug("validateTo: %s", user)
        return lambda: QueuedSaveMessage(self.counter)

    def validateFrom(self, helo, orginAddress):
        self.logger.debug("validateFrom: helo:%s orginAddress:%s", helo, orginAddress)
        return orginAddress

    def resetClearCall(self):
        self.logger.info("resetting Clear Count")
        self.clearCall.stop()
        self.counter.clearCount()
        self.clearCall.start(_config.getfloat("LocalDelivery","clearAfter"))

class SMTPFactory(protocol.ServerFactory):

    def __init__(self, delivery):
        self.delivery = delivery
        self.logger = logging.getLogger("SMTPFactory")
    
    def buildProtocol(self, addr):
        self.logger.debug("Setting up protocol")
        smtpProtocol = smtp.SMTP(self.delivery)
        smtpProtocol.factory = self
        return smtpProtocol
