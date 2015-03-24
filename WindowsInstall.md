# Introduction #

Basic install instructions for a windows box

Last followed 18/12/09

# Details #

Current install instructions:
  1. Install python 2.6
    1. Download python-2.6.4.msi
    1. Run installer.  Choose to install to c:\python\26
  1. Install genshi
    1. Download Genshi-0.5.1.win32-py2.6.exe
    1. Run installer.
  1. Install Twisted
    1. Download Twisted-9.0.0.win32-py2.6.exe
    1. Run installer
  1. Install Win32 extensions
    1. Download pywin32-214.win32-py2.6.exe
    1. Run installer
  1. Copy the source code to a directory
  1. Run `mtWindowsServer` to install the service
  1. Configure the service as required
    1. Rememeber the service uses the `mailThrottler.ini` in the same directory as a config file
  1. Run !