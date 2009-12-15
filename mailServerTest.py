#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
Unit tests for mailServer
"""
#Internal Modules
import mailServer
from mailServer import BaseMessage, BaseMessageCounter
#Python BulitIns
import unittest, sys, collections
#External Modules
from twisted.internet import defer


#TODO: Find better way of doing this counting
class FunctionCallCount(BaseMessage):
    def __init__(self, counter):
        BaseMessage.__init__(self, counter)
        self.calls = collections.defaultdict(int)

    def eomReceived(self):
        self.calls["eomReceived"] += 1
        return BaseMessage.eomReceived(self)

    def standardProcess(self, d):
        self.calls["standardProcess"] += 1
        return BaseMessage.standardProcess(self, d)

    def excessProcess(self, d):
        self.calls["excessProcess"] += 1
        return BaseMessage.excessProcess(self, d)

class BaseMessageTest(unittest.TestCase):

    def setUp(self):
        self.counter = BaseMessageCounter()
        self.testObj = FunctionCallCount( self.counter )

    def test_001_init_State(self):
        self.assertEquals(len(self.testObj.lines), 0, 'MailDir init state should be 0 lines') #Assert lines start with 0

    def test_002_eomIncrementsCount(self):
        self.assertEquals( self.counter.count , 0 , 'BaseMessage init should not increment count')
        self.testObj.eomReceived()
        self.assertEquals( self.counter.count , 1 , 'BaseMessage eomReceived should increment count')
        for i in xrange(30):
            self.testObj.eomReceived()
        self.assertEquals( self.counter.count , 31 , 'BaseMessage eomReceived should increment count')

    def test_003_eomCallsStandardProcess(self):
        for i in xrange(10):
            self.testObj.eomReceived()

        self.assertEquals(self.testObj.calls["eomReceived"], 10)
        self.assertEquals(self.testObj.calls["standardProcess"], 10)        

    def test_004_canConfigureExcessAmount(self):
        #self.testObj.importConfig({"excessAmount": 5})
        mailServer._config.set("BaseMessageCounter", "excessAmount", "5" )
        for i in xrange(10):
            self.testObj.eomReceived()

        self.assertEquals(self.testObj.calls["eomReceived"], 10)
        self.assertEquals(self.testObj.calls["standardProcess"], 5)
        self.assertEquals(self.testObj.calls["excessProcess"], 5)

#     def test_005_importConfig(self):
#         config = collections.defaultdict(str)
#         config["excessAmount"] = 5
#         self.testObj.importConfig(config)
#         self.assertEquals(self.testObj.excessAmount , 5 , "excessAmount should be set")

    def test_006_eomReturnsDefered(self):
        m = self.testObj.eomReceived()
        self.assert_(isinstance(m, defer.Deferred), "eomReceived must return a defered")


def main():
    unittest.main()

if __name__ == "__main__":
    main()


