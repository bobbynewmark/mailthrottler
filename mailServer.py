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
import os, time, logging
from email.Header import Header
import tempfile

#External Modules
from twisted.mail import smtp, maildir
from twisted.web import server
from zope.interface import implements
from twisted.internet import protocol, reactor, defer, task

class BaseMessage(object): 
    implements(smtp.IMessage)

    defaultValues = {}

    def __init__(self, counter):
        self.logger = logging.getLogger("BaseMessage")
        self.lines = []
        self.counter = counter
        _config.importDefaults(self.__class__.defaultValues)
                    
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

    def __init__(self, counter):
        BaseMessage.__init__(self,counter)
        _config.importDefaults(self.__class__.defaultValues)

    def standardProcess(self, d):
        f = tempfile.NamedTemporaryFile(mode="w",dir=_config["saveFilePath"], delete=False)
        f.write( "\r\n".join(self.lines) )
        f.close()
        d.callback("File Saved")

    def excessProcess(self, d):
        d.callback("File not saved")

class LocalDelivery(object): 
    implements(smtp.IMessageDelivery)

    def __init__(self, counter, clearAfter=1.0):
        self.logger = logging.getLogger("LocalDelivery")
        #TODO: Should this happen here or somewhere else?
        self.counter = counter
        self.clearCall = task.LoopingCall(self.counter.clearCount)
        self.clearCall.start(clearAfter) # call every second TODO: Config

    def receivedHeader(self, helo, orgin, recipents):
        myHostname, clientIP = helo
        headerValue = "by %s from %s with ESMTP; %s" % (
            myHostname, clientIP, smtp.rfc822date())
        retval = "Recieved: %s" % Header(headerValue)
        self.logger.debug("receivedHeader: helo:%s orgin:%s recipents:%s", helo, orgin, [r.dest for r in recipents] )
        return retval

    def validateTo(self, user):
        self.logger.debug("validateTo: %s", user)
        return lambda: PrintMessage(self.counter)

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
