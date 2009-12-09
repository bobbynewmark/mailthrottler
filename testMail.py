#!/usr/local/bin/python
import smtplib, time, threading, sys
from email.mime.text import MIMEText

fromaddr = sys.argv[1]
toaddr = sys.argv[2]


def createMessage(fromaddr, toaddr, subject, msgtxt):
    msg = MIMEText(msgtxt)
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddr
    return msg

def sendMails(threadId):
    server = smtplib.SMTP('localhost', 8001)
    for i in xrange(25):
        server.sendmail(fromaddr, [toaddr], createMessage(fromaddr, toaddr, "This is from thread %s" % threadId, "Some header" ).as_string())
    server.quit()

threads = [threading.Thread(target=sendMails, args=(i,)) for i in range(10)]

for t in threads:
    t.start()

for t in threads:
    t.join()
     
    

