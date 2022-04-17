from calendar import c
from flask import Flask, render_template, request
import re
import os
import subprocess

app = Flask(__name__)

cpuSpecs = []
RAMSpecs = []
biosType = []
vmPathList = []
vncPorts = []
vmNames = []

vmrunPath = '' 

#vmrun.exe has a different path based on if VMware is Workstation or Player
if os.path.exists('C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'):
    vmrunPath = 'C:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe'
elif os.path.exists('C:\Program Files (x86)\VMware\VMware Player\\vmrun.exe'):
    vmrunPath = 'C:\Program Files (x86)\VMware\VMware Player\\vmrun.exe'

#Checks for a specific line and gives everything that comes next to the given part of the string
def CheckForSpecs(specString, txt):
    for line in txt:
        vmSpec = ''
        if specString in line:
            line = line.replace(specString, "")
            for letter in line:
                if letter != '"':
                    vmSpec+=letter
                else:
                    break
            return vmSpec

def GetSlicedVMXPath(path):
    for match in re.finditer(' = "', path):
        slicePosition = match.end()
        slicedPath = path[slicePosition:]
        slicedPath = slicedPath.replace('"\n', "")
    return slicedPath

def SearchVMsInFileWorkstation(txt):
    vmList = ''
    for line in txt:
        lineToSearch = '.config = "'
        lineNotToSearch = '.config = ""'
        if lineToSearch in line and lineNotToSearch not in line and not(re.search('folder.', line)):
            vmPathList.append(GetSlicedVMXPath(line))
            sliceIndex = 0
            for match in re.finditer('.vmx', line):
                vmxPosition = match.start()
                slicedLine = line[:vmxPosition]
                i = 0
                for letter in slicedLine:
                    if slicedLine[-i] == "\\":
                        sliceIndex = -i
                        break
                    i+=1
            vmList+=slicedLine[sliceIndex:]
            vmList+="    "
    
    return vmList

def SearchVMsInFilePlayer(txt):
    vmList = ''
    for line in txt:
        lineToSearch = '.filename = "'
        if lineToSearch in line:
            vmPathList.append(GetSlicedVMXPath(line))
            sliceIndex = 0
            for match in re.finditer('.vmx', line):
                vmxPosition = match.start()
                slicedLine = line[:vmxPosition]
                i = 0
                for letter in slicedLine:
                    if slicedLine[-i] == "\\":
                        sliceIndex = -i
                        break
                    i+=1
            vmList+=slicedLine[sliceIndex:]
            vmList+="    "
    
    return vmList


@app.route("/")
def main():

    global cpuSpecs, RAMSpecs, biosType, vmPathList, vncPorts, vmrunPath

    #Clearing the content of the arrays in case of a reload of the page since this are global arrays
    cpuSpecs.clear()
    RAMSpecs.clear()
    biosType.clear()
    vmPathList.clear()
    vncPorts.clear()
    vmList = ''


    #TODO: Do this in a decent way


    appDataPath = os.getenv('APPDATA') + "\VMware\inventory.vmls"
    if os.path.exists(appDataPath):
        f = open(appDataPath)
        txt = f.readlines()
        vmList+=SearchVMsInFileWorkstation(txt)
        f.close()

    appDataPath = os.getenv('APPDATA') + "\VMware\preferences.ini"
    if os.path.exists(appDataPath):
        f = open(appDataPath)
        txt = f.readlines()
        vmList+=SearchVMsInFilePlayer(txt)
        f.close()
    
    for path in vmPathList:
        f = open(path)
        txt = f.readlines()

        #VMware .vmx files don't have the 'numvcpus=' line when the VM only has 1 core, so we say the VM only has 1 core when we don't find that line
        coreNumber = CheckForSpecs('numvcpus = "', txt)
        if coreNumber!=None:
            cpuSpecs.append(coreNumber)
        else:
            cpuSpecs.append('1')

        RAMSpecs.append(CheckForSpecs('memsize = "', txt))
        vmNames.append(CheckForSpecs('displayName = "', txt))

        #VMware .vmx files don't have the 'firmware=' line when the VM is legacy, so we say the VM is legacy when we don't find that line
        isEFI = CheckForSpecs('firmware = "', txt)
        if isEFI=='efi':
            biosType.append('efi')
        else:
            biosType.append('legacy')

        #VMware .vmx files don't have the 'RemoteDisplay.vnc.port =' line when using the default port 5900
        vncPort = CheckForSpecs('RemoteDisplay.vnc.port = "', txt)
        if CheckForSpecs('RemoteDisplay.vnc.enabled = "', txt) == 'TRUE':
            if vncPort == None:
                vncPorts.append('5900')
            elif vncPorts != None:
                vncPorts.append(vncPort)
        else:
            vncPorts.append(None)
        f.close()

    return render_template("list.html", vmList=vmList)


@app.route("/specs.html")
def specs():
    global cpuSpecs, RAMSpecs, vncPorts, vmrunPath
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    isON = None
    #Checking if the VM is running based on the output of 'vmrun list'
    print(vmrunPath)
    if vmrunPath!='':
        isON = False
        result = subprocess.run([vmrunPath ,'list'], stdout=subprocess.PIPE)
        result = str(result.stdout)
        list = result.split('\\r\\n')
        for item in list:
            item = item.encode().decode('unicode_escape') #get rid of // 
            if item == vmPathList[x]:
                isON = True
        
    return render_template("specs.html", cpuSpecs1=cpuSpecs[x], RAMSpecs1=RAMSpecs[x], biosType1=biosType[x], vmPath1=vmPathList[x], vmNumber=vmNumber, vncPort=vncPorts[x], vmName=vmNames[x], isON=str(isON))

@app.route("/runVM")
def runVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    if vmrunPath != '':
        subprocess.run([vmrunPath, 'start', vmPathList[x]])
        return 'VM Run'
    else:
        return 'VM not run'

@app.route("/stopVM")
def stopVM():
    vmNumber = request.args.get("vmNumber")
    x = int(vmNumber)
    if vmrunPath != '':
        print(vmrunPath)
        subprocess.run([vmrunPath, 'stop', vmPathList[x]])
        return 'VM Stop'
    else:
        return 'VM not Stop'

@app.route("/edit.html")
def editPage():
    vmNumber = request.args.get("vmNumber")
    return render_template("edit.html", vmNumber=vmNumber)



@app.route("/editVM", methods=['POST'])
def editVM():
    if request.method == 'POST':
        vmNumber = request.form.get('vmNumber')
        cpuCores = request.form.get('cpuCores')
        ram = request.form.get('ram')
        vncEnabled = request.form.get('vncEnabled')
        print(vmNumber)
        
        return '<script>window.location.href = "/";</script>'