#This file is used to check the components of the host computer in Windows

import subprocess
import os


#return the size (in MiB) of the installed RAM in a Windows-based system
def maxRAM():
    result = subprocess.run(['wmic' ,'computersystem', 'get', 'totalphysicalmemory'], stdout=subprocess.PIPE)
    result = str(result.stdout)
    list = result.split('\\r\\r\\n')
    maxRAMSize = int(int(list[1])/1048576)
    return maxRAMSize

def inventory():
    return os.getenv('APPDATA') + "\VMware\inventory.vmls"

def preferences()->str:
    return os.getenv('APPDATA') + "\VMware\preferences.ini"


def isWorkstationInstalled():
    #vmrun.exe has a different path based on if VMware is Workstation or Player
    if os.path.isdir('C:\Program Files (x86)\VMware\VMware Workstation'):
        return True
    return False

def vmrunPath():
    if isWorkstationInstalled():
        return os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe"
    return os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Player\\vmrun.exe"

def pathSeparator():
    return '\\'

def vmwarePath():
    if isWorkstationInstalled():
        return os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Workstation\\vmware.exe"
    return os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Player\\vmplayer.exe"

def workstationPath() -> str:
    return os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Workstation\\vmware.exe"

