#!/usr/local/bin/python
import smtplib, time, threading, sys, random, datetime, os, urllib
from email.mime.text import MIMEText

maildroplocation = "maildrop"
fromAddr = "abi@ssgl.com"
fromAddrs = ["abi1@ssgl.com", "abi2@ssgl.com" ,"abi3@ssgl.com"]
toAddr = "ac@ssgl.com"
msgBody = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed fermentum posuere diam vel venenatis.
Mauris sed diam lectus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.
Nunc ut lacus in nunc fringilla ullamcorper nec id dolor. Suspendisse ut nulla ut risus viverra fermentum eu sit amet neque.
Nam tincidunt tempus tempus. Sed sollicitudin sapien eget justo lacinia tincidunt. Quisque ultrices euismod ornare.
Ut at ante orci. Quisque congue porta odio sit amet interdum. Nulla auctor fringilla leo, et pharetra diam vestibulum vel.
Pellentesque nec sagittis purus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus justo nibh, egestas eget fermentum id, luctus a turpis."""
msgSubject = "Test"
sleepTime = 5.0

def createMessage(fromaddr, toaddr, subject, msgtxt):
    msg = MIMEText(msgtxt)
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddr
    return msg

def sendMail(fromaddr, toaddr, msg):
    server = smtplib.SMTP('localhost', 8001)
    server.sendmail(fromaddr, [toaddr], msg.as_string())
    server.quit()

def cleanUpMailDrop():
    for fp in os.listdir(maildroplocation):
        os.remove( os.path.join( maildroplocation, fp ) )
               
def checkFileExists(numberToCheckFor=1):
    return len(os.listdir(maildroplocation)) == numberToCheckFor

def forceClear():
    urllib.urlopen("http://127.0.0.1:8080/forceclear")


def test_delayInSend():
    """Tests that there is a delay in sending the emails 
    """
    msg = createMessage(fromAddr, toAddr, msgSubject, msgBody)
    cleanUpMailDrop()
    sendMail(fromAddr, toAddr, msg)
    if checkFileExists():
        print "TEST CASE - BAD"
    time.sleep(sleepTime)
    if checkFileExists():
        print "TEST CASE - OK"
    else:
        print "TEST CASE - BAD"
    cleanUpMailDrop()

def test_sendsEmailsWhenLessThanOverflow():
    """Tests that if we send 19 emails in a second then it does not drop any
    """
    msg = createMessage(fromAddr, toAddr, msgSubject, msgBody)
    cleanUpMailDrop()
    for i in xrange(19):
        sendMail(fromAddr, toAddr, msg)
    time.sleep(sleepTime)
    if checkFileExists(19):
        print "TEST CASE - OK"
    else:
        print "TEST CASE - BAD"
    cleanUpMailDrop()

def test_sendsExcessEmailWhenMoreThanOverflow():
    """Tests that if we send 21 emails in a second then it drops them and only sends a excess email
    """
    msg = createMessage(fromAddr, toAddr, msgSubject, msgBody)
    cleanUpMailDrop()
    for i in xrange(21):
        sendMail(fromAddr, toAddr, msg)
    time.sleep(sleepTime)
    if checkFileExists(1):
        print "TEST CASE - OK"
    else:
        print "TEST CASE - BAD"
    cleanUpMailDrop()

def test_sendsExcessEmailWhenMoreThanOverflowForProlongedPeriod():
    """Tests that if we send lots of emails over a large period then it drops them and only sends a excess email
    """
    
    msg = createMessage(fromAddr, toAddr, msgSubject, msgBody)
    cleanUpMailDrop()
    begin = datetime.datetime.today()
    forceClear()
    for i in xrange(9):
        for i in xrange(21):
            sendMail(fromAddr, toAddr, msg)
        time.sleep(1)
    time.sleep(sleepTime)
    forceClear()
    end = datetime.datetime.today()
    #print end - begin    
    if checkFileExists(1):
        print "TEST CASE - OK"
    else:
        print "TEST CASE - BAD"
    cleanUpMailDrop()

def test_sendsExcessEmailWhenMoreThanOverflowWithMultipleFroms():
    """Tests that if we send 21 emails from different uses in a second then it drops them and only sends a excess email
    """
    cleanUpMailDrop()
    for fromAddr in fromAddrs:
        msg = createMessage(fromAddr, toAddr, msgSubject, msgBody)
        for i in xrange(21):
            sendMail(fromAddr, toAddr, msg)
    time.sleep(sleepTime)
    if checkFileExists(1):
        print "TEST CASE - OK"
    else:
        print "TEST CASE - BAD"
    cleanUpMailDrop()




def main():
    funs = [globals()[f] for f in globals().keys() if f.startswith("test_")]
    for fun in funs:
        time.sleep(sleepTime)
        print "*" *10 , fun.__name__ , "*" * 10
        print fun.__doc__
        fun()   
    

if __name__ == "__main__":
    main()

