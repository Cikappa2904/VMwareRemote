from importlib.resources import path
import subprocess
import os
import configparser
import platform
import zipfile
import shutil


tempFolder = os.environ['TEMP']

print('Installing pip (if not already installed): ')
# Installing pip
subprocess.run(['python3', '-m', 'ensurepip'])

# Installing Flask
print('Installing Flask, if not already installed')
subprocess.run(['python3', '-m', 'pip', 'install', 'flask'])

# Installing requests
print('Installing requests, if not already installed')
subprocess.run(['python3', '-m', 'pip', 'install', 'requests'])
import requests

if 'Linux' in platform.uname():
    hostOS = 'Linux'
    workstationPath = "/usr/bin/vmware"
    playerPath = "/usr/bin/vmplayer"
    pathSeparator = "/"
elif 'Windows' in platform.uname():
    hostOS = 'Windows' #Setting this variable here so calling functions is not needed again later in the program   
    workstationPath = os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Workstation\\vmware.exe"
    playerPath = os.environ['SYSTEMDRIVE'] + "\Program Files (x86)\VMware\VMware Player\\vmplayer.exe"
    pathSeparator = "\\"
else:
    raise Exception("Platform not supported: " + platform.uname())

config = configparser.ConfigParser()
config.add_section("VMware_Configuration")
def chooseBetweenProAndPlayer():
    while True:
        choice = input("It looks like you have both VMware Workstation Pro and VMware Workstation Player installed, would you like to use: \n1. VMware Workstation Pro \n2. VMware Workstation Player \n")
        if choice == 1:
            #config["VMware_Configuration"]["VMware_Version"] = "Pro"
            config.set("VMware_Configuration", "VMware_Version", "Pro")
            return choice
        elif choice == 2:
            #config["VMware_Configuration"]["VMware_Version"] = "Player"
            config.set("VMware_Configuration", "VMware_Version", "Player")
            return choice
        else:
            print(choice + " is not a valid option")

# Setting up the config file
if os.path.exists(workstationPath):
    chooseBetweenProAndPlayer()    
    config.set("VMware_Configuration", "VMware_Path", workstationPath)
elif os.path.exists(playerPath):
    #config["VMware_Configuration"]["VMware_Version"] = "Player"
    config.set("VMware_Configuration", "VMware_Version", "Player")
    config.set("VMware_Configuration", "VMware_Path", playerPath)
else:
    print("Unable to find your VMware installation. Maybe it's in a different path?: ")
    while True:
        installPath = input("Please insert a valid installation path for VMware Workstation Pro/Player")
        if (os.path.exists(installPath + "\\vmware.exe")):
            choice = chooseBetweenProAndPlayer()
            if choice == 1:
                #config["VMware_Configuration"]["VMware_Path"] = installPath + "\\vmware.exe"
                config.set("VMware_Configuration", "VMware_Path", installPath + "\\vmware.exe")
            else:
                #config["VMware_Configuration"]["VMware_Path"] = installPath + "\\vmplayer.exe"
                config.set("VMware_Configuration", "VMware_Path", installPath + "\\vmplayer.exe")
            break
        elif (os.path.exists(installPath + "\\vmplayer.exe")):
            #config["VMware_Configuration"]["VMware_Version"] = "Player"
            config.set("VMware_Configuration", "VMware_Version", "Player")
            break

# Downloading the repo from GitHub

if hostOS == 'Windows':
    installPath = input('Where do you want to install VMwareRemote? ("' + os.path.expanduser("~") + '\VMwareRemote")') or os.path.expanduser("~") + "\VMwareRemote"
    if installPath == os.path.expanduser("~") + "\VMwareRemote" and not os.path.exists (os.path.expanduser("~") + "\VMwareRemote"):
        os.mkdir (installPath)
elif hostOS == 'Linux':
    installPath = input('Where do you want to install VMwareRemote? ("' + os.getenv("HOME") + '/VMwareRemote")') or os.getenv("HOME") + '/VMwareRemote'
    if installPath == os.getenv("HOME") + '/VMwareRemote' and not os.path.exists(installPath):
        os.mkdir (installPath)

repoURL = "https://github.com/Cikappa2904/VMwareRemote/archive/development.zip"
r = requests.get(repoURL, allow_redirects=True)
open(tempFolder + pathSeparator + 'VMwareRemote.zip', 'wb').write(r.content)
with zipfile.ZipFile(tempFolder + pathSeparator +'VMwareRemote.zip',"r") as zip_ref:
    zip_ref.extractall(tempFolder)

    source_dir = tempFolder + pathSeparator + "VMwareRemote-development"
    target_dir = installPath
        
    file_names = os.listdir(source_dir)
        
    for file_name in file_names:
        shutil.move(os.path.join(source_dir, file_name), target_dir)

with open(installPath + pathSeparator + "config.ini", 'w') as configfile:    # save
    config.write(configfile)

print("Installation completed. You may now run the start script from the installation folder.")