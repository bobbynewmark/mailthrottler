#Details of the configuration settings for the application

# Introduction #

These are the configuration settings that are used in the application.

At any time you can see the current configuration of the application by clicking on the "View Current Config" link on the home page of the admin console.

The configuration file is in a basic ini format.  With the sections being each of the headings below.

For example:

```
[BaseMessageCounter]
excessAmount:10
```

# Details #
## Core ##
  * saveFilePath
> > (path) This is the path that is use to save messages to then it is trying send them
  * templatePath
> > (path) This is the full path to the templates directory
> > this path should contain the contents of \templates
## BaseMessageCounter ##
  * excessAmount
> > (int) This is the amount the queues must exceed before a flood is registered
## LocalDelivery ##
  * clearAfter
> > (float) This is the time in seconds after which to clear the counts in any queues
## MTDaemon ##
  * webInterface
> > (string) the IP address to listen on for the Admin Console.  blank for all IPs
  * webPort
> > (int) the port for the admin console to listen on
  * mailInterface
> > (string) the IP address to listen on for the SMTP service.  blank for all IPs
  * mailPort
> > (int) The port to listen on for the SMTP service
## RollingMemoryHandler ##
  * logSize
> > (int) the amount of log entries to keep in memory for display on the Admin Console
## QueueMessageCounter ##
  * excessMailFrom
> > (email address) the email address to use as the from in the excess email
  * excessMailTo
> > (email address) the email address to send the excess email to
  * sendExcessEmailMinTimeDelta\_s
> > (int) the amount of seconds between each excess email
## WindowsMT ##
  * logFilePath
> > (path) the path to the file for the log
  * logBackupCount
> > (int) the amount of logs files to keep (they roll at midnight)