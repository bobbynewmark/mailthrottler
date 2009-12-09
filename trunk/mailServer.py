#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
The mail server itself
"""
#Internal Modules
from core import _config , BaseMessageCounter, RollingMemoryHandler, loggerSetup
import webServer 

#Python BulitIns
import os, time, logging, uuid
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
        self.counter = counter        
                    
    def lineReceived(self, line):
        self.logger.debug("lineRecieved")
        self.lines.append(line)

    def eomReceived(self):
        self.logger.debug("eomReceived")        
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

class PrintMessage(BaseMessage):
    def standardProcess(self, d):
        self.logger.info("recieved into standard process msg %s" , self.counter.count)
        d.callback("standardProcess")
    
    def excessProcess(self, d):
        self.logger.info("recieved into excess process msg %s" , self.counter.count)
        d.callback("execessProcess")

class SaveMessage(BaseMessage):

    defaultValues = {"saveFilePath": "maildrop" }
    _config.importDefaults("SaveMessage", defaultValues)

    def __init__(self, counter):
        BaseMessage.__init__(self,counter)
        

    def standardProcess(self, d):
        filepath = os.path.join(_config.get("SaveMessage", "saveFilePath"), str(uuid.uuid4()) + ".msg" )
        f = open(filepath, "w")
        f.write( "\n".join(self.lines) )
        f.close()
        self.logger.info("Saved Message as %s" , filepath)
        d.callback("File Saved")

    def excessProcess(self, d):
        d.callback("File not saved")

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
        #retval = "Recieved: %s" % Header(headerValue)
        retval = ""
        self.logger.debug("receivedHeader: helo:%s orgin:%s recipents:%s", helo, orgin, [r.dest for r in recipents] )
        return retval

    def validateTo(self, user):
        self.logger.debug("validateTo: %s", user)
        return lambda: SaveMessage(self.counter)

    def validateFrom(self, helo, orginAddress):
        self.logger.debug("validateFrom: helo:%s orginAddress:%s", helo, orginAddress)
        return orginAddress

class SMTPFactory(protocol.ServerFactory):

    def __init__(self, delivery):
        self.delivery = delivery
        self.logger = logging.getLogger("SMTPFactory")
    
    def buildProtocol(self, addr):
        self.logger.debug("Setting up protocol")
        smtpProtocol = smtp.SMTP(self.delivery)
        smtpProtocol.factory = self
        return smtpProtocol
