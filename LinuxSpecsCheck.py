#This file is used to check the components of the host computer in both Windows and Linux

import psutil

#return the size (in MiB) of the installed RAM in a Windows-based system
def maxRAM():
    return int((psutil.virtual_memory().total)/1048576)

