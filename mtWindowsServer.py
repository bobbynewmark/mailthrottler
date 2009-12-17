#!/usr/local/bin/python
# Copyright (c) Andrew Cox 2009
# See LICENCE for details
"""
This runs the mail throttler as a window service
Base code for the service is taken from http://code.activestate.com/recipes/551780/
"""
#Internal Modules
from mailThrottler import MTDaemon
from core import _config
#Python BulitIns
from os.path import splitext, abspath
from sys import modules, argv
import logging
from logging.handlers import TimedRotatingFileHandler
#External Modules
import win32serviceutil
import win32service
import win32event
import win32api

class Service(win32serviceutil.ServiceFramework):
    _svc_name_ = '_unNamed'
    _svc_display_name_ = '_Service Template'
    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.log('init')
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
    
    def log(self, msg):
        import servicemanager
        servicemanager.LogInfoMsg(str(msg))
    
    def sleep(self, sec):
            win32api.Sleep(sec*1000, True)
	
    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log('start')
            self.start()
            self.log('wait')
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            self.log('done')
        except Exception, x:
            self.log('Exception : %s' % x)
            self.SvcStop()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.log('stopping')
        self.stop()
        self.log('stopped')
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
    
    # to be overridden
    def start(self): pass
    # to be overridden
    def stop(self): pass

def instart(cls, name, display_name=None, stay_alive=True):
    '''
    Install and  Start (auto) a Service
    
    cls : the class (derived from Service) that implement the Service
    name : Service name
    display_name : the name displayed in the service manager
    stay_alive : Service will stop on logout if False
    '''
    cls._svc_name_ = name
    cls._svc_display_name_ = display_name or name
    try:
        module_path=modules[cls.__module__].__file__
    except AttributeError:
        # maybe py2exe went by
        from sys import executable
        module_path=executable
    module_file=splitext(abspath(module_path))[0]
    cls._svc_reg_class_ = '%s.%s' % (module_file, cls.__name__)
    if stay_alive: 
        win32api.SetConsoleCtrlHandler(lambda x: True, True)
    try:
        win32serviceutil.InstallService(
            cls._svc_reg_class_,
            cls._svc_name_,
            cls._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START
            )
        print "Install ok"
        win32serviceutil.StartService(
            cls._svc_name_
            )
        print 'Start ok'
    except Exception, x:
        print str(x)

class WindowsMT(Service):
    
    defaultValues = { "logFilePath": "logfiles/mailthrotter.log", "logBackupCount" : "5" }
    _config.importDefaults("WindowsMT", defaultValues)

    
    def start(self):
        filepath = ""
        filepath = splitext(modules[MTDaemon.__module__].__file__)[0] + ".ini"
        self.daemon = MTDaemon(filepath)
        #Attach rolling file logger
        log = TimedRotatingFileHandler( _config.get("WindowsMT", "logFilePath") , when='midnight', backupCount=_config.getint("WindowsMT", "logBackupCount"))
        log.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        log.setFormatter(formatter)
        logging.getLogger("").addHandler(log)
        self.daemon.start()

    def stop(self):
        self.daemon.stop()
        del(self.daemon)

instart(WindowsMT, 'MailThrotter', 'MailThrotter python service')
