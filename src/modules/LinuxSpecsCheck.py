#This file is used to check the components of the host computer in both Windows and Linux

import psutil
import os

#return the size (in MiB) of the installed RAM in a Windows-based system
def maxRAM():
    return int((psutil.virtual_memory().total)/1048576)

def inventory()->str:
    return os.path.expanduser('~') + '/.vmware/inventory.vmls'

def preferences()->str:
    return os.path.expanduser('~') + '/.vmware/preferences.ini'

def isWorkstationInstalled():
    if os.path.exists("/usr/bin/vmware"):
        return True
    return False

def vmrunPath():
    return 'vmrun'