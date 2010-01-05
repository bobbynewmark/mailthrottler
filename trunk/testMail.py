#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009-10
# See LICENCE for details
"""
Basic tests for the mail server, to be used during development
"""
#Python BulitIns
import smtplib, time, threading, sys, random, datetime
from email.mime.text import MIMEText

fromaddr = sys.argv[1].split(",")
toaddr = sys.argv[2]
mailsToSend = 20
threadCount = 10
sleepBetweenSends=0.1
sustainedFloodForSeconds=60


def createMessage(fromaddr, toaddr, subject, msgtxt):
    msg = MIMEText(msgtxt)
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddr
    return msg

def sendMails(threadId):
    server = smtplib.SMTP('localhost', 8001)
    for i in xrange(mailsToSend):
        actualFrom = random.choice(fromaddr)
        server.sendmail(actualFrom, [toaddr], createMessage(actualFrom, toaddr, "This is from thread %s" % threadId, "Some header" ).as_string())
        
    server.quit()

def sendMailsFor(threadId):
    start = datetime.datetime.today()
    while ( datetime.datetime.today() - start ) < datetime.timedelta(seconds=sustainedFloodForSeconds):
        sendMails(threadId)
        if sleepBetweenSends:
            time.sleep(sleepBetweenSends)
    

threads = [threading.Thread(target=sendMailsFor, args=(i,)) for i in range(threadCount)]

for t in threads:
    t.start()

for t in threads:
    t.join()
     
    

