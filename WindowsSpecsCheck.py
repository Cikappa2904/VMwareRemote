#This file is used to check the components of the host computer in Windows

import subprocess


#return the size (in MiB) of the installed RAM in a Windows-based system
def maxRAM():
    result = subprocess.run(['wmic' ,'computersystem', 'get', 'totalphysicalmemory'], stdout=subprocess.PIPE)
    result = str(result.stdout)
    list = result.split('\\r\\r\\n')
    maxRAMSize = int(int(list[1])/1048576)
    return maxRAMSize

