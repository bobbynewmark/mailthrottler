#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009-10
# See LICENCE for details
"""
Unit tests for the core.py module
"""
#Internal Modules
import core

#Python BulitIns
import unittest, logging, datetime

#External Modules


class RollingMemoryHandlerTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_NewlyCreatedHandlerHasAEmptyLog(self):
        log = core.RollingMemoryHandler()
        self.assertEquals(len(log.currentLog), 0, 'RollingMemoryHandler should start with an empty log') 

    def test_NewlyCreatedHandlerSetsLogSize(self):
        log = core.RollingMemoryHandler()
        self.assertEquals(log.logSize, int(core.RollingMemoryHandler.defaultValues["logSize"]), 'RollingMemoryHandler should start with a logSize') 
        
    def test_HandlerAddsLogMsgs(self):
        testObj = core.RollingMemoryHandler()
        testObj.addSelfToLogging(logging.DEBUG)
        logger = logging.getLogger("TEST")
        logger.setLevel(logging.DEBUG)
        logger.debug("Test Msg 1")
        self.assertEquals(len(testObj.currentLog), 1, 'RollingMemoryHandler should pickup DEBUG message') 
        logger.info("Test Msg 2")
        self.assertEquals(len(testObj.currentLog), 2, 'RollingMemoryHandler should pickup INFO message') 
        logger.error("Test Msg 3")
        self.assertEquals(len(testObj.currentLog), 3, 'RollingMemoryHandler should pickup ERROR message')

    def test_HandlerRollsMsgs(self):
        testObj = core.RollingMemoryHandler()
        testObj.addSelfToLogging(logging.DEBUG)
        logger = logging.getLogger("TEST")
        logger.setLevel(logging.DEBUG)
        for x in xrange(30):
            logger.debug("Test Msg %s", x)
            if x < testObj.logSize:
                self.assertEquals(len(testObj.currentLog), x+1, "RollingMemoryHandler should pickup msgs, failed at x:%s" % x) #add 1 as x starts at 0
            else:
                self.assertEquals(len(testObj.currentLog), testObj.logSize, "RollingMemoryHandler should roll msgs, failed at x:%s" % x)
    
    def test_HandlerAddMsgAtStartOfQueue(self):
        testObj = core.RollingMemoryHandler()
        testObj.addSelfToLogging(logging.DEBUG)
        logger = logging.getLogger("TEST")
        logger.setLevel(logging.DEBUG)
        logger.debug("Test Msg %s", 1)
        logger.debug("Test Msg %s", 2)
        self.assertEquals( testObj.currentLog[0][1].args[0], 2 ) 
        logger.debug("Test Msg %s", 3)
        self.assertEquals( testObj.currentLog[0][1].args[0], 3 ) 

    def test_setLevelClearsQueue(self):
        testObj = core.RollingMemoryHandler()
        testObj.addSelfToLogging(logging.DEBUG)
        logger = logging.getLogger("TEST")
        logger.setLevel(logging.DEBUG)
        logger.debug("Test Msg %s", 1)
        logger.debug("Test Msg %s", 2)
        logger.debug("Test Msg %s", 3)
        self.assertEquals(len(testObj.currentLog), 3, "RollingMemoryHandler should pickup 3 msgs")
        testObj.setLevel(logging.INFO)
        self.assertEquals(len(testObj.currentLog), 0, "RollingMemoryHandler should clear msgs")
        logger.debug("Test Msg %s", 1)
        logger.debug("Test Msg %s", 2)
        logger.info("Test Msg %s", 3)
        logger.info("Test Msg %s", 4)
        self.assertEquals(len(testObj.currentLog), 2, "RollingMemoryHandler should only count info msgs")
        
class ConfigTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_importDefaultsAddsNewSection(self):
        c = core.Config()
        self.assertTrue( not c.has_section("Test") , "Config should not have test section until imported")
        c.importDefaults("Test", {"a":"b"})
        self.assertEquals( c.get("Test", "a") , "b" , "Config should import default and create section" )

    def test_importDefaultsDoesNotOverride(self):
        c = core.Config()
        c.add_section( "Test" )
        c.set( "Test", "a", "testvalue" )
        c.importDefaults("Test", {"a":"b"})
        self.assertEquals( c.get("Test", "a") , "testvalue" , "Config should not import default when there is already a value" )

    def test_setDoesNotChangeCass(self):
        c = core.Config()
        c.add_section( "TesT" )
        c.set( "TesT", "AbC", "TestValuE" )
        self.assertEquals( c.get("TesT", "AbC") , "TestValuE" , "Config should not change case of imported values" )

class BaseMessageCounterTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_createCounterStartsAtZero(self):
        c = core.BaseMessageCounter()
        self.assertEquals( c.count , 0 , "Count should start at zero")
        self.assertEquals( c.totalCount, 0, "TotalCount should start at zero")
    
    def test_incrementCountWorks(self):
        c = core.BaseMessageCounter()
        c.incrementCount(None)
        self.assertEquals( c.count , 1 , "Count should be 1")
        self.assertEquals( c.totalCount, 1, "TotalCount should be 1")

    def test_clearCount(self):
        c = core.BaseMessageCounter()
        for i in xrange(20):
            c.incrementCount(None)
        self.assertEquals( c.count , 20 , "Count should be 20")
        self.assertEquals( c.totalCount, 20, "TotalCount should be 20")
        c.clearCount()
        self.assertEquals( c.count , 0 , "Count should be 0 after clear")
        self.assertEquals( c.totalCount, 20, "TotalCount should be 20 after clear")
    
    def test_reachedExcessAmount(self):
        c = core.BaseMessageCounter()
        excessAmount = int(core.BaseMessageCounter.defaultValues["excessAmount"])
        for i in xrange(1, excessAmount * 2):
            c.incrementCount(None)
            if i <= excessAmount:
                self.assertFalse( c.reachedExcessAmount(None), "reachedExcessAmount should be false if count %s <= %s" % ((i+1) , excessAmount) )
            else:
                self.assertTrue( c.reachedExcessAmount(None), "reachedExcessAmount should be true if count %i > %s" % ((i+1) , excessAmount) )
        
    def test_getCounts(self):
        c = core.BaseMessageCounter()
        d = c.getCounts()
        self.assertEquals( d["total"] , 0 , "getCounts should return 0 at start")
        self.assertEquals( d["current"] , 0 , "getCounts should return 0 at start")
        for i in xrange(20):
            c.incrementCount(None)
        d = c.getCounts()
        self.assertEquals( d["total"] , 20 , "getCounts should return 20")
        self.assertEquals( d["current"] , 20 , "getCounts should return 20")
        c.clearCount()
        for i in xrange(20):
            c.incrementCount(None)
        d = c.getCounts()
        self.assertEquals( d["total"] , 40 , "getCounts should return 40 after clear")
        self.assertEquals( d["current"] , 20 , "getCounts should return 20 after clear")

class QueueMessageCounterTest(unittest.TestCase):
    
    class MockMessage(object):
        def __init__(self, myFrom):
            self.FROM = myFrom

    

    def setUp(self):
        pass
    
    def test_createCounterStartsAtZero(self):
        c = core.QueueMessageCounter()
        self.assertEqual(len(c.queues) , 0 , "queues len should be 0 on creation" )
        self.assertEqual(len(c.queuetotals) , 0 , "queuetotals len should be 0 on creation" )
        self.assertEqual(len(c.mailQueues) , 0 , "mailQueues len should be 0 on creation" )
        self.assertEqual(c.lastExcessEmailSent , datetime.datetime.min , "lastExcessEmailSent should be datetime.min at creation" )
    
    def test_incrementCountSingleFrom(self):
        c = core.QueueMessageCounter()
        c.incrementCount(QueueMessageCounterTest.MockMessage("a@b.com"))
        self.assertEquals( c.count , 1 , "Count should be 1")
        self.assertEquals( c.totalCount, 1, "TotalCount should be 1")
        self.assertEqual(len(c.queues) , 1 , "queues len should be 1 after increment" )
        self.assertEqual(len(c.queuetotals) , 1 , "queuetotals len should be 1 after increment" )
        self.assertEqual(c.queues["a@b.com"] , 1 , "queues len should be 1 after increment" )
        self.assertEqual(c.queuetotals["a@b.com"] , 1 , "queuetotals len should be 1 after increment" )

    def test_incrementCountMulipleFrom(self):
        c = core.QueueMessageCounter()
        for i in xrange(5):
            c.incrementCount(QueueMessageCounterTest.MockMessage("a@b.com"))
        for i in xrange(5):
            c.incrementCount(QueueMessageCounterTest.MockMessage("a@c.com"))
            
        self.assertEquals( c.count , 10 , "Count should be 10")
        self.assertEquals( c.totalCount, 10, "TotalCount should be 10")
        self.assertEqual(len(c.queues) , 2 , "queues len should be 2 after increment" )
        self.assertEqual(len(c.queuetotals) , 2 , "queuetotals len should be 2 after increment" )
        self.assertEqual(c.queues["a@b.com"] , 5 , "queues len should be 5 after increment" )
        self.assertEqual(c.queuetotals["a@b.com"] , 5 , "queuetotals len should be 5 after increment" )
        self.assertEqual(c.queues["a@c.com"] , 5 , "queues len should be 5 after increment" )
        self.assertEqual(c.queuetotals["a@c.com"] , 5 , "queuetotals len should be 5 after increment" )

    def test_clearCount(self):
        c = core.QueueMessageCounter()
        for i in xrange(10):
            c.incrementCount(QueueMessageCounterTest.MockMessage("a@b.com"))
        c.clearCount()
        self.assertEquals( c.count , 0 , "Count should be 0 after clear")
        self.assertEquals( c.totalCount, 10, "TotalCount should be 10 after clear")
        self.assertEqual(c.queues["a@b.com"] , 0 , "queues len should be 0 after clear" )
        self.assertEqual(c.queuetotals["a@b.com"] , 10 , "queuetotals len should be 10 after clear" )
        
    def test_reachedExcessAmount(self):
        c = core.QueueMessageCounter()
        excessAmount = int(core.BaseMessageCounter.defaultValues["excessAmount"])
        msgs = [ QueueMessageCounterTest.MockMessage("a@b.com") , QueueMessageCounterTest.MockMessage("a@c.com") ]
        for msg in msgs:        
            for i in xrange(1, excessAmount * 2):
                c.incrementCount(msg)
                if i <= excessAmount:
                    self.assertFalse( c.reachedExcessAmount(msg), "reachedExcessAmount should be false if count %s <= %s" % ((i+1) , excessAmount) )
                else:
                    self.assertTrue( c.reachedExcessAmount(msg), "reachedExcessAmount should be true if count %i > %s" % ((i+1) , excessAmount) )
    
    def test_getCounts(self):
        c = core.QueueMessageCounter()
        msgs = [ QueueMessageCounterTest.MockMessage("a@b.com") , QueueMessageCounterTest.MockMessage("a@c.com") ]
        for msg in msgs:
            for i in xrange(10):
                c.incrementCount(msg)
        d = c.getCounts()
        self.assertEquals( d["total"] , 20 , "total in getCount should be 20")
        self.assertEquals( d["current"], 20, "current in getCount should be 20")
        self.assertEqual( d["a@b.com"]["total"], 10, "%s in getCount should be %s" % ("a@b.com - total", 10))
        self.assertEqual( d["a@b.com"]["current"], 10, "%s in getCount should be %s" % ("a@b.com - current", 10))
        self.assertEqual( d["a@c.com"]["total"], 10, "%s in getCount should be %s" % ("a@c.com - total", 10))
        self.assertEqual( d["a@c.com"]["current"], 10, "%s in getCount should be %s" % ("a@c.com - current", 10))
        c.clearCount()
        d = c.getCounts()
        self.assertEquals( d["total"] , 20 , "total in getCount should be 20")
        self.assertEquals( d["current"], 0, "current in getCount should be 0")
        self.assertEqual( d["a@b.com"]["total"], 10, "%s in getCount should be %s" % ("a@b.com - total", 10))
        self.assertEqual( d["a@b.com"]["current"], 0, "%s in getCount should be %s" % ("a@b.com - current", 0))
        self.assertEqual( d["a@c.com"]["total"], 10, "%s in getCount should be %s" % ("a@c.com - total", 10))
        self.assertEqual( d["a@c.com"]["current"], 0, "%s in getCount should be %s" % ("a@c.com - current", 0))

    def test_saveMsgLater_Single(self):
        c = core.QueueMessageCounter()
        c.saveMsgLater( QueueMessageCounterTest.MockMessage("a@b.com"), "/dev/null", "test text of really boring type/n" * 20 )
        self.assertEqual(len(c.mailQueues) , 1 , "mailQueues len should be 1 after save" )
        self.assertEqual(len(c.mailQueues["a@b.com"]), 1, "mailQueues len should be 1 after save" )
    
    def test_saveMsgLater_Mulitple(self):
        c = core.QueueMessageCounter()
        msgs = [ QueueMessageCounterTest.MockMessage("a@b.com") , QueueMessageCounterTest.MockMessage("a@c.com") ]
        for msg in msgs:
            for i in xrange(10):
                c.saveMsgLater( msg, "/dev/null", "test text of really boring type/n" * 20 )

        self.assertEqual(len(c.mailQueues) , 2 , "mailQueues len should be 2 after save.  len is %s" % len(c.mailQueues) )
        self.assertEqual(len(c.mailQueues["a@b.com"]), 10, "mailQueues len should be 10 after save" )
        self.assertEqual(len(c.mailQueues["a@c.com"]), 10, "mailQueues len should be 10 after save" )
     
    
    def test_clearMailQueue(self):
        c = core.QueueMessageCounter()
        msgs = [ QueueMessageCounterTest.MockMessage("a@b.com") , QueueMessageCounterTest.MockMessage("a@c.com") ]
        for msg in msgs:
            for i in xrange(10):
                c.saveMsgLater( msg, "/dev/null", "test text of really boring type/n" * 20 )

        c.clearMailQueue("a@b.com")
        self.assertEqual(len(c.mailQueues) , 2 , "mailQueues len should be 2 after clear.  len is %s" % len(c.mailQueues) )
        self.assertEqual(len(c.mailQueues["a@b.com"]), 0, "mailQueues len should be 0 after clear" )
        self.assertEqual(len(c.mailQueues["a@c.com"]), 10, "mailQueues len should be 10 after clear" )

    def test_sendMailQueue(self):
        c = core.QueueMessageCounter()
        
        global count
        count = 0

        def fakeWriteMsgToDisk(a, b):
            global count
            if a == "/dev/null" and b == "TestMsg-a@b.com":
                count += 1

        c.writeMsgToDisk = fakeWriteMsgToDisk
        msgs = [ QueueMessageCounterTest.MockMessage("a@b.com") , QueueMessageCounterTest.MockMessage("a@c.com") ]
        for msg in msgs:
            for i in xrange(10):
                c.saveMsgLater( msg, "/dev/null", "TestMsg-%s" % msg.FROM )
        
        c.sendMailQueue("a@b.com")
        self.assertEqual( count, 10, "writeMsgToDisk called %s should be called 10 times" % count )

        del count # Clean up count for everyone else

    def test_sendExcessEmailWithNoExcess(self):
        c = core.QueueMessageCounter()
        def raiseException(*args):
            raise Exception("createExcessEmail should not be called")
        c.createExcessEmail = raiseException
        lastSent = c.lastExcessEmailSent
        emailSent = c.sendExcessEmail([])
        self.assertFalse(emailSent, "An emtpy excess queue should not send an email")
        self.assertEqual(c.lastExcessEmailSent, lastSent, "lastExcessEmailSent should not change when an email is not sent")
    
    def test_sendExcessEmailWithExcess(self):
        c = core.QueueMessageCounter()
        c.createExcessEmail = lambda *args: "Test Msg"
        global count
        count = 0

        def fakeWriteMsgToDisk(a, b):
            global count
            if b == "Test Msg":
                count += 1

        c.writeMsgToDisk = fakeWriteMsgToDisk
        lastSent = c.lastExcessEmailSent
        emailSent = c.sendExcessEmail(["a@b.com"])
        self.assertTrue(emailSent, "An excess queue should send an email")
        self.assertEqual(count , 1, "WriteMsgToDisk should be called")
        self.assertTrue(c.lastExcessEmailSent != lastSent, "lastExcessEmailSent should change when an email is sent")
    
    def test_sendExcessEmailWithExcessButSentOneInLastMinTimeDelta(self):
        c = core.QueueMessageCounter()
        def raiseException(*args):
            raise Exception("function should not be called")
        c.createExcessEmail = raiseException
        c.writeMsgToDisk = raiseException
        c.notWithinExcessEmailTimeDelta = lambda *args: False
        lastSent = c.lastExcessEmailSent
        emailSent = c.sendExcessEmail(["a@b.com"])
        self.assertFalse(emailSent, "An emtpy excess queue should not send an email")
        self.assertEqual(c.lastExcessEmailSent, lastSent, "lastExcessEmailSent should not change when an email is not sent")

    def test_notWithinExcessEmailTimeDelta(self):
        #override datetime.today()
        oldclass = datetime.datetime

        class fakedatetime (datetime.datetime):
            
            @staticmethod
            def today():
                return datetime.datetime(2009, 10, 2, 13, 13, 0)

        core.datetime = fakedatetime
        c = core.QueueMessageCounter()
        val1 = c.notWithinExcessEmailTimeDelta() 
        timedelta = int(core.QueueMessageCounter.defaultValues["sendExcessEmailMinTimeDelta_s"])
        c.lastExcessEmailSent = datetime.datetime(2009, 10, 2, 13, 13, 0) 
        val2 = c.notWithinExcessEmailTimeDelta() 
        c.lastExcessEmailSent = datetime.datetime(2009, 10, 2, 13, 13, 0) - datetime.timedelta(seconds=(timedelta/2))
        val3 = c.notWithinExcessEmailTimeDelta() 
        c.lastExcessEmailSent = datetime.datetime(2009, 10, 2, 13, 13, 0) - datetime.timedelta(seconds=(timedelta))
        val4 = c.notWithinExcessEmailTimeDelta() 
        c.lastExcessEmailSent = datetime.datetime(2009, 10, 2, 13, 13, 0) - datetime.timedelta(seconds=(timedelta+1))
        val5 = c.notWithinExcessEmailTimeDelta() 
        
        
        #restore datetime.today()
        core.datetime = oldclass       

        self.assertTrue( val1 , "A new object should always return true" )
        self.assertFalse( val2 , "If lastExcessEmailSent == today should return false" )
        self.assertFalse( val3 , "If lastExcessEmailSent - today = 30s  should return false" )
        self.assertFalse( val4 , "If lastExcessEmailSent - today = 60s should return false" )
        self.assertTrue( val5 , "If lastExcessEmailSent - today = 61s should return true" )
        

def main():
    unittest.main()

if __name__ == "__main__":
    main()
